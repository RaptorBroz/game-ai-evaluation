"""Denial attacker with repaired search, bounded evaluation cache and counterplay.

Retains the original denial heuristic. Terminal certificates from the backward
trace supply verified counterplay; there are no hard-coded opening moves.
"""
from player_versions.verified_denial_08.KnowledgeTracePlayer06 import Searcher as Foundation, Config
from player_versions.verified_denial_08.ProofTransitionRacePlayer import Guidance as BaseGuidance
from player_versions.verified_denial_08.BonusDenialPlayer import denial_margin


class Guidance(BaseGuidance):
    def evaluate(self,pos):
        self.stats['eval_calls']+=1
        key=(pos.board,pos.turn)
        value=self.eval_new.get(key)
        if value is None:value=self.eval_old.get(key)
        if value is None:
            value=round(100*denial_margin(pos))
            if len(self.eval_new)>=self.eval_capacity//2:
                self.eval_old=self.eval_new;self.eval_new={}
            self.eval_new[key]=value
        else:self.stats['eval_cache_hits']+=1
        return pos.turn*(100*pos.diff+value)


class Searcher(Foundation):
    def __init__(self,config=None,proof_capacity=100000):
        super().__init__(config,proof_capacity)
        self.normal=Guidance(self.normal.config,self.proofs)
    def choose(self,state):
        move=super().choose(state)
        self.stats['attack_profile']='verified-denial-08'
        return move


_player=None
def configure(seconds=29,max_nodes=0):
    global _player
    _player=Searcher(Config(seconds=seconds,max_nodes=max_nodes))
def name():return 'Verified denial counterplay attacker 08'
def getMove(state):
    global _player
    if _player is None:configure()
    return _player.choose(state)
def getStats():return dict(_player.stats) if _player else {}
