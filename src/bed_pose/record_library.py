"""Read-only, root-confined browsing of original live measurement records."""
from array import array
from collections import OrderedDict
from pathlib import Path
from .pose_display import display_people
import re
import threading

from .contracts import IntegrityError
from .io_utils import file_hash,load_json,strict_loads
from .live_recording import FILES,SUPPORTED_SCHEMAS,verify_live

ID=re.compile(r'[0-9a-f]{32}')


def pagination(offset,limit):
    if type(offset) is not int or offset<0 or type(limit) is not int or not 1<=limit<=100:
        raise ValueError('페이지 위치는 0 이상, 한 페이지는 1~100개여야 합니다.')


def confined_files(directory):
    for name in ('manifest.json',)+FILES:
        path=directory/name
        if path.is_symlink() or path.resolve().parent!=directory or not path.is_file():
            raise ValueError('기록 파일이 없거나 지원하지 않는 경로입니다.')
        if name=='manifest.json' and path.stat().st_size>4*1024**2:
            raise ValueError('기록 요약 파일이 지원 범위를 넘습니다.')


def metadata(manifest,record_id):
    if (not isinstance(manifest,dict) or manifest.get('measurement_id')!=record_id
            or manifest.get('schema_version') not in SUPPORTED_SCHEMAS):
        raise ValueError('지원하는 측정 기록이 아닙니다.')
    finished=manifest.get('ledger_complete') is True and manifest.get('run_status') in ('succeeded','failed')
    source=manifest.get('source_profile') or {}
    if (not isinstance(source,dict) or type(manifest.get('recorded_frames')) is not int
            or manifest['recorded_frames']<0 or manifest.get('run_status') not in ('recording','succeeded','failed')):
        raise ValueError('기록 요약 형식이 맞지 않습니다.')
    utc=manifest.get('started_utc_ns')
    if not isinstance(utc,str) or len(utc)>24 or not utc.isascii() or not utc.isdigit():utc=None
    return {'record_id':record_id,'started_utc_ns':utc,
            'source_kind':source.get('kind') if source.get('kind') in ('camera','video_file','synthetic') else None,
            'execution_kind':manifest.get('execution_kind') if manifest.get('execution_kind') in ('model_inference','synthetic') else None,
            'run_status':manifest.get('run_status'),'recorded_frames':manifest.get('recorded_frames'),
            'classifier_id':manifest.get('posture_classifier') if isinstance(manifest.get('posture_classifier'),str) else None,
            'availability':'ready' if finished else 'incomplete',
            'integrity':'not_checked','video_recording':manifest.get('video_recording',False)}


