"""Attack hypothesis: restrict replies to contest who receives the final bonus.

One-ply continuation counts are heuristic features, never proof labels. Uses the
frozen learned search, clock and cache policy, without the refresh experiment.
"""
from player_versions.verified_denial_08.GameCore import generate, SQUARES
from player_versions.verified_denial_08.LearnedPhasePlayer import Searcher as Learned, LearnedGuidance, Config, future_margin


def termination_pressure(pos, side):
    """Best own post-move stack discounted by actual opponent reply count."""
    options = generate(pos._replace(turn=side))
    return max((max(e.child.board[i] for i in SQUARES[side]) /
                (1+len(generate(e.child))) for e in options), default=0.0)


def denial_margin(pos):
    stones = sum(pos.board)
    value = future_margin(pos)
    if stones <= 26 and sum(n > 0 for n in pos.board) <= 14:
        value += .6*(termination_pressure(pos, 1)-termination_pressure(pos, -1))
    return max(-stones, min(stones, value))


class DenialGuidance(LearnedGuidance):
    def evaluate(self, pos):
        self.stats['eval_calls'] += 1
        return pos.turn*(100*pos.diff+round(100*denial_margin(pos)))


class Searcher(Learned):
    def __init__(self, config=None, proof_capacity=100000):
        super().__init__(config, proof_capacity)
        self.normal = DenialGuidance(self.normal.config)

    def choose(self, state):
        move = super().choose(state)
        self.stats['attack_profile'] = 'reply-restriction-bonus-denial-01'
        return move


_player = None
def configure(seconds=29.0, max_nodes=0):
    global _player
    _player = Searcher(Config(seconds=seconds, max_nodes=max_nodes))
def name(): return 'Reply restriction / bonus denial attacker (experimental)'
def getMove(state):
    global _player
    if _player is None: configure()
    return _player.choose(state)
def getStats(): return dict(_player.stats) if _player else {}
