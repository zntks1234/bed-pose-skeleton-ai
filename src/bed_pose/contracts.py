"""Model-independent benchmark contracts."""
from dataclasses import dataclass
from enum import Enum

SCHEMA_VERSION = 'benchmark-0.1-draft'

class ProcessingStatus(str, Enum):
    OK = 'ok'
    FAILED = 'failed'
    NOT_PROCESSED = 'not_processed'

@dataclass(frozen=True)
class FrameKey:
    run_id: str
    video_id: str
    frame_id: int

    def __post_init__(self):
        if not self.run_id or not self.video_id:
            raise ValueError('Frame identifiers must not be empty')
        if type(self.frame_id) is not int or self.frame_id < 0:
            raise ValueError('frame_id must be a nonnegative integer')
