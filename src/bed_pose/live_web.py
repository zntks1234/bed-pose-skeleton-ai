"""Loopback HTML workspace. Cameras, inference and records remain in Python."""
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import json
import hashlib
from copy import deepcopy
import math
from pathlib import Path
import queue
import secrets
import tempfile
import threading
import time
from urllib.parse import parse_qs, urlsplit
import uuid
import webbrowser
from .preview_worker import PreviewWorker
from .live_engine import LiveWorker
from .group_session import MeasurementGroup
from .live_factory import make_engine
from .live_sources import CameraSource, SyntheticSource, VideoFileSource, probe_cameras, named_cameras
from .io_utils import strict_loads
from .preview_quality import encode_preview, PROFILES as PREVIEW_PROFILES, DEFAULT as PREVIEW_DEFAULT


@dataclass
class Session:
    id: str
    title: str
    kind: str
    worker: LiveWorker
    state: dict = field(default_factory=dict)
    view: dict | None = None
    sequence: int = 0
    remove: bool = False
    preview_frame: dict | None = None
    preview_worker: object | None = None
    preview_generation: int = 0
    displayed_generation: int = -1
    preview_epoch: int = 0
    raw_worker: object | None = None
    raw_view: object | None = None
    raw_sequence: int = -1
    raw_requested_until: float = 0
    raw_quality: str | None = None
    settings_sources: tuple | None = None
    settings_bundle: dict | None = None
    settings_key: str | None = None
    preview_rgb: object | None = None  # One current frame per input, RAM only.


