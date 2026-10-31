"""Conservative current-frame bed association, not identity recognition."""
POLICY='unique-person-in-bed-v1'


def eligible(candidate_count, assessment, region):
    if region is None or type(candidate_count) is not int or candidate_count != 1 or not isinstance(assessment,dict):
        return False
    relation=assessment.get('rule_features',{}).get('bed_relation') or {}
    return (bool(assessment.get('candidate_id')) and relation.get('status')=='observed'
            and relation.get('relation') in ('inside','edge'))
