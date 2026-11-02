"""Cheap symmetry-invariant features for a learned future-score evaluator.

All signed features are Light minus Dark. No banked captures enter the vector.
The side-to-move features represent tempo, not the Light tie-breaking rule.
"""
from player_versions.verified_denial_08.GameCore import SQUARES, RAYS

NAMES = ('material', 'largest', 'combines', 'captures', 'best_capture',
         'capture_coverage', 'stacks', 'safe_largest', 'bonus_access',
         'tempo', 'tempo_capture')
KNOTS = (10, 23, 36)


def phase_mix(stones):
    if stones <= KNOTS[0]: return (1.0, 0.0, 0.0)
    if stones < KNOTS[1]:
        t = (stones-KNOTS[0])/(KNOTS[1]-KNOTS[0])
        return (1-t, t, 0.0)
    t = min(1.0, (stones-KNOTS[1])/(KNOTS[2]-KNOTS[1]))
    return (0.0, 1-t, t)


def raw_features(pos):
    board = pos.board
    sides = []
    attacked = []
    for side in (1, -1):
        material = largest = combines = captures = best = stacks = 0
        targets = set()
        for i in SQUARES[side]:
            size = board[i]
            if not size: continue
            material += size; stacks += 1
            if size > largest: largest = size
            for ray in RAYS[i][:4]:
                for j in ray:
                    if board[j]:
                        combines += 1
                        break
            if size >= 2:
                for ray in RAYS[i][4:]:
                    gain = 0
                    for j in ray[:size:2]:
                        if 0 < board[j] < size:
                            gain += board[j]+1; targets.add(j)
                    if gain:
                        captures += 1
                        if gain > best: best = gain
        sides.append((material, largest, combines, captures, best,
                      sum(board[j] for j in targets), stacks))
        attacked.append(targets)
    light, dark = sides
    values = [a-b for a,b in zip(light,dark)]
    safe_light = max((board[i] for i in SQUARES[1] if i not in attacked[1]), default=0)
    safe_dark = max((board[i] for i in SQUARES[-1] if i not in attacked[0]), default=0)
    lm, dm = light[2]+light[3], dark[2]+dark[3]
    access = (light[1]*(lm+1)-dark[1]*(dm+1))/(lm+dm+2)
    values.extend((safe_light-safe_dark, access, pos.turn, pos.turn*(light[4]+dark[4])))
    return tuple(values)


def vector(pos):
    raw = raw_features(pos)
    return tuple(weight*x for weight in phase_mix(sum(pos.board)) for x in raw)


def baseline_future(pos):
    f = raw_features(pos)
    return .12*f[0]+.08*f[1]+.02*(f[2]+f[3])+.14*f[4]


def canonical_board(board):
    """Four color-preserving transforms, used offline only."""
    return min(tuple(board[i] for i in order) for order in TRANSFORMS)


TRANSFORMS = (
    tuple(range(36)), tuple(reversed(range(36))),
    tuple((i%6)*6+i//6 for i in range(36)),
    tuple((5-i%6)*6+5-i//6 for i in range(36)),
)
