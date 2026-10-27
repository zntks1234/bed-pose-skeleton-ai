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