class WebWorkspace:
    def __init__(self, model=None, output_root=Path('recordings/live'), *, engine_factory=make_engine,
                 clip_model=None, clip_device='auto', clip_state_min=.5, clip_direction_min=.5):
        self.model = Path(model or 'checkpoints/pose_landmarker_full.task').resolve()
        self.output_root = Path(output_root).resolve()
        from .record_library import RecordLibrary
        self.records=RecordLibrary(self.output_root)
        self.temp = tempfile.TemporaryDirectory(prefix='bed-pose-browser-')
        self.temp_root = Path(self.temp.name)
        self.factory = engine_factory
        from .clip_assets import DEFAULT_DIRECTORY,read_assets
        from .clip_posture import policy,resolve_device
        from importlib.metadata import version,PackageNotFoundError
        if clip_device not in ('auto','cpu','cuda'):raise ValueError('CLIP 실행 장치를 확인하세요.')
        policy(clip_state_min,clip_direction_min,'cpu' if clip_device=='auto' else clip_device)
        self.clip_model=Path(clip_model or DEFAULT_DIRECTORY).expanduser().resolve()
        self.clip_options={'clip_model':self.clip_model,'clip_device':clip_device,
                           'clip_state_min':clip_state_min,'clip_direction_min':clip_direction_min}
        try:
            read_assets(self.clip_model)
            for package in ('torch','transformers','Pillow'):version(package)
            self.clip_options['clip_device']=resolve_device(clip_device)
            self.clip_status={'available':True,'reason':None}
        except (ValueError,OSError,ImportError,PackageNotFoundError):
            self.clip_status={'available':False,'reason':'CLIP 준비 필요: python -m pip install -e ".[clip]" 후 python -m bed_pose clip-setup 실행'}
        self.sessions, self.assets = {}, {}
        self.groups = {}
        self.target_tickets = {}
        self.lock = threading.RLock()
        self.quality_lock=threading.Lock()
        self.quality_epoch=0
        self.preview_quality = PREVIEW_DEFAULT
        self.stop_requested = threading.Event()
        self.monitor_stop = threading.Event()
        self.scan_state = {'busy': False, 'indices': [], 'error': None}
        self.monitor = threading.Thread(target=self._monitor, daemon=True)
        self.monitor.start()

    def register_asset(self, path, kind, name):
        asset_id = uuid.uuid4().hex
        with self.lock:
            self.assets[asset_id] = {'path': Path(path), 'kind': kind, 'name': name[:200]}
        return {'asset_id': asset_id, 'name': name[:200], 'kind': kind}

    def add(self, values):
        with self.lock:
            if self.stop_requested.is_set():
                raise ValueError('작업실을 종료하고 있습니다.')
            kind = values.get('kind')
            model = self.model
            if values.get('model_asset'):
                if values['model_asset'] not in self.assets:
                    raise ValueError('모델 파일을 다시 선택하세요.')
                asset = self.assets[values['model_asset']]
                if asset['kind'] != 'model':
                    raise ValueError('모델 파일을 다시 선택하세요.')
                model = asset['path']
            if kind == 'camera':
                index = values.get('camera')
                if type(index) is not int or index < 0:
                    raise ValueError('카메라 번호는 0 이상의 정수여야 합니다.')
                if self.scan_state['busy']:
                    raise ValueError('장치 확인이 끝난 뒤 연결하세요.')
                if any(s.kind == 'camera' and not s.state['closed'] and s.worker.engine.source.index == index
                       for s in self.sessions.values()):
                    raise ValueError('이미 연결한 카메라입니다. 기존 입력을 선택하세요.')
                capture=values.get('camera_settings',{})
                if not isinstance(capture,dict) or set(capture)-{'resolution','fps'}:
                    raise ValueError('카메라 입력 설정을 확인하세요.')
                source = CameraSource(index,**capture)
                title = next((d['name'] for d in self.scan_state.get('devices', []) if d['index'] == index), f'카메라 {index} · 이름 미확인')
            elif kind == 'video_file':
                if values.get('video_asset') not in self.assets:
                    raise ValueError('촬영 영상 파일을 먼저 선택하세요.')
                asset = self.assets[values['video_asset']]
                if asset['kind'] != 'video':
                    raise ValueError('영상 파일을 다시 선택하세요.')
                source, title = VideoFileSource(asset['path']), asset['name']
            elif kind == 'demo':
                source, title = SyntheticSource(), '합성 입력 · 실제 인식 아님'
            else:
                raise ValueError('입력 종류를 선택하세요.')
            silhouette=values.get('silhouette',False)
            if type(silhouette) is not bool:raise ValueError('실루엣 분석 사용 여부를 확인하세요.')
            use_clip=values.get('use_clip',self.clip_status['available'] and kind!='demo')
            if type(use_clip) is not bool:raise ValueError('CLIP 사용 여부를 확인하세요.')
            if use_clip and (kind=='demo' or not self.clip_status['available']):
                raise ValueError(self.clip_status['reason'] or '합성 입력에는 실제 CLIP을 적용하지 않습니다.')
            engine = self.factory(source, model, self.output_root, self.temp_root, demo=kind == 'demo',
                                  **(self.clip_options if use_clip else {}), **({'silhouette':True} if silhouette else {}))
            worker = LiveWorker(engine)
            session_id = uuid.uuid4().hex
            state = {'id': session_id, 'title': title, 'kind': kind, 'phase': 'opening',
                     'closed': False, 'recording': False, 'pending': None, 'region': None,
                     'paused': kind == 'video_file', 'frame_id': None, 'sequence': 0,
                     'candidate_count': None, 'recorded_frames': 0, 'elapsed': 0,
                     'media_seconds': None, 'directory': None, 'integrity': None, 'error': None, 'preview_error': None,
                     'width': None, 'height': None, 'posture': 'not_implemented', 'posture_assessment': None,
                     'posture_model_id':engine.posture_classifier.model_id if engine.posture_classifier else None,
                     'automatic_posture_profile':engine.posture_classifier.profile if engine.posture_classifier else None,
                     'body_state_provider_profile':engine.body_state_profile, 'silhouette_enabled':silhouette}
            self.sessions[session_id] = Session(session_id, title, kind, worker, state)
            session=self.sessions[session_id]
            session.preview_worker=PreviewWorker(lambda rgb,quality:encode_preview(rgb,quality),
                lambda job,result,error:self._preview_ready(session,job,result,error))
            if getattr(engine.source,"latest_camera",False):
                session.raw_worker=PreviewWorker(lambda rgb,quality:encode_preview(rgb,quality),
                    lambda job,result,error:self._raw_ready(session,job,result,error))
            worker.start()
            return {'id': session_id}

    def snapshot(self, compact=False, known_profiles=()):
        with self.lock:
            sessions=[];profiles={}
            fixed=('automatic_posture_profile','body_state_provider_profile','posture_reference_profile')
            for session in self.sessions.values():
                if not compact:
                    sessions.append(session.state)
                    continue
                sources=tuple((k in session.state,session.state.get(k)) for k in fixed)
                if session.settings_sources is None or any(a[0]!=b[0] or a[1] is not b[1] for a,b in zip(sources,session.settings_sources)):
                    from .io_utils import object_hash
                    session.settings_sources=sources
                    session.settings_bundle=deepcopy({k:session.state[k] for k in fixed if k in session.state})
                    session.settings_key=object_hash(session.settings_bundle)
                sessions.append(dict({k:v for k,v in session.state.items() if k not in fixed},settings_key=session.settings_key))
                if session.settings_key not in known_profiles:profiles[session.settings_key]=session.settings_bundle
            result={'sessions':sessions,'groups':[g.public() for g in self.groups.values()],
                    'scan':self.scan_state,'closing':self.stop_requested.is_set(),
                    'preview_quality':self.preview_quality,'model':self.model.name,
                    'model_available':self.model.is_file(),'clip':self.clip_status}
            if compact:result['profiles']=profiles
            # Detach mutable values once; HTTP performs the single JSON serialization.
            return deepcopy(result)

    def set_preview_quality(self, quality):
        if not isinstance(quality,str) or quality not in PREVIEW_PROFILES:
            raise ValueError('표준 또는 고화질 표시를 선택하세요.')
        # Serialize quality commands, without holding the workspace lock while encoding.
        with self.quality_lock:
            with self.lock:
                if self.stop_requested.is_set():raise ValueError('작업실을 종료하고 있습니다.')
                jobs=[(session,self._preview_job(session,quality)) for session in self.sessions.values()
                      if session.preview_frame is not None]
            updates=[(session,job,encode_preview(job['frame']['rgb'],quality)) for session,job in jobs]
            with self.lock:
                if self.stop_requested.is_set():raise ValueError('작업실을 종료하고 있습니다.')
                self.preview_quality=quality;self.quality_epoch+=1
                for session,job,result in updates:
                    job=dict(job,quality_epoch=self.quality_epoch)
                    self._preview_ready(session,job,result,False)
                # A moving source may have advanced during the quality change.
                for session in self.sessions.values():
                    if session.preview_frame is not None:
                        session.preview_worker.submit(self._preview_job(session,quality))
                return {'quality':quality,**PREVIEW_PROFILES[quality]}

    def _preview_job(self,session,quality=None):
        return {'frame':session.preview_frame,'generation':session.preview_generation,
                'epoch':session.preview_epoch,'quality_epoch':self.quality_epoch,
                'quality':quality or self.preview_quality}

    def _preview_ready(self,session,job,result,error):
        with self.lock:
            if (self.stop_requested.is_set() or self.sessions.get(session.id) is not session
                    or session.state['phase']=='error' or job['epoch']!=session.preview_epoch
                    or job['quality_epoch']!=self.quality_epoch
                    or job['generation']<session.displayed_generation):return
            self._publish_preview(session,job['frame'],result,error)
            session.displayed_generation=job['generation']

    def capture_target(self, session_id):
        with self.lock:
            session=self.sessions[session_id]
            if session.state['closed'] or not session.view or not session.view.get('image') or not session.view['people']:
                raise ValueError('선택할 관절 후보가 없습니다. 입력을 확인하세요.')
            ticket=uuid.uuid4().hex
            capture=json.loads(json.dumps(session.view))
            capture.update(ticket=ticket,input_id=session_id,stream_id=session.worker.engine.stream_id)
            # Retain bounded frozen selections; pictures stay in RAM only.
            for old in [key for key,value in self.target_tickets.items() if value['input_id']==session_id][:-3]:
                self.target_tickets.pop(old,None)
            self.target_tickets[ticket]=capture
            return capture

    def select_target(self, values):
        with self.lock:
            capture=self.target_tickets.get(values.get('ticket'))
            if not capture:raise ValueError('대상 선택 창을 다시 여세요.')
            session=self.sessions[capture['input_id']]
            group=self.active_group(session.id)
            if group is not None and group.data['phase'] not in ('preparing','recording'):raise ValueError('그룹 시작/정리 완료 후 대상을 지정하세요.')
            candidate=next((p for p in capture['people'] if p['candidate_id']==values.get('candidate_id')),None)
            if session.state['closed'] or candidate is None:raise ValueError('선택할 후보를 확인하세요.')
            from .target_tracking import TrackingConfig
            from dataclasses import asdict
            config=asdict(TrackingConfig.load(values.get('tracking_config')))
            selection_id=uuid.uuid4().hex
            session.state['target_selection_pending']=selection_id
            session.state['target_selection_error']=None
            session.state['error']=None
            session.worker.submit('target_select',frame_id=capture['frame_id'],candidate_id=candidate['candidate_id'],config=config,selection_id=selection_id)
            return {'accepted':True,'selection_id':selection_id}

    def group_command(self, values):
        with self.lock:
            if self.stop_requested.is_set():raise ValueError('작업실 종료 중입니다.')
            if values['action']=='start':
                ids=values.get('inputs')
                if not isinstance(ids,list) or len(ids)!=2 or len(set(ids))!=2:
                    raise ValueError('서로 다른 입력 두 개를 선택하세요.')
                members=[self.sessions[sid] for sid in ids]
                if len({s.kind for s in members})!=1:
                    raise ValueError('카메라끼리 또는 영상 파일끼리 묶으세요.')
                for session in members:
                    if (session.state['closed'] or session.worker.stop_requested.is_set() or session.state['phase']=='closing' or session.state['pending']
                            or session.state['recording'] or session.state['frame_id'] is None or not session.state['region']
                            or self.active_group(session.id)):
                        raise ValueError('두 입력의 연결과 침대 영역을 준비하고 개별 측정을 종료하세요.')
                tolerance=values.get('max_skew_ms')
                if tolerance is not None and (type(tolerance) not in (int,float) or not math.isfinite(tolerance) or tolerance<0 or not math.isfinite(tolerance*1_000_000)):
                    raise ValueError('허용 시간 차이에 0 이상의 유한한 ms 값을 입력하세요.')
                selections=values.get('target_selections')
                targets=[]
                if selections is not None:
                    if not isinstance(selections,list) or len(selections)!=2 or values.get('same_person_confirmed') is not True:
                        raise ValueError('양쪽 대상을 지정하고 동일인 지정을 확인하세요.')
                    for session,selection in zip(members,selections):
                        if not isinstance(selection,dict):raise ValueError('대상 지정 형식을 확인하세요.')
                        if not session.view or not session.view['people']:raise ValueError('대상이 검출되지 않습니다. 다시 지정하세요.')
                        capture=self.target_tickets.get(selection.get('ticket'))
                        if not capture or capture['input_id']!=session.id or capture['stream_id']!=session.worker.engine.stream_id:
                            raise ValueError('입력에 맞춰 대상을 다시 지정하세요.')
                        candidate=next((p for p in capture['people'] if p['candidate_id']==selection.get('candidate_id')),None)
                        if candidate is None:raise ValueError('선택한 관절 후보를 확인하세요.')
                        tracking=session.worker.engine.target_tracker.current()
                        if values.get('tracking_required') is True and (tracking.get('segment_start_frame_id')!=capture['frame_id']
                                or tracking.get('seed_candidate_id')!=candidate['candidate_id']):
                            raise ValueError('선택한 후보에 맞춰 추적 대상을 다시 적용하세요.')
                        targets.append({'input_id':session.id,'stream_id':capture['stream_id'],
                                        'selected_frame_id':capture['frame_id'],'candidate_id':candidate['candidate_id'],
                                        'clock_id':capture['clock_id'],'received_ns':capture['received_ns'],
                                        'width':capture['width'],'height':capture['height'],
                                        'candidate_snapshot':candidate,'selection_method':'operator_frozen_preview',
                                        'tracking_at_group_start':session.worker.engine.target_tracker.current()})
                if values.get('tracking_required') is True and any(s.worker.engine.target_tracker.current()['status']!='tracking_provisional' for s in members):
                    raise ValueError('양쪽 대상을 다시 지정해 잠정 추적을 준비하세요.')
                group=MeasurementGroup(members,self.output_root,None if tolerance is None else int(tolerance*1_000_000),targets=targets,plan=values.get('measurement_plan'))
                self.groups[group.id]=group
                try:group.start()
                except Exception:
                    group.fail('START_DISPATCH_FAILED')
                    raise
                return {'group_id':group.id}
            if values['action']=='ready':
                self.groups[values['group_id']].ready()
                return {'accepted':True}
            if values['action']=='confirm_targets':
                group=self.groups[values['group_id']]
                if group.finished or group.data['phase'] not in ('preparing','recording') or values.get('same_person_confirmed') is not True:
                    raise ValueError('측정 중 양쪽 대상을 확인하고 동일인 지정을 체크하세요.')
                states=[member.worker.engine.target_tracker.current() for member in group.members]
                if any(state['status']!='tracking_provisional' for state in states):
                    raise ValueError('양쪽 대상을 다시 지정해 잠정 추적을 준비하세요.')
                group.data.setdefault('target_pair_confirmations',[]).append({
                    'requested_perf_counter_ns':str(time.perf_counter_ns()),
                    'assertion':'operator_report_not_verified',
                    'members':[{'input_id':member.id,'track_id':state['track_id'],'frame_id':state['frame_id']} for member,state in zip(group.members,states)]})
                group.data['target_pair_status']='operator_reconfirmed_not_verified'
                group.save()
                return {'accepted':True}
            if values['action']=='stop':
                self.groups[values['group_id']].stop()
                return {'accepted':True}
            raise ValueError('지원하지 않는 그룹 조작입니다.')

    def active_group(self, session_id):
        return next((g for g in self.groups.values() if not g.finished and any(s.id==session_id for s in g.members)),None)

    def command(self, session_id, action, values):
        with self.lock:
            session = self.sessions[session_id]
            state = session.state
            group=self.active_group(session_id)
            if group is not None:
                if action in ('remove','close'):
                    session.remove=action=='remove'
                    group.stop(close_inputs=True)
                    return
                if action!='region' or group.data['phase'] not in ('preparing','recording'):
                    raise ValueError('그룹 측정 중입니다. 그룹 종료 버튼을 사용하세요.')
            if action in ('close', 'remove'):
                session.remove = action == 'remove'
                if session.remove and state['closed']:
                    session.preview_worker.stop()
                    del self.sessions[session_id]
                    self.target_tickets={k:v for k,v in self.target_tickets.items() if v['input_id']!=session_id}
                else:
                    state['phase'] = 'closing'
                    session.worker.request_close()
                if session.raw_worker:session.raw_worker.stop()
                return
            if state['closed'] or state['phase'] == 'closing' or state['pending']:
                raise ValueError('이전 작업이 끝난 뒤 다시 조작하세요.')
            if action == 'region':
                if state['frame_id'] is None:
                    raise ValueError('첫 영상을 기다려 주세요.')
                points=values.get('points')
                if points is not None:
                    from .bed_geometry import make_quadrilateral
                    make_quadrilateral(points,state['width'],state['height'])
                    if values.get('box') is not None:raise ValueError('영역 형식을 하나만 지정하세요.')
                box = values.get('box')
                if box is not None and (not isinstance(box, list) or len(box) != 4 or
                        any(type(x) not in (int, float) or not math.isfinite(x) for x in box)):
                    raise ValueError('영역 좌표가 올바르지 않습니다.')
                selected_id = values.get('selected_frame_id')
                if type(selected_id) is not int or not 0 <= selected_id <= state['frame_id']:
                    raise ValueError('영역을 지정한 영상 프레임이 유효하지 않습니다.')
                session.worker.submit('region', box=box, points=points, width=state['width'], height=state['height'],
                                      selected_frame_id=selected_id)
            elif action == 'posture_mode':
                if state['recording']:raise ValueError('측정을 종료한 뒤 판정 설정을 바꾸세요.')
                if values.get('mode') not in ('automatic','off') or values.get('view','auto') not in ('auto','body_state','bed_auto','oblique','overhead'):raise ValueError('판정 방식과 촬영 각도를 확인하세요.')
                session.worker.submit('posture_mode',mode=values['mode'],view=values.get('view','auto'))
            elif action == 'posture_reference':
                if state['recording']:raise ValueError('측정 종료 후 기준을 변경하세요.')
                if values.get('clear') is not True and values.get('confirmed') is not True:raise ValueError('실제 자세를 확인한 뒤 등록하세요.')
                session.worker.submit('posture_reference',label=values.get('label'),selected_frame_id=values.get('selected_frame_id'),
                    max_distance=values.get('max_distance',.35),min_margin=values.get('min_margin',.10),clear=values.get('clear') is True)
            elif action == 'start':
                from .automatic_posture import SEPARATED_METHOD,BODY_STATE_METHOD
                independent=(state.get('automatic_posture_profile') or {}).get('version') in (SEPARATED_METHOD,BODY_STATE_METHOD)
                if state['frame_id'] is None or (not state['region'] and not independent) or state['recording']:
                    raise ValueError('영상에서 침대 영역을 먼저 지정하세요.')
                session.worker.submit('start')
            elif action == 'stop':
                if not state['recording']:
                    raise ValueError('진행 중인 측정이 없습니다.')
                session.worker.submit('stop')
            elif action == 'playback':
                if session.kind != 'video_file' or type(values.get('paused')) is not bool:
                    raise ValueError('재생 조작을 확인하세요.')
                session.worker.submit('playback', paused=values['paused'])
            else:
                raise ValueError('지원하지 않는 조작입니다.')
            state['pending'] = action
            state['error'] = None

    def scan(self):
        with self.lock:
            if self.scan_state['busy']:
                return
            excluded = {s.worker.engine.source.index for s in self.sessions.values()
                        if s.kind == 'camera' and not s.state['closed']}
            self.scan_state = dict(self.scan_state, busy=True, error=None)
        def run():
            try:
                devices = named_cameras()
                indices = sorted({d['index'] for d in devices} | excluded)
                if not devices:
                    indices = sorted(set(probe_cameras(excluded=excluded)) | excluded)
                error = None
            except Exception as exc:
                devices = []
                try:
                    indices = sorted(set(probe_cameras(excluded=excluded)) | excluded)
                except Exception:
                    indices = sorted(excluded)
                error = '장치 이름을 읽지 못해 번호로 표시합니다. 선택 의존성 재설치 후 작업실을 다시 실행하세요.'
            with self.lock:
                self.scan_state = {'busy': False, 'indices': indices, 'devices': devices, 'error': error}
        threading.Thread(target=run, daemon=True).start()

    def _message(self, session, kind, value):
        state = session.state
        if kind == 'ready':
            state['phase'] = 'preview'
            state['source_profile'] = dict(session.worker.engine.source_profile)
        elif kind == 'region':
            state.update(region=value['region'], pending=None)
        elif kind == 'started':
            state.update(recording=True, pending=None, directory=value['directory'], recorded_frames=0,
                         elapsed=0, phase='recording', integrity=None)
            state['started_ns'] = value['started_ns']
        elif kind == 'stopped':
            manifest = value['manifest']
            state.update(recording=False, pending=None, directory=value['directory'],
                         recorded_frames=manifest['recorded_frames'],
                         elapsed=(int(manifest['finished_ns'])-int(manifest['started_ns']))/1e9,
                         integrity='verified' if manifest['ledger_complete'] else 'incomplete',
                         phase='error' if manifest['run_status'] == 'failed' else 'preview')
            if manifest['run_status'] == 'failed' and not state['error']:
                state['error'] = '오류로 측정을 종료했습니다. 기록을 확인하세요.'
        elif kind == 'posture_mode':
            state.update(automatic_posture_profile=value['profile'],posture_reference_profile=None,posture_model_id=value['model_id'],pending=None)
        elif kind == 'posture_reference':
            state['automatic_posture_profile']=None
            state['posture_model_id']=value['model_id']
            state['posture_reference_profile']=value['profile']
            state['posture_reference_model_id']=value['model_id']
            state['pending']=None
        elif kind == 'target_selected':
            state['target_tracking']=value['tracking']
            state['target_selection_applied']=value.get('selection_id')
            state['target_selection_pending']=None
        elif kind == 'playback':
            state['paused'] = value['paused']
            if state['pending'] == 'playback':
                state['pending'] = None
        elif kind in ('error', 'command_rejected'):
            state.update(error=value['message'], pending=None)
            if value.get('action')=='target_select':
                state['target_selection_pending']=None
                state['target_selection_error']=value['message']
            if kind == 'error':
                state['phase'] = 'error'
                state['candidate_count'] = None
                state['posture_assessment'] = None
                state['posture_diagnostics'] = session.worker.engine.posture_diagnostics.latest
                session.view = None  # Never send a previous observation as a current failed frame.
                session.preview_rgb = None
                session.preview_frame = None
                session.preview_epoch += 1
                if session.preview_worker:session.preview_worker.stop()
        elif kind == 'eof':
            state['eof'] = True
        elif kind == 'closed':
            state.update(closed=True, pending=None, recording=False)
            state['phase'] = 'error' if state['error'] else ('ended' if state.get('eof') else 'closed')

        group=self.active_group(session.id)
        if group is not None:
            try:group.message(session,kind,value)
            except Exception:
                group.failed=group.finished=True
                group.data.update(phase='failed',ledger_complete=False)
                group.data['errors'].append({'code':'GROUP_WRITE_FAILED'})
                for member in group.members:member.worker.request_close()

    def _raw_ready(self,session,job,result,error):
        with self.lock:
            if (session.id not in self.sessions or session.state['closed'] or session.state['phase']=='error'
                    or job['quality']!=self.preview_quality):return
            if error:return
            packet=job['frame']
            session.raw_view={'capture_frame_id':packet['capture_frame_id'],'received_ns':str(packet['received_ns']),
                              'image':result[0],'preview':result[1]}

    def raw_view(self,session_id):
        with self.lock:
            session=self.sessions[session_id]
            if session.state['closed'] or session.state['phase']=='error':return None
            session.raw_requested_until=time.monotonic()+1.0
            self._refresh_raw(session)
            view=session.raw_view
            if not view:return None
            age=max(0,session.worker.engine.clock()-int(view['received_ns']))/1e6
            return dict(view,age_ms=age)

    def _refresh_raw(self,session):
        if not session.raw_worker:return
        if session.state['closed'] or session.state['phase']=='error':
            session.raw_worker.stop();session.raw_view=None
            return
        if time.monotonic()>=session.raw_requested_until:return
        packet=session.worker.engine.source.latest()
        if packet and (packet['capture_frame_id']>session.raw_sequence or session.raw_quality!=self.preview_quality):
            session.raw_sequence=packet['capture_frame_id'];session.raw_quality=self.preview_quality
            session.raw_worker.submit({'frame':packet,'quality':self.preview_quality})

    def _refresh(self, session):
        while True:
            try:
                self._message(session, *session.worker.messages.get_nowait())
            except queue.Empty:
                break
        state = session.state
        self._refresh_raw(session)
        try:
            frame = session.worker.frames.get_nowait()
        except queue.Empty:
            return
        if state['phase'] == 'error':
            return
        session.preview_rgb=frame['rgb']
        session.preview_frame=frame
        session.preview_generation+=1
        if state['recording'] and int(frame['row']['received_ns'])>=int(state['started_ns']):
            state['recorded_frames']=frame['recorded_frames']
            state['elapsed']=(int(frame['row']['received_ns'])-int(state['started_ns']))/1e9
        state['processing_fps']=frame.get('processing_fps')
        state['processing_ms']=frame.get('processing_ms')
        state['image_runtime']=frame.get('image_runtime')
        session.preview_worker.submit(self._preview_job(session))

    def _publish_preview(self,session,frame,result,error):
        state=session.state
        rgb,row=frame['rgb'],frame['row']
        height,width=rgb.shape[:2]
        image,preview=result
        state['preview_error']=('미리보기 변환 실패 · 분석과 진행 중인 기록은 계속됩니다. 다음 프레임에서 재시도하며, 정지 영상은 화질을 전환해 재시도할 수 있습니다.' if error else None)
        media = row.get('source_media')
        session.sequence += 1
        state.update(frame_id=row['stream_frame_id'], sequence=session.sequence, width=width, height=height,
                     preview=preview,
                     candidate_count=row['candidate_count'],
                     media_seconds=int(media['relative_time_ns'])/1e9 if media else None)
        state['target_tracking']=row['target_tracking']
        state['posture_assessment']=row['posture_assessment']
        state['posture_evidence']=row.get('posture_evidence')
        state['silhouette_assessment']=row.get('silhouette_assessment')
        state['posture_diagnostics']=frame.get('posture_diagnostics')
        state['posture']=row['posture_assessment']['label'] or ('held' if row['posture_assessment']['classifier_id'] else 'not_implemented')
        session.view = {'sequence': session.sequence, 'frame_id': row['stream_frame_id'],
                        'width': width, 'height': height, 'people': row['mapped_people'],
                        'clock_id':row['clock_id'],'received_ns':row['received_ns'],
                        'target_tracking':row['target_tracking'],
                        'posture_assessment':row['posture_assessment'],
                        'posture_evidence':row.get('posture_evidence'),
                        'silhouette_assessment':row.get('silhouette_assessment'),
                        'silhouette_preview':frame.get('silhouette_preview'),
                        'body_state_input_preview':frame.get('body_state_input_preview'),
                        'body_state_ms':(int(row['body_state_finished_ns'])-int(row['body_state_started_ns']))/1e6 if 'body_state_finished_ns' in row else None,
                        'candidate_count': row['candidate_count'],
                        'inference_ms': (int(row['inference_finished_ns'])-int(row['inference_started_ns']))/1e6,
                        'read_ms': (int(row['received_ns'])-int(row['read_started_ns']))/1e6,
                        'media_seconds': int(media['relative_time_ns'])/1e9 if media else None,
                        'image':image,'preview':preview}

    def _monitor(self):
        while not self.monitor_stop.wait(.015):
            with self.lock:
                for session in list(self.sessions.values()):
                    try:
                        self._refresh(session)
                    except Exception as exc:
                        self._message(session, 'error', {'message': '화면 전달 오류: '+str(exc)})
                        session.worker.request_close()
                        if session.raw_worker:session.raw_worker.stop()
                    if session.remove and session.state['closed']:
                        session.preview_worker.stop()
                        self.sessions.pop(session.id, None)
                        self.target_tickets={k:v for k,v in self.target_tickets.items() if v['input_id']!=session.id}

                self._tick_groups()

    def _tick_groups(self):
        for group in self.groups.values():
            try:group.tick()
            except Exception:
                group.failed=True
                group.data["phase"]="failed"
                group.data["ledger_complete"]=False
                group.data["errors"].append({"code":"GROUP_WRITE_FAILED"})
                group.finished=True
                for member in group.members:member.worker.request_close()

    def view(self, session_id, clip_preview=True):
        with self.lock:
            session=self.sessions[session_id]
            provider=session.worker.engine.body_state_provider
            if provider is not None:provider.input_preview_enabled=clip_preview
            result=session.view
            if result is not None and not clip_preview:return dict(result,body_state_input_preview=None)
            if result is not None and callable(getattr(provider,'input_preview',None)):
                return dict(result,body_state_input_preview=provider.input_preview(result['frame_id']))
            return result

    def close(self):
        self.stop_requested.set()
        with self.lock:
            sessions = list(self.sessions.values())
            for session in sessions:
                session.worker.request_close()
                if session.raw_worker:session.raw_worker.stop()
        # Wait for owners to finalize records. Do not delete assets while they are in use.
        while any(s.worker.is_alive() for s in sessions):
            for session in sessions:
                session.worker.join(timeout=.1)
        with self.lock:
            for session in sessions:self._refresh(session)
            self._tick_groups()
        while any(not group.finished for group in self.groups.values()):
            with self.lock:
                self._tick_groups()
            time.sleep(.03)
        self.monitor_stop.set()
        self.monitor.join(timeout=2)
        for session in sessions:session.preview_worker.stop()
        for session in sessions:session.preview_worker.thread.join(timeout=.2)
        self.temp.cleanup()


class WorkspaceHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    def __init__(self, workspace, port=0):
        self.workspace, self.token = workspace, secrets.token_urlsafe(32)
        super().__init__(('127.0.0.1', port), WorkspaceHandler)
        self.origin = f'http://127.0.0.1:{self.server_address[1]}'
        self.url = self.origin+'/#'+self.token


class WorkspaceHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # No local paths, tokens or video data in access logs.

    def _reply(self, status, value, mime='application/json; charset=utf-8', etag=None):
        body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode() if mime.startswith('application/json') and not isinstance(value,bytes) else value
        self.send_response(status)
        self.send_header('Content-Type', mime)
        if status!=304:self.send_header('Content-Length', str(len(body)))
        if etag is not None:self.send_header('ETag',etag)
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        if body:self.wfile.write(body)

    def _authorized(self):
        origin = self.headers.get('Origin')
        return (self.headers.get('Host') == self.server.origin.removeprefix('http://')
                and (origin is None or origin == self.server.origin)
                and secrets.compare_digest(self.headers.get('X-BedPose-Token', ''), self.server.token))

    def do_GET(self):
        try:
            url=urlsplit(self.path)
            path = url.path
            if path == '/':
                if self.headers.get('Host') != self.server.origin.removeprefix('http://'):
                    return self._reply(403, {'error': 'Invalid host'})
                return self._reply(200, files('bed_pose').joinpath('templates/live_workspace.html').read_bytes(), 'text/html; charset=utf-8')
            if not self._authorized():
                return self._reply(403, {'error': '작업실 실행 주소로 다시 접속하세요.'})
            if path == '/api/state':
                query=parse_qs(url.query)
                compact=query.get('compact',['0'])[0]=='1'
                known=set(query.get('known_profiles',[''])[0].split(','))
                data=self.server.workspace.snapshot(compact=compact,known_profiles=known)
                body=json.dumps(data,ensure_ascii=False,allow_nan=False).encode()
                etag='"'+hashlib.sha256(body).hexdigest()+'"'
                if self.headers.get('If-None-Match')==etag:return self._reply(304,b'',etag=etag)
                return self._reply(200,body,etag=etag)
            if path == '/api/records/timeline':
                query=parse_qs(url.query)
                result=self.server.workspace.records.timeline(query.get('record_id',[''])[0],
                    query.get('basis',[None])[0],int(query.get('bins',['240'])[0]))
                return self._reply(200,result)
            if path in ('/api/records','/api/records/frames'):
                query=parse_qs(url.query)
                offset=int(query.get('offset',['0'])[0]);limit=int(query.get('limit',['50'])[0])
                library=self.server.workspace.records
                result=(library.catalog(offset,limit) if path=='/api/records' else
                        library.frames(query.get('record_id',[''])[0],offset,limit))
                return self._reply(200,result)
            if path.startswith('/api/live-view/'):
                return self._reply(200,self.server.workspace.raw_view(path.split('/')[-1]))
            if path.startswith('/api/view/'):
                return self._reply(200, self.server.workspace.view(path.split('/')[-1],parse_qs(url.query).get('clip_preview',['1'])[0]=='1'))
            self._reply(404, {'error': 'Not found'})
        except KeyError:
            self._reply(404, {'error': '입력을 찾을 수 없습니다.'})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except (ValueError,TypeError,OSError):
            self._reply(400, {'error': '기록을 읽을 수 없습니다. 목록 새로고침 후 다시 여세요.'})

    def do_POST(self):
        self.connection.settimeout(30)
        self.close_connection = True
        try:
            if not self._authorized():
                return self._reply(403, {'error': '작업실 실행 주소로 다시 접속하세요.'})
            if self.headers.get('Transfer-Encoding'):
                raise ValueError('Length required')
            length = int(self.headers.get('Content-Length', '-1'))
            if length < 0:
                raise ValueError('Length required')
            url = urlsplit(self.path)
            workspace = self.server.workspace
            if url.path == '/api/upload':
                query = parse_qs(url.query)
                kind = query.get('kind', [''])[0]
                name = query.get('name', ['input'])[0]
                limit = 512*1024**2 if kind == 'model' else 16*1024**3
                if kind not in ('video', 'model') or length == 0 or length > limit:
                    raise ValueError('모델은 512MB, 영상은 16GB 이하 파일을 선택하세요.')
                suffix = '.task' if kind == 'model' else Path(name).suffix.lower()
                if suffix not in ('.task', '.mp4', '.mov', '.mkv', '.avi', '.webm', '.m4v'):
                    raise ValueError('지원하는 모델/영상 확장자를 선택하세요.')
                path = workspace.temp_root/(uuid.uuid4().hex+suffix)
                try:
                    with path.open('xb') as stream:
                        remaining = length
                        while remaining:
                            chunk = self.rfile.read(min(1024**2, remaining))
                            if not chunk:
                                raise ValueError('파일 전달이 중단되었습니다.')
                            stream.write(chunk)
                            remaining -= len(chunk)
                    return self._reply(200, workspace.register_asset(path, kind, name))
                except Exception:
                    path.unlink(missing_ok=True)
                    raise
            if length > 65536:
                raise ValueError('Request too large')
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError('Incomplete request')
            values = strict_loads(body.decode('utf-8'))
            if not isinstance(values, dict):
                raise ValueError('JSON object required')
            if url.path == '/api/inputs':
                result = workspace.add(values)
            elif url.path == '/api/preview-quality':
                result=workspace.set_preview_quality(values.get('quality'))
            elif url.path == '/api/records/image':
                with workspace.lock:
                    asset=workspace.assets.get(values.get('video_asset'))
                    if not asset or asset['kind']!='video':raise ValueError('대조할 원본 영상 파일을 선택하세요.')
                    video=asset['path']
                result=workspace.records.image(values.get('record_id'),values.get('frame_id'),video)
            elif url.path == '/api/records/open':
                result=workspace.records.open(values.get('record_id'))
            elif url.path == '/api/target-select':
                result = workspace.select_target(values)
            elif url.path == '/api/target-capture':
                result = workspace.capture_target(values['id'])
            elif url.path == '/api/group':
                result = workspace.group_command(values)
            elif url.path == '/api/control':
                workspace.command(values['id'], values['action'], values)
                result = {'accepted': True}
            elif url.path == '/api/scan':
                workspace.scan()
                result = {'accepted': True}
            elif url.path == '/api/shutdown':
                workspace.stop_requested.set()
                result = {'closing': True}
            else:
                return self._reply(404, {'error': 'Not found'})
            self._reply(200, result)
        except (KeyError, ValueError, TypeError) as exc:
            self._reply(400, {'error': str(exc)})
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:
            self._reply(500, {'error': '요청 처리에 실패했습니다. 경로·저장 공간·입력을 확인하세요.'})

    def do_OPTIONS(self):
        self._reply(403, {'error': 'Cross-origin requests are not supported'})


