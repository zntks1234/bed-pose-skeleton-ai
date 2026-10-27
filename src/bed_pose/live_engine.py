"""Single-owner live capture/inference/measurement lifecycle, independent of GUI."""
from dataclasses import asdict
from pathlib import Path
import platform
import queue
import threading
import time
import uuid
import numpy as np
from .contracts import FramePacket, ModelInput, IntegrityError
from .mapping import MappingProfile, map_keypoints, raw_json_value
from .live_recording import LiveRecorder, make_region
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
            expected = 'synthetic' if self.execution_kind == 'synthetic' else 'camera'
            if self.source_profile['kind'] != expected:
                raise ValueError('Live input cannot silently switch to synthetic data')
            self.opened = True
        except Exception:
            self.close('failed')
            raise

    def set_region(self, box, width, height, request=None, selected_frame_id=None):
        if self.geometry != (width, height):
            raise ValueError('최신 영상 크기에 맞춰 침대 영역을 다시 지정하세요.')
        if selected_frame_id is not None and (type(selected_frame_id) is not int or not 0 <= selected_frame_id < self.next_frame_id):
            raise ValueError('영역을 지정한 미리보기 프레임이 유효하지 않습니다.')
        region = make_region(box, width, height) if box is not None else None
        self.region_revision += 1
        self.region = region
        self.region_selection = {'selected_stream_frame_id': selected_frame_id,
                                 'applied_time_ns': str(self.clock()), 'applied_utc_ns': str(self.utc_clock()),
                                 'effective_stream_frame_id': self.next_frame_id, 'request': request}
        if self.recorder:
            self.recorder.event('bed_region_changed', region=region, revision=self.region_revision,
                                effective_stream_frame_id=self.next_frame_id, request=request, selection=self.region_selection)
        return self.region

    def start_measurement(self, request=None):
        if not self.opened or self.geometry is None or self.region is None:
            raise ValueError('영상이 표시된 뒤 침대 영역을 먼저 지정하세요.')
        if self.recorder:
            raise ValueError('이미 측정 중입니다.')
        from .runner import _code_version
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
                    'video_recording': False, 'tracking_scope': 'camera_stream',
                    'preview_tracking_history_retained': True, 'hardware_dropped_frames': None, 'start_request': request,
                    'target_policy': 'none', 'posture_classifier': 'not_implemented', 'event_analyzer': 'not_implemented'}
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
        timestamp = received // 1_000_000
        row = {'stream_id': self.stream_id, 'stream_frame_id': frame_id, 'clock_id': self.clock_id,
               'read_started_ns': str(read_started), 'received_ns': str(received), 'received_utc_ns': str(utc),
               'timestamp_source': 'received_after_read', 'camera_exposure_ns': None,
               'model_timestamp_ms': str(timestamp), 'inference_started_ns': None,
               'inference_finished_ns': None, 'mapping_finished_ns': None,
               'processing_status': 'ok', 'candidate_count': None, 'raw_candidates': None,
               'mapped_people': None, 'sdk_call_started': False, 'error': None,
               'bed_region_revision': self.region_revision,
               'posture_prediction': {'status': 'not_implemented', 'label': None},
               'event_predictions': [], 'event_analysis_status': 'not_implemented',
               'bed_occupancy_status': 'not_implemented',
               'target_resolution': {'status': 'not_configured', 'candidate_id': None}, 'target_posture': None,
               'verified_gt': None, 'sensor_results': None}
        failure = None
        stage = 'inference'
        try:
            if self.last_model_ms is not None and timestamp <= self.last_model_ms:
                raise LiveFailure('MODEL_TIMESTAMP_COLLISION', '모델 입력 시각이 중복되었습니다.')
            row['inference_started_ns'] = str(self.clock())
            self.last_model_ms = timestamp
            output = self.adapter.estimate(ModelInput(FramePacket(self.stream_id, frame_id, rgb, {}), timestamp))
            row['sdk_call_started'] = output.sdk_call_started
            if output.model_timestamp_ms != timestamp:
                raise ValueError('Adapter timestamp mismatch')
            row['inference_finished_ns'] = str(self.clock())
            row['candidate_count'] = len(output.candidates)
            row['raw_candidates'] = raw_json_value(output.candidates)
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
        if self.recorder:
            self.recorder.frame(row)
        if failure:
            raise failure
        return {'rgb': rgb, 'row': row, 'bed_region': self.region, 'bed_revision': self.region_revision,
                'recorded_frames': self.recorder.manifest['recorded_frames'] if self.recorder else 0}

    def close(self, outcome='succeeded', error=None, request=None):
        errors = [error] if error else []
        for resource in (self.source, self.adapter):
            try:
                resource.close()
            except Exception as exc:
                errors.append({'code': 'CLEANUP_ERROR', 'exception_type': type(exc).__name__})
        self.opened = False
        if self.recorder:
            return self.stop_measurement('failed' if errors or outcome == 'failed' else 'succeeded',
                                         errors, reason='stream_closed', request=request)
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

    def submit(self, action, **values):
        request = {'requested_time_ns': str(self.engine.clock()), 'requested_utc_ns': str(self.engine.utc_clock())}
        self.commands.put((action, values, request))

    def request_close(self):
        if not self.stop_requested.is_set():
            self.close_request = {'requested_time_ns': str(self.engine.clock()), 'requested_utc_ns': str(self.engine.utc_clock())}
            self.stop_requested.set()

    def run(self):
        outcome, error = 'succeeded', None
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
                        elif action == 'start':
                            path = self.engine.start_measurement(request=request)
                            self.messages.put(('started', {'directory': str(path), 'started_ns': self.engine.recorder.manifest['started_ns']}))
                        elif action == 'stop':
                            path, manifest = self.engine.stop_measurement(request=request)
                            self.messages.put(('stopped', {'directory': str(path), 'manifest': manifest}))
                        else:
                            raise ValueError('Unknown live command')
                    except ValueError as exc:
                        if isinstance(exc, IntegrityError):
                            raise
                        self.messages.put(('command_rejected', {'message': str(exc)}))
                if self.stop_requested.is_set():
                    break
                frame = self.engine.step()
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
                result = self.engine.close(outcome, error, request=self.close_request)
                if result:
                    if result[0] is not None:
                        self.messages.put(('stopped', {'directory': str(result[0]), 'manifest': result[1]}))
                    elif result[1]['run_status'] == 'failed' and error is None:
                        self.messages.put(('error', {'code': 'CLEANUP_ERROR', 'message': '장치 종료 중 오류가 발생했습니다.'}))
            except Exception as exc:
                self.messages.put(('error', {'code': 'RECORDING_ERROR', 'message': str(exc)}))
            self.messages.put(('closed', {}))
