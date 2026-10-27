"""Streaming FIFO one-to-one receive-time alignment; not exposure synchronization."""
import os
from pathlib import Path
from .io_utils import load_json, strict_loads, json_text, file_hash


def fifo_pairs(left, right, max_skew_ns):
    if type(max_skew_ns) is not int or max_skew_ns < 0:
        raise ValueError('Explicit nonnegative alignment tolerance required')
    iterators=[iter(left),iter(right)]
    previous=[None,None]
    def advance(side):
        value=next(iterators[side],None)
        if value is not None:
            stamp=value['time_ns']
            if type(stamp) is not int or previous[side] is not None and stamp<=previous[side]:
                raise ValueError('Alignment source timestamps must strictly increase')
            previous[side]=stamp
        return value
    a,b=advance(0),advance(1)
    while a is not None or b is not None:
        if a is None:
            yield {'status':'unmatched','left':None,'right':b,'reason':'partner_end','delta_ns':None}
            b=advance(1)
        elif b is None:
            yield {'status':'unmatched','left':a,'right':None,'reason':'partner_end','delta_ns':None}
            a=advance(0)
        else:
            delta=b['time_ns']-a['time_ns']
            if abs(delta)<=max_skew_ns:
                yield {'status':'matched','left':a,'right':b,'reason':None,'delta_ns':str(delta)}
                a,b=advance(0),advance(1)
            elif delta>0:
                yield {'status':'unmatched','left':a,'right':None,'reason':'outside_tolerance','delta_ns':None}
                a=advance(0)
            else:
                yield {'status':'unmatched','left':None,'right':b,'reason':'outside_tolerance','delta_ns':None}
                b=advance(1)


def references(directory, manifest):
    origin=int(manifest['clock_origin_perf_counter_ns'])
    with (Path(directory)/'live_frames.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row=strict_loads(line)
            yield {'measurement_id':manifest['measurement_id'],'frame_id':row['frame_id'],
                   'stream_frame_id':row['stream_frame_id'],'clock_id':row['clock_id'],
                   'received_ns':row['received_ns'],'time_ns':origin+int(row['received_ns']),
                   'processing_status':row['processing_status']}


def align_group(members, directory, max_skew_ns):
    manifests=[load_json(Path(m['run_directory'])/'manifest.json') for m in members]
    if any(m['source_profile']['kind']=='video_file' for m in manifests):
        return {'status':'blocked_media_offset_required','reason':'File PTS needs a verified common-time offset; decode receive time is not media time.'}
    # Caller owns both workers in this process and verifies their immutable run records first.
    target=Path(directory)/'alignment.jsonl'
    temp=Path(directory)/'alignment.jsonl.tmp'
    counts={'matched':0,'unmatched_left':0,'unmatched_right':0}
    try:
        with temp.open('x',encoding='utf-8',newline='\n') as stream:
            sources=[references(m['run_directory'],manifest) for m,manifest in zip(members,manifests)]
            for index,row in enumerate(fifo_pairs(*sources,max_skew_ns)):
                if row['status']=='matched':counts['matched']+=1
                else:counts['unmatched_left' if row['left'] else 'unmatched_right']+=1
                # Decimal strings preserve ns precision in downstream JavaScript.
                for side in ('left','right'):
                    if row[side] is not None:row[side]['time_ns']=str(row[side]['time_ns'])
                stream.write(json_text(dict(row,alignment_id=index))+'\n')
            stream.flush();os.fsync(stream.fileno())
        if (counts['matched']+counts['unmatched_left']!=manifests[0]['recorded_frames']
                or counts['matched']+counts['unmatched_right']!=manifests[1]['recorded_frames']):
            raise ValueError('Alignment frame coverage mismatch')
        os.replace(temp,target)
        return {'status':'receive_time_approximation','method':'fifo_one_to_one_v1',
                'clock_scope':'same_process_perf_counter','exposure_synchronized':False,
                'max_skew_ns':str(max_skew_ns),'counts':counts,'path':target.name,'sha256':file_hash(target)}
    except Exception:
        temp.unlink(missing_ok=True)
        raise
