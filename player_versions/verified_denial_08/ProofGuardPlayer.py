"""Use completed root-child proofs when the integrated solver runs out of time.

The frozen learned evaluation and original TT policy are unchanged. Prefer a
proved win; exclude proved losing root moves only while another move is not
proved losing. If all moves are known losses, retain ordinary margin search.
No heuristic value is converted into a proof or an exact numeric margin.
"""
from player_versions.verified_denial_08.GameCore import from_state, generate
from player_versions.verified_denial_08.LearnedPhasePlayer import Searcher as Learned, LearnedGuidance, Config
from player_versions.verified_denial_08.SelectiveEndgamePlayer import proof_key, unpack


class GuardGuidance(LearnedGuidance):
    def __init__(self, config, proofs):
        super().__init__(config)
        self.proofs = proofs

    def _start(self, seconds=None):
        super()._start(seconds)
        self.filtered = False
        self.excluded = set()

    def _order(self, pos, edges, preferred, ply):
        if ply == 0:
            kept = []
            rejected = []
            for edge in edges:
                fact = self.proofs.get(proof_key(edge.child))
                if fact is not None and unpack(fact)[0]:
                    rejected.append(edge.move)
                else:
                    kept.append(edge)
            if kept and rejected:
                edges = kept
                self.filtered = True
                self.excluded.update(rejected)
        return super()._order(pos, edges, preferred, ply)

    def choose(self, state):
        move = super().choose(state)
        if self.filtered:
            # The selected subset can establish an outcome, but cannot claim
            # the best numerical losing margin across excluded alternatives.
            # No descendant search can revisit the root in this acyclic game.
            self.table.pop(from_state(state), None)
        self.stats['root_proved_losses_excluded'] = len(self.excluded)
        return move


class Searcher(Learned):
    def __init__(self, config=None, proof_capacity=100000):
        super().__init__(config, proof_capacity)
        self.normal = GuardGuidance(self.normal.config, self.proofs)

    def choose(self, state):
        pos = from_state(state)
        for edge in generate(pos):
            fact = self.proofs.get(proof_key(edge.child))
            if fact is not None and not unpack(fact)[0]:
                self.proofs.put(proof_key(pos), True, edge.move)
                break
        move = super().choose(state)
        self.stats['root_proved_losses_excluded'] = max(
            (p.get('root_proved_losses_excluded', 0) for p in self.stats['phases']), default=0)
        self.stats['search_version'] = 'root-proof-guard-01'
        return move


_player = None
def configure(seconds=29.0, max_nodes=0):
    global _player
    _player = Searcher(Config(seconds=seconds, max_nodes=max_nodes))
def name(): return 'Learned evaluator with completed-root-proof guard (experimental)'
def getMove(state):
    global _player
    if _player is None: configure()
    return _player.choose(state)
def getStats(): return dict(_player.stats) if _player else {}
