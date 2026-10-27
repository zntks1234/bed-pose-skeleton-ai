"""Append-only frame ledger; completion and execution outcome are independent."""
import json
import os
from pathlib import Path


class FrameLedger:
    def __init__(self, directory, expected_frames):
        if type(expected_frames) is not int or expected_frames < 1:
            raise ValueError('expected_frames must be positive')
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=False)
        self.expected = expected_frames
        self.count = 0
        self.errors = 0
        self.closed = False
        self._manifest('running', False)
        self.stream = (self.directory / 'frames.jsonl').open('x', encoding='utf-8')

    def _manifest(self, outcome, complete):
        temp = self.directory / 'manifest.tmp'
        with temp.open('w', encoding='utf-8') as stream:
            json.dump({'run_status': outcome, 'ledger_complete': complete,
                       'expected_frames': self.expected, 'recorded_frames': self.count},
                      stream, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp, self.directory / 'manifest.json')

    def append(self, frame_id, status, payload=None):
        if self.closed or frame_id != self.count or self.count >= self.expected:
            raise ValueError('Frames must be written once in manifest order')
        if status not in ('ok', 'failed', 'not_processed'):
            raise ValueError('Invalid processing status')
        line = json.dumps({'frame_id': frame_id, 'processing_status': status,
                           'payload': payload}, allow_nan=False)
        self.stream.write(line + '\n')
        self.stream.flush()
        self.count += 1
        self.errors += status != 'ok'

    def finalize(self, outcome):
        if self.closed or outcome not in ('succeeded', 'failed', 'cancelled'):
            raise ValueError('Invalid finalization')
        if self.count != self.expected or (outcome == 'succeeded' and self.errors):
            raise ValueError('Cannot declare successful or complete execution')
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.stream.close()
        self.closed = True
        self._manifest(outcome, True)

    def close(self):
        if not self.closed:
            self.stream.close()
            self.closed = True
