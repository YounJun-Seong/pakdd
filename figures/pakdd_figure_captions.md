# PAKDD 2027 figure captions (draft, 2026-11-22)

**Fig. 1.** Experimental framework. Factorial design: Query Awareness (Aware / Blind) × Evidence Competition
(Single / Multi). The source M0 is rewritten four times (M1–M4) under the same memory budget B in both
conditions. In Query-Aware the writer receives the future query q at every step; in Query-Blind q is revealed
only to the final reader. Outcomes: ELR on the final answer, WP on the memory M4, and the Blindness ×
Competition difference-in-differences (DiD).

**Fig. 2.** Compression-dependent evidence loss. Blindness × Competition DiD for ELR (final answer) and WP
(memory) with a fixed ~1,000-token source and memory budgets of 100 / 200 / 400 / 800 tokens.
Truncation-free generation; judge-based evaluation with the frozen evaluator; n = 294 articles per cell.
Error bars: 95 % CIs from a paired article bootstrap (2,000 resamples). Hollow markers: CI includes 0.

**Fig. 3.** Effect of the budget-enforcement protocol on the judge-based ELR DiD. Enforced cap: one generation
per write, cut at B tokens when it exceeds the budget. Truncation-free: regenerated until it fits, never cut.
Both protocols use the same source, memory budgets, and factorial conditions. Error bars: 95 % CIs
(paired article bootstrap, 2,000 resamples). Hollow markers: CI includes 0.

Note for the text (not a caption): the two protocols differ in more than the cut (the truncation-free writer
is re-prompted with a stricter length instruction), so the gap between the two lines is not a causal estimate
of hard truncation alone. Paired contrasts (enforced − truncation-free DiD) are in
`results/ratio_protocol_contrast.csv`.

## E19 figure (2026-11-23) — `pakdd_fig_e19_length_position.(pdf|png)`
Blind − Aware gap (percentage points) against source length with the target position held fixed (Qwen3-14B,
200-token budget, truncation-free, original prompts, n = 243 articles). Left: ELR; right: WP. The target finding
is the only finding in the source; the rest is non-finding prose. Error bars: 95 % paired article bootstrap CI;
filled markers: CI excludes 0. The gap is absent at 200 tokens at every position and grows with length; at
1,000 tokens it is about three times larger when the target is in the middle or at the end than when it is first.
