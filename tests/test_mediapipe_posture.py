"""Controlled joint observations and replay checks, not measured pose accuracy."""
import copy
import json
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import patch
from bed_pose.automatic_posture import AutomaticClassifier,NATIVE_DEFAULTS,SEPARATED_DEFAULTS
from bed_pose.posture import assess_frame
from bed_pose.contracts import PoseOutput,IntegrityError
from bed_pose.io_utils import load_json,atomic_json,file_hash
from bed_pose.live_recording import verify_live
from test_automatic_posture import observation
from test_posture_evidence import sample


class MediaPipeOnlyTests(unittest.TestCase):
    def setUp(self):self.model=AutomaticClassifier(NATIVE_DEFAULTS)

    def test_final_labels_without_clip(self):
        with patch('bed_pose.body_state.observe',side_effect=AssertionError('CLIP invoked')):
            for pose in ('supine','side','edge_sitting','standing'):
                label,reason,e=self.model.evaluate(observation(pose))
                self.assertEqual(label,pose,(pose,reason,e))
                self.assertIsNone(reason)
                self.assertEqual(e['information_path'],'mediapipe_joint_geometry')
                self.assertFalse(e['context_assessment']['physical_posture_verified'])
                self.assertAlmostEqual(sum(e['body_state']['scores'].values()),1)

    def test_sitting_inside_and_without_region(self):
        obs=observation('edge_sitting')
        for region,expected in (((20,20,620,350),'sitting'),(None,'sitting')):
            self.assertEqual(self.model.predict(replace(obs,bed_rectangle=region)),expected)
        self.assertEqual(self.model.predict(replace(observation('supine'),bed_rectangle=None)),'supine')

    def test_missing_joints_and_no_target_hold(self):
        for pose,index,reason in (('supine',5,'automatic_torso_joints_missing'),
                                  ('standing',15,'automatic_lower_body_needed')):
            obs=observation(pose);p=list(obs.points);p[index]=None
            self.assertEqual(self.model.evaluate(replace(obs,points=tuple(p)))[1],reason)
        row=sample();row['mapped_people']=[]
        self.assertEqual(assess_frame(row,640,360,None,self.model)['reasons'],['no_candidate'])

    def test_quality_and_nonvisual_inputs(self):
        row=sample();expected=assess_frame(row,640,360,None,self.model)
        self.assertEqual(expected['label'],'supine')
        changed=copy.deepcopy(row);changed.update(target_posture='standing',verified_gt='standing',sensor_results={'label':'standing'})
        self.assertEqual(assess_frame(changed,640,360,None,self.model),expected)
        source=changed['mapped_people'][0]['joints'][5]['source_index']
        changed['raw_candidates'][0]['sdk_landmarks']['image'][source]['visibility']=.1
        self.assertEqual(assess_frame(changed,640,360,None,self.model)['reasons'],['automatic_torso_joints_missing'])

    def test_old_separation_profile_keeps_old_results(self):
        old=AutomaticClassifier(SEPARATED_DEFAULTS)
        self.assertIsNone(old.predict(observation('supine')))
        self.assertEqual(self.model.predict(observation('supine')),'supine')

    def test_valid_registered_bed_axis_overrides_screen_axis(self):
        obs=replace(observation('standing'),bed_rectangle={'placeholder':True},world_points=((0.,0.,0.),)*17)
        geometry={'torso_plane_normal_cos':0.}
        with patch('bed_pose.viewpoint_posture.evaluate',return_value=('side',None,geometry)):
            label,_,e=self.model.evaluate(obs)
        self.assertEqual(label,'side')
        self.assertEqual(e['body_state']['details']['axis_source'],'bed_registered_model_3d')

    def test_projected_bed_geometry_with_camera_rotation(self):
        from test_viewpoint_posture import scene
        for pose in ('supine','side','edge_sitting','standing'):
            for roll,tilt in ((0,0),(35,25),(90,55)):
                with self.subTest(pose=pose,roll=roll,tilt=tilt):
                    label,reason,e=self.model.evaluate(scene(pose,roll,tilt))
                    self.assertEqual(label,pose,(reason,e))
                    self.assertEqual(e['body_state']['details']['axis_source'],'bed_registered_model_3d')

    def test_native_group_still_requires_time_target_and_agreement(self):
        from bed_pose.reference_posture import combine_views
        views=[{'input_id':sid,'closed':False,'time_ns':'1000','max_age_ns':100,
                'tracking_provisional':False,'unique_bed_candidate':True,
                'reference_profile':NATIVE_DEFAULTS,'assessment':{'status':'predicted','label':'supine'}}
               for sid in ('a','b')]
        def result():return combine_views(views,50,[],True,1000,association_policy='bed-priority-v2')
        self.assertEqual(result()['label'],'supine')
        views[1]['unique_bed_candidate']=False
        self.assertIn('bed_person_unavailable_or_ambiguous',result()['reasons'])
        views[1]['unique_bed_candidate']=True;views[1]['time_ns']='900'
        self.assertIn('pair_time_mismatch',result()['reasons'])
        views[1]['time_ns']='1000';views[1]['assessment']['label']='standing'
        self.assertIn('view_posture_conflict',result()['reasons'])

    def test_live_recording_replay_and_rehashed_tamper(self):
        from bed_pose.live_engine import LiveEngine
        from bed_pose.live_sources import SyntheticSource
        from bed_pose.pose.fake import FakeAdapter
        from bed_pose.pose.mediapipe import mapping_profile
        from bed_pose.record_library import RecordLibrary
        class Adapter(FakeAdapter):
            def estimate(self,m):return PoseOutput(copy.deepcopy(sample()['raw_candidates']),m.model_timestamp_ms,True)
        with tempfile.TemporaryDirectory() as tmp:
            engine=LiveEngine(SyntheticSource(interval=0),Adapter(),{'execution_mode':'ordered_sequence'},tmp,
                              profile=mapping_profile(),execution_kind='synthetic')
            engine.posture_classifier=self.model
            with patch('bed_pose.body_state.observe',side_effect=AssertionError('CLIP invoked')):
                try:
                    engine.open();engine.step()
                    directory=engine.start_measurement()
                    result=engine.step()
                    engine.stop_measurement()
                finally:engine.close()
            self.assertEqual(result['row']['posture_assessment']['label'],'supine')
            self.assertEqual(verify_live(directory)['integrity'],'verified')
            library=RecordLibrary(Path(tmp));library.open(directory.name)
            manifest=load_json(directory/'manifest.json')
            self.assertNotIn('body_state_provider_profile',manifest)
            p=directory/'live_frames.jsonl';rows=[json.loads(v) for v in p.read_text().splitlines()]
            rows[0]['posture_assessment']['label']='standing'
            p.write_text(''.join(json.dumps(v)+'\n' for v in rows),encoding='utf-8')
            manifest['artifact_sha256'][p.name]=file_hash(p);atomic_json(directory/'manifest.json',manifest)
            with self.assertRaises(IntegrityError):verify_live(directory)


