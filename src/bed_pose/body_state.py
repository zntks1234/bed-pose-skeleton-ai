"""Independent camera-image evidence contract and posture composition.

This is not an image model: a configured provider must supply its own decision.
Predicted labels remain experimental and never become verified ground truth.
"""
from dataclasses import dataclass
from copy import deepcopy
import math
from .io_utils import json_text,strict_loads

VERSION='camera-body-state-0.1'
STATES=('lying','sitting','standing','other','unknown')
DIRECTIONS=('supine','side','prone','unknown')
PROFILE_KEYS={'version','source','model_id','model_sha256','preprocess_id','decision_policy','execution_kind'}


@dataclass(frozen=True)
class ImageBodyInput:
    rgb: object
    stream_frame_id: int
    clock_id: str
    received_ns: str
    candidate_id: str
    points: tuple
    image_bounds: tuple


def validate_profile(profile,execution_kind):
    if (not isinstance(profile,dict) or set(profile)!=PROFILE_KEYS or profile['version']!=VERSION
            or profile['source']!='camera_image' or profile['execution_kind']!=execution_kind
            or execution_kind not in ('synthetic','model_inference')
            or any(not isinstance(profile[k],str) or not profile[k].strip() for k in ('model_id','preprocess_id'))
            or not isinstance(profile['model_sha256'],str) or len(profile['model_sha256'])!=64
            or any(c not in '0123456789abcdef' for c in profile['model_sha256'])):
        raise ValueError('Invalid independent image-state provider profile')
    if not isinstance(profile['decision_policy'],dict) or not profile['decision_policy']:
        raise ValueError('Body-state decision policy must be explicit')
    try:
        if strict_loads(json_text(profile['decision_policy']))!=profile['decision_policy']:
            raise ValueError('Decision policy must use JSON values')
    except (ValueError,TypeError) as exc:raise ValueError('Invalid body-state decision policy') from exc
    if profile['model_id']=='openai/clip-vit-base-patch16':
        from .clip_posture import validate_policy
        validate_policy(profile['decision_policy'])
        assets=profile['decision_policy']['assets_manifest']
        if (profile['execution_kind']!='model_inference' or assets.get('model_id')!=profile['model_id']
                or assets.get('files',{}).get('pytorch_model.bin')!=profile['model_sha256']
                or profile['preprocess_id']!=profile['decision_policy']['preprocess']):
            raise ValueError('CLIP provider asset identity mismatch')
    return deepcopy(profile)


def validate_decision(value):
    if not isinstance(value,dict) or set(value) not in ({'state','lying_direction','scores','score_semantics'},
            {'state','lying_direction','scores','score_semantics','details'}):
        raise ValueError('Invalid independent image-state output')
    if value['state'] not in STATES or value['lying_direction'] not in DIRECTIONS:
        raise ValueError('Unsupported body-state label')
    if value['state']!='lying' and value['lying_direction']!='unknown':
        raise ValueError('Lying direction requires a lying state')
    if (not isinstance(value['scores'],dict) or set(value['scores'])-set(STATES)
            or any(type(x) not in (int,float) or not math.isfinite(x) for x in value['scores'].values())
            or value['score_semantics'] not in ('logits','similarity','uncalibrated_probability','not_reported')
            or (value['score_semantics']=='not_reported' and value['scores'])
            or (value['score_semantics']=='uncalibrated_probability' and any(not 0<=x<=1 for x in value['scores'].values()))):
        raise ValueError('Invalid body-state score semantics')
    if 'details' in value and (not isinstance(value['details'],dict) or strict_loads(json_text(value['details']))!=value['details']):
        raise ValueError('Invalid image evidence details')
    return deepcopy(value)


