"""Fusion behavior with prescribed scores, not posture recognition accuracy."""
from copy import deepcopy
import unittest
from bed_pose.multiview_posture import POLICY
from bed_pose.reference_posture import combine_views
from test_clip_posture import configuration


def views():
    profile={'model_id':'openai/clip-vit-base-patch16','model_sha256':'0'*64,'preprocess_id':'test','decision_policy':configuration()}
    result=[]
    for i in range(2):
        body={'status':'held','state':'lying','score_semantics':'uncalibrated_probability',
              'input_quality':{'status':'usable'},'scores':{'lying':.8,'sitting':.1,'standing':.05,'other':.05},
              'details':{'direction_scores':{'supine':.45,'side':.4,'prone':.15}}}
        result.append({'input_id':str(i),'closed':False,'time_ns':str(1000+i*10),'max_age_ns':500,
                       'tracking_provisional':True,'image_profile':deepcopy(profile),
                       'reference_profile':{'version':'automatic-posture-rules-0.8'},
                       'assessment':{'status':'held','label':None,'track_id':'t'+str(i),'rule_features':{
                            'body_state':body,'bed_relation':{'status':'unknown','relation':None}}}})
    return result


def evaluate(v,**kw):
    return combine_views(v,kw.get('skew',50),kw.get('confirmations',[(0,{'0':'t0','1':'t1'})]),True,kw.get('now',1050),fusion_policy=POLICY)


class MultiviewTests(unittest.TestCase):
    def test_direction_complements_held_local_prediction_without_bed_or_pixel_averaging(self):
        v=views();v[1]['assessment']['rule_features']['body_state']['details']['direction_scores']={'supine':.9,'side':.05,'prone':.05}
        a=evaluate(v);self.assertEqual(a['label'],'supine');self.assertEqual(a['fusion_evidence']['mode'],'two_view_fusion')
        self.assertAlmostEqual(a['fusion_evidence']['direction_scores']['supine'],.675)

    def test_unusable_image_uses_one_view_but_reports_fallback(self):
        v=views();v[0]['assessment']['rule_features']['body_state']={'input_quality':{'status':'held'},'reasons':['body_state_crop_quality_insufficient']}
        v[1]['assessment']['rule_features']['body_state']['details']['direction_scores']={'supine':.1,'side':.8,'prone':.1}
        a=evaluate(v);self.assertEqual(a['label'],'side');self.assertEqual(a['fusion_evidence']['mode'],'single_view_fallback')
        self.assertEqual([x['used'] for x in a['fusion_evidence']['contributors']],[False,True])

    def test_disagreement_and_no_evidence_hold(self):
        v=views()
        for i,d in enumerate(({'supine':.8,'side':.1,'prone':.1},{'supine':.1,'side':.8,'prone':.1})):
            v[i]['assessment']['rule_features']['body_state']['details']['direction_scores']=d
        self.assertIsNone(evaluate(v)['label'])
        for x in v:x['assessment']['rule_features']['body_state']={}
        self.assertIn('fusion_no_usable_view',evaluate(v)['reasons'])

    def test_gates_are_not_relaxed_by_fusion_or_fallback(self):
        for mutation,expected in ((lambda v:v[0].update(time_ns='1'),'pair_time_mismatch'),
             (lambda v:v[0]['assessment'].update(track_id='new'),'operator_pair_confirmation_missing'),
             (lambda v:v[0].update(tracking_provisional=False),'view_features_unavailable'),
             (lambda v:v[0].update(closed=True),'view_unavailable')):
            v=views();mutation(v);self.assertIn(expected,evaluate(v)['reasons'])
        self.assertIn('stale_observation',evaluate(views(),now=5000)['reasons'])

    def test_execution_device_does_not_change_fusion_and_models_must_match(self):
        v=views();a=evaluate(v)
        v[0]['image_profile']['decision_policy']['device']='cpu';v[1]['image_profile']['decision_policy']['device']='cuda'
        self.assertEqual(a['fusion_evidence'],evaluate(v)['fusion_evidence'])
        v[1]['image_profile']['decision_policy']['device']='mps'
        self.assertEqual(a['fusion_evidence'],evaluate(v)['fusion_evidence'])
        v[1]['image_profile']['model_sha256']='1'*64;self.assertIn('fusion_provider_mismatch',evaluate(v)['reasons'])

    def test_sitting_requires_edge_context_and_conflicts_hold(self):
        v=views()
        for x in v:x['assessment']['rule_features']['body_state']['scores']={'lying':.05,'sitting':.85,'standing':.05,'other':.05}
        self.assertIsNone(evaluate(v)['label'])
        v[0]['assessment']['rule_features']['bed_relation']={'status':'observed','relation':'edge'}
        self.assertEqual(evaluate(v)['label'],'edge_sitting')
        v[1]['assessment']['rule_features']['bed_relation']={'status':'observed','relation':'outside'}
        self.assertIsNone(evaluate(v)['label'])

    def test_goal_sensor_and_gt_do_not_change_predictions(self):
        v=views();a=evaluate(v)
        for x in v:x.update(target_posture='side',sensor_results={'label':'side'},verified_gt='side')
        self.assertEqual(a['fusion_evidence'],evaluate(v)['fusion_evidence'])


