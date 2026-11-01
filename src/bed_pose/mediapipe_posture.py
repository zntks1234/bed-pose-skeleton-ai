"""Experimental joint-only state prediction; no CLIP, goals or sensor inputs.

Rule scores are not probabilities. Image vertical is an explicit fallback
assumption when bed-plane registration is unavailable, not measured gravity.
"""
import math
from .separated_posture import evaluate as separate, _angle
from .posture_decision import finalize_forced


def evaluate(obs,cfg):
    _,_,e=separate(obs,cfg)
    e['information_path']='mediapipe_joint_geometry'
    def held(reason):
        e['body_state']={'status':'unavailable','state':'unknown','lying_direction':'unknown',
                         'reasons':[reason],'scores':{},'score_semantics':'normalized_rule_fit_not_probability'}
        e['context_assessment'].update(status='held',label=None,candidate_label=None,reasons=[reason])
        return None,reason,e
    p=obs.points
    if len(p)!=17 or any(p[i] is None for i in (5,6,11,12)):
        return held('automatic_torso_joints_missing')
    shoulder=tuple((p[5][k]+p[6][k])/2 for k in (0,1))
    hip=tuple((p[11][k]+p[12][k])/2 for k in (0,1))
    length=math.dist(shoulder,hip)
    if length<=1e-6:return held('degenerate_body_geometry')
    vertical=abs(hip[1]-shoulder[1])/length
    source='image_vertical_assumed';registered_label=None
    # Use the existing bed-plane registration when valid; do not require CLIP
    # or OpenCV just to classify ordinary image-coordinate observations.
    if obs.world_points is not None and isinstance(obs.bed_rectangle,dict):
        from .viewpoint_posture import evaluate as registered
        try:
            registered_label,_,geometry=registered(obs,cfg)
            e['camera_geometry']=geometry
            if 'torso_plane_normal_cos' in geometry:
                vertical=geometry['torso_plane_normal_cos'];source='bed_registered_model_3d'
        except (ImportError,ValueError,OverflowError):
            e['camera_geometry']={'status':'unavailable'}
    upright=max(0.,min(1.,(vertical-cfg['lying_cos'])/(cfg['upright_cos']-cfg['lying_cos'])))
    lower=all(p[i] is not None for i in (13,14,15,16))
    if not lower and upright>.5:return held('automatic_lower_body_needed')
    xyz=obs.world_points
    use_world=(xyz is not None and len(xyz)==17 and
               all(len(v)==3 and all(type(x) in (int,float) and math.isfinite(x) for x in v) for v in xyz))
    q=xyz if use_world else p
    hips=[];knees=[];bend=0.
    if lower and upright>0:
        hips=[_angle(q[s],q[h],q[k]) for s,h,k in ((5,11,13),(6,12,14))]
        knees=[_angle(q[h],q[k],q[a]) for h,k,a in ((11,13,15),(12,14,16))]
        if any(v is None for v in hips+knees):return held('degenerate_body_geometry')
        def bent(v):
            return max(0.,min(1.,(cfg['straight_knee_min']-v)/(cfg['straight_knee_min']-cfg['score_knee_peak'])))
        # Knees alone cannot establish sitting (e.g. standing with bent knees).
        bend=min(bent(v) for v in hips+knees)
    scores={'lying':1-upright,'sitting':upright*bend,'standing':upright*(1-bend),'other':0.}
    shape=e['body_assessment'].get('orientation') or {}
    orientation=(shape.get('score_decision') or {}).get('scores') or {}
    directions={}
    if registered_label in ('supine','side'):
        directions={name:float(name==registered_label) for name in ('supine','side','prone')}
    elif shape.get('label') in ('front_shape','side_shape'):
        front,side=(orientation.get(k) for k in ('front_shape','side_shape'))
        if all(type(v) in (int,float) and math.isfinite(v) for v in (front,side)) and front+side>0:
            directions={'supine':front/(front+side),'side':side/(front+side),'prone':0.}
    state=max(scores,key=scores.get)
    direction=max(directions,key=directions.get) if directions else 'unknown'
    body={'status':'predicted','state':state,'lying_direction':direction if state=='lying' else 'unknown',
          'reasons':[],'scores':scores,'score_semantics':'normalized_rule_fit_not_probability',
          'details':{'version':'mediapipe-joint-state-0.1','direction_scores':directions,
                     'axis_source':source,'torso_upright_cos':vertical,'upright_fit':upright,
                     'hip_angles':hips,'knee_angles':knees,'leg_geometry':'model_3d' if use_world else 'image_2d',
                     'validation':'experimental_not_accuracy_validated'}}
    label,reason,decision=finalize_forced(body,e['bed_relation'])
    decision['method']='maximum_joint_rule_fit'
    decision['warnings'].append('joint_geometry_not_clip_equivalent')
    if source=='image_vertical_assumed':decision['warnings'].append('image_vertical_is_not_measured_gravity')
    e.update(body_state=body,forced_decision=decision)
    e['context_assessment'].update(status='predicted' if label else 'held',label=label,candidate_label=label,
        reasons=[reason] if reason else [],evidence_source='mediapipe_joint_geometry',physical_posture_verified=False)
    return label,reason,e
