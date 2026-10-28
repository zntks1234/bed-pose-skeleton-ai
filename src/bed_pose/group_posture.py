"""Reproducible experimental two-camera predictions on the saved FIFO pairs."""
from collections import Counter
from pathlib import Path
import os
from .fusion_inputs import iter_inputs,confirmations
from .reference_posture import combine_views
from .io_utils import load_json,json_text,file_hash,strict_loads
from .contracts import IntegrityError


def profiles(group):
    return [load_json(Path(m['run_directory'])/'manifest.json').get('reference_posture_profile') for m in group['members']]


def predictions(group,directory):
    configs=profiles(group);timeline=confirmations(group)
    for row in iter_inputs(group,directory):
        views=[]
        times=[int(v['time_ns']) for v in row['views'] if v]
        for index,v in enumerate(row['views']):
            views.append({'input_id':group['members'][index]['input_id'],'closed':v is None,
                'time_ns':v['time_ns'] if v else '0','max_age_ns':int(group['alignment_max_skew_ns'])+1,
                'tracking_provisional':v is not None and v['tracking']['status']=='tracking_provisional',
                'reference_profile':configs[index],'assessment':v.get('posture_assessment') if v else None})
        a=combine_views(views,int(group['alignment_max_skew_ns']),timeline,True,max(times,default=0))
        if row['status']=='held':a.update(status='held',label=None,reasons=list(dict.fromkeys(a['reasons']+row['hold_reasons'])))
        yield {'version':'group-reference-posture-0.1','group_id':group['group_id'],'alignment_id':row['alignment_id'],
               'frame_refs':[{'measurement_id':v['measurement_id'],'frame_id':v['frame_id']} if v else None for v in row['views']],
               'status':a['status'],'label':a['label'],'reasons':a['reasons'],'normalized_distances':a.get('normalized_distances'),
               'experimental':True,'identity_verified':False,'exposure_synchronized':False}


def build_predictions(group,directory):
    if group.get('fusion_inputs',{}).get('status')!='generated':return {'status':'blocked_alignment_unavailable'}
    if not any(profiles(group)):return {'status':'not_configured'}
    root=Path(directory);temp=root/'posture_predictions.jsonl.tmp';target=root/'posture_predictions.jsonl';counts=Counter(predicted=0,held=0)
    try:
        with temp.open('x',encoding='utf-8',newline='\n') as stream:
            for row in predictions(group,directory):counts[row['status']]+=1;stream.write(json_text(row)+'\n')
            stream.flush();os.fsync(stream.fileno())
        os.replace(temp,target)
        return {'status':'generated','path':target.name,'sha256':file_hash(target),'counts':dict(counts),'method':'mean_reference_distance_v1'}
    except Exception:
        temp.unlink(missing_ok=True);raise


def verify_predictions(group,directory):
    artifact=group['posture_predictions'];root=Path(directory)
    if artifact.get('method')!='mean_reference_distance_v1':raise IntegrityError('Unsupported group posture method')
    if artifact['path']!='posture_predictions.jsonl' or file_hash(root/artifact['path'])!=artifact['sha256']:raise IntegrityError('Group posture checksum mismatch')
    counts=Counter(predicted=0,held=0)
    with (root/artifact['path']).open(encoding='utf-8') as stream:
        for expected in predictions(group,directory):
            line=next(stream,None)
            if line is None or strict_loads(line)!=expected:raise IntegrityError('Group posture differs from original observations')
            counts[expected['status']]+=1
        if next(stream,None) is not None:raise IntegrityError('Extra group posture prediction')
    if dict(counts)!=artifact['counts']:raise IntegrityError('Group posture counts mismatch')
