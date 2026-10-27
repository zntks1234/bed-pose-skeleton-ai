"""Camera RGB input and an explicitly synthetic source for development checks."""
import math
import time
import numpy as np
from .contracts import SourceError


class CameraSource:
    def __init__(self, camera_index=0):
        if type(camera_index) is not int or camera_index < 0:
            raise ValueError('Camera index must be a nonnegative integer')
        self.index, self.capture = camera_index, None

    def open(self):
        import cv2
        self.cv2 = cv2
        self.capture = cv2.VideoCapture(self.index, cv2.CAP_ANY)
        if not self.capture.isOpened():
            self.close()
            raise SourceError('카메라를 열 수 없습니다. 연결·권한·장치 번호를 확인하세요.')
        rate = self.capture.get(cv2.CAP_PROP_FPS)
        return {'kind': 'camera', 'camera_index': self.index,
                'backend': self.capture.getBackendName(), 'opencv_version': cv2.__version__,
                'driver_reported_fps': rate if math.isfinite(rate) and rate > 0 else None,
                'timestamp_source': 'received_after_read', 'exposure_timestamp_available': False,
                'hardware_dropped_frames': None, 'pixel_format': 'rgb24', 'mirror': False}

    def read(self):
        ok, bgr = self.capture.read()
        if not ok or bgr is None:
            raise SourceError('카메라 프레임 수신이 중단되었습니다.')
        return self.cv2.cvtColor(bgr, self.cv2.COLOR_BGR2RGB)

    def close(self):
        if self.capture is not None:
            capture, self.capture = self.capture, None
            capture.release()


class SyntheticSource:
    def __init__(self, interval=0.1):
        self.interval, self.index = interval, 0

    def open(self):
        return {'kind': 'synthetic', 'timestamp_source': 'received_after_read',
                'exposure_timestamp_available': False, 'hardware_dropped_frames': None,
                'pixel_format': 'rgb24', 'mirror': False}

    def read(self):
        if self.interval:
            time.sleep(self.interval)
        image = np.zeros((360, 640, 3), dtype=np.uint8)
        image[:] = [24, 35, 51]
        image[80:280, 120:520] = [55, 70, 87]
        x = 130 + self.index % 300
        image[150:190, x:x+30] = [100, 155, 180]
        self.index += 1
        return image

    def close(self):
        pass


class VideoFileSource:
    """Sequential file replay. Never uses decoder wall time as media/model time."""
    is_file = True

    def __init__(self, path):
        from pathlib import Path
        self.path = Path(path).resolve()
        self.container = None
        self.media = None
        self.sha256 = None

    def open(self):
        import av
        from .video import _stream, decoder_profile
        from .io_utils import file_hash
        if not self.path.is_file():
            raise SourceError('영상 파일을 찾을 수 없습니다.')
        self.container = av.open(str(self.path))
        stream = _stream(self.container)
        self.frames = iter(self.container.decode(stream))
        self.first_time = self.last_time = None
        self.index = 0
        self.sha256 = file_hash(self.path)
        return {'kind': 'video_file', 'path': str(self.path), 'sha256': self.sha256,
                'decoder': decoder_profile(), 'timestamp_source': 'received_after_read',
                'model_timestamp_source': 'relative_media_pts', 'playback': 'processing_speed_no_skip',
                'exposure_timestamp_available': False, 'hardware_dropped_frames': None,
                'pixel_format': 'rgb24', 'mirror': False}

    def read(self):
        from .video import canonical_rgb, frame_spec, frame_time
        frame = next(self.frames)  # StopIteration means normal EOF, not camera failure.
        rgb = canonical_rgb(frame)
        spec = frame_spec(frame, rgb, str(self.path), self.index)
        current = frame_time(spec)
        if current is None or self.last_time is not None and current <= self.last_time:
            raise SourceError('영상 PTS가 없거나 증가하지 않아 연속 분석을 중단했습니다.')
        if self.first_time is None:
            self.first_time = current
        self.last_time = current
        self.media = {k: spec[k] for k in ('source_pts', 'time_base_num', 'time_base_den', 'pixel_sha256')}
        self.media.update(source_frame_id=self.index, relative_time_ns=str(int((current-self.first_time)*1_000_000_000)))
        self.index += 1
        return rgb

    def close(self):
        if self.container is not None:
            container, self.container = self.container, None
            container.close()
            from .io_utils import file_hash
            if self.sha256 is not None and file_hash(self.path) != self.sha256:
                raise SourceError('분석 도중 원본 영상이 변경되었습니다.')


def probe_cameras(indices=range(6), excluded=()):
    """Explicit bounded probe; OpenCV has no portable friendly-name enumeration."""
    import cv2
    found = []
    for index in indices:
        if index in excluded:
            continue
        capture = cv2.VideoCapture(index, cv2.CAP_ANY)
        try:
            if capture.isOpened():
                ok, frame = capture.read()
                if ok and frame is not None:
                    found.append(index)
        finally:
            capture.release()
    return found
