import unittest
from bed_pose.bed_association import eligible, POLICY
from bed_pose.reference_posture import combine_views
from test_multiview_posture import views


class BedAssociationTests(unittest.TestCase):
    def test_empty_multiple_outside_and_missing_hips_are_not_associated(self):
        assessment={'candidate_id':'p0','rule_features':{'bed_relation':{'status':'observed','relation':'inside'}}}
        self.assertTrue(eligible(1,assessment,{'method':'bed'}))
        self.assertFalse(eligible(0,assessment,{'method':'bed'}))
        self.assertFalse(eligible(2,assessment,{'method':'bed'}))
        self.assertFalse(eligible(1,assessment,None))
        assessment['rule_features']['bed_relation']['relation']='outside'
        self.assertFalse(eligible(1,assessment,{'method':'bed'}))
        assessment['rule_features']['bed_relation']={'status':'unknown','relation':None}
        self.assertFalse(eligible(1,assessment,{'method':'bed'}))

    def test_time_gate_and_bed_gate_both_required(self):
        from bed_pose.multiview_posture import POLICY as FUSION
        v=views()
        for x in v:
            x['unique_bed_candidate']=True
            x['assessment']['rule_features']['body_state']['details']['direction_scores']={'supine':.8,'side':.1,'prone':.1}
        a=combine_views(v,50,[],True,1050,fusion_policy=FUSION,association_policy=POLICY)
        self.assertEqual(a['label'],'supine');self.assertFalse(a['identity_verified'])
        v[0]['unique_bed_candidate']=False
        self.assertIn('bed_person_unavailable_or_ambiguous',combine_views(v,50,[],True,1050,fusion_policy=FUSION,association_policy=POLICY)['reasons'])
        v[0]['unique_bed_candidate']=True;v[0]['time_ns']='1'
        self.assertIn('pair_time_mismatch',combine_views(v,50,[],True,1050,fusion_policy=FUSION,association_policy=POLICY)['reasons'])
