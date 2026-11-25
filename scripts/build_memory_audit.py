"""④ Human memory-warrant audit package (pre-registered: docs/phase4_prereg.md).

360 last-intermediate memories from the enforced-25 grid (the Figure 2b data):
3 models x 4 cells (aware/blind x single/multi) x 30 articles, stratified
10/10/10 by gold label, seed 42. Annotators see the target ICO, the annotated
gold evidence span, and the memory — never the condition, model, or the
evaluator's verdict. Items are shuffled.

Outputs (data/annotation/):
  memory_audit_task.csv   item_id, intervention, comparator, outcome,
                          gold_evidence, memory, + 4 empty answer columns
  memory_audit_key.csv    item_id, sample_id, model, mode, icoset, gold_label,
                          evaluator claim_label / direction / certainty /
                          supported (== complete warrant preserved)
  memory_audit_README.md  the annotation instructions
"""
import json
import random
from pathlib import Path

import pandas as pd

MODELS = ["qwen3-8b", "qwen3-14b", "gpt-5.4-mini"]
CELLS = [("aware", "single"), ("aware", "multi"), ("blind", "single"), ("blind", "multi")]
PER_LABEL = 10
LABELS = ["INCREASE", "NO_DIFFERENCE", "DECREASE"]
OUT = Path("data/annotation")

README = """# Memory-warrant audit — instructions

Each item shows a clinical research question (intervention vs comparator on an
outcome), the ANNOTATED EVIDENCE from the source article that answers it, and a
short MEMORY note written by an automated pipeline. Judge the memory ONLY
against the annotated evidence; do not use outside knowledge.

Answer four yes/no questions per item (write Y or N):

1. target_present   — Does the memory mention this specific outcome for this
                       comparison at all (even vaguely)?
2. direction_correct — If it does, is the direction of effect stated in the memory
                       the same as in the evidence (increase / decrease / no
                       difference)? Write N if the memory states a different
                       direction OR states no direction at all. N/A if not present.
3. stat_status_preserved — Is the statistical status preserved: a significant
                       finding is still presented as a real effect, a
                       non-significant / "no difference" finding is NOT presented
                       as an effect (and vice versa)? N/A if not present.
4. complete_warrant — Would a reader of the memory ALONE reach the same
                       conclusion about this question as a reader of the
                       evidence, with the same confidence? This is Y only if 1-3
                       are all Y and nothing in the memory contradicts or hedges
                       the finding away.

Optional free-text `note`.
Items are in random order; the pipeline condition is hidden on purpose.
"""


def main():
    rng = random.Random(42)
    samples = {json.loads(l)["sample_id"]: json.loads(l) for l in open("data/gate2/gate2_v1.jsonl")}
    items = []
    for m in MODELS:
        mem = {(r["sample_id"], r["mode"], r["icoset"]): r["text"]
               for r in map(json.loads, open(f"results/extra_hardmem_{m}.jsonl"))}
        sc = pd.read_csv(f"results/extra_hardmem_{m}_scored.csv")
        sc = sc[sc["step"] == 4].set_index(["sample_id", "mode", "icoset"])
        for mode, ico in CELLS:
            for lab in LABELS:
                sids = sorted(s for s, x in samples.items() if x["target"]["gold_label"] == lab)
                rng.shuffle(sids)
                for sid in sids[:PER_LABEL]:
                    t = samples[sid]["target"]
                    v = sc.loc[(sid, mode, ico)]
                    items.append({
                        "sample_id": sid, "model": m, "mode": mode, "icoset": ico,
                        "gold_label": lab, "intervention": t["intervention"],
                        "comparator": t["comparator"], "outcome": t["outcome"],
                        "gold_evidence": t["evidence"], "memory": mem[(sid, mode, ico)],
                        "eval_claim_label": v["claim_label"], "eval_direction": v["direction"],
                        "eval_certainty": v["certainty"], "eval_complete_warrant": bool(v["supported"]),
                    })
    rng.shuffle(items)
    for i, it in enumerate(items, 1):
        it["item_id"] = f"MA-{i:03d}"
    df = pd.DataFrame(items)
    task_cols = ["item_id", "intervention", "comparator", "outcome", "gold_evidence", "memory"]
    task = df[task_cols].copy()
    for c in ["target_present", "direction_correct", "stat_status_preserved", "complete_warrant", "note"]:
        task[c] = ""
    OUT.mkdir(exist_ok=True)
    task.to_csv(OUT / "memory_audit_task.csv", index=False)
    key_cols = ["item_id", "sample_id", "model", "mode", "icoset", "gold_label",
                "eval_claim_label", "eval_direction", "eval_certainty", "eval_complete_warrant"]
    df[key_cols].to_csv(OUT / "memory_audit_key.csv", index=False)
    (OUT / "memory_audit_README.md").write_text(README)
    print(f"memory audit: {len(df)} items -> {OUT}/memory_audit_task.csv (+key, README)")
    print(df.groupby(["model", "mode", "icoset"]).size().unstack([1, 2]))
    print("evaluator complete-warrant rate in the audit sample:",
          f"{df['eval_complete_warrant'].mean():.1%}")


if __name__ == "__main__":
    main()
