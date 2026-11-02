"""Experimental learned evaluation on the unchanged integrated v1/v5 search.

Standard-library runtime. No training, disk database, or network use in a turn.
The terminal win/tie convention and bounded exact outcome solver are inherited.
"""
from player_versions.verified_denial_08.PhaseFeatures import raw_features, phase_mix, NAMES
from player_versions.verified_denial_08.LearnedPhaseWeights import COEFFICIENTS, VERSION
from player_versions.verified_denial_08.SelectiveEndgamePlayer import Searcher as Integrated, Config, _Guidance

WIDTH = len(NAMES)
if len(COEFFICIENTS) != 3*WIDTH:
    raise ValueError('Feature/model dimension mismatch')

# Phase interpolation depends only on the remaining stones, not the clock.
WEIGHTS = tuple(tuple(sum(mix[k]*COEFFICIENTS[k*WIDTH+j] for k in range(3))
                      for j in range(WIDTH)) for mix in map(phase_mix,range(37)))


def future_margin(pos):
    stones = sum(pos.board)
    estimate = sum(w*x for w,x in zip(WEIGHTS[stones],raw_features(pos)))
    # A bounded heuristic remains an estimate; it never creates a proof flag.
    return max(-stones,min(stones,estimate))


class LearnedGuidance(_Guidance):
    def evaluate(self,pos):
        self.stats['eval_calls'] += 1
        return pos.turn*(100*pos.diff+round(100*future_margin(pos)))


class Searcher(Integrated):
    def __init__(self,config=None,proof_capacity=100000):
        super().__init__(config,proof_capacity)
        self.normal = LearnedGuidance(self.normal.config)

    def choose(self,state):
        move = super().choose(state)
        self.stats['evaluation_version'] = VERSION
        return move


_player = None


def configure(seconds=29.0,max_nodes=0):
    global _player
    _player = Searcher(Config(seconds=seconds,max_nodes=max_nodes))


def name(): return 'Learned phase evaluation 01 (experimental)'


def getMove(state):
    global _player
    if _player is None: configure()
    return _player.choose(state)


def getStats(): return dict(_player.stats) if _player else {}
