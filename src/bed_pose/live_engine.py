"""Single-owner live capture/inference/measurement lifecycle, independent of GUI."""
from dataclasses import asdict
from pathlib import Path
import platform
import math
import queue
import threading
import time
import uuid
import numpy as np
from .contracts import FramePacket, ModelInput, IntegrityError
from .mapping import MappingProfile, map_keypoints, raw_json_value
from .live_recording import LiveRecorder, make_region
from .target_tracking import TargetTracker
from .io_utils import object_hash


class LiveFailure(RuntimeError):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


class LiveEngine:
    def __init__(self, source, adapter, settings, output_root, *, profile=None,
                 execution_kind='model_inference', clock=time.perf_counter_ns, utc_clock=time.time_ns):
        self.source, self.adapter, self.settings = source, adapter, settings
        self.output_root = Path(output_root)
        self.profile = profile or MappingProfile()
        self.execution_kind = execution_kind
        self.clock_function, self.utc_clock = clock, utc_clock
        self.origin = clock()
        self.utc_reference_ns = str(utc_clock())
        self.stream_id = uuid.uuid4().hex
        self.clock_id = self.stream_id + ':perf_counter_ns'
        self.next_frame_id, self.last_model_ms = 0, None
        self.geometry = None
        self.region, self.region_revision = None, 0
        self.region_selection = None
        self.recorder = None
        self.opened = False
        self.ever_opened = False
        self.source_profile, self.adapter_profile = {}, {}
        from .processing_rate import ProcessingRate
        self.processing_rate=ProcessingRate()
        self.target_tracker=TargetTracker()
        from .posture_diagnostics import PostureDiagnostics
        self.posture_diagnostics=PostureDiagnostics()
        from .automatic_posture import AutomaticClassifier,SEPARATED_DEFAULTS
        self.posture_classifier=AutomaticClassifier(SEPARATED_DEFAULTS) if execution_kind=='model_inference' else None

    def clock(self):
        return self.clock_function() - self.origin

    def open(self):
        if self.ever_opened or self.settings['execution_mode'] != 'ordered_sequence':
            raise ValueError('새 스트림은 새 LiveEngine과 연속 실행 모드로 시작해야 합니다.')
        self.ever_opened = True
        try:
            self.adapter_profile = self.adapter.open(self.settings)
            if self.adapter_profile.get('execution_kind') != self.execution_kind:
                raise ValueError('Live adapter execution kind mismatch')
            self.reset_profile = self.adapter.reset_for_video()
            self.source_profile = self.source.open()
            allowed = ('synthetic',) if self.execution_kind == 'synthetic' else ('camera', 'video_file')
            if self.source_profile['kind'] not in allowed:
                raise ValueError('Live input cannot silently switch to synthetic data')
            self.opened = True
        except Exception:
            self.close('failed')
            raise

    def set_region(self, box, width, height, request=None, selected_frame_id=None, points=None):
        if self.geometry != (width, height):
            raise ValueError('최신 영상 크기에 맞춰 침대 영역을 다시 지정하세요.')
        if selected_frame_id is not None and (type(selected_frame_id) is not int or not 0 <= selected_frame_id < self.next_frame_id):
            raise ValueError('영역을 지정한 미리보기 프레임이 유효하지 않습니다.')
        from .bed_geometry import make_quadrilateral
        if box is not None and points is not None:raise ValueError('영역 형식을 하나만 지정하세요.')
        region = make_quadrilateral(points,width,height) if points is not None else make_region(box, width, height) if box is not None else None
        self.region_revision += 1
        self.region = region
        self.region_selection = {'selected_stream_frame_id': selected_frame_id,
                                 'applied_time_ns': str(self.clock()), 'applied_utc_ns': str(self.utc_clock()),
                                 'effective_stream_frame_id': self.next_frame_id, 'request': request}
        if self.recorder:
            self.recorder.event('bed_region_changed', region=region, revision=self.region_revision,
                                effective_stream_frame_id=self.next_frame_id, request=request, selection=self.region_selection)
        return self.region

    def configure_posture(self, label=None, selected_frame_id=None, max_distance=.35, min_margin=.10, clear=False):
        if self.recorder:raise ValueError('측정을 종료한 뒤 기준 자세를 변경하세요.')
        if clear:
            self.posture_classifier=None
            return
        from .posture import assess_frame,PostureInput
        from .reference_posture import ReferenceClassifier,features,distance,METHOD
        from copy import deepcopy
        if type(selected_frame_id) is not int:raise ValueError('등록 프레임 번호를 확인하세요.')
        if self.region and self.region.get('method')=='manual_quadrilateral':raise ValueError('네 점 영역은 자동 판정을 사용하세요. 이전 기준 등록은 사각형 기록용입니다.')
        if label not in ('supine','side','edge_sitting') or self.region is None:raise ValueError('침대 영역과 기준 자세를 선택하세요.')
        with self.target_tracker.lock:
            snapshot=next((s for s in self.target_tracker.history if s['frame_id']==selected_frame_id),None)
            if snapshot is None:raise ValueError('선택 프레임이 만료됐습니다. 다시 등록하세요.')
            row={'stream_frame_id':snapshot['frame_id'],'clock_id':self.clock_id,'received_ns':str(snapshot['time_ns']),
                'processing_status':snapshot['processing_status'],'mapped_people':snapshot['people']}
            # Reference capture requires exactly one visible candidate, avoiding a stale ID match.
            a=assess_frame(row,*self.geometry,self.region)
            if a['reasons']!=['classifier_not_configured']:raise ValueError('한 사람의 관절이 보이는 프레임으로 등록하세요.')
            person=snapshot['people'][0]
            points=tuple((j['x_px'],j['y_px']) if j.get('availability')=='predicted' and
                type(j.get('x_px')) in (int,float) and type(j.get('y_px')) in (int,float) and
                math.isfinite(j['x_px']) and math.isfinite(j['y_px']) and 0<=j['x_px']<self.geometry[0] and 0<=j['y_px']<self.geometry[1] else None for j in person['joints'])
            box=[self.region[k] for k in ('x1','y1','x2','y2')]
            vector=features(PostureInput(points,*self.geometry,tuple(box)))
            if vector is None:raise ValueError('어깨·골반·무릎·발목의 화면 내 관절이 모두 필요합니다.')
            previous=self.posture_classifier.profile if isinstance(self.posture_classifier,ReferenceClassifier) else None
            refs=deepcopy(previous['references']) if previous and previous['bed_rectangle']==box else {}
            profile={'version':METHOD,'label_source':'operator_reference_not_verified','width':self.geometry[0],'height':self.geometry[1],
                     'bed_rectangle':box,'max_distance':max_distance,'min_margin':min_margin,'references':refs}
            ReferenceClassifier(profile)  # Validate experimental settings before numeric operations.
            for other,ref in refs.items():
                if other!=label and distance(vector,ref['features'])<min_margin:
                    raise ValueError('다른 자세 기준과 너무 비슷합니다. 실제 자세와 관절을 확인하세요.')
            profile['references'][label]={'features':vector,'source':{'stream_id':self.stream_id,'stream_frame_id':selected_frame_id,
                 'clock_id':self.clock_id,'observation_time_ns':str(snapshot['time_ns']),'time_basis':'media_relative' if getattr(self.source,'is_file',False) else 'stream_receive',
                 'registered_ns':str(self.clock()),'assertion':'operator_reference_not_verified'}}
            self.posture_classifier=ReferenceClassifier(profile)

    def start_measurement(self, request=None):
        from .automatic_posture import SEPARATED_METHOD
        independent=self.posture_classifier and self.posture_classifier.profile['version']==SEPARATED_METHOD
        if not self.opened or self.geometry is None or (self.region is None and not independent):
            raise ValueError('영상이 표시된 뒤 침대 영역을 먼저 지정하세요.')
        if self.recorder:
            raise ValueError('이미 측정 중입니다.')
        from .runner import _code_version
        from .posture import PROFILE
        from .posture_evidence import PROFILE as EVIDENCE_PROFILE
        from .silhouette import PROFILE as SILHOUETTE_PROFILE
        width, height = self.geometry
        measurement_id = uuid.uuid4().hex
        manifest = {'measurement_id': measurement_id, 'stream_id': self.stream_id,
                    'clock_id': self.clock_id, 'clock_origin_perf_counter_ns': str(self.origin),
                    'utc_reference_ns': self.utc_reference_ns,
                    'started_ns': str(self.clock()), 'started_utc_ns': str(self.utc_clock()),
                    'execution_kind': self.execution_kind, 'mode': 'free',
                    'width': width, 'height': height, 'first_stream_frame_id': self.next_frame_id,
                    'initial_bed_region': self.region, 'initial_bed_revision': self.region_revision,
                    'initial_bed_selection': self.region_selection,
                    'adapter_profile': self.adapter_profile, 'source_profile': self.source_profile,
                    'mapping_profile': asdict(self.profile), 'code': _code_version(),
                    'adapter_profile_sha256': object_hash(self.adapter_profile),
                    'source_profile_sha256': object_hash(self.source_profile),
                    'mapping_profile_sha256': object_hash(asdict(self.profile)),
                    'requested_settings': self.settings, 'requested_settings_sha256': object_hash(self.settings),
                    'execution_mode': self.settings['execution_mode'], 'stream_reset': self.reset_profile,
                    'environment': {'python': platform.python_version(), 'platform': platform.platform(), 'numpy': np.__version__},
                    'video_recording': False, 'tracking_scope': 'input_stream',
                    'preview_tracking_history_retained': True, 'hardware_dropped_frames': None, 'start_request': request,
                    'target_tracking_initial':self.target_tracker.current(),
                    'posture_assessment_profile':dict(PROFILE),
                    'posture_evidence_profile':dict(EVIDENCE_PROFILE),
                    'silhouette_profile':dict(SILHOUETTE_PROFILE),
                    'reference_posture_profile':self.posture_classifier.profile if self.posture_classifier and self.posture_classifier.profile['version']=='reference-posture-0.1' else None,
                    'automatic_posture_profile':self.posture_classifier.profile if self.posture_classifier and self.posture_classifier.profile['version'].startswith('automatic-posture') else None,
                    'target_policy': 'none', 'posture_classifier': self.posture_classifier.model_id if self.posture_classifier else 'not_implemented', 'event_analyzer': 'not_implemented'}
        self.recorder = LiveRecorder(self.output_root/measurement_id, manifest, self.clock)
        self.recorder.event('measurement_started', effective_stream_frame_id=self.next_frame_id, request=request)
        return self.recorder.directory

    def stop_measurement(self, outcome='succeeded', errors=(), reason='user_stop', request=None):
        if self.recorder is None:
            raise ValueError('진행 중인 측정이 없습니다.')
        recorder = self.recorder
        try:
            recorder.event('measurement_stopped', reason=reason, effective_stream_frame_id=self.next_frame_id, request=request)
            manifest = recorder.finalize(outcome, errors)
            return recorder.directory, manifest
        except Exception as exc:
            try:
                recorder.finalize('failed', [{'code': 'RECORDING_ERROR'}])
            except Exception:
                pass
            raise IntegrityError('측정 기록을 완료하지 못했습니다.') from exc
        finally:
            self.recorder = None

    def step(self):
        if not self.opened:
            raise RuntimeError('Live engine is closed')
        read_started = self.clock()
        try:
            rgb = self.source.read()
        except StopIteration:
            if getattr(self.source, 'is_file', False):
                raise
            raise LiveFailure('SOURCE_READ_FAILED', '카메라 입력이 종료되었습니다.')
        except Exception as exc:
            raise LiveFailure('SOURCE_READ_FAILED', str(exc)) from exc
        received, utc = self.clock(), self.utc_clock()
        if not isinstance(rgb, np.ndarray) or rgb.dtype != np.uint8 or rgb.ndim != 3 or rgb.shape[2] != 3 or min(rgb.shape[:2]) < 1:
            raise LiveFailure('INVALID_CAMERA_FRAME', '카메라가 유효한 RGB 영상을 반환하지 않았습니다.')
        geometry = (rgb.shape[1], rgb.shape[0])
        if self.geometry is not None and geometry != self.geometry:
            raise LiveFailure('CAMERA_GEOMETRY_CHANGED', '영상 크기가 바뀌었습니다. 다시 연결하고 침대 영역을 지정하세요.')
        self.geometry = geometry
        rgb = np.ascontiguousarray(rgb)
        rgb.setflags(write=False)
        frame_id = self.next_frame_id
        self.next_frame_id += 1
        media = getattr(self.source, 'media', None)
        timestamp = int(media['relative_time_ns']) // 1_000_000 if media else received // 1_000_000
        row = {'stream_id': self.stream_id, 'stream_frame_id': frame_id, 'clock_id': self.clock_id,
               'read_started_ns': str(read_started), 'received_ns': str(received), 'received_utc_ns': str(utc),
               'timestamp_source': 'received_after_read', 'camera_exposure_ns': None,
               'model_timestamp_ms': str(timestamp), 'inference_started_ns': None,
               'inference_finished_ns': None, 'mapping_finished_ns': None,
               'processing_status': 'ok', 'candidate_count': None, 'raw_candidates': None,
               'mapped_people': None, 'sdk_call_started': False, 'error': None,
               'silhouette_observation':None,
               'bed_region_revision': self.region_revision,
               'posture_prediction': {'status': 'not_implemented', 'label': None},
               'event_predictions': [], 'event_analysis_status': 'not_implemented',
               'bed_occupancy_status': 'not_implemented',
               'target_resolution': {'status': 'not_configured', 'candidate_id': None}, 'target_posture': None,
               'verified_gt': None, 'sensor_results': None}
        if media is not None:
            row['source_media'] = dict(media)
        failure = None
        preview_packet = None
        stage = 'inference'
        try:
            if self.last_model_ms is not None and timestamp <= self.last_model_ms:
                raise LiveFailure('MODEL_TIMESTAMP_COLLISION', '모델 입력 시각이 중복되었습니다.')
            row['inference_started_ns'] = str(self.clock())
            self.last_model_ms = timestamp
            output = self.adapter.estimate(ModelInput(FramePacket(self.stream_id, frame_id, rgb, {}), timestamp))
            preview_packet = getattr(output, 'silhouette_preview', None)
            row['sdk_call_started'] = output.sdk_call_started
            if output.model_timestamp_ms != timestamp:
                raise ValueError('Adapter timestamp mismatch')
            row['inference_finished_ns'] = str(self.clock())
            row['candidate_count'] = len(output.candidates)
            row['raw_candidates'] = raw_json_value(output.candidates)
            try:row['silhouette_observation']=raw_json_value(getattr(output,'silhouette_observation',None))
            except Exception:row['silhouette_observation']=None
            stage = 'mapping'
            row['mapped_people'] = map_keypoints(output, *geometry, self.profile)
            row['mapping_finished_ns'] = str(self.clock())
        except Exception as exc:
            if row['inference_started_ns'] is not None and row['inference_finished_ns'] is None:
                row['inference_finished_ns'] = str(self.clock())
            if stage == 'mapping':
                row['mapping_finished_ns'] = str(self.clock())
            code = getattr(exc, 'code', 'INFERENCE_ERROR' if stage == 'inference' else 'MAPPING_ERROR')
            row.update(processing_status='failed', error={'code': code, 'exception_type': type(exc).__name__},
                       sdk_call_started=row['sdk_call_started'] or bool(getattr(exc, 'sdk_call_started', False)))
            failure = LiveFailure(code, str(exc))
        row['target_tracking']=self.target_tracker.observe(row,*geometry)
        from .posture import assess_frame
        row['posture_assessment']=assess_frame(row,*geometry,self.region,self.posture_classifier)
        from .posture_evidence import compare_frame
        row['posture_evidence']=compare_frame(row,*geometry,row['posture_assessment'])
        from .silhouette import assess as assess_silhouette
        row['silhouette_assessment']=assess_silhouette(row,*geometry)
        from .silhouette_overlay import select_preview
        try:silhouette_preview=select_preview(preview_packet,row,*geometry)
        except Exception:silhouette_preview=None
        if self.posture_classifier:
            a=row['posture_assessment']
            row['posture_prediction']={'status':'experimental' if a['label'] else 'held','label':a['label']}
        if self.recorder:
            self.recorder.frame(row)
        diagnostics=self.posture_diagnostics.observe(row['posture_assessment'],self.region_revision)
        if failure:
            raise failure
        return {'processing_fps':self.processing_rate.observe(self.clock()), 'rgb': rgb, 'row': row, 'silhouette_preview':silhouette_preview,
                'posture_diagnostics':diagnostics, 'bed_region': self.region, 'bed_revision': self.region_revision,
                'recorded_frames': self.recorder.manifest['recorded_frames'] if self.recorder else 0}

    def close(self, outcome='succeeded', error=None, request=None, reason='stream_closed'):
        self.target_tracker.hold('input_closed')
        errors = [error] if error else []
        for resource in (self.source, self.adapter):
            try:
                resource.close()
            except Exception as exc:
                errors.append({'code': 'CLEANUP_ERROR', 'exception_type': type(exc).__name__})
        self.opened = False
        if self.recorder:
            return self.stop_measurement('failed' if errors or outcome == 'failed' else 'succeeded',
                                         errors, reason=reason, request=request)
        if errors:
            return None, {'run_status': 'failed', 'errors': errors}
        return None


