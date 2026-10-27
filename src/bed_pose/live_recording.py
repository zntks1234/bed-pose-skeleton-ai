"""Live recording contract: received timestamps, explicit unknowns, no video data."""
from collections import Counter
from pathlib import Path
import math
import os
from .contracts import IntegrityError
from .io_utils import atomic_json, file_hash, json_text, load_json, strict_loads, object_hash

LIVE_SCHEMA = 'live-0.1-draft'
FILES = ('live_frames.jsonl', 'control_events.jsonl')


def unsigned_ns(value):
    if not isinstance(value, str) or not value.isascii() or not value.isdigit():
        raise IntegrityError('Invalid live timestamp')
    return int(value)


def validate_region(region, width, height):
    if (not isinstance(region, dict) or set(region) != {'x1', 'y1', 'x2', 'y2', 'width', 'height', 'normalized', 'method'}
            or region['width'] != width or region['height'] != height or region['method'] != 'manual_rectangle'):
        raise ValueError('침대 영역의 영상 크기 또는 형식이 맞지 않습니다.')
    box = [region[k] for k in ('x1', 'y1', 'x2', 'y2')]
    if any(type(v) not in (int, float) or not math.isfinite(v) for v in box):
        raise ValueError('침대 영역 좌표가 유효하지 않습니다.')
    x1, y1, x2, y2 = box
    if not 0 <= x1 < x2 <= width or not 0 <= y1 < y2 <= height:
        raise ValueError('침대 영역을 영상 안의 사각형으로 지정하세요.')
    expected = [x1/width, y1/height, x2/width, y2/height]
    if region['normalized'] != expected:
        raise ValueError('침대 영역 정규화 좌표가 맞지 않습니다.')


def make_region(box, width, height):
    x1, y1, x2, y2 = box
    region = {'x1': x1, 'y1': y1, 'x2': x2, 'y2': y2, 'width': width, 'height': height,
              'normalized': [x1/width, y1/height, x2/width, y2/height], 'method': 'manual_rectangle'}
    validate_region(region, width, height)
    return region


def validate_selection(selection, effective_frame):
    if (selection['effective_stream_frame_id'] != effective_frame
            or type(effective_frame) is not int or effective_frame < 0):
        raise IntegrityError('Invalid bed selection frame boundary')
    selected = selection['selected_stream_frame_id']
    if selected is not None and (type(selected) is not int or not 0 <= selected < effective_frame):
        raise IntegrityError('Invalid selected preview frame')
    applied = unsigned_ns(selection['applied_time_ns'])
    unsigned_ns(selection['applied_utc_ns'])
    if selection['request'] is not None and unsigned_ns(selection['request']['requested_time_ns']) > applied:
        raise IntegrityError('Bed selection request occurs after application')
    return applied


