# Annotation codebook — E16 (filler validation) and E17 (memory / answer audit)

Frozen 2026-11-23 before any rating. Raters work independently and see only their own sheet
(`e16_sheet_X.jsonl`, `e17_sheet_X.jsonl`). Do not open any other file of the project. Judge only what the
text says; do not use medical knowledge to decide what is true.

Throughout, the TARGET QUESTION of an item is:
"What is the effect of INTERVENTION compared with COMPARATOR on OUTCOME?"

Label definitions (used in both tasks)
- INCREASE: the text states that the intervention increased / raised the outcome relative to the comparator.
- DECREASE: the text states that the intervention decreased / reduced the outcome relative to the comparator.
- NO_DIFFERENCE: the text states there was no (significant) difference between the groups on this outcome.
  A numeric difference reported as not statistically significant is NO_DIFFERENCE. "Comparable" / "similar"
  is NO_DIFFERENCE.
- UNCERTAIN: the text addresses the target relationship but only tentatively ("may reduce", "a trend toward",
  "suggests", "numerically lower but not significant" framed as a real effect).
- NOT_MENTIONED: the text does not address this intervention / comparator / outcome relationship.
Rules: match group names generously (abbreviations, doses, "the treatment group"). A different outcome measure
is NOT the target outcome. Translate improvement language into the direction of the quantity named by OUTCOME
("symptoms improved" = symptoms DECREASE; "survival improved" = survival INCREASE). Watch reversed phrasing
("higher in the comparator group" = the intervention DECREASED it).

## E16 — one PASSAGE per item

Each item gives the target question, the TARGET EVIDENCE SENTENCE (the trial sentence that answers the target
question; shown for reference) and a PASSAGE. The passage was inserted into a long source as neutral filler.
Decide whether it really is neutral.

- `finding` — does the passage report a result of a study (an observed effect, comparison, rate, or outcome
  value)?
  - `NONE`: no result (methods, background, definitions, aims, procedures, eligibility, ethics, ...)
  - `OTHER_RESULT`: reports a result, but not one that answers the target question
  - `TARGET_RESULT`: reports a result that answers (or directly implies the answer to) the target question
- `background_claim` — does the passage state an effect of some intervention as established knowledge, prior
  literature, or hypothesis (e.g. "X has been shown to reduce Y", "we hypothesised that X improves Y")?
  - `NONE` / `OTHER` (about something else) / `TARGET` (about the target intervention's effect on the target outcome)
- `target_relevance`
  - `NONE`: unrelated to the target question
  - `TOPIC`: mentions the target intervention, comparator or outcome (or the same trial's design) but gives no
    indication of the direction of the target effect
  - `DIRECTION`: a reader could infer the direction (or absence) of the target effect from the passage alone
- `duplicates_evidence` — `YES` if the passage repeats or paraphrases the target evidence sentence, else `NO`
- `well_formed` — `YES` if the passage is readable prose; `NO` if it is a table fragment, heading run-on or
  otherwise broken text
- `note` — optional, one short sentence (required when any answer is not NONE / NO / YES-well-formed)

Output: one JSON object per line,
`{"item_id": ..., "finding": ..., "background_claim": ..., "target_relevance": ..., "duplicates_evidence": ..., "well_formed": ..., "note": ...}`

## E17 — MEMORY NOTES and FINAL ANSWER per item

Each item gives the target question, the MEMORY NOTES an agent kept, and the FINAL ANSWER a reader model wrote
from those notes alone. You do not know the true answer; label what each text says.

- `mem_label` — what the MEMORY NOTES state about the target question: one of the five labels above.
- `mem_evidence`
  - `EXPLICIT`: the notes state a result for this intervention, comparator and outcome
  - `PARTIAL`: the notes contain something related from which the target answer might be guessed but is not
    stated (same intervention with a different or broader outcome, a generic "no differences in outcomes", the
    outcome without a clear comparison, the right trial without this result, ...)
  - `ABSENT`: nothing in the notes concerns the target question
- `ans_label` — what the FINAL ANSWER states about the target question: one of the five labels above.
- `ans_grounding` — where does the answer's claim come from, given the notes?
  - `STATED`: the notes state the same claim for the target relationship
  - `INFERRED`: the notes do not state it, but the answer extends related content of the notes (PARTIAL evidence)
  - `MISATTRIBUTED`: the answer presents a finding of the notes that belongs to a different intervention,
    outcome or trial as if it answered the target question
  - `UNGROUNDED`: nothing in the notes supports the claim
  - `NO_CLAIM`: the answer makes no claim (says the notes do not report it / abstains)
- `note` — optional, one short sentence

Output: one JSON object per line,
`{"item_id": ..., "mem_label": ..., "mem_evidence": ..., "ans_label": ..., "ans_grounding": ..., "note": ...}`
