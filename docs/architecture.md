# Architecture and source map

```text
valid engine state
    -> immutable board / side / capture difference
    -> legal actions and verified-outcome lookup
    -> iterative deepening alpha-beta guidance
    -> bounded exact outcome search when eligible
    -> completed result or legal fallback
    -> public move dictionary
```

`SeanGilbert.py` privately loads embedded frozen modules and exposes the instructor's two-function interface. The readable source tree is preserved for review. It is not a separately improved player.

| Component | Source | Purpose |
|---|---|---|
| State and legal moves | `GameCore.py` | Immutable positions; combines, sowing captures, last-mover bonus |
| Search foundation | `challengers/LeafV5.py`, `EfficientPreventionPlayer.py` | Negamax, alpha-beta bounds, iterative deepening, move ordering, deferred child construction |
| Final heuristic | `VerifiedDenial08.py`, `BonusDenialPlayer.py` | Learned future-margin estimate plus bounded reply-restriction pressure |
| Learned estimate | `LearnedPhasePlayer.py`, `PhaseFeatures.py`, `LearnedPhaseWeights.py` | 11 features across three interpolated phases, 33 frozen coefficients |
| Exact outcomes | `SelectiveEndgamePlayer.py`, `KnowledgeTracePlayer06.py` | Bounded proof cache, terminal solver, backward-trace knowledge |
| Loss-mode repair | `ProofTransitionRacePlayer.py` | Recheck newly proved losses and clear incompatible cached values |

The final `VerifiedDenial08.Guidance.evaluate` overrides inherited race-evaluation methods. It calls `denial_margin`, which starts with the learned phase estimate and adds termination pressure in smaller positions. The inherited class names do not mean the final player uses every earlier evaluation path.

The heuristic is an estimate. Verified book entries and completed exact searches represent win/loss facts at applicable score differences. A proved outcome is not an exact final-score margin. Transposition keys include board, turn, and score difference; the heuristic's future-margin cache omits capture difference because that term is added separately.

The solver normally considers positions with at most 20 stones and 24 legal moves. Time-limited unknown parents remain unknown, while completed descendant proofs can survive in bounded caches. The agent uses a single process at runtime. Parallel search experiments were not adopted in this frozen submission.