def _verify(directory, manifest, hashes=True):
    if (any(type(manifest[k]) is not int or manifest[k] < 1 for k in ('width','height','initial_bed_revision'))
            or type(manifest['recorded_frames']) is not int or manifest['recorded_frames'] < 0
            or type(manifest['recorded_events']) is not int or manifest['recorded_events'] < 2
            or any(type(manifest['counts'][k]) is not int or manifest['counts'][k] < 0 for k in ('ok','failed'))):
        raise IntegrityError('Invalid live manifest counters or geometry')
    if manifest['schema_version'] != LIVE_SCHEMA:
        raise IntegrityError('Unknown live schema')
    for key in ('adapter_profile','source_profile','mapping_profile','requested_settings'):
        if object_hash(manifest[key]) != manifest[key+'_sha256']:
            raise IntegrityError('Live profile/settings checksum mismatch')
    if manifest['execution_mode'] != manifest['requested_settings']['execution_mode']:
        raise IntegrityError('Live execution mode mismatch')
    if hashes:
        if manifest['ledger_complete'] is not True or manifest['run_status'] not in ('succeeded', 'failed'):
            raise IntegrityError('Live measurement is incomplete')
        if set(manifest['artifact_sha256']) != set(FILES) or any(
                file_hash(directory/name) != manifest['artifact_sha256'][name] for name in FILES):
            raise IntegrityError('Live artifact checksum mismatch')
    region = manifest['initial_bed_region']
    validate_region(region, manifest['width'], manifest['height'])
    selection = manifest['initial_bed_selection']
    if (selection['effective_stream_frame_id'] > manifest['first_stream_frame_id']
            or validate_selection(selection, selection['effective_stream_frame_id']) > unsigned_ns(manifest['started_ns'])):
        raise IntegrityError('Initial bed selection occurs after measurement start')
    revision = manifest['initial_bed_revision']
    changes = []
    event_types = []
    previous_effective_id = manifest['first_stream_frame_id']
    with (directory/'control_events.jsonl').open(encoding='utf-8') as stream:
        previous_time = 0
        for index, line in enumerate(stream):
            event = strict_loads(line)
            if (event['event_index'] != index or event['measurement_id'] != manifest['measurement_id']
                    or event['clock_id'] != manifest['clock_id'] or unsigned_ns(event['time_ns']) < previous_time):
                raise IntegrityError('Invalid control event identity/order')
            previous_time = unsigned_ns(event['time_ns'])
            request = event.get('request')
            if request is not None:
                if unsigned_ns(request['requested_time_ns']) > previous_time:
                    raise IntegrityError('Control request occurs after its application')
                unsigned_ns(request['requested_utc_ns'])
            event_types.append(event['type'])
            effective_id = event['effective_stream_frame_id']
            if type(effective_id) is not int or not previous_effective_id <= effective_id <= manifest['first_stream_frame_id']+manifest['recorded_frames']:
                raise IntegrityError('Invalid event frame boundary')
            previous_effective_id = effective_id
            if event['type'] == 'bed_region_changed':
                if validate_selection(event['selection'], effective_id) > previous_time:
                    raise IntegrityError('Bed selection metadata occurs after the control event')
                if event['revision'] <= revision:
                    raise IntegrityError('Bed revisions are not increasing')
                revision = event['revision']
                if event['region'] is not None:
                    validate_region(event['region'], manifest['width'], manifest['height'])
                changes.append((event['effective_stream_frame_id'], revision))
    if (not event_types or event_types[0] != 'measurement_started' or event_types[-1] != 'measurement_stopped'
            or event_types.count('measurement_started') != 1 or event_types.count('measurement_stopped') != 1
            or len(event_types) != manifest['recorded_events']
            or any(kind not in ('measurement_started', 'measurement_stopped', 'bed_region_changed') for kind in event_types)):
        raise IntegrityError('Live measurement control events are incomplete')
    last_event_time = previous_time
    counts = Counter(ok=0, failed=0)
    previous_id, previous_time, previous_model_ms = -1, 0, None
    with (directory/'live_frames.jsonl').open(encoding='utf-8') as stream:
        for index, line in enumerate(stream):
            row = strict_loads(line)
            if (row['schema_version'] != LIVE_SCHEMA or row['measurement_id'] != manifest['measurement_id']
                    or row['frame_id'] != index or row['stream_id'] != manifest['stream_id']
                    or row['clock_id'] != manifest['clock_id']
                    or row['stream_frame_id'] != manifest['first_stream_frame_id'] + index):
                raise IntegrityError('Invalid live frame identity/order')
            previous_id = row['stream_frame_id']
            expected_revision = manifest['initial_bed_revision']
            for effective_id, change_revision in changes:
                if effective_id <= previous_id:
                    expected_revision = change_revision
            if row['bed_region_revision'] != expected_revision:
                raise IntegrityError('Live frame references the wrong bed revision')
            for field in ('read_started_ns', 'received_ns', 'inference_started_ns', 'inference_finished_ns', 'mapping_finished_ns', 'record_started_ns'):
                value = row[field]
                if value is not None:
                    value = unsigned_ns(value)
                    if value < previous_time:
                        raise IntegrityError('Live frame timing is not monotonic')
                    previous_time = value
            unsigned_ns(row['received_utc_ns'])
            if row['camera_exposure_ns'] is not None or row['timestamp_source'] != 'received_after_read':
                raise IntegrityError('Unverified camera exposure timestamp')
            model_ms = unsigned_ns(row['model_timestamp_ms'])
            if model_ms != unsigned_ns(row['received_ns']) // 1_000_000:
                raise IntegrityError('Live SDK time differs from the recorded receive time')
            collision = (row['processing_status'] == 'failed' and row['error'] is not None
                         and row['error']['code'] == 'MODEL_TIMESTAMP_COLLISION' and not row['sdk_call_started'])
            if previous_model_ms is not None and model_ms <= previous_model_ms and not collision:
                raise IntegrityError('Live model timestamp is not increasing')
            if not collision:
                previous_model_ms = model_ms
            if (row['posture_prediction'] != {'status': 'not_implemented', 'label': None}
                    or row['event_predictions'] != [] or row['event_analysis_status'] != 'not_implemented'
                    or row['bed_occupancy_status'] != 'not_implemented'
                    or row['target_resolution'] != {'status': 'not_configured', 'candidate_id': None}
                    or any(row[k] is not None for k in ('target_posture', 'verified_gt', 'sensor_results'))):
                raise IntegrityError('Unsupported live prediction or label injection')
            status = row['processing_status']
            if status not in counts:
                raise IntegrityError('Unknown live frame status')
            if status == 'ok':
                if row['candidate_count'] != len(row['raw_candidates']) or row['candidate_count'] != len(row['mapped_people']):
                    raise IntegrityError('Live candidate count mismatch')
                if [p['candidate_id'] for p in row['raw_candidates']] != [p['candidate_id'] for p in row['mapped_people']]:
                    raise IntegrityError('Live candidate identity mismatch')
                if row['error'] is not None:
                    raise IntegrityError('Successful frame has an error')
            elif row['error'] is None:
                raise IntegrityError('Failed frame has no error')
            counts[status] += 1
    if dict(counts) != manifest['counts'] or sum(counts.values()) != manifest['recorded_frames']:
        raise IntegrityError('Live frame counters differ')
    if manifest['run_status'] == 'succeeded' and (counts['failed'] or manifest['errors']):
        raise IntegrityError('Failed live measurement declared successful')
    if unsigned_ns(manifest['finished_ns']) < max(previous_time, last_event_time, unsigned_ns(manifest['started_ns'])):
        raise IntegrityError('Invalid live recording end time')
    return dict(counts)