class LiveWorker(threading.Thread):
    """Only this thread owns camera, SDK and recording streams; UI uses messages."""
    def __init__(self, engine):
        super().__init__(daemon=True)
        self.engine = engine
        self.commands = queue.Queue()
        self.messages = queue.Queue()
        self.frames = queue.Queue(maxsize=1)
        self.stop_requested = threading.Event()
        self.display_replaced = 0
        self.close_request = None
        self.paused = bool(getattr(engine.source, 'is_file', False))

    def submit(self, action, **values):
        request = {'requested_time_ns': str(self.engine.clock()), 'requested_utc_ns': str(self.engine.utc_clock())}
        self.commands.put((action, values, request))

    def request_close(self):
        if not self.stop_requested.is_set():
            self.close_request = {'requested_time_ns': str(self.engine.clock()), 'requested_utc_ns': str(self.engine.utc_clock())}
            self.stop_requested.set()

    def run(self):
        outcome, error = 'succeeded', None
        close_reason = 'stream_closed'
        try:
            self.engine.open()
            self.messages.put(('ready', {}))
            while not self.stop_requested.is_set():
                while not self.commands.empty():
                    action, values, request = self.commands.get_nowait()
                    try:
                        if action == 'region':
                            self.engine.set_region(**values, request=request)
                            self.messages.put(('region', {'region': self.engine.region, 'revision': self.engine.region_revision}))
                        elif action == 'target_select':
                            tracking=self.engine.target_tracker.select(values['frame_id'],values['candidate_id'],values.get('config'))
                            if self.engine.recorder:
                                self.engine.recorder.event('target_reselected',effective_stream_frame_id=self.engine.next_frame_id,
                                    request=request,selection=values,tracking=tracking)
                            self.messages.put(('target_selected',{'tracking':tracking,'selection_id':values.get('selection_id')}))
                        elif action == 'posture_mode':
                            if self.engine.recorder:raise ValueError('측정을 종료한 뒤 설정을 바꾸세요.')
                            from .automatic_posture import AutomaticClassifier,DEFAULTS,AUTO_DEFAULTS,SEPARATED_DEFAULTS
                            mode=values.get('mode')
                            if mode not in ('automatic','off') or values.get('view') not in ('auto','bed_auto','oblique','overhead'):raise ValueError('판정 방식과 촬영 각도를 확인하세요.')
                            profile=SEPARATED_DEFAULTS if values['view']=='auto' else AUTO_DEFAULTS if values['view']=='bed_auto' else dict(DEFAULTS,view=values['view'])
                            self.engine.posture_classifier=AutomaticClassifier(profile) if mode=='automatic' else None
                            model=self.engine.posture_classifier
                            self.messages.put(('posture_mode',{'profile':model.profile if model else None,'model_id':model.model_id if model else None}))
                        elif action == 'posture_reference':
                            self.engine.configure_posture(**values)
                            model=self.engine.posture_classifier
                            self.messages.put(('posture_reference',{'profile':model.profile if model else None,'model_id':model.model_id if model else None}))
                        elif action == 'start':
                            path = self.engine.start_measurement(request=request)
                            if getattr(self.engine.source, 'is_file', False):
                                self.paused = False
                                self.engine.processing_rate.reset()
                                self.messages.put(('playback', {'paused': False}))
                            self.messages.put(('started', {'directory': str(path), 'started_ns': self.engine.recorder.manifest['started_ns']}))
                        elif action == 'stop':
                            path, manifest = self.engine.stop_measurement(request=request)
                            self.messages.put(('stopped', {'directory': str(path), 'manifest': manifest}))
                            if getattr(self.engine.source, 'is_file', False):
                                self.paused = True
                                self.messages.put(('playback', {'paused': True}))
                        elif action == 'playback' and getattr(self.engine.source, 'is_file', False):
                            self.paused = bool(values['paused'])
                            self.engine.processing_rate.reset()
                            if self.engine.recorder:
                                self.engine.recorder.event('playback_changed', paused=self.paused, effective_stream_frame_id=self.engine.next_frame_id, request=request)
                            self.messages.put(('playback', {'paused': self.paused}))
                        else:
                            raise ValueError('Unknown live command')
                    except ValueError as exc:
                        if isinstance(exc, IntegrityError):
                            raise
                        self.messages.put(('command_rejected', {'message': str(exc),'action':action}))
                if self.stop_requested.is_set():
                    break
                if self.paused and self.engine.next_frame_id > 0:
                    self.stop_requested.wait(0.03)
                    continue
                try:
                    frame = self.engine.step()
                except StopIteration:
                    close_reason = 'video_eof'
                    self.messages.put(('eof', {}))
                    break
                if self.frames.full():
                    try:
                        self.frames.get_nowait()
                        self.display_replaced += 1
                    except queue.Empty:
                        pass
                frame['display_replaced'] = self.display_replaced
                self.frames.put_nowait(frame)
        except Exception as exc:
            outcome = 'failed'
            error = {'code': getattr(exc, 'code', 'LIVE_ERROR'), 'exception_type': type(exc).__name__}
            self.messages.put(('error', {'message': str(exc), **error}))
        finally:
            try:
                result = self.engine.close(outcome, error, request=self.close_request, reason=close_reason)
                if result:
                    if result[0] is not None:
                        self.messages.put(('stopped', {'directory': str(result[0]), 'manifest': result[1]}))
                    elif result[1]['run_status'] == 'failed' and error is None:
                        self.messages.put(('error', {'code': 'CLEANUP_ERROR', 'message': '장치 종료 중 오류가 발생했습니다.'}))
            except Exception as exc:
                self.messages.put(('error', {'code': 'RECORDING_ERROR', 'message': str(exc)}))
            self.messages.put(('closed', {}))
