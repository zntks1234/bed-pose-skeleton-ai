"""Loopback HTML workspace. Cameras, inference and records remain in Python."""
import base64
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib.resources import files
import json
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
from .live_engine import LiveWorker
from .group_session import MeasurementGroup
from .live_factory import make_engine
from .live_sources import CameraSource, SyntheticSource, VideoFileSource, probe_cameras, named_cameras
from .io_utils import strict_loads


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


class WebWorkspace:
    def __init__(self, model=None, output_root=Path('recordings/live'), *, engine_factory=make_engine):
        self.model = Path(model or 'checkpoints/pose_landmarker_full.task').resolve()
        self.output_root = Path(output_root).resolve()
        self.temp = tempfile.TemporaryDirectory(prefix='bed-pose-browser-')
        self.temp_root = Path(self.temp.name)
        self.factory = engine_factory
        self.sessions, self.assets = {}, {}
        self.groups = {}
        self.lock = threading.RLock()
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
                source = CameraSource(index)
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
            engine = self.factory(source, model, self.output_root, self.temp_root, demo=kind == 'demo')
            worker = LiveWorker(engine)
            session_id = uuid.uuid4().hex
            state = {'id': session_id, 'title': title, 'kind': kind, 'phase': 'opening',
                     'closed': False, 'recording': False, 'pending': None, 'region': None,
                     'paused': kind == 'video_file', 'frame_id': None, 'sequence': 0,
                     'candidate_count': None, 'recorded_frames': 0, 'elapsed': 0,
                     'media_seconds': None, 'directory': None, 'integrity': None, 'error': None,
                     'width': None, 'height': None, 'posture': 'not_implemented'}
            self.sessions[session_id] = Session(session_id, title, kind, worker, state)
            worker.start()
            return {'id': session_id}

    def snapshot(self):
        with self.lock:
            # Detach mutable nested dictionaries before handing them to HTTP serialization.
            return json.loads(json.dumps({'sessions': [s.state for s in self.sessions.values()],
                                         'groups': [g.public() for g in self.groups.values()],
                                         'scan': self.scan_state, 'closing': self.stop_requested.is_set(),
                                         'model': self.model.name, 'model_available': self.model.is_file()}))

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
                    if (session.state['closed'] or session.state['phase']=='closing' or session.state['pending']
                            or session.state['recording'] or session.state['frame_id'] is None or not session.state['region']
                            or self.active_group(session.id)):
                        raise ValueError('두 입력의 연결과 침대 영역을 준비하고 개별 측정을 종료하세요.')
                tolerance=values.get('max_skew_ms')
                if tolerance is not None and (type(tolerance) not in (int,float) or not math.isfinite(tolerance) or tolerance<0 or not math.isfinite(tolerance*1_000_000)):
                    raise ValueError('허용 시간 차이에 0 이상의 유한한 ms 값을 입력하세요.')
                group=MeasurementGroup(members,self.output_root,None if tolerance is None else int(tolerance*1_000_000))
                self.groups[group.id]=group
                try:group.start()
                except Exception:
                    group.fail('START_DISPATCH_FAILED')
                    raise
                return {'group_id':group.id}
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
                raise ValueError('그룹 측정 중입니다. 그룹 종료 버튼을 사용하세요.')
            if action in ('close', 'remove'):
                session.remove = action == 'remove'
                if session.remove and state['closed']:
                    del self.sessions[session_id]
                else:
                    state['phase'] = 'closing'
                    session.worker.request_close()
                return
            if state['closed'] or state['phase'] == 'closing' or state['pending']:
                raise ValueError('이전 작업이 끝난 뒤 다시 조작하세요.')
            if action == 'region':
                if state['frame_id'] is None:
                    raise ValueError('첫 영상을 기다려 주세요.')
                box = values.get('box')
                if box is not None and (not isinstance(box, list) or len(box) != 4 or
                        any(type(x) not in (int, float) or not math.isfinite(x) for x in box)):
                    raise ValueError('영역 좌표가 올바르지 않습니다.')
                selected_id = values.get('selected_frame_id')
                if type(selected_id) is not int or not 0 <= selected_id <= state['frame_id']:
                    raise ValueError('영역을 지정한 영상 프레임이 유효하지 않습니다.')
                session.worker.submit('region', box=box, width=state['width'], height=state['height'],
                                      selected_frame_id=selected_id)
            elif action == 'start':
                if state['frame_id'] is None or not state['region'] or state['recording']:
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
        elif kind == 'playback':
            state['paused'] = value['paused']
            if state['pending'] == 'playback':
                state['pending'] = None
        elif kind in ('error', 'command_rejected'):
            state.update(error=value['message'], pending=None)
            if kind == 'error':
                state['phase'] = 'error'
                state['candidate_count'] = None
                session.view = None  # Never send a previous observation as a current failed frame.
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

    def _refresh(self, session):
        while True:
            try:
                self._message(session, *session.worker.messages.get_nowait())
            except queue.Empty:
                break
        state = session.state
        try:
            frame = session.worker.frames.get_nowait()
        except queue.Empty:
            return
        if state['phase'] == 'error':
            return
        import cv2
        rgb, row = frame['rgb'], frame['row']
        height, width = rgb.shape[:2]
        ratio = min(1, 1280/max(width, height))
        preview = cv2.resize(rgb, (max(1, round(width*ratio)), max(1, round(height*ratio)))) if ratio < 1 else rgb
        ok, encoded = cv2.imencode('.jpg', cv2.cvtColor(preview, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ok:
            raise ValueError('브라우저 미리보기 영상을 만들지 못했습니다.')
        media = row.get('source_media')
        session.sequence += 1
        state.update(frame_id=row['stream_frame_id'], sequence=session.sequence, width=width, height=height,
                     candidate_count=row['candidate_count'],
                     media_seconds=int(media['relative_time_ns'])/1e9 if media else None)
        if state['recording'] and int(row['received_ns']) >= int(state['started_ns']):
            state['recorded_frames'] = frame['recorded_frames']
            state['elapsed'] = (int(row['received_ns'])-int(state['started_ns']))/1e9
        session.view = {'sequence': session.sequence, 'frame_id': row['stream_frame_id'],
                        'width': width, 'height': height, 'people': row['mapped_people'],
                        'candidate_count': row['candidate_count'],
                        'inference_ms': (int(row['inference_finished_ns'])-int(row['inference_started_ns']))/1e6,
                        'read_ms': (int(row['received_ns'])-int(row['read_started_ns']))/1e6,
                        'media_seconds': int(media['relative_time_ns'])/1e9 if media else None,
                        'image': 'data:image/jpeg;base64,'+base64.b64encode(encoded).decode('ascii')}

    def _monitor(self):
        while not self.monitor_stop.wait(.015):
            with self.lock:
                for session in list(self.sessions.values()):
                    try:
                        self._refresh(session)
                    except Exception as exc:
                        self._message(session, 'error', {'message': '화면 전달 오류: '+str(exc)})
                        session.worker.request_close()
                    if session.remove and session.state['closed']:
                        self.sessions.pop(session.id, None)

                for group in self.groups.values():
                    try:group.tick()
                    except Exception:
                        group.failed=True
                        group.data["phase"]="failed"
                        group.data["ledger_complete"]=False
                        group.data["errors"].append({"code":"GROUP_WRITE_FAILED"})
                        group.finished=True
                        for member in group.members:member.worker.request_close()

    def view(self, session_id):
        with self.lock:
            return self.sessions[session_id].view

    def close(self):
        self.stop_requested.set()
        with self.lock:
            sessions = list(self.sessions.values())
            for session in sessions:
                session.worker.request_close()
        # Wait for owners to finalize records. Do not delete assets while they are in use.
        while any(s.worker.is_alive() for s in sessions):
            for session in sessions:
                session.worker.join(timeout=.1)
        with self.lock:
            for session in sessions:self._refresh(session)
            for group in self.groups.values():group.tick()
        self.monitor_stop.set()
        self.monitor.join(timeout=2)
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

    def _reply(self, status, value, mime='application/json; charset=utf-8'):
        body = json.dumps(value, ensure_ascii=False, allow_nan=False).encode() if mime.startswith('application/json') else value
        self.send_response(status)
        self.send_header('Content-Type', mime)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        self.wfile.write(body)

    def _authorized(self):
        origin = self.headers.get('Origin')
        return (self.headers.get('Host') == self.server.origin.removeprefix('http://')
                and (origin is None or origin == self.server.origin)
                and secrets.compare_digest(self.headers.get('X-BedPose-Token', ''), self.server.token))

    def do_GET(self):
        try:
            path = urlsplit(self.path).path
            if path == '/':
                if self.headers.get('Host') != self.server.origin.removeprefix('http://'):
                    return self._reply(403, {'error': 'Invalid host'})
                return self._reply(200, files('bed_pose').joinpath('templates/live_workspace.html').read_bytes(), 'text/html; charset=utf-8')
            if not self._authorized():
                return self._reply(403, {'error': '작업실 실행 주소로 다시 접속하세요.'})
            if path == '/api/state':
                return self._reply(200, self.server.workspace.snapshot())
            if path.startswith('/api/view/'):
                return self._reply(200, self.server.workspace.view(path.split('/')[-1]))
            self._reply(404, {'error': 'Not found'})
        except KeyError:
            self._reply(404, {'error': '입력을 찾을 수 없습니다.'})
        except (BrokenPipeError, ConnectionResetError):
            pass

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
                   video=None, *, port=0, open_browser=True):
    workspace = WebWorkspace(model, output_root)
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