class OpenRecord:
    def __init__(self,directory,record_id):
        self.directory=directory
        confined_files(directory)
        initial_hash=file_hash(directory/'manifest.json')
        verify_live(directory)  # Pure replay/checks only; no SDK or source video.
        self.manifest=load_json(directory/'manifest.json')
        self.manifest_hash=initial_hash
        self.meta=metadata(self.manifest,record_id)
        if self.meta['availability']!='ready':raise ValueError('측정 종료 후 기록을 열 수 있습니다.')
        self.check()
        self.offsets=array('Q')
        with (directory/'live_frames.jsonl').open('rb') as stream:
            while True:
                position=stream.tell()
                if not stream.readline():break
                self.offsets.append(position)
        if len(self.offsets)!=self.manifest['recorded_frames']:raise ValueError('기록 프레임 수가 변경되었습니다.')
        self.check()
        self.timeline_cache=OrderedDict()
        self.timeline_lock=threading.Lock()
        self.image_lock=threading.Lock()

    def check(self):
        confined_files(self.directory)
        if (file_hash(self.directory/'manifest.json')!=self.manifest_hash or any(
                file_hash(self.directory/name)!=self.manifest['artifact_sha256'][name] for name in FILES)):
            raise ValueError('열어 둔 기록이 변경되었습니다. 기록 목록에서 다시 확인하세요.')

    def page(self,offset,limit):
        pagination(offset,limit);self.check()
        rows=[]
        with (self.directory/'live_frames.jsonl').open('rb') as stream:
            for i in range(offset,min(offset+limit,len(self.offsets))):
                stream.seek(self.offsets[i]);row=strict_loads(stream.readline().decode('utf-8'))
                a=row.get('posture_assessment')
                assessment=None if a is None else {k:a.get(k) for k in (
                    'status','label','reasons','candidate_id','track_id','classifier_id','quality_status')}
                orientation=(a or {}).get('rule_features',{}).get('orientation_decision',{})
                rows.append({'frame_id':row['frame_id'],'stream_frame_id':row['stream_frame_id'],
                    'clock_id':row['clock_id'],'received_ns':row['received_ns'],
                    'received_elapsed_ns':str(int(row['received_ns'])-int(self.manifest['started_ns'])),
                    'source_media':row.get('source_media'),'processing_status':row['processing_status'],
                    'candidate_count':row['candidate_count'],'assessment':assessment,
                    'score_decision':(a or {}).get('rule_features',{}).get('score_decision'),
                    'body_assessment':(a or {}).get('rule_features',{}).get('body_assessment'),
                    'body_state':(a or {}).get('rule_features',{}).get('body_state'),
                    'bed_relation':(a or {}).get('rule_features',{}).get('bed_relation'),
                    'context_assessment':(a or {}).get('rule_features',{}).get('context_assessment'),
                    'silhouette_assessment':row.get('silhouette_assessment'),
                    'decision_source':orientation.get('source'),'error':row.get('error')})
        self.check()
        return {'record_id':self.meta['record_id'],'offset':offset,'limit':limit,
                'total':len(self.offsets),'frames':rows}

    def image(self,frame_id,video):
        with self.image_lock:return self._image(frame_id,video)

    def _image(self,frame_id,video):
        from .live_sources import VideoFileSource
        from .preview_quality import encode_preview
        if type(frame_id) is not int or not 0<=frame_id<len(self.offsets):
            raise ValueError('기록 프레임 번호를 확인하세요.')
        if self.meta['source_kind']!='video_file':
            raise ValueError('원본 시각이 기록된 영상 파일 측정만 대조할 수 있습니다. 카메라 원본 영상은 저장되지 않았습니다.')
        self.check()
        with (self.directory/'live_frames.jsonl').open('rb') as stream:
            stream.seek(self.offsets[frame_id]);row=strict_loads(stream.readline().decode('utf-8'))
        media=row.get('source_media')
        if not media or type(media.get('source_frame_id')) is not int or media['source_frame_id']<0:
            raise ValueError('이 기록에는 원본 프레임 식별 정보가 없습니다.')
        source=VideoFileSource(video)
        try:
            profile=source.open()
            if profile['sha256']!=self.manifest['source_profile'].get('sha256'):
                raise ValueError('측정에 사용한 원본 영상과 파일 해시가 다릅니다. 원본을 다시 선택하세요.')
            for _ in range(media['source_frame_id']+1):rgb=source.read()
            if source.media!=media or rgb.shape[:2]!=(self.manifest['height'],self.manifest['width']):
                raise ValueError('원본 프레임의 시각·픽셀·크기가 기록과 다릅니다. 현재 디코더로 대조할 수 없습니다.')
            image,preview=encode_preview(rgb,'high')
        except StopIteration as exc:
            raise ValueError('기록에 대응하는 원본 프레임을 찾지 못했습니다.') from exc
        finally:source.close()
        region=self.manifest['initial_bed_region']
        with (self.directory/'control_events.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                event=strict_loads(line)
                if event['type']=='bed_region_changed' and event['revision']==row['bed_region_revision']:region=event['region']
        self.check()
        return {'record_id':self.meta['record_id'],'frame_id':frame_id,
                'stream_frame_id':row['stream_frame_id'],'source_media':media,
                'width':self.manifest['width'],'height':self.manifest['height'],
                'image':image,'preview':preview,'people':display_people(row,self.manifest['width'],self.manifest['height']),
                'native_pose_cues':row.get('native_pose_cues'),
                'bed_region':region,'posture_assessment':row.get('posture_assessment'),
                'silhouette_assessment':row.get('silhouette_assessment'),
                'verification':'source_sha256_pts_pixels_geometry_verified',
                'inference_performed':False,'full_silhouette_available':False}

    def timeline(self,basis,bins):
        from .record_timeline import summarize
        with self.timeline_lock:
            self.check()
            key=(basis,bins)
            if key not in self.timeline_cache:
                def rows():
                    with (self.directory/'live_frames.jsonl').open(encoding='utf-8') as stream:
                        for line in stream:yield strict_loads(line)
                summary=summarize(rows,self.manifest,basis,bins)
                self.check()
                self.timeline_cache[key]=dict(summary,record_id=self.meta['record_id'])
                while len(self.timeline_cache)>4:self.timeline_cache.popitem(last=False)
            self.timeline_cache.move_to_end(key)
            self.check()
            return self.timeline_cache[key]


class RecordLibrary:
    def __init__(self,root):
        self.root=Path(root).resolve();self.opened=OrderedDict();self.lock=threading.RLock()

    def directory(self,record_id):
        if not isinstance(record_id,str) or ID.fullmatch(record_id) is None:
            raise ValueError('기록 목록에서 측정을 선택하세요.')
        path=self.root/record_id
        if path.is_symlink() or path.resolve().parent!=self.root or not path.is_dir():
            raise ValueError('측정 기록을 찾을 수 없습니다.')
        return path.resolve()

    def catalog(self,offset=0,limit=50):
        pagination(offset,limit);items=[]
        for path in self.root.iterdir() if self.root.is_dir() else []:
            if ID.fullmatch(path.name) is None:continue
            try:
                directory=self.directory(path.name)
                if (directory/'manifest.json').is_symlink() or (directory/'manifest.json').stat().st_size>4*1024**2:
                    raise ValueError('Unsupported manifest')
                item=metadata(load_json(directory/'manifest.json'),path.name)
            except (OSError,ValueError,TypeError,KeyError,AttributeError,RecursionError):
                item={'record_id':path.name,'availability':'invalid','integrity':'not_checked'}
            items.append(item)
        def order(item):
            value=item.get('started_utc_ns')
            stamp=int(value) if isinstance(value,str) and value.isascii() and value.isdigit() else 0
            return stamp,item['record_id']
        items.sort(key=order,reverse=True)
        return {'items':items[offset:offset+limit],'offset':offset,'limit':limit,'total':len(items)}

    def open(self,record_id):
        try:
            record=OpenRecord(self.directory(record_id),record_id)
        except (IntegrityError,OSError,KeyError,TypeError) as exc:
            raise ValueError('기록 검사에 실패했습니다. 파일 누락·변경·지원 형식을 확인하세요.') from exc
        with self.lock:
            self.opened[record_id]=record;self.opened.move_to_end(record_id)
            while len(self.opened)>4:self.opened.popitem(last=False)
        # Return original settings for inspection, never for live reconfiguration.
        return dict(record.meta,integrity='verified',counts=record.manifest['counts'],
                    automatic_profile=record.manifest.get('automatic_posture_profile'),
                    score_semantics='independent_rule_fit_not_probability',
                    content='stored_frame_results_no_video_replay')

    def frames(self,record_id,offset=0,limit=50):
        self.directory(record_id)
        with self.lock:record=self.opened.get(record_id)
        if record is None:raise ValueError('기록 목록에서 측정을 먼저 여세요.')
        return record.page(offset,limit)

    def timeline(self,record_id,basis=None,bins=240):
        self.directory(record_id)
        with self.lock:record=self.opened.get(record_id)
        if record is None:raise ValueError('기록 목록에서 측정을 먼저 여세요.')
        if basis is None:basis='media' if record.meta['source_kind']=='video_file' else 'receive'
        return record.timeline(basis,bins)

    def image(self,record_id,frame_id,video):
        self.directory(record_id)
        with self.lock:record=self.opened.get(record_id)
        if record is None:raise ValueError('기록 목록에서 측정을 먼저 여세요.')
        return record.image(frame_id,video)