def observe(row,rgb,assessment,provider,profile):
    """Only the current image and selected visual target go to the provider."""
    result={'version':VERSION,'stream_frame_id':row['stream_frame_id'],'clock_id':row['clock_id'],
            'received_ns':row['received_ns'],'candidate_id':assessment['candidate_id'],
            'provider':deepcopy(profile),'status':'unavailable','reasons':[],
            'decision':None,'verified_gt':False}
    if provider is None:result['reasons']=['body_state_provider_not_configured'];return result
    if provider.profile!=profile:result.update(status='held',reasons=['body_state_provider_profile_changed']);return result
    if row['processing_status']!='ok':result['reasons']=['processing_failed'];return result
    if row.get('target_tracking',{}).get('status')=='held':result['reasons']=['target_held'];return result
    people=[p for p in row.get('mapped_people') or [] if p['candidate_id']==assessment['candidate_id']]
    if len(people)!=1:result['reasons']=['body_state_target_unavailable'];return result
    # A provider gets no bed region, planned goal, sensor result or GT field.
    h,w=rgb.shape[:2]
    def point(j):
        x,y=j.get('x_px'),j.get('y_px')
        return (x,y) if (j.get('availability')=='predicted' and type(x) in (int,float) and type(y) in (int,float)
                         and math.isfinite(x) and math.isfinite(y) and 0<=x<w and 0<=y<h) else None
    points=tuple(point(j) for j in people[0]['joints'])
    valid=[p for p in points if p is not None]
    if len(valid)<2:
        result.update(status='held',reasons=['body_state_target_unavailable']);return result
    xs,ys=zip(*valid);dx=max(xs)-min(xs);dy=max(ys)-min(ys)
    if dx<=0 or dy<=0:
        result.update(status='held',reasons=['body_state_target_unavailable']);return result
    # Fixed, versioned preprocessing, not a posture threshold: crop the selected
    # person's observed joints with 10% padding; do not send a whole room.
    x1=max(0,math.floor(min(xs)-.1*dx));x2=min(w,math.ceil(max(xs)+.1*dx)+1)
    y1=max(0,math.floor(min(ys)-.1*dy));y2=min(h,math.ceil(max(ys)+.1*dy)+1)
    local=tuple((p[0]-x1,p[1]-y1) if p is not None else None for p in points)
    try:
        decision=validate_decision(provider.estimate(ImageBodyInput(rgb[y1:y2,x1:x2],row['stream_frame_id'],row['clock_id'],
                                                                 row['received_ns'],assessment['candidate_id'],local,(x1,y1,x2,y2))))
    except Exception:
        result.update(status='held',reasons=['body_state_provider_failed']);return result
    result.update(status='predicted' if decision['state']!='unknown' else 'held',decision=decision,
                  reasons=[] if decision['state']!='unknown' else ['body_state_unknown'])
    return result


def validate_observation(value,row,candidate,profile):
    expected={'stream_frame_id':row['stream_frame_id'],'clock_id':row['clock_id'],
              'received_ns':row['received_ns'],'candidate_id':candidate}
    if (not isinstance(value,dict) or set(value)!={'version',*expected,'provider','status','reasons','decision','verified_gt'}
            or value.get('version')!=VERSION or value.get('verified_gt') is not False
            or any(value.get(k)!=v or type(value.get(k)) is not type(v) for k,v in expected.items())
            or value.get('provider')!=profile or value.get('status') not in ('unavailable','held','predicted')
            or not isinstance(value.get('reasons'),list) or any(not isinstance(r,str) for r in value['reasons'])):
        raise ValueError('Body-state identity or provider mismatch')
    decision=validate_decision(value['decision']) if value['decision'] is not None else None
    if profile and profile['model_id']=='openai/clip-vit-base-patch16' and decision is not None:
        from .clip_posture import validate_recorded_decision
        validate_recorded_decision(decision,profile)
    if ((profile is None and (decision is not None or value['status']!='unavailable'))
            or (value['status']=='predicted' and (decision is None or decision['state']=='unknown' or value['reasons']))
            or (value['status']!='predicted' and (not value['reasons'] or decision is not None and decision['state']!='unknown'))):
        raise ValueError('Inconsistent body-state observation')
    return value


def read_observation(value,row,candidate,profile):
    """Validate recorded evidence before composition; do not rerun the model."""
    result={'status':'held','state':'unknown','lying_direction':'unknown','reasons':['body_state_observation_invalid']}
    if value is None:
        result.update(status='unavailable',reasons=['body_state_provider_not_configured']);return result
    try:validate_observation(value,row,candidate,profile)
    except (ValueError,TypeError):
        result['reasons']=['body_state_identity_or_provider_mismatch'];return result
    if value.get('status') in ('unavailable','held') and value.get('decision') is None:
        result['reasons']=value.get('reasons') or ['body_state_unknown'];return result
    try:decision=validate_decision(value['decision'])
    except (KeyError,ValueError,TypeError):return result
    if 'details' in decision:
        result.update(details=decision['details'],scores=decision['scores'],score_semantics=decision['score_semantics'])
    if value.get('status')!='predicted' or decision['state']=='unknown':
        result['reasons']=['body_state_unknown'];return result
    result.update(status='predicted',state=decision['state'],lying_direction=decision['lying_direction'],
                  reasons=[],scores=decision['scores'],score_semantics=decision['score_semantics'])
    return result


def compose(state,relation):
    """Body predictions do not require a bed; edge_sitting adds bed context."""
    if state['status']!='predicted':return None,(state['reasons'] or ['body_state_unknown'])[0]
    if state['state']=='lying':
        direction=state['lying_direction']
        if direction in ('supine','side'):return direction,None
        return None,'prone_out_of_scope' if direction=='prone' else 'lying_direction_evidence_missing'
    if state['state']=='sitting':
        if relation['status']=='observed' and relation['relation']=='edge':return 'edge_sitting',None
        return None,'bed_edge_relation_unconfirmed'
    return None,'standing_or_other_out_of_scope'
