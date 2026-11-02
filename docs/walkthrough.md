# Walkthrough questions

These are preparation tasks, not evidence of a passed independent assessment.

1. In `GameCore.generate`, trace a three-stone Light stack moving east across an empty enemy square, a friendly square, and a smaller enemy stack. Explain why only the positive smaller enemy stack is captured. Compare your prediction with the edge-case test.
2. In `SelectiveEndgamePlayer.proof_key`, explain why board and side alone cannot identify a win/loss fact. Change only `diff` in two positions and inspect the keys.
3. In `EfficientPreventionPlayer._search`, trace the negation of child values and the alpha/beta window. Explain when a stored result is exact versus an upper or lower bound.
4. In `LearnedPhasePlayer.future_margin` and `BonusDenialPlayer.denial_margin`, separate the learned estimate from the hand-set denial term. Explain why neither produces a proof certificate.
5. In `ProofTransitionRacePlayer.Guidance.choose`, explain why a newly proved loss changes value semantics and requires a table reset. Connect this to keeping practical choices among losing moves.
6. Run the historical summarizer. Explain why 14/22 is a count in this selected sample, why color pairing helps, and why exposure and outcome-informed scheduling still limit the conclusion.

For each explanation, identify the actual source and state what you would inspect if the behavior failed. Independent fluency in these areas has not yet been assessed.
