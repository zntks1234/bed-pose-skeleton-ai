"""Uncalibrated 2D geometric baseline. Thresholds are experimental, not accuracy claims."""
import math
from copy import deepcopy
from .io_utils import object_hash

LEGACY_METHOD='automatic-posture-rules-0.1'
PREVIOUS_METHOD='automatic-posture-rules-0.2'
METHOD='automatic-posture-rules-0.3'
DEFAULTS={'version':METHOD,'view':'oblique','upright_cos':.85,'lying_cos':.55,
          'side_span_max':.22,'front_span_min':.40,'straight_knee_min':155.,
          'bent_knee_min':65.,'bent_knee_max':135.,'edge_fraction':.18}
CORE=(5,6,11,12,13,14,15,16)

def midpoint(a,b):return ((a[0]+b[0])/2,(a[1]+b[1])/2)
def angle(a,b,c):
    u=(a[0]-b[0],a[1]-b[1]);v=(c[0]-b[0],c[1]-b[1])
    size=math.hypot(*u)*math.hypot(*v)
    if size==0:return None
    return math.degrees(math.acos(max(-1.,min(1.,(u[0]*v[0]+u[1]*v[1])/size))))

class AutomaticClassifier:
    def __init__(self,profile=None):
        self.profile=deepcopy(DEFAULTS if profile is None else profile)
        if set(self.profile)!=set(DEFAULTS) or self.profile['version'] not in (LEGACY_METHOD,PREVIOUS_METHOD,METHOD) or self.profile['view'] not in ('oblique','overhead'):raise ValueError('Unknown automatic posture profile')
        for k in set(DEFAULTS)-{'version','view'}:
            v=self.profile[k]
            if type(v) not in (float,int) or not math.isfinite(v) or v<=0:raise ValueError('Invalid automatic threshold')
        if not (self.profile['lying_cos']<self.profile['upright_cos']<=1 and self.profile['side_span_max']<self.profile['front_span_min'] and
                self.profile['bent_knee_min']<self.profile['bent_knee_max']<self.profile['straight_knee_min']<=180 and self.profile['edge_fraction']<.5):raise ValueError('Inconsistent automatic thresholds')
        self.model_id=self.profile['version']+':'+object_hash(self.profile)

    def _evaluate_v1(self,obs):
        evidence={'view':self.profile['view']}
        def held(reason):return None,reason,evidence
        if obs.bed_rectangle is None:return held('bed_region_required')
        if len(obs.points)!=17 or any(obs.points[i] is None for i in CORE):return held('automatic_joints_missing')
        p=obs.points;s=midpoint(p[5],p[6]);h=midpoint(p[11],p[12]);torso=math.dist(s,h)
        if torso<=0:return held('degenerate_body_geometry')
        k1,k2=angle(p[11],p[13],p[15]),angle(p[12],p[14],p[16])
        if k1 is None or k2 is None:return held('degenerate_body_geometry')
        c=abs(h[1]-s[1])/torso
        spans=(math.dist(p[5],p[6])/torso,math.dist(p[11],p[12])/torso)
        from .bed_geometry import contains,relative_xy
        hips_inside=all(contains(obs.bed_rectangle,p[i]) for i in (11,12))
        shoulders_inside=all(contains(obs.bed_rectangle,p[i]) for i in (5,6))
        uv=relative_xy(obs.bed_rectangle,h)
        if uv is None:return held('bed_coordinate_unavailable')
        if isinstance(obs.bed_rectangle,tuple):
            x1,y1,x2,y2=obs.bed_rectangle
            edge=min((h[0]-x1)/(x2-x1),(x2-h[0])/(x2-x1),(h[1]-y1)/(y2-y1),(y2-h[1])/(y2-y1))
        else:
            edge=min(uv[0],1-uv[0],uv[1],1-uv[1])
            if hips_inside and -1e-9<edge<0:edge=0.
        evidence.update(torso_vertical_cos=c,shoulder_span_ratio=spans[0],hip_span_ratio=spans[1],knee_angles=[k1,k2],hip_edge_fraction=edge)
        cfg=self.profile
        if cfg['view']=='oblique':
            upright=c>=cfg['upright_cos'] and s[1]<h[1]
            legs_down=all(p[k][1]>p[hip][1] and p[a][1]>p[k][1] for hip,k,a in ((11,13,15),(12,14,16)))
            if upright and legs_down and min(k1,k2)>=cfg['straight_knee_min']:return held('standing_or_upright_out_of_scope')
            bent=all(cfg['bent_knee_min']<=a<=cfg['bent_knee_max'] for a in (k1,k2))
            thighs_across=all(abs(p[k][1]-p[hip][1])<=cfg['lying_cos']*math.dist(p[k],p[hip]) for hip,k in ((11,13),(12,14)))
            feet_down=all(p[a][1]>p[k][1] for k,a in ((13,15),(14,16)))
            if upright and bent and thighs_across and feet_down and hips_inside and 0<=edge<=cfg['edge_fraction']:
                return 'edge_sitting',None,evidence
            if c>cfg['lying_cos']:return held('view_or_body_orientation_ambiguous')
        elif all(cfg['bent_knee_min']<=a<=cfg['bent_knee_max'] for a in (k1,k2)):
            return held('overhead_sitting_ambiguous')
        # Overhead mode permits upright image projections of lying people, but cannot infer gravity/sitting.
        if not hips_inside or not shoulders_inside:return held('body_outside_bed_region')
        if max(spans)<=cfg['side_span_max']:return 'side',None,evidence
        if min(spans)>=cfg['front_span_min']:
            if any(p[i] is None for i in (0,1,2)):return held('front_facing_evidence_missing')
            # Anatomical left/right chirality is a weak anterior-facing cue, not a prone detector.
            across=(p[5][0]-p[6][0],p[5][1]-p[6][1]);down=(h[0]-s[0],h[1]-s[1])
            if across[0]*down[1]-across[1]*down[0]<=0:return held('front_back_ambiguous')
            return 'supine',None,evidence
        return held('lying_orientation_ambiguous')

    def _evaluate_v2(self,obs):
        if self.profile['version']==LEGACY_METHOD:return self._evaluate_v1(obs)
        evidence={'view':self.profile['view']}
        def held(reason):return None,reason,evidence
        if obs.bed_rectangle is None:return held('bed_region_required')
        torso_indices=(5,6,11,12)
        if len(obs.points)!=17 or any(obs.points[i] is None for i in torso_indices):return held('automatic_torso_joints_missing')
        if all(obs.points[i] is not None for i in CORE):return self._evaluate_v1(obs)
        p=obs.points;s=midpoint(p[5],p[6]);h=midpoint(p[11],p[12]);torso=math.dist(s,h)
        if torso<=0:return held('degenerate_body_geometry')
        c=abs(h[1]-s[1])/torso
        spans=(math.dist(p[5],p[6])/torso,math.dist(p[11],p[12])/torso)
        evidence.update(torso_vertical_cos=c,shoulder_span_ratio=spans[0],hip_span_ratio=spans[1],
            missing_lower_joints=[i for i in (13,14,15,16) if p[i] is None])
        # This is a class-specific information gate, not a relaxed angle/score threshold.
        if c>self.profile['lying_cos']:return held('automatic_lower_body_needed')
        from .bed_geometry import contains
        if not all(contains(obs.bed_rectangle,p[i]) for i in torso_indices):return held('body_outside_bed_region')
        if max(spans)<=self.profile['side_span_max']:return 'side',None,evidence
        if min(spans)>=self.profile['front_span_min']:
            if any(p[i] is None for i in (0,1,2)):return held('front_facing_evidence_missing')
            across=(p[5][0]-p[6][0],p[5][1]-p[6][1]);down=(h[0]-s[0],h[1]-s[1])
            if across[0]*down[1]-across[1]*down[0]<=0:return held('front_back_ambiguous')
            return 'supine',None,evidence
        return held('lying_orientation_ambiguous')

    def evaluate(self,obs):
        if self.profile['version']==LEGACY_METHOD:return self._evaluate_v1(obs)
        if self.profile['version']==PREVIOUS_METHOD:return self._evaluate_v2(obs)
        # Keep old rule paths unchanged so saved observations remain reproducible.
        cfg=self.profile;evidence={'view':cfg['view']}
        def held(reason):return None,reason,evidence
        if obs.bed_rectangle is None:return held('bed_region_required')
        torso_indices=(5,6,11,12)
        if len(obs.points)!=17 or any(obs.points[i] is None for i in torso_indices):return held('automatic_torso_joints_missing')
        p=obs.points;s=midpoint(p[5],p[6]);h=midpoint(p[11],p[12]);torso=math.dist(s,h)
        if torso<=0:return held('degenerate_body_geometry')
        c=abs(h[1]-s[1])/torso
        spans=(math.dist(p[5],p[6])/torso,math.dist(p[11],p[12])/torso)
        knees=[];invalid=[]
        for hip,knee,ankle in ((11,13,15),(12,14,16)):
            complete=all(p[i] is not None for i in (hip,knee,ankle))
            value=angle(p[hip],p[knee],p[ankle]) if complete else None
            knees.append(value)
            if complete and value is None:invalid.append(knee)
        evidence.update(torso_vertical_cos=c,shoulder_span_ratio=spans[0],hip_span_ratio=spans[1],
            knee_angles=knees,missing_lower_joints=[i for i in (13,14,15,16) if p[i] is None],
            invalid_knee_geometry=invalid)
        lower_usable=all(a is not None for a in knees)
        bent=lower_usable and all(cfg['bent_knee_min']<=a<=cfg['bent_knee_max'] for a in knees)
        from .bed_geometry import contains,relative_xy
        hips_inside=all(contains(obs.bed_rectangle,p[i]) for i in (11,12))
        if cfg['view']=='oblique' and c>cfg['lying_cos']:
            evidence['information_path']='upright_lower_body'
            upright=c>=cfg['upright_cos'] and s[1]<h[1]
            # Extra leg coordinates cannot resolve an intermediate torso projection.
            if not upright:return held('view_or_body_orientation_ambiguous')
            if not lower_usable:return held('automatic_lower_body_needed')
            legs_down=all(p[k][1]>p[hip][1] and p[a][1]>p[k][1] for hip,k,a in ((11,13,15),(12,14,16)))
            if legs_down and min(knees)>=cfg['straight_knee_min']:return held('standing_or_upright_out_of_scope')
            uv=relative_xy(obs.bed_rectangle,h)
            if uv is None:return held('bed_coordinate_unavailable')
            edge=min(uv[0],1-uv[0],uv[1],1-uv[1])
            if isinstance(obs.bed_rectangle,tuple):
                # Retain the legacy rectangle arithmetic and boundary behavior.
                x1,y1,x2,y2=obs.bed_rectangle
                edge=min((h[0]-x1)/(x2-x1),(x2-h[0])/(x2-x1),(h[1]-y1)/(y2-y1),(y2-h[1])/(y2-y1))
            elif hips_inside and -1e-9<edge<0:edge=0.
            evidence['hip_edge_fraction']=edge
            thighs_across=all(abs(p[k][1]-p[hip][1])<=cfg['lying_cos']*math.dist(p[k],p[hip]) for hip,k in ((11,13),(12,14)))
            feet_down=all(p[a][1]>p[k][1] for k,a in ((13,15),(14,16)))
            if bent and thighs_across and feet_down and hips_inside and 0<=edge<=cfg['edge_fraction']:
                return 'edge_sitting',None,evidence
            return held('view_or_body_orientation_ambiguous')
        if cfg['view']=='overhead':
            evidence['information_path']='overhead'
            if bent:return held('overhead_sitting_ambiguous')
            # Preserve the conservative v2 gate for non-horizontal partial bodies.
            if not lower_usable and c>cfg['lying_cos']:return held('automatic_lower_body_needed')
        else:evidence['information_path']='lying_torso'
        # Lying decisions do not consume knee angles. Preserve invalid leg evidence
        # instead of letting an unused zero-length projection veto the whole frame.
        if not hips_inside or not all(contains(obs.bed_rectangle,p[i]) for i in (5,6)):
            return held('body_outside_bed_region')
        if max(spans)<=cfg['side_span_max']:return 'side',None,evidence
        if min(spans)>=cfg['front_span_min']:
            if any(p[i] is None for i in (0,1,2)):return held('front_facing_evidence_missing')
            across=(p[5][0]-p[6][0],p[5][1]-p[6][1]);down=(h[0]-s[0],h[1]-s[1])
            if across[0]*down[1]-across[1]*down[0]<=0:return held('front_back_ambiguous')
            return 'supine',None,evidence
        return held('lying_orientation_ambiguous')

    def predict(self,observation):return self.evaluate(observation)[0]
