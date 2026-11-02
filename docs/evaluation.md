# Evaluation methods and limits

## Historical selection

Version: frozen VerifiedDenial08, packaged as `sean-gilbert-denial08-2026-10-17`.

Environment recorded in the selection plan: Python 3.12.14, macOS 27.0.1, arm64, 18 logical CPUs reported. Games ran one at a time. The external move limit was 30 seconds; the player's requested allowance was 29 seconds. No timing guarantee is made for other systems.

`evidence/selection_games.json` contains only the 22 completed eligible selection results involving this player. Rows retain game IDs, board IDs, colors, winner, final scores, plies, and source-file SHA-256 values. They were derived from the original result records, excluding supplementary withdrawn-player games. The summarizer checks duplicate IDs, result consistency, and balanced colors within opponent/board pairs before calculating counts.

| Slice | Wins | Losses |
|---|---:|---:|
| Earlier included games | 8 | 6 |
| Random-board extension | 6 | 2 |
| Combined selected sample | 14 | 8 |
| Light | 7 | 4 |
| Dark | 7 | 4 |

The player faced three internal opponents on seven distinct boards. The random extension used different boards for different opponent pairs, matched within each pair and played in both colors. The schedule was outcome-informed; prior exposure was possible. No confidence interval or general strength probability is inferred. Class tournament results remain unconfirmed.

The compact dataset supports recomputing these reported totals. It does not include all original logs, other players, the instructor engine, training corpus, or original harness. Consequently this package does not reproduce the full historical tournament or training procedure.

## Historical packaging validation

The October 17 packaging report records 12 paired equal-work calls using six early/middle/late states across both colors with cold and warm caches. Moves and non-time statistics matched the frozen reference. Two short-clock instructor-engine integration games completed 53 legal plies; five default public calls passed, with maximum observed elapsed time 28.420289 seconds. These are bounded validation results, not a playing-strength assessment.

The standalone player hash and readable runtime hashes are in `evidence/frozen_manifest.json`. A compact transcription of the original validation totals is in `evidence/historical_packaging.json`. The original files remain preserved separately.

## Current portfolio checks

The new unit tests exercise a zero-budget public fallback on saved states, unchanged inputs, terminal-state behavior, capture edge cases, the last-mover bonus, proof-cache invariants, and invalid historical-data handling. Identity checks confirm the standalone player and readable source have not diverged. `evidence/portfolio_checks.json` records the actual local run and its environment.

No new competitive games, strength benchmarks, default full-clock calls, or model training were run for this portfolio package. CI is configured to repeat only these unit checks and historical aggregation on Python 3.12. The workflow has not run on GitHub.
