"""Experimental v1.2: v5 guidance, bounded win/loss proof, v5 fallback.

No evaluation changes, opening database, heuristic proof labels, or promotion.
At <=20 stones and <=24 legal moves: 10% of the clock for v5 guidance,
up to 50% for a terminal-outcome solver, then remaining time for v5 if unknown.
Completed proofs survive turns in two bounded generations. A proof of loss
does not replace v5's choice among losing moves. All phases share one deadline.
"""
from dataclasses import replace
import time
import player_versions.verified_denial_08.challengers.LeafV5 as v5
from player_versions.verified_denial_08.GameCore import from_state, generate, decode, encode, terminal_diff

Config = v5.Config
VERSION = 'selective-endgame-v12-experimental'
PROOF_ENTRIES = 100000
NORMAL_ENTRIES = 50000
WIN_BIT = 512
NO_MOVE = 511


def proof_key(pos):
    # Capture score is essential for win/loss facts, unlike exact remaining swing.
    return bytes(pos.board)+bytes((int(pos.turn==1), pos.diff+36))


def unpack(record):
    move = record & 511
    return bool(record & WIN_BIT), None if move == NO_MOVE else move


class ProofTimeout(Exception):
    pass


class ProofCache:
    """Two generations; no hash-only matches and no unbounded third table."""
    def __init__(self, capacity=PROOF_ENTRIES):
        if capacity < 2: raise ValueError('Proof capacity must be at least two')
        self.half = capacity//2
        self.new = {}; self.old = {}; self.rotations = 0

    def get(self, key):
        record = self.new.get(key)
        return self.old.get(key) if record is None else record

    def put(self, key, won, move):
        record = (WIN_BIT if won else 0) | (NO_MOVE if move is None else move)
        existing = self.get(key)
        if existing is not None:
            assert unpack(existing)[0] == won, 'Contradictory proof'
            return
        if len(self.new) >= self.half:
            self.old = self.new; self.new = {}; self.rotations += 1
        self.new[key] = record

    def __len__(self):
        return len(self.new)+len(self.old)


class OutcomeSolver:
    def __init__(self, cache, guidance=None):
        self.cache = cache; self.guidance = guidance if guidance is not None else {}
        self.stats = dict(nodes=0, hits=0, terminals=0, score_bounds=0)

    def solve(self, pos, deadline, max_nodes=0, preferred=None):
        if time.perf_counter() >= deadline or (max_nodes and self.stats['nodes'] >= max_nodes):
            raise ProofTimeout
        self.stats['nodes'] += 1
        k = proof_key(pos); found = self.cache.get(k)
        if found is not None:
            self.stats['hits'] += 1
            return unpack(found)
        edges = generate(pos)
        if not edges:
            light_wins = terminal_diff(pos) >= 0
            answer = light_wins if pos.turn==1 else not light_wins
            self.stats['terminals'] += 1
            self.cache.put(k, answer, None)
            return answer, None
        # Future captures plus the one final bonus cannot exceed remaining stones.
        # This proves an outcome for EVERY continuation, including Light's tie.
        remaining = sum(pos.board)
        if pos.diff >= remaining or pos.diff < -remaining:
            light_wins = pos.diff >= remaining
            answer = light_wins if pos.turn==1 else not light_wins
            self.stats['score_bounds'] += 1
            self.cache.put(k, answer, edges[0].move)
            return answer, edges[0].move
        if preferred is None:
            entry = self.guidance.get(pos)
            preferred = entry[3] if entry else None
        edges.sort(key=lambda edge:(edge.move==preferred, edge.gain), reverse=True)
        for edge in edges:
            child_won, _ = self.solve(edge.child, deadline, max_nodes)
            if not child_won:
                # One losing opponent child proves our win. Other moves may stay unknown.
                self.cache.put(k, True, edge.move)
                return True, edge.move
        # A loss requires every legal reply to have been proved winning for the opponent.
        self.cache.put(k, False, edges[0].move)
        return False, edges[0].move


class _Guidance(v5.Searcher):
    def _start(self, seconds=None):
        # Preserve the table when resuming the same move, even if it became full.
        saved = self.table if getattr(self,'resume',False) else None
        if saved is not None: self.table = {}
        super()._start(seconds)
        if saved is not None: self.table = saved
        self.deadline = min(self.deadline, self.outer_deadline)


