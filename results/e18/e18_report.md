# E18 One-pass vs recursive memory — analysis

Qwen3-14B, B = 200, truncation-free, judge-based outcomes. One-pass = the chain stopped after the first write (M1);
four-pass = the existing chains (M4). `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples).
G = Blind − Aware; LENGTH = G_Filler − G_Single; COMPETITION = G_Multi − G_Filler; RECURSION = four-pass − one-pass.
First write identical to the four-pass chain's (same first-write attempt count): 100.0% of 3348 chains. Failed one-pass chains: 0.

## original prompts (primary)

M1 length (model tokens): aware/single 99, aware/filler 151, aware/multi 142, blind/single 81, blind/filler 170, blind/multi 175.

### ELR  (n = 279)

| Memory | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |
|---|---|---|---|---|---|---|
| one-pass (M1) | 94.6 | 95.0 | 93.5 | 76.7 | 92.1 | 73.5 |
| four-pass (M4) | 93.5 | 96.4 | 92.8 | 72.4 | 92.8 | 71.7 |
| RECURSION (M4 − M1) | -1.1 [-3.2, +1.1] | +1.4 [-0.7, +3.6] | -0.7 [-3.2, +1.8] | -4.3 [-8.2, -0.7]* | +0.7 [-1.8, +3.2] | -1.8 [-4.7, +0.7] |

| Estimand | One-pass | Four-pass | RECURSION |
|---|---|---|---|
| G_single | +0.4 [-2.5, +3.2] | +2.9 [+0.0, +6.1] | +2.5 [-0.7, +5.7] |
| G_filler | -16.8 [-22.2, -11.5]* | -20.4 [-25.8, -15.4]* | -3.6 [-8.2, +1.1] |
| G_multi | -18.6 [-24.0, -13.3]* | -21.1 [-26.5, -15.8]* | -2.5 [-6.5, +1.4] |
| LENGTH | **-17.2 [-23.3, -11.1]*** | -23.3 [-29.7, -17.2]* | -6.1 [-12.2, -0.4]* |
| COMPETITION | -1.8 [-8.2, +4.7] | -0.7 [-7.2, +6.1] | +1.1 [-4.7, +6.8] |
| TOTAL | -19.0 [-24.7, -13.3]* | -24.0 [-30.1, -18.3]* | -5.0 [-10.0, +0.0] |

### WP  (n = 279)

| Memory | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |
|---|---|---|---|---|---|---|
| one-pass (M1) | 93.9 | 95.0 | 91.8 | 57.7 | 92.5 | 62.7 |
| four-pass (M4) | 92.5 | 94.6 | 90.7 | 52.7 | 91.8 | 60.6 |
| RECURSION (M4 − M1) | -1.4 [-3.6, +0.7] | -0.4 [-2.9, +2.2] | -1.1 [-3.9, +1.8] | -5.0 [-9.0, -1.4]* | -0.7 [-3.2, +1.8] | -2.2 [-5.7, +1.4] |

| Estimand | One-pass | Four-pass | RECURSION |
|---|---|---|---|
| G_single | +1.1 [-2.2, +4.7] | +2.2 [-1.1, +5.7] | +1.1 [-1.8, +3.9] |
| G_filler | -34.1 [-39.8, -28.0]* | -38.0 [-44.1, -31.5]* | -3.9 [-8.6, +0.4] |
| G_multi | -29.7 [-36.2, -23.3]* | -31.2 [-37.3, -25.4]* | -1.4 [-5.7, +2.9] |
| LENGTH | **-35.1 [-41.9, -28.3]*** | -40.1 [-47.0, -33.3]* | -5.0 [-10.4, +0.4] |
| COMPETITION | +4.3 [-3.2, +11.8] | +6.8 [-0.7, +14.3] | +2.5 [-3.9, +9.0] |
| TOTAL | -30.8 [-38.0, -24.0]* | -33.3 [-40.1, -26.9]* | -2.5 [-7.9, +3.2] |

## matched prompt (secondary)

M1 length (model tokens): aware/single 103, aware/filler 155, aware/multi 154, blind/single 83, blind/filler 170, blind/multi 173.

### ELR  (n = 279)

| Memory | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |
|---|---|---|---|---|---|---|
| one-pass (M1) | 96.1 | 96.1 | 90.3 | 73.1 | 92.8 | 68.8 |
| four-pass (M4) | 96.1 | 96.8 | 90.3 | 72.8 | 94.6 | 70.3 |
| RECURSION (M4 − M1) | +0.0 [-1.8, +1.8] | +0.7 [-1.4, +2.9] | +0.0 [-2.9, +2.9] | -0.4 [-3.9, +2.9] | +1.8 [-0.4, +4.3] | +1.4 [-1.4, +4.3] |

| Estimand | One-pass | Four-pass | RECURSION |
|---|---|---|---|
| G_single | +0.0 [-2.9, +3.2] | +0.7 [-1.8, +3.6] | +0.7 [-2.2, +3.2] |
| G_filler | -17.2 [-23.3, -11.1]* | -17.6 [-23.3, -12.2]* | -0.4 [-5.0, +3.9] |
| G_multi | -24.0 [-29.7, -18.6]* | -24.4 [-30.1, -18.6]* | -0.4 [-3.9, +3.2] |
| LENGTH | **-17.2 [-24.0, -10.4]*** | -18.3 [-24.4, -12.5]* | -1.1 [-6.8, +3.9] |
| COMPETITION | -6.8 [-13.3, +0.0] | -6.8 [-13.3, +0.0] | +0.0 [-5.4, +5.7] |
| TOTAL | -24.0 [-30.5, -17.6]* | -25.1 [-31.2, -18.6]* | -1.1 [-5.7, +3.9] |

### WP  (n = 279)

| Memory | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |
|---|---|---|---|---|---|---|
| one-pass (M1) | 95.0 | 93.9 | 87.5 | 59.5 | 92.1 | 64.5 |
| four-pass (M4) | 95.0 | 92.8 | 87.1 | 54.8 | 93.5 | 60.6 |
| RECURSION (M4 − M1) | +0.0 [-2.2, +2.2] | -1.1 [-3.9, +1.8] | -0.4 [-2.5, +1.8] | -4.7 [-8.2, -1.1]* | +1.4 [-0.7, +3.9] | -3.9 [-7.5, -0.7]* |

| Estimand | One-pass | Four-pass | RECURSION |
|---|---|---|---|
| G_single | -1.1 [-4.3, +2.2] | -2.2 [-5.7, +1.4] | -1.1 [-4.7, +2.9] |
| G_filler | -28.0 [-33.7, -22.2]* | -32.3 [-38.4, -26.5]* | -4.3 [-8.6, +0.0] |
| G_multi | -27.6 [-33.3, -21.9]* | -33.0 [-39.1, -27.2]* | -5.4 [-9.7, -1.1]* |
| LENGTH | **-26.9 [-33.3, -20.4]*** | -30.1 [-37.3, -22.9]* | -3.2 [-9.0, +2.5] |
| COMPETITION | +0.4 [-7.5, +8.2] | -0.7 [-8.6, +7.2] | -1.1 [-7.2, +5.0] |
| TOTAL | -26.5 [-33.0, -20.1]* | -30.8 [-37.6, -24.0]* | -4.3 [-10.0, +1.1] |

## Reading rule (pre-registered; primary = ELR, original prompts)

- original, ELR: LENGTH one-pass -17.2 [-23.3, -11.1], four-pass -23.3; RECURSION -6.1 [-12.2, -0.4] -> **present after one write; aggravated by rewriting**
- original, WP: LENGTH one-pass -35.1 [-41.9, -28.3], four-pass -40.1; RECURSION -5.0 [-10.4, +0.4] -> **present after one write; not aggravated by rewriting**
- matched, ELR: LENGTH one-pass -17.2 [-24.0, -10.4], four-pass -18.3; RECURSION -1.1 [-6.8, +3.9] -> **present after one write; not aggravated by rewriting**
- matched, WP: LENGTH one-pass -26.9 [-33.3, -20.4], four-pass -30.1; RECURSION -3.2 [-9.0, +2.5] -> **present after one write; not aggravated by rewriting**

## Summary and reading (2026-11-23)

- The loss is present after ONE write. Original prompts: ELR LENGTH −17.2 [−23.3, −11.1] after the first write
  against −23.3 after four; WP LENGTH −35.1 [−41.9, −28.3] against −40.1. Matched prompt: ELR −17.2, WP −26.9.
  About three quarters (ELR, original prompts) to more than nine tenths (matched) of the four-pass loss already
  exists in M1; it is not a product of recursive rewriting.
- Rewrites 2–4 add a small further loss, concentrated in the Blind/Filler cell: ELR −4.3 [−8.2, −0.7] and WP −5.0
  [−9.0, −1.4] (original prompts); WP −4.7 [−8.2, −1.1] in Blind/Filler and −3.9 [−7.5, −0.7] in Blind/Multi
  (matched). By the pre-registered rule the ELR LENGTH component is "aggravated by rewriting" under the original
  prompts (RECURSION −6.1 [−12.2, −0.4]) but not under the matched prompt (−1.1 [−6.8, +3.9]) and not for WP; the
  aggravation is therefore small and not robust to the prompt.
- Aware cells and all Single cells do not change between M1 and M4 (all |change| ≤ 1.8, CIs include 0).
- COMPETITION is n.s. after one write as after four.
- The first write is the same generation as in the four-pass chains (100 % identical first-write attempt counts; 59
  and 73 chains have M1 = M4 verbatim and reuse the cached answer). 0 failed chains, 0 dirty verdicts.
- Limits: one model (Qwen3-14B), one budget (200); one-pass = first step of the same chain, so M1 (170–175 tokens
  for Blind long inputs) is slightly longer than M4 (153–170).
