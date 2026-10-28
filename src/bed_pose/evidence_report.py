"""Export verified live-frame comparison features without changing source records."""
from collections import Counter
import csv
from pathlib import Path

from .io_utils import atomic_json,file_hash,load_json,strict_loads
from .live_recording import verify_live
from .posture import assess_frame
from .posture_evidence import PROFILE,compare_frame
from .contracts import IntegrityError


COLUMNS=('measurement_id','frame_id','stream_frame_id','clock_id','received_ns','candidate_id',
         'baseline_status','baseline_label','baseline_reasons','baseline_classifier_id',
         'body_2d_status','body_2d_reasons','shoulder_transverse_2d','shoulder_axial_2d',
         'hip_transverse_2d','hip_axial_2d','line_angle_2d',
         'world_3d_status','world_3d_reasons','shoulder_transverse_3d','shoulder_axial_3d',
         'hip_transverse_3d','hip_axial_3d','line_angle_3d',
         'shoulder_depth_fraction','hip_depth_fraction','normal_world_x','normal_world_y','normal_world_z',
         'combined_status','combined_reasons','decision_source','orientation_2d','orientation_3d',
         'score_supine','score_side','score_edge_sitting','score_minimum','score_gap','score_close_candidates')


def _cells(row,evidence):
    baseline=evidence['baseline'];body=evidence['body_2d'];world=evidence['world_3d'];combined=evidence['combined']
    values={k:row[k] for k in ('measurement_id','frame_id','stream_frame_id','clock_id','received_ns')}
    values.update(candidate_id=evidence['candidate_id'],baseline_status=baseline['status'],baseline_label=baseline['label'],
                  baseline_reasons='|'.join(baseline['reasons']),baseline_classifier_id=baseline['classifier_id'],
                  body_2d_status=body['status'],body_2d_reasons='|'.join(body['reasons']),
                  world_3d_status=world['status'],world_3d_reasons='|'.join(world['reasons']),
                  combined_status=combined['status'],combined_reasons='|'.join(combined['reasons']))
    orientation=row.get('posture_assessment',{}).get('rule_features',{}).get('orientation_decision',{})
    values.update(decision_source=orientation.get('source'),orientation_2d=orientation.get('orientation_2d'),
                  orientation_3d=orientation.get('orientation_3d'))
    decision=row.get('posture_assessment',{}).get('rule_features',{}).get('score_decision',{})
    for name in ('supine','side','edge_sitting'):values['score_'+name]=decision.get('scores',{}).get(name)
    values.update(score_minimum=decision.get('minimum'),score_gap=decision.get('gap'),
                  score_close_candidates=decision.get('close_candidates'))
    for node,suffix in ((body,'2d'),(world,'3d')):
        f=node['features']
        for part,name in (('shoulders','shoulder'),('hips','hip')):
            for component in ('transverse','axial'):values[name+'_'+component+'_'+suffix]=f[part][component] if f else None
        values['line_angle_'+suffix]=f['line_angle_degrees'] if f else None
    f=world['features']
    for key in ('shoulder_depth_fraction','hip_depth_fraction'):values[key]=f[key] if f else None
    for i,axis in enumerate('xyz'):values['normal_world_'+axis]=f['torso_normal_world'][i] if f else None
    # Avoid spreadsheet formula execution if an adapter supplies an unusual ID.
    return {k:"'"+v if isinstance(v,str) and v.startswith(('=','+','-','@','\t','\r')) else v for k,v in values.items()}


def export_evidence(directory,output):
    directory=Path(directory).resolve();output=Path(output).resolve()
    if output==directory or directory in output.parents:raise ValueError('비교 보고서는 원본 측정 폴더 밖에 저장하세요.')
    verify_live(directory)
    manifest=load_json(directory/'manifest.json')
    manifest_hash=file_hash(directory/'manifest.json')
    output.mkdir(parents=True,exist_ok=False)
    counts={key:Counter() for key in ('baseline','body_2d','world_3d','combined')};frames=0
    try:
        with (output/'features.csv').open('x',encoding='utf-8-sig',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=COLUMNS);writer.writeheader()
            with (directory/'live_frames.jsonl').open(encoding='utf-8') as original:
                for line in original:
                    row=strict_loads(line)
                    assessment=row.get('posture_assessment') or assess_frame(row,manifest['width'],manifest['height'],None)
                    evidence=compare_frame(row,manifest['width'],manifest['height'],assessment)
                    writer.writerow(_cells(row,evidence));frames+=1
                    for key in counts:counts[key][evidence[key]['status']]+=1
        frames_hash=file_hash(directory/'live_frames.jsonl')
        if frames_hash!=manifest['artifact_sha256']['live_frames.jsonl'] or file_hash(directory/'manifest.json')!=manifest_hash:
            raise IntegrityError('Source record changed while exporting evidence')
        summary={'version':'posture-evidence-report-0.3','profile':PROFILE,'run_directory':str(directory),
                 'measurement_id':manifest['measurement_id'],'execution_kind':manifest['execution_kind'],
                 'source_manifest_sha256':manifest_hash,'source_frames_sha256':frames_hash,
                 'frame_count':frames,'counts':{k:dict(v) for k,v in counts.items()},
                 'features_csv_sha256':file_hash(output/'features.csv'),
                 'feature_origin':'recomputed_from_verified_original_observations',
                 'evaluation_status':'features_only_no_ground_truth_accuracy',
                 'classification_policy':'source_record_profile_unchanged_not_reclassified',
                 'source_automatic_posture_profile':manifest.get('automatic_posture_profile'),
                 'world_coordinates':'monocular_estimate_not_bed_height_or_external_sensor'}
        atomic_json(output/'summary.json',summary)
        return output,summary
    except Exception:
        for name in ('features.csv','summary.json'):(output/name).unlink(missing_ok=True)
        raise
