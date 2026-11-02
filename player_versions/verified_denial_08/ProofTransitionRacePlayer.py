"""Preserve practical search when a loss is proved during the current turn.

The original wrapper checks loss status only at turn entry. A proof completed
between guidance and fallback therefore left outcome anchors enabled, flattening
all root choices to -WIN and ending fallback at depth one. Recheck at every
normal phase, and invalidate cached values whenever anchor semantics change.
"""
from player_versions.verified_denial_08.GameCore import from_state
from player_versions.verified_denial_08.EfficientRacePlayer import Searcher as Efficient, Guidance as EfficientGuidance, Config
from player_versions.verified_denial_08.SelectiveEndgamePlayer import proof_key, unpack


class Guidance(EfficientGuidance):
    def __init__(self,config,proofs):
        super().__init__(config,proofs);self.cache_lost_mode=False
    def choose(self,state):
        fact=self.proofs.get(proof_key(from_state(state)))
        lost=fact is not None and not unpack(fact)[0]
        changed=lost!=self.cache_lost_mode
        if changed:self.table.clear()
        self.root_already_lost=lost;self.cache_lost_mode=lost
        move=super().choose(state)
        self.stats.update(loss_mode_transition=changed,root_already_lost=lost)
        return move


class Searcher(Efficient):
    def __init__(self,config=None,proof_capacity=100000):
        super().__init__(config,proof_capacity);self.normal=Guidance(self.normal.config,self.proofs)
    def choose(self,state):
        move=super().choose(state)
        self.stats.update(search_version='proof-transition-race-06',
            loss_mode_transitions=sum(p.get('loss_mode_transition',False) for p in self.stats['phases']))
        return move

_player=None
def configure(seconds=29.0,max_nodes=0):
    global _player
    _player=Searcher(Config(seconds=seconds,max_nodes=max_nodes))
def name():return 'Race-calibrated player with proof transition repair'
def getMove(state):
    global _player
    if _player is None:configure()
    return _player.choose(state)
def getStats():return dict(_player.stats) if _player else {}