def verify_live(directory):
    directory = Path(directory)
    try:
        manifest = load_json(directory/'manifest.json')
        counts = _verify(directory, manifest)
        return {'measurement_id': manifest['measurement_id'], 'run_status': manifest['run_status'],
                'ledger_complete': True, 'counts': counts, 'integrity': 'verified'}
    except IntegrityError:
        raise
    except Exception as exc:
        raise IntegrityError(f'Live record validation failed ({type(exc).__name__})') from exc


class LiveRecorder:
    def __init__(self, directory, manifest, clock):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.clock, self.broken = clock, False
        self.streams = {}
        self.event_count = 0
        self.manifest = dict(manifest, recorded_events=0, schema_version=LIVE_SCHEMA, run_status='recording',
                             ledger_complete=False, artifact_sha256={}, recorded_frames=0,
                             counts={'ok': 0, 'failed': 0}, errors=[])
        atomic_json(self.directory/'manifest.json', self.manifest)
        try:
            for name in FILES:
                self.streams[name] = (self.directory/name).open('x', encoding='utf-8', newline='\n')
        except Exception:
            self.broken = True
            self.close()
            raise

    def _write(self, name, row):
        if self.broken:
            raise IntegrityError('Live recorder is incomplete')
        try:
            self.streams[name].write(json_text(row)+'\n')
            self.streams[name].flush()
        except Exception:
            self.broken = True
            raise IntegrityError('Live record write failed') from None

    def event(self, kind, **values):
        self._write('control_events.jsonl', dict(values, type=kind, event_index=self.event_count,
            measurement_id=self.manifest['measurement_id'], clock_id=self.manifest['clock_id'], time_ns=str(self.clock())))
        self.event_count += 1
        self.manifest['recorded_events'] = self.event_count

    def frame(self, row):
        row = dict(row, schema_version=LIVE_SCHEMA, measurement_id=self.manifest['measurement_id'],
                   frame_id=self.manifest['recorded_frames'], record_started_ns=str(self.clock()))
        self._write('live_frames.jsonl', row)
        self.manifest['recorded_frames'] += 1
        self.manifest['counts'][row['processing_status']] += 1

    def close(self):
        errors = []
        for stream in self.streams.values():
            if not stream.closed:
                try:
                    stream.flush()
                    os.fsync(stream.fileno())
                except Exception as exc:
                    errors.append(exc)
                finally:
                    try:
                        stream.close()
                    except Exception as exc:
                        errors.append(exc)
        if errors:
            self.broken = True
            raise errors[0]

    def finalize(self, outcome='succeeded', errors=()):
        self.manifest.update(run_status=outcome, errors=list(errors))
        try:
            self.close()
            self.manifest['finished_ns'] = str(self.clock())
            if self.broken:
                raise IntegrityError('Live recording failed')
            _verify(self.directory, self.manifest, hashes=False)
            self.manifest['artifact_sha256'] = {name: file_hash(self.directory/name) for name in FILES}
            self.manifest['ledger_complete'] = True
            atomic_json(self.directory/'manifest.json', self.manifest)
            return self.manifest
        except Exception:
            self.manifest.update(run_status='failed', ledger_complete=False)
            self.manifest['errors'].append({'code': 'RECORDING_ERROR'})
            atomic_json(self.directory/'manifest.json', self.manifest)
            raise