class MultiviewWebTests(unittest.TestCase):
    from test_clip_posture import ClipWebTests
    setUp=ClipWebTests.setUp
    cleanup=ClipWebTests.cleanup

    def start_pair(self):
        from bed_pose.live_sources import SyntheticSource
        original=self.workspace.factory
        class Camera(SyntheticSource):
            def __init__(self,index):super().__init__(interval=.02);self.index=index
            def open(self):return dict(super().open(),kind='camera')
        def factory(source,*args,**kwargs):return original(Camera(source.index),*args,**kwargs)
        self.workspace.factory=factory
        ids=[];selections=[]
        for index in (0,1):
            status,result=self.request('/api/inputs',{'kind':'camera','camera':index,'use_clip':True})
            self.assertEqual(status,200,result);sid=result['id'];ids.append(sid)
            self.wait(lambda x:any(s['id']==sid and s['frame_id'] is not None for s in x['sessions']))
            capture=self.workspace.capture_target(sid);candidate=capture['people'][0]['candidate_id']
            selected=self.workspace.select_target({'ticket':capture['ticket'],'candidate_id':candidate,
                'tracking_config':{'max_gap_ms':10000,'max_speed_diagonals_per_second':100}})
            self.wait(lambda x:any(s['id']==sid and s.get('target_selection_applied')==selected['selection_id'] for s in x['sessions']))
            selections.append({'ticket':capture['ticket'],'candidate_id':candidate})
        status,result=self.request('/api/group',{'action':'start','inputs':ids,'max_skew_ms':1000,
            'target_selections':selections,'same_person_confirmed':True,'tracking_required':True})
        self.assertEqual(status,200,result)
        return result['group_id']

    def test_live_fusion_no_bed_record_replay_and_tampering(self):
        import json
        from pathlib import Path
        from bed_pose.fusion_inputs import inspect_group
        from bed_pose.io_utils import load_json,atomic_json,file_hash
        from bed_pose.contracts import IntegrityError
        gid=self.start_pair()
        result=self.wait(lambda x:x['groups'][0]['posture_assessment']['label']=='supine' and all(s['recorded_frames']>=4 for s in x['sessions']))
        self.assertEqual(result['groups'][0]['posture_assessment']['fusion_evidence']['mode'],'two_view_fusion')
        self.request('/api/group',{'action':'stop','group_id':gid})
        group=self.wait(lambda x:x['groups'][0]['phase']=='completed')['groups'][0];root=Path(group['directory'])
        self.assertEqual(inspect_group(root)['integrity'],'verified')
        manifest=load_json(root/'manifest.json');self.assertEqual(manifest['posture_predictions']['method'],'gated_image_score_fusion_v1')
        path=root/'posture_predictions.jsonl';rows=[json.loads(l) for l in path.read_text(encoding='utf-8').splitlines()]
        row=next(r for r in rows if r['label']=='supine');self.assertEqual(row['version'],'group-posture-0.3')
        row['fusion_evidence']['state_scores']['lying']=0.
        path.write_text(''.join(json.dumps(r)+'\n' for r in rows),encoding='utf-8')
        manifest['posture_predictions']['sha256']=file_hash(path);atomic_json(root/'manifest.json',manifest)
        with self.assertRaises(IntegrityError):inspect_group(root)
