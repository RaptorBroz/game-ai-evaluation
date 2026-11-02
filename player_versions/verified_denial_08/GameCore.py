"""Compact, pure rules used by search; differential-tested against GameRules.py.

Square ownership: Light=+1, Dark=-1. Scores are Light minus Dark.
The tournament itself always advances states with the professor's rules.
"""
from typing import NamedTuple

DIRECTIONS = ('NW', 'NE', 'SW', 'SE', 'N', 'E', 'S', 'W')
DELTAS = ((-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (0,1), (1,0), (0,-1))
COLORS = tuple(1 if (i//6+i%6)%2 else -1 for i in range(36))
SQUARES = {s: tuple(i for i in range(36) if COLORS[i] == s) for s in (-1,1)}

def _rays(i):
    result = []
    for dr, dc in DELTAS:
        r, c = i//6+dr, i%6+dc
        ray = []
        while 0 <= r < 6 and 0 <= c < 6:
            ray.append(r*6+c)
            r, c = r+dr, c+dc
        result.append(tuple(ray))
    return tuple(result)

RAYS = tuple(_rays(i) for i in range(36))

class Position(NamedTuple):
    board: tuple
    turn: int
    diff: int

class Edge(NamedTuple):
    move: int
    child: Position
    gain: int

def from_state(state):
    return Position(tuple(state['Board']), 1 if state['Turn']=='Light' else -1,
                    state['LightCapture']-state['DarkCapture'])

def decode(move):
    square, direction = divmod(move, 8)
    return {'Row': square//6, 'Col': square%6, 'Direction': DIRECTIONS[direction]}

def encode(move):
    return (move['Row']*6+move['Col'])*8+DIRECTIONS.index(move['Direction'])

def generate(pos):
    """Generate each legal successor once, in the reference engine's order."""
    board, side, diff = pos
    result = []
    for i in SQUARES[side]:
        size = board[i]
        if not size:
            continue
        rays = RAYS[i]
        for d in range(4):
            for target in rays[d]:
                if board[target]:
                    b = list(board)
                    b[target] += size
                    b[i] = 0
                    result.append(Edge(i*8+d, Position(tuple(b), -side, diff), 0))
                    break
        if size < 2:
            continue
        for d in range(4,8):
            path = rays[d][:size]
            # Enemy squares occur at offsets 0, 2, 4. Zero is never capturable.
            gain = sum(board[j]+1 for j in path[::2] if 0 < board[j] < size)
            if not gain:
                continue
            b = list(board)
            b[i] = size-len(path)
            for offset, j in enumerate(path):
                b[j] = 0 if offset%2 == 0 and 0 < board[j] < size else board[j]+1
            result.append(Edge(i*8+d, Position(tuple(b), -side, diff+side*gain), gain))
    return result

def terminal_diff(pos):
    """Call only when the side to move has no legal moves. Bonus exactly once."""
    previous = -pos.turn
    bonus = max(pos.board[i] for i in SQUARES[previous])
    return pos.diff+previous*bonus

def potential(pos):
    """Strictly decreases on every legal move; proves games cannot repeat."""
    return 6*sum(pos.board)+sum(n>0 for n in pos.board)

def features(pos):
    """Cheap board features, in Light-minus-Dark orientation.

    Threat is the best immediately available capture, not a guaranteed gain.
    Mobility counts legal directions (as the engine does), including combines.
    """
    board = pos.board
    material = largest = mobility = threats = 0
    for side in (1,-1):
        total = biggest = moves = threat = 0
        for i in SQUARES[side]:
            size = board[i]
            if not size:
                continue
            total += size
            biggest = max(biggest, size)
            for ray in RAYS[i][:4]:
                for j in ray:
                    if board[j]:
                        moves += 1
                        break
            if size >= 2:
                for ray in RAYS[i][4:]:
                    gain = sum(board[j]+1 for j in ray[:size:2] if 0 < board[j] < size)
                    if gain:
                        moves += 1
                        threat = max(threat, gain)
        material += side*total
        largest += side*biggest
        mobility += side*moves
        threats += side*threat
    return {'material': material, 'largest': largest, 'mobility': mobility, 'threat': threats}
