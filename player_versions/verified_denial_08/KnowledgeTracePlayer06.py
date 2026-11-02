"""Review candidate: retain the successful foundation and add verified knowledge.

Only complete outcome certificates enter this compact embedded book. The large
offline bound archive is not loaded by the player. No automatic selection.
"""
from player_versions.verified_denial_08.ProofTransitionRacePlayer import Searcher as Foundation, Guidance, Config
from player_versions.verified_denial_08.SelectiveEndgamePlayer import ProofCache, WIN_BIT, NO_MOVE
from player_versions.verified_denial_08.VerifiedAvoidancePlayer import IndexedProofs
from player_versions.verified_denial_08.TraceOutcomeBook06 import RECORDS, VERSION


class TraceProofs(IndexedProofs):
    def get(self,key):
        if key==getattr(self,'suppressed_root',None):return None
        fact=ProofCache.get(self,key)
        if fact is not None:return fact
        row=RECORDS.get(key[:37])
        if row is None:return None
        low,light_move,high,dark_move=row;diff=key[37]-36
        if low is not None and diff>=low:light_wins,move=True,light_move
        elif high is not None and diff<=high:light_wins,move=False,dark_move
        else:return None
        won=light_wins if key[36] else not light_wins
        self.book_hits+=1
        return (WIN_BIT if won else 0)|(NO_MOVE if move is None else move)


class Searcher(Foundation):
    def __init__(self,config=None,proof_capacity=100000):
        super().__init__(config,proof_capacity)
        if proof_capacity<=len(RECORDS)+2:raise ValueError('Proof capacity too small for embedded book')
        self.proofs=TraceProofs(proof_capacity-len(RECORDS))
        self.normal=Guidance(self.normal.config,self.proofs)

    def choose(self,state):
        move=super().choose(state)
        self.stats.update(search_version='knowledge-trace-07',book_version=VERSION,
                          book_entries=len(RECORDS),total_outcome_entries=len(self.proofs)+len(RECORDS))
        return move


_player=None
def configure(seconds=29,max_nodes=0):
    global _player
    _player=Searcher(Config(seconds=seconds,max_nodes=max_nodes))
def name():return 'Learned race player with verified backward-trace knowledge'
def getMove(state):
    global _player
    if _player is None:configure()
    return _player.choose(state)
def getStats():return dict(_player.stats) if _player else {}
