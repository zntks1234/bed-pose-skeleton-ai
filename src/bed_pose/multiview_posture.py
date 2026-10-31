"""Experimental image-score fusion, independent of OS, inference backend and bed geometry."""
from copy import deepcopy
import math
from .posture_decision import finalize as compose, choose, scores_valid
from .decision_evidence import camera

POLICY={'version':'two-view-image-scores-0.1','pooling':'equal_mean_of_usable_views',
        'direction_pooling':'views_whose_top_state_is_lying',
        'thresholds':'maximum_of_member_thresholds','single_view_fallback':True,
        'bed_policy':'edge_observed_without_outside_or_boundary_conflict',
        'validation':'experimental_not_accuracy_validated'}
STATES=('lying','sitting','standing','other')
DIRECTIONS=('supine','side','prone')


def supported(profiles):
    return len(profiles)==2 and all(isinstance(p,dict) and p.get('model_id')=='openai/clip-vit-base-patch16' for p in profiles)


def compatible(profiles):
    if not supported(profiles):return False
    a,b=profiles
    if any(not isinstance(p.get('decision_policy'),dict) or not isinstance(p.get('model_sha256'),str) or len(p['model_sha256'])!=64 for p in profiles):return False
    if any(type(p['decision_policy'].get(k)) not in (int,float) or not math.isfinite(p['decision_policy'][k]) or not 0<=p['decision_policy'][k]<=1 for p in profiles for k in ('state_min','direction_min')):return False
    return all(a.get(k)==b.get(k) for k in ('model_id','model_sha256','preprocess_id')) and all(
        a['decision_policy'].get(k)==b['decision_policy'].get(k) for k in ('prompts','score_policy','text_pooling','dtype'))


def fuse(views,policy):
    if policy!=POLICY:raise ValueError('Unsupported two-view posture policy')
    result={'status':'held','label':None,'reasons':[],'method':POLICY['version'],
            'views':[{k:value for k,value in v.items() if k!='image_profile'} for v in views],'experimental':True,'identity_verified':False,'exposure_synchronized':False}
    profiles=[v.get('image_profile') for v in views]
    if not compatible(profiles):result['reasons']=['fusion_provider_mismatch'];return result
    evidence={'policy':deepcopy(policy),'mode':'unavailable','contributors':[],'state_scores':{},'direction_scores':{}}
    result['fusion_evidence']=evidence
    usable=[]
    for v in views:
        body=v['assessment'].get('rule_features',{}).get('body_state',{})
        common=camera(v['assessment'],input_id=v['input_id'],time_ns=v.get('time_ns'),profile=v.get('image_profile'))
        ok=common['fusion_usable']
        evidence['contributors'].append({'input_id':v['input_id'],'used':ok,
             'reasons':[] if ok else body.get('reasons') or ['fusion_view_evidence_unavailable']})
        if ok:usable.append((v,common))
    if not usable:result['reasons']=['fusion_no_usable_view'];return result
    evidence['mode']='two_view_fusion' if len(usable)==2 else 'single_view_fallback'
    evidence['state_scores']={k:math.fsum(b['state_scores'][k] for _,b in usable)/len(usable) for k in STATES}
    cfgs=[p['decision_policy'] for p in profiles]
    state_min=max(c['state_min'] for c in cfgs);direction_min=max(c['direction_min'] for c in cfgs)
    evidence.update(state_min=state_min,direction_min=direction_min)
    state=choose(evidence['state_scores'],state_min)
    direction_views=[b for _,b in usable if max(b['state_scores'],key=b['state_scores'].get)=='lying']
    if direction_views:
        evidence['direction_scores']={k:math.fsum(b['direction_scores'][k] for b in direction_views)/len(direction_views) for k in DIRECTIONS}
    direction=choose(evidence['direction_scores'],direction_min) if state=='lying' else None
    evidence.update(state=state or 'unknown',lying_direction=direction or 'unknown')
    relations=[v['assessment'].get('rule_features',{}).get('bed_relation',{}) for v,_ in usable]
    observed=[x.get('relation') for x in relations if x.get('status')=='observed']
    relation={'status':'unknown','relation':None}
    if 'edge' in observed and not any(x in ('outside','boundary') for x in observed):relation={'status':'observed','relation':'edge'}
    label,reason=compose({'status':'predicted' if state else 'held','state':state or 'unknown',
                         'lying_direction':direction or 'unknown','reasons':[] if state else ['fusion_state_score_insufficient']},relation)
    evidence['bed_relations']=observed
    if reason:result['reasons']=[reason]
    else:result.update(status='predicted',label=label)
    return result
