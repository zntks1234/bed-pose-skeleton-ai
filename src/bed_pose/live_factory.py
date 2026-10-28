"""Construct independent engines without importing a desktop GUI."""
from pathlib import Path
import uuid
from .io_utils import atomic_json, file_hash
from .live_engine import LiveEngine


def make_engine(source, model, output_root, options_root, *, demo=False):
    if demo:
        from .pose.fake import FakeAdapter
        return LiveEngine(source, FakeAdapter(), {'execution_mode': 'ordered_sequence'},
                          output_root, execution_kind='synthetic')
    from .pose.mediapipe import MediaPipeAdapter, DEFAULT_OPTIONS, mapping_profile
    model = Path(model).expanduser().resolve()
    if not model.is_file():
        raise ValueError('추론 모델(.task)을 먼저 선택하세요.')
    options = Path(options_root)/(uuid.uuid4().hex+'.json')
    atomic_json(options, DEFAULT_OPTIONS)
    settings = {'execution_mode': 'ordered_sequence', 'requested_device': 'cpu',
                'assets': [{'role': 'pose_landmarker_task', 'path': str(model), 'sha256': file_hash(model)}],
                'adapter_options_path': str(options), 'adapter_options_sha256': file_hash(options)}
    return LiveEngine(source, MediaPipeAdapter(silhouette=True), settings, output_root, profile=mapping_profile())
