"""Apply verified search-work savings to the successful race-calibration candidate.

The race coefficients, original 33 learned coefficients, proof book and move
ordering are unchanged. This is a performance revision, not a new strategy.
"""
from player_versions.verified_denial_08.EfficientPreventionPlayer import Searcher as Efficient, EfficientGuidance, Config
from player_versions.verified_denial_08.RacePlayer import WEIGHT_TABLE, raw_features, VERSION


class Guidance(EfficientGuidance):
    def evaluate(self,pos):
        stones=sum(pos.board)
        if stones>=24:return super().evaluate(pos)
        self.stats['eval_calls']+=1
        key=(pos.board,pos.turn);value=self.eval_new.get(key)
        if value is None:value=self.eval_old.get(key)
        if value is None:
            future=sum(w*x for w,x in zip(WEIGHT_TABLE[stones],raw_features(pos)))
            value=round(100*max(-stones,min(stones,future)))
            if len(self.eval_new)>=self.eval_capacity//2:
                self.eval_old=self.eval_new;self.eval_new={}
            self.eval_new[key]=value
        else:self.stats['eval_cache_hits']+=1
        return pos.turn*(100*pos.diff+value)


class Searcher(Efficient):
    def __init__(self,config=None,proof_capacity=100000):
        super().__init__(config,proof_capacity)
        self.normal=Guidance(self.normal.config,self.proofs)
    def choose(self,state):
        move=super().choose(state)
        self.stats.update(search_version='efficient-race-05',evaluation_version=VERSION)
        return move

_player=None
def configure(seconds=29.0,max_nodes=0):
    global _player
    _player=Searcher(Config(seconds=seconds,max_nodes=max_nodes))
def name():return 'Race-calibrated learned player with efficient search'
def getMove(state):
    global _player
    if _player is None:configure()
    return _player.choose(state)
def getStats():return dict(_player.stats) if _player else {}
