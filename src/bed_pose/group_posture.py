"""Reproducible experimental two-camera predictions on the saved FIFO pairs."""
from collections import Counter
from pathlib import Path
import os
from .fusion_inputs import iter_inputs,confirmations
from .reference_posture import combine_views
from .io_utils import load_json,json_text,file_hash,strict_loads
from .contracts import IntegrityError


def profiles(group):
    return [load_json(Path(m['run_directory'])/'manifest.json').get('automatic_posture_profile') or load_json(Path(m['run_directory'])/'manifest.json').get('reference_posture_profile') for m in group['members']]


def predictions(group,directory):
    configs=profiles(group);timeline=confirmations(group)
    policy=group.get('posture_fusion_policy')
    if policy is not None:
        from .multiview_posture import POLICY
        if policy!=POLICY:raise IntegrityError('Unsupported group fusion policy')
    image_profiles=[load_json(Path(m['run_directory'])/'manifest.json').get('body_state_provider_profile') for m in group['members']]
    automatic=any(c and c.get('version','').startswith('automatic-posture') for c in configs)
    for row in iter_inputs(group,directory):
        views=[]
        times=[int(v['time_ns']) for v in row['views'] if v]
        for index,v in enumerate(row['views']):
            views.append({'input_id':group['members'][index]['input_id'],'closed':v is None,
                'time_ns':v['time_ns'] if v else '0','max_age_ns':int(group['alignment_max_skew_ns'])+1,
                'tracking_provisional':v is not None and v['tracking']['status']=='tracking_provisional',
                'image_profile':image_profiles[index],'reference_profile':configs[index],'assessment':v.get('posture_assessment') if v else None})
        a=combine_views(views,int(group['alignment_max_skew_ns']),timeline,True,max(times,default=0),fusion_policy=policy)
        if row['status']=='held' and policy is None:a.update(status='held',label=None,reasons=list(dict.fromkeys(a['reasons']+row['hold_reasons'])))
        result={'version':'group-posture-0.3' if policy is not None else 'group-posture-0.2' if automatic else 'group-reference-posture-0.1','group_id':group['group_id'],'alignment_id':row['alignment_id'],
               'frame_refs':[{'measurement_id':v['measurement_id'],'frame_id':v['frame_id']} if v else None for v in row['views']],
               'status':a['status'],'label':a['label'],'reasons':a['reasons'],'normalized_distances':a.get('normalized_distances'),
               'experimental':True,'identity_verified':False,'exposure_synchronized':False}
        if policy is not None:
            result['method']=a['method'];result['fusion_evidence']=a.get('fusion_evidence')
        yield result


def build_predictions(group,directory):
    if group.get('fusion_inputs',{}).get('status')!='generated':return {'status':'blocked_alignment_unavailable'}
    if not any(profiles(group)):return {'status':'not_configured'}
    root=Path(directory);temp=root/'posture_predictions.jsonl.tmp';target=root/'posture_predictions.jsonl';counts=Counter(predicted=0,held=0)
    try:
        with temp.open('x',encoding='utf-8',newline='\n') as stream:
            for row in predictions(group,directory):counts[row['status']]+=1;stream.write(json_text(row)+'\n')
            stream.flush();os.fsync(stream.fileno())
        os.replace(temp,target)
        return {'status':'generated','path':target.name,'sha256':file_hash(target),'counts':dict(counts),'method':'gated_image_score_fusion_v1' if group.get('posture_fusion_policy') is not None else 'gated_posture_combination_v2'}
    except Exception:
        temp.unlink(missing_ok=True);raise


def verify_predictions(group,directory):
    artifact=group['posture_predictions'];root=Path(directory)
    if artifact.get('method') not in ('mean_reference_distance_v1','gated_posture_combination_v2','gated_image_score_fusion_v1'):raise IntegrityError('Unsupported group posture method')
    new=artifact['method']=='gated_image_score_fusion_v1'
    if new!=(group.get('posture_fusion_policy') is not None):raise IntegrityError('Fusion policy/method mismatch')
    if artifact['path']!='posture_predictions.jsonl' or file_hash(root/artifact['path'])!=artifact['sha256']:raise IntegrityError('Group posture checksum mismatch')
    counts=Counter(predicted=0,held=0)
    with (root/artifact['path']).open(encoding='utf-8') as stream:
        for expected in predictions(group,directory):
            line=next(stream,None)
            from .replay_compare import equivalent
            if line is None:raise IntegrityError('Missing group posture observation')
            saved=strict_loads(line)
            if not (equivalent(saved,expected) if new else saved==expected):raise IntegrityError('Group posture differs from original observations')
            counts[expected['status']]+=1
        if next(stream,None) is not None:raise IntegrityError('Extra group posture prediction')
    if dict(counts)!=artifact['counts']:raise IntegrityError('Group posture counts mismatch')
