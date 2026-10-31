"""Shared instantaneous decision functions; no temporal or quality policy changes."""

import math


def scores_valid(scores, names):
    return (isinstance(scores, dict) and set(scores) == set(names)
            and all(type(v) in (int, float) and math.isfinite(v) and 0 <= v <= 1 for v in scores.values())
            and abs(math.fsum(scores.values())-1) < 1e-6)


def choose(scores, threshold, tie_tolerance=1e-8):
    """Select a unique maximum above the existing threshold; no runner-up margin."""
    if not scores:
        return None
    best = max(scores, key=scores.get)
    return best if (scores[best] >= threshold and
                    sum(abs(v-scores[best]) <= tie_tolerance for v in scores.values()) == 1) else None


def finalize(state, relation):
    """Compose image posture and independent bed relation with the existing rules."""
    if state['status'] != 'predicted':
        return None, (state['reasons'] or ['body_state_unknown'])[0]
    if state['state'] == 'lying':
        direction = state['lying_direction']
        if direction in ('supine', 'side'):
            return direction, None
        return None, 'prone_out_of_scope' if direction == 'prone' else 'lying_direction_evidence_missing'
    if state['state'] == 'sitting':
        if relation['status'] == 'observed' and relation['relation'] == 'edge':
            return 'edge_sitting', None
        return None, 'bed_edge_relation_unconfirmed'
    return None, 'standing_or_other_out_of_scope'