import test_web_workspace as web

class MediaPipeWorkspaceTests(unittest.TestCase):
    setUp=web.WebTests.setUp
    cleanup=web.WebTests.cleanup
    request=web.WebTests.request
    wait=web.WebTests.wait
    demo=web.WebTests.demo
    control=web.WebTests.control

    def native_input(self):
        from bed_pose.live_engine import LiveEngine
        from bed_pose.pose.fake import FakeAdapter
        from bed_pose.pose.mediapipe import mapping_profile
        class Adapter(FakeAdapter):
            def estimate(self,m):return PoseOutput(copy.deepcopy(sample()['raw_candidates']),m.model_timestamp_ms,True)
        def factory(source,model,output_root,options_root,**kwargs):
            return LiveEngine(source,Adapter(),{'execution_mode':'ordered_sequence'},output_root,
                              profile=mapping_profile(),execution_kind='synthetic')
        self.workspace.factory=factory
        sid=self.demo()
        self.assertEqual(self.control(sid,'posture_mode',mode='automatic')[0],200)
        self.wait(lambda x:any(s['id']==sid and (s['posture_assessment'] or {}).get('label')=='supine' for s in x['sessions']))
        return sid

    def test_single_workspace_without_clip_or_bed(self):
        sid=self.native_input()
        status,view=self.request('/api/view/'+sid)
        self.assertEqual(status,200)
        self.assertEqual(view['posture_assessment']['label'],'supine')
        self.assertEqual(self.control(sid,'start')[0],200)
        self.wait(lambda x:x['sessions'][0]['recorded_frames']>=2)
        self.assertEqual(self.control(sid,'stop')[0],200)
        state=self.wait(lambda x:x['sessions'][0]['integrity']=='verified')['sessions'][0]
        self.assertEqual(state['automatic_posture_profile'],NATIVE_DEFAULTS)
        self.assertEqual(verify_live(state['directory'])['integrity'],'verified')
        record_id=load_json(Path(state['directory'])/'manifest.json')['measurement_id']
        self.assertEqual(self.request('/api/records/open',{'record_id':record_id})[0],200)
        status,page=self.request('/api/records/frames?record_id='+record_id+'&offset=0&limit=50')
        self.assertEqual(status,200)
        self.assertEqual(page['frames'][0]['assessment']['label'],'supine')

    def test_two_native_views_agree_without_clip(self):
        ids=[self.native_input(),self.native_input()]
        self.wait(lambda x:len(x['sessions'])==2 and all(s['frame_id'] is not None and s['pending'] is None for s in x['sessions']))
        for sid in ids:
            _,view=self.request('/api/view/'+sid)
            self.assertEqual(self.control(sid,'region',box=[1,1,639,359],selected_frame_id=view['frame_id'])[0],200)
        self.wait(lambda x:all(s['region'] is not None and s['pending'] is None for s in x['sessions']))
        status,result=self.request('/api/group',{'action':'start','inputs':ids,'max_skew_ms':1000,
                                  'association_policy':'bed-priority-v2','bed_regions_confirmed':True})
        self.assertEqual(status,200,result)
        self.wait(lambda x:x['groups'][0]['phase']=='recording' and all(s['recorded_frames']>=3 for s in x['sessions']))
        self.wait(lambda x:(x['groups'][0].get('posture_assessment') or {}).get('label')=='supine')
        self.request('/api/group',{'action':'stop','group_id':result['group_id']})
        group=self.wait(lambda x:x['groups'][0]['phase']=='completed')['groups'][0]
        from bed_pose.group_posture import verify_predictions
        verify_predictions(load_json(Path(group['directory'])/'manifest.json'),Path(group['directory']))
        for member in group['members']:
            self.assertEqual(verify_live(member['run_directory'])['integrity'],'verified')


if __name__=='__main__':unittest.main()
