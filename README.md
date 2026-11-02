# Game AI and evaluation

A Python player for a custom 6 × 6 adversarial board game, with selected evidence from its development and submission checks. The main audience is someone reviewing how I compared candidates, investigated failures, and selected a player under a 30-second turn limit.

**Status:** frozen portfolio release. The course instructor approved sharing this project on GitHub. Class tournament results are unconfirmed.

The player combines negamax/alpha-beta search, iterative deepening, a learned linear board evaluation, a reply-restriction heuristic, bounded caches, and verified win/loss knowledge. It runs sequentially using Python's standard library. AI tools helped develop it; no LLM runs during a move.

## Try it

Use Python 3.12. No packages, credentials, network connection, or instructor files are needed for these examples. From this folder:

```sh
python3 demo.py
python3 -m evaluation.summarize
python3 -m unittest discover -s tests -v
```

`demo.py` uses one saved state and a zero-second search budget to demonstrate a legal fallback without playing a game. It prints the public name, returned move, and whether the input was preserved. The tests check packaging integrity, API behavior, several rule edge cases, proof-cache behavior, and historical-data validation. They do not run competitive games or measure strength.

`SeanGilbert.py` is the byte-identical standalone submission player. `name()` returns `Sean Gilbert`; `getMove(state)` accepts a dictionary containing `Board`, `Turn`, `LightCapture`, and `DarkCapture`. `Board` has 36 counts in row-major order; `Turn` is `Light` or `Dark`. The function returns `Row`, `Col`, and `Direction`. It expects a valid, nonterminal state and raises `ValueError` when no move exists. Malformed-input validation is not a promise of the frozen API.

The normal requested allowance is 29 seconds, with an inherited internal deadline of 28.42 seconds. A real engine should enforce its own external timeout. Performance on other machines is unverified. The instructor's engine and rules files are not included.

## Evidence

The final internal selection record was **14 wins and 8 losses across seven boards against three internal opponents**: 6–4 against each of the two other finalists and 2–0 against the learned predecessor. These were selected internal comparisons with an outcome-informed schedule. They do not estimate a general win probability or establish a class tournament result.

Historical packaging checks recorded **12 paired equal-work checks**, **two short-clock engine games covering 53 legal plies**, and five default public calls. The largest observed default-call time was 28.420289 seconds on the tested machine. These are bounded compatibility checks, not a new strength result.

The included summarizer recomputes the internal selection counts from 22 curated historical result rows. It does not rerun games, reproduce the entire experiment, or independently certify the original move logs. See [evaluation methods and limits](docs/evaluation.md).

## My contribution and AI assistance

I set the goals and constraints, directed experiments and loss investigations, questioned promising changes, and selected the final submission. ChatGPT and Codex helped explain the supplied rules, propose algorithms, write and revise Python, build evaluation tools, and analyze failures. This was AI-assisted development; I am not claiming that I manually wrote every line or independently mastered every algorithm.

The game rules, engine, and assignment were supplied by my instructor. The new portfolio wrapper, summarizer, tests, and documentation were prepared with Codex in November 2026. [Attribution and rights](ATTRIBUTION.md) separates the supplied material from this work.

## Read the implementation

- [Architecture and source map](docs/architecture.md)
- [Two decisions and the evidence behind them](docs/decisions.md)
- [Evaluation methods and limits](docs/evaluation.md)
- [Walkthrough questions](docs/walkthrough.md)

The readable `player_versions/verified_denial_08/` tree preserves the 21 runtime files used to assemble the standalone player, including 19 embedded source modules. Old module docstrings describe their individual development stages; the active final evaluation is in `VerifiedDenial08.py` and `BonusDenialPlayer.py`.
