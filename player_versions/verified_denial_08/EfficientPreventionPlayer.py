"""Same learned policy and proof guard; avoid redundant search work.

Move descriptors defer board copies until a branch is visited. Quiet ordering
is algebraically identical to V1/V5. A bounded cache reuses the unchanged
rounded future-margin estimate, independent of banked capture scores.
No selective pruning, retraining, or new book knowledge.
"""
import time
from player_versions.verified_denial_08.GameCore import Position, RAYS, SQUARES
from player_versions.verified_denial_08.LearnedPhasePlayer import future_margin, Config
from player_versions.verified_denial_08.VerifiedAvoidancePlayer import Searcher as Base, PreventionGuidance
from player_versions.verified_denial_08.SelectiveEndgamePlayer import proof_key, unpack
from player_versions.verified_denial_08.challengers.LeafV5 import WIN, INF, EXACT, LOWER, UPPER, has_legal_move


def descriptors(pos):
    """(move, gain, combine target or sow path), professor order."""
    board,side,_=pos
    result=[]
    for i in SQUARES[side]:
        size=board[i]
        if not size:continue
        for d,ray in enumerate(RAYS[i][:4]):
            for j in ray:
                if board[j]:
                    result.append((i*8+d,0,j));break
        if size<2:continue
        for d in range(4,8):
            path=RAYS[i][d][:size]
            gain=sum(board[j]+1 for j in path[::2] if 0<board[j]<size)
            if gain:result.append((i*8+d,gain,path))
    return result


def advance(pos, item):
    move,gain,target=item;source=move//8
    b=list(pos.board);size=b[source]
    if not gain:
        b[target]+=size;b[source]=0
    else:
        b[source]=size-len(target)
        for offset,j in enumerate(target):
            b[j]=0 if offset%2==0 and 0<pos.board[j]<size else pos.board[j]+1
    return Position(tuple(b),-pos.turn,pos.diff+pos.turn*gain)


class EfficientGuidance(PreventionGuidance):
    def __init__(self,config,proofs):
        super().__init__(config,proofs)
        self.eval_new={};self.eval_old={}
        self.eval_capacity=25000

    def _start(self,seconds=None):
        super()._start(seconds)
        self.stats.update(eval_cache_hits=0,child_boards_built=0,legal_descriptors=0)

    def evaluate(self,pos):
        self.stats['eval_calls']+=1
        key=(pos.board,pos.turn)
        value=self.eval_new.get(key)
        if value is None:value=self.eval_old.get(key)
        if value is None:
            value=round(100*future_margin(pos))
            if len(self.eval_new)>=self.eval_capacity//2:
                self.eval_old=self.eval_new;self.eval_new={}
            self.eval_new[key]=value
        else:self.stats['eval_cache_hits']+=1
        return pos.turn*(100*pos.diff+value)

    def _ordered_descriptors(self,pos,moves,preferred,ply):
        board=pos.board;largest=max(board[i] for i in SQUARES[pos.turn])
        killers=self.killers.get(ply,())
        def key(item):
            move,gain,target=item
            score=self.history.get((pos.turn,move),0)
            if move==preferred:score+=10000000
            score+=gain*10000
            if move in killers:score+=1000
            if not gain:score+=4*max(largest,board[move//8]+board[target])
            return score
        return sorted(moves,key=key,reverse=True)

    def _search(self,pos,depth,alpha,beta,ply=0):
        self._check();self.stats['nodes']+=1
        if not self.root_already_lost:
            fact=self.proofs.get(proof_key(pos))
            if fact is not None:
                self.stats['prevention_hits']+=1
                won,_=unpack(fact)
                self.stats['prevention_win_hits' if won else 'prevention_loss_hits']+=1
                return WIN if won else -WIN
        original_alpha,original_beta=alpha,beta
        entry=self.table.get(pos) if self.config.tt else None
        preferred=entry[3] if entry else None
        if entry:
            self.stats['tt_hits']+=1
            if entry[0]>=depth:
                _,value,flag,_=entry
                if flag==EXACT:return value
                if flag==LOWER:alpha=max(alpha,value)
                else:beta=min(beta,value)
                if alpha>=beta:
                    self.stats['tt_cutoffs']+=1;return value
        if depth==0:
            self.stats['leaf_probes']+=1
            if has_legal_move(pos):return self.evaluate(pos)
            self.stats['terminal_nodes']+=1;self.stats['leaf_terminal_nodes']+=1
            return self.terminal(pos)
        moves=descriptors(pos)
        self.stats['legal_descriptors']+=len(moves)
        if not moves:
            self.stats['terminal_nodes']+=1;return self.terminal(pos)
        best,best_move=-INF,None
        for item in self._ordered_descriptors(pos,moves,preferred,ply):
            move,gain,_=item
            self.stats['child_boards_built']+=1
            value=-self._search(advance(pos,item),depth-1,-beta,-alpha,ply+1)
            if value>best:best,best_move=value,move
            alpha=max(alpha,value)
            if alpha>=beta:
                self.stats['cutoffs']+=1
                if not gain:
                    k=(pos.turn,move);self.history[k]=self.history.get(k,0)+depth*depth
                    old=self.killers.get(ply,());self.killers[ply]=(move,)+tuple(m for m in old if m!=move)[:1]
                break
        flag=UPPER if best<=original_alpha else LOWER if best>=original_beta else EXACT
        self._store(pos,depth,best,flag,best_move)
        return best

    def _store(self,pos,depth,value,flag,move):
        # Preserve V1/V5 admission policy for the isolated performance revision.
        if self.config.tt and len(self.table)<self.config.tt_size:
            self.table[pos]=(depth,value,flag,move)


class Searcher(Base):
    def __init__(self,config=None,proof_capacity=100000):
        super().__init__(config,proof_capacity)
        self.normal=EfficientGuidance(self.normal.config,self.proofs)
    def choose(self,state):
        move=super().choose(state)
        self.stats['search_version']='efficient-prevention-04'
        for k in ('eval_cache_hits','child_boards_built','legal_descriptors'):
            self.stats[k]=sum(p.get(k,0) for p in self.stats['phases'])
        self.stats['evaluation_cache_entries']=len(self.normal.eval_new)+len(self.normal.eval_old)
        return move

_player=None
def configure(seconds=29.0,max_nodes=0):
    global _player
    _player=Searcher(Config(seconds=seconds,max_nodes=max_nodes))
def name():return 'Learned prevention with deferred board construction'
def getMove(state):
    global _player
    if _player is None:configure()
    return _player.choose(state)
def getStats():return dict(_player.stats) if _player else {}
