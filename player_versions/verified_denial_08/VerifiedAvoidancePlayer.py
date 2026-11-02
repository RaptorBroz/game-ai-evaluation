"""Learned evaluation + root proof guard + verified outcome reuse before heuristic search.

The compact offline book stores proved thresholds, never patterns learned from
game winners. It has no network or disk-database dependency and fits inside the
existing 100k outcome-entry allowance together with the live proof cache.
"""
from player_versions.verified_denial_08.GameCore import from_state
from player_versions.verified_denial_08.LearnedPhasePlayer import Config, LearnedGuidance
from player_versions.verified_denial_08.ProofGuardPlayer import Searcher as Guard, GuardGuidance
from player_versions.verified_denial_08.SelectiveEndgamePlayer import ProofCache, proof_key, unpack, WIN_BIT, NO_MOVE
from player_versions.verified_denial_08.VerifiedOutcomeBook import RECORDS, VERSION
from player_versions.verified_denial_08.challengers.LeafV5 import WIN


def lookup(key):
    row = RECORDS.get(key[:37])
    if row is None: return None
    low, light_move, high, dark_move = row; diff = key[37] - 36
    if low is not None and diff >= low: light_wins, move = True, light_move
    elif high is not None and diff <= high: light_wins, move = False, dark_move
    else: return None
    won = light_wins if key[36] else not light_wins
    return (WIN_BIT if won else 0) | (NO_MOVE if move is None else move)


class IndexedProofs(ProofCache):
    def __init__(self, capacity):
        super().__init__(capacity); self.book_hits = 0

    def get(self, key):
        if key == getattr(self, 'suppressed_root', None): return None
        value = super().get(key)
        if value is not None: return value
        value = lookup(key)
        if value is not None: self.book_hits += 1
        return value


class PreventionGuidance(GuardGuidance):
    def _order(self,pos,edges,preferred,ply):
        if self.root_already_lost:
            return LearnedGuidance._order(self,pos,edges,preferred,ply)
        return super()._order(pos,edges,preferred,ply)

    def _start(self, seconds=None):
        super()._start(seconds)
        self.stats.update(prevention_hits=0, prevention_win_hits=0, prevention_loss_hits=0)

    def _search(self, pos, depth, alpha, beta, ply=0):
        self._check()
        if not self.root_already_lost:
            fact = self.proofs.get(proof_key(pos))
            if fact is not None:
                self.stats['nodes'] += 1; self.stats['prevention_hits'] += 1
                won, _ = unpack(fact)
                self.stats['prevention_win_hits' if won else 'prevention_loss_hits'] += 1
                return WIN if won else -WIN
        return super()._search(pos, depth, alpha, beta, ply)


class Searcher(Guard):
    def __init__(self, config=None, proof_capacity=100000):
        super().__init__(config,proof_capacity)
        if proof_capacity <= len(RECORDS) + 2: raise ValueError('Outcome capacity too small for the frozen book')
        self.proofs = IndexedProofs(proof_capacity-len(RECORDS))
        self.normal = PreventionGuidance(self.normal.config,self.proofs)

    def choose(self,state):
        pos = from_state(state); fact = self.proofs.get(proof_key(pos))
        self.normal.root_already_lost = fact is not None and not unpack(fact)[0]
        # Some certificates prove a win without retaining a move. They are
        # sufficient inside search but cannot be an instant root response.
        self.proofs.suppressed_root = proof_key(pos) if fact is not None and unpack(fact) == (True,None) else None
        before = self.proofs.book_hits
        try: move = super().choose(state)
        finally: self.proofs.suppressed_root = None
        for key in ('prevention_hits','prevention_win_hits','prevention_loss_hits'):
            self.stats[key] = sum(p.get(key,0) for p in self.stats['phases'])
        self.stats.update(search_version='verified-prevention-01',book_version=VERSION,
            book_hits=self.proofs.book_hits-before, book_entries=len(RECORDS),
            total_outcome_entries=len(self.proofs)+len(RECORDS),
            normal_value_semantics='Heuristic scores or proved outcome anchors; not exact final margins.')
        return move


_player = None
def configure(seconds=29.0,max_nodes=0):
    global _player
    _player = Searcher(Config(seconds=seconds,max_nodes=max_nodes))
def name(): return 'Learned player with verified loss prevention'
def getMove(state):
    global _player
    if _player is None: configure()
    return _player.choose(state)
def getStats(): return dict(_player.stats) if _player else {}