def launch_browser(model=None, camera=None, output_root=Path('recordings/live'), demo=False,
                   video=None, *, port=0, open_browser=True,clip_model=None,clip_device='auto',
                   clip_state_min=.5,clip_direction_min=.5):
    workspace = WebWorkspace(model, output_root,clip_model=clip_model,clip_device=clip_device,
                             clip_state_min=clip_state_min,clip_direction_min=clip_direction_min)
    server = None
    try:
        server = WorkspaceHTTPServer(workspace, port)
        if demo:
            workspace.add({'kind': 'demo'})
        elif video is not None:
            asset = workspace.register_asset(Path(video).resolve(), 'video', Path(video).name)
            workspace.add({'kind': 'video_file', 'video_asset': asset['asset_id']})
        elif camera is not None:
            workspace.add({'kind': 'camera', 'camera': camera})
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        print('BedPose 브라우저 작업실: '+server.url, flush=True)
        print('브라우저에서 종료하거나 이 터미널에서 Ctrl+C를 누르세요. 탭을 닫아도 측정은 계속됩니다.', flush=True)
        if open_browser:
            webbrowser.open(server.url)
        try:
            while not workspace.stop_requested.wait(.2):
                pass
        except KeyboardInterrupt:
            pass
    finally:
        print('입력과 측정 기록을 정리하고 있습니다.', flush=True)
        workspace.close()
        if server is not None:
            server.shutdown() if 'thread' in locals() else None
            server.server_close()
    return 0
