"""Legacy features plus general combine-reserve/bonus-race estimates.

Connected components use legal diagonal combine links. Without captures, a
component can be merged into one stack. Captures can change this graph, so the
reserve and bonus-race values are evaluation features, never outcome proofs.
"""
from player_versions.verified_denial_08.GameCore import SQUARES, RAYS
from player_versions.verified_denial_08.PhaseFeatures import NAMES as LEGACY_NAMES

NAMES=LEGACY_NAMES+('combine_reserve','component_mass','quiet_race_bonus','isolated_mass')


def raw_features(pos):
    board=pos.board;parents=list(range(36));sides=[];attacked=[];reserves=[];masses=[];isolated=[]
    for side in (1,-1):
        material=largest=combines=captures=best=stacks=0;targets=set()
        for i in SQUARES[side]:
            size=board[i]
            if not size:continue
            material+=size;stacks+=1
            if size>largest:largest=size
            for ray in RAYS[i][:4]:
                for j in ray:
                    if board[j]:
                        combines+=1
                        if i<j:
                            a,b=i,j
                            while parents[a]!=a:a=parents[a]
                            while parents[b]!=b:b=parents[b]
                            if a!=b:parents[b]=a
                        break
            if size>=2:
                for ray in RAYS[i][4:]:
                    gain=0
                    for j in ray[:size:2]:
                        if 0<board[j]<size:gain+=board[j]+1;targets.add(j)
                    if gain:
                        captures+=1
                        if gain>best:best=gain
        sides.append((material,largest,combines,captures,best,sum(board[j] for j in targets),stacks));attacked.append(targets)
        groups={};counts={}
        for i in SQUARES[side]:
            if board[i]:
                root=i
                while parents[root]!=root:root=parents[root]
                groups[root]=groups.get(root,0)+board[i];counts[root]=counts.get(root,0)+1
        reserves.append(stacks-len(groups));masses.append(max(groups.values(),default=0))
        isolated.append(sum(m for k,m in groups.items() if counts[k]==1))
    light,dark=sides;values=[a-b for a,b in zip(light,dark)]
    safe_light=max((board[i] for i in SQUARES[1] if i not in attacked[1]),default=0)
    safe_dark=max((board[i] for i in SQUARES[-1] if i not in attacked[0]),default=0)
    lm,dm=light[2]+light[3],dark[2]+dark[3]
    access=(light[1]*(lm+1)-dark[1]*(dm+1))/(lm+dm+2)
    values.extend((safe_light-safe_dark,access,pos.turn,pos.turn*(light[4]+dark[4])))
    light_last=reserves[0]>reserves[1] or (reserves[0]==reserves[1] and pos.turn==-1)
    bonus=(masses[0] if light_last else -masses[1])/(1+light[3]+dark[3])
    values.extend((reserves[0]-reserves[1],masses[0]-masses[1],bonus,isolated[0]-isolated[1]))
    return tuple(values)