class Searcher:
    def __init__(self, config=None, proof_capacity=PROOF_ENTRIES):
        self.config = config or Config()
        self.normal = _Guidance(replace(self.config, tt_size=min(self.config.tt_size,NORMAL_ENTRIES)))
        self.proofs = ProofCache(proof_capacity)
        self.stats = {}

    def choose(self, state):
        started = time.perf_counter()
        budget = min(29.0, max(0,self.config.seconds))*.98
        deadline = started+budget
        pos = from_state(state); edges = generate(pos)
        if not edges: raise ValueError('getMove called on terminal state')
        eligible = sum(pos.board)<=20 and len(edges)<=24
        phases = []; move = decode(edges[0].move); value = None; proven = False
        proof_won = None; proof_attempted = False; proof_seconds = 0.0
        proof_stats = dict(nodes=0,hits=0,terminals=0,score_bounds=0)
        normal_nodes = 0; proof_move = None; proof_reused = False
        self.normal.outer_deadline = deadline
        self.normal.resume = False

        def normal_phase(stop):
            nonlocal move, value, proven, normal_nodes
            remaining = stop-time.perf_counter()
            allowance = self.config.max_nodes-normal_nodes-proof_stats['nodes'] if self.config.max_nodes else 0
            if remaining<=0 or (self.config.max_nodes and allowance<=0): return
            self.normal.outer_deadline = min(stop, deadline)
            self.normal.config = replace(self.normal.config, seconds=remaining/.98, max_nodes=allowance)
            move = self.normal.choose(state)
            phase = dict(self.normal.stats); phases.append(phase)
            normal_nodes += phase['nodes']; value = phase['value']; proven = phase['proven_outcome']
            self.normal.resume = True

        cached = self.proofs.get(proof_key(pos))
        if cached is not None:
            proof_won, proof_move = unpack(cached); proof_reused = True
        if proof_won is True:
            assert proof_move in {edge.move for edge in edges}
            move = decode(proof_move); proven = True
        elif not eligible or proof_won is False:
            normal_phase(deadline)
        else:
            normal_phase(started+budget*.1)
            if not proven and time.perf_counter()<deadline:
                solver = OutcomeSolver(self.proofs, self.normal.table)
                proof_started = time.perf_counter()
                allowance = self.config.max_nodes-normal_nodes if self.config.max_nodes else 0
                if not self.config.max_nodes or allowance>0:
                    proof_attempted = True
                    try:
                        proof_won, proof_move = solver.solve(pos, min(deadline, started+budget*.6),
                                                           allowance, encode(move))
                    except ProofTimeout:
                        pass  # Completed descendants survive; interrupted parent stays unknown.
                proof_stats = dict(solver.stats)
                proof_seconds = time.perf_counter()-proof_started
                if proof_won is True:
                    move = decode(proof_move); proven = True
                else:
                    normal_phase(deadline)
        elapsed = time.perf_counter()-started
        if proof_won is True:
            value = None  # An exact outcome is NOT an exact numeric margin.
        proven = proven or proof_won is not None
        fields = ('nodes','tt_hits','tt_cutoffs','cutoffs','eval_calls','terminal_nodes','leaf_probes','leaf_terminal_nodes')
        self.stats = {field:sum(p.get(field,0) for p in phases) for field in fields}
        self.stats['nodes'] += proof_stats['nodes']
        self.stats.update(depth=max((p['depth'] for p in phases),default=0), elapsed=elapsed,
            value=value, proven_outcome=proven, proof_outcome=proof_won, proof_kind='win_loss_only' if proof_won is not None else None,
            timed_out=any(p['timed_out'] for p in phases), nps=round(self.stats['nodes']/max(elapsed,1e-9)),
            tt_entries=len(self.normal.table), proof_entries=len(self.proofs), proof_rotations=self.proofs.rotations,
            proof_eligible=eligible, proof_attempted=proof_attempted, proof_reused=proof_reused,
            proof_seconds=proof_seconds, proof_stats=proof_stats,
            proof_root_hit=proof_reused and proof_won is True,
            iterations=phases[-1]['iterations'] if phases else [], phases=phases, pv=[move],
            normal_table_limit=self.normal.config.tt_size, proof_table_limit=self.proofs.half*2)
        return move


_player = None


def configure(seconds=29.0, max_nodes=0):
    global _player
    _player = Searcher(Config(seconds=seconds,max_nodes=max_nodes))


def name():
    return 'Selective endgame v1.2 (experimental)'


def getMove(state):
    global _player
    if _player is None: _player = Searcher()
    return _player.choose(state)


def getStats():
    return dict(_player.stats) if _player else {}
