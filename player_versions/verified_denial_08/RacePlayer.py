"""Successful learned foundation plus verified-data bonus-race evaluation."""
from player_versions.verified_denial_08.LearnedPhasePlayer import WEIGHTS, LearnedGuidance
from player_versions.verified_denial_08.RaceFeatures import raw_features
from player_versions.verified_denial_08.RaceWeights import DELTA, VERSION
from player_versions.verified_denial_08.VerifiedAvoidancePlayer import Searcher as Prevention, PreventionGuidance, Config

WEIGHT_TABLE=tuple(tuple(w+max(0,min(1,(24-s)/8))*d for w,d in zip(tuple(row)+(0,)*4,DELTA)) for s,row in enumerate(WEIGHTS))


class Guidance(PreventionGuidance):
    def evaluate(self,pos):
        stones=sum(pos.board)
        if stones>=24:return LearnedGuidance.evaluate(self,pos)
        self.stats['eval_calls']+=1
        future=sum(w*x for w,x in zip(WEIGHT_TABLE[stones],raw_features(pos)))
        return pos.turn*(100*pos.diff+round(100*max(-stones,min(stones,future))))


class Searcher(Prevention):
    def __init__(self,config=None,proof_capacity=100000):
        super().__init__(config,proof_capacity)
        self.normal=Guidance(self.normal.config,self.proofs)

    def choose(self,state):
        move=super().choose(state)
        self.stats['evaluation_version']=VERSION;self.stats['search_version']=VERSION
        return move


_player=None
def configure(seconds=29.0,max_nodes=0):
    global _player
    _player=Searcher(Config(seconds=seconds,max_nodes=max_nodes))
def name():return 'Learned player with calibrated move reserves'
def getMove(state):
    global _player
    if _player is None:configure()
    return _player.choose(state)
def getStats():return dict(_player.stats) if _player else {}
