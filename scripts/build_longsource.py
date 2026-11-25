"""E13 compression-ratio experiment (docs/phase6_prereg.md, 2026-11-22): build the ~1,000-token
source for every gate2_v1 article.

The home article's Multi material is kept exactly as in the main experiment (spans_original);
real annotated evidence spans from OTHER cohort articles are added, article by article, until the
rendered material is 950-1,050 tokens (o200k_base, the fixed reference tokenizer of Phase 4).
Nothing is padded or paraphrased: every added span is a distinct annotated finding of a different
trial, with its own gold label.

Output data/longsource/longsource_v1.jsonl, one row per article:
  sample_id, pmcid, blocks [{pmcid, sample_id, spans}], home_index, n_tokens_ref,
  n_spans, n_findings, candidates [{sample_id, pmcid, prompt_id, outcome, gold_label}],
  target_span_start (relative token position of the target evidence in the material)
"""
import json
import random
import sys
from pathlib import Path

import tiktoken

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_phase4 import load_samples, spans_original  # noqa: E402

ENC = tiktoken.get_encoding("o200k_base")
LO, HI = 950, 1050
OUT = Path("data/longsource/longsource_v1.jsonl")


def ntok(t):
    return len(ENC.encode(t, disallowed_special=()))


def render(blocks):
    return "\n\n".join(f"Excerpts from source article [PMC{b['pmcid']}]:\n" + "\n".join(f"- {s}" for s in b["spans"])
                       for b in blocks)


def norm(x):
    return " ".join(x.lower().split())


def unique_spans(s):
    seen, out = set(), []
    for sp in spans_original(s, "multi"):
        if sp not in seen:
            seen.add(sp); out.append(sp)
    return out


def build(s, samples):
    t = s["target"]
    home = {"pmcid": s["pmcid"], "sample_id": s["sample_id"], "spans": spans_original(s, "multi")}
    blocks = [home]
    others = [o for o in samples if o["sample_id"] != s["sample_id"]]
    random.Random(f"{s['sample_id']}-long").shuffle(others)
    home_ev = set(home["spans"])
    for o in others:
        total = ntok(render(blocks))
        if total >= LO:
            break
        # a filler trial must not answer the home question: no shared intervention + outcome, no shared span
        if any(norm(p["intervention"]) == norm(t["intervention"]) and norm(p["outcome"]) == norm(t["outcome"])
               for p in [o["target"]] + o["distractors"]):
            continue
        blk = {"pmcid": o["pmcid"], "sample_id": o["sample_id"], "spans": []}
        for sp in unique_spans(o):
            if sp in home_ev:
                continue
            trial = blocks + [{**blk, "spans": blk["spans"] + [sp]}]
            if ntok(render(trial)) <= HI:
                blk["spans"].append(sp)
        if blk["spans"]:
            blocks.append(blk)
    random.Random(f"{s['sample_id']}-long-order").shuffle(blocks)
    material = render(blocks)
    by_id = {o["sample_id"]: o for o in samples}
    cands = []
    for b in blocks:
        o = by_id[b["sample_id"]]
        for p in [o["target"]] + o["distractors"]:
            if p["evidence"] in b["spans"]:
                cands.append({"sample_id": o["sample_id"], "pmcid": o["pmcid"], "prompt_id": p["prompt_id"],
                              "outcome": p["outcome"], "gold_label": p["gold_label"]})
    pos = material.find(t["evidence"])
    assert pos >= 0
    return {"sample_id": s["sample_id"], "pmcid": s["pmcid"], "blocks": blocks,
            "home_index": next(i for i, b in enumerate(blocks) if b["sample_id"] == s["sample_id"]),
            "n_tokens_ref": ntok(material), "n_spans": sum(len(b["spans"]) for b in blocks),
            "n_findings": len(cands), "candidates": cands,
            "target_span_start": ntok(material[:pos]) / ntok(material)}


def main():
    samples = load_samples()
    rows = [build(s, samples) for s in samples]
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    import numpy as np
    n = np.array([r["n_tokens_ref"] for r in rows])
    print(f"wrote {OUT}: {len(rows)} sources; tokens mean {n.mean():.0f} min {n.min()} max {n.max()}; "
          f"outside [{LO},{HI}]: {int(((n < LO) | (n > HI)).sum())}")
    for k in ("n_spans", "n_findings"):
        v = np.array([r[k] for r in rows]); print(f"  {k}: mean {v.mean():.1f} min {v.min()} max {v.max()}")
    v = np.array([len(r["blocks"]) for r in rows]); print(f"  trials per source: mean {v.mean():.1f} min {v.min()} max {v.max()}")
    v = np.array([r["target_span_start"] for r in rows])
    print(f"  target position (relative start): mean {v.mean():.2f}; thirds {np.histogram(v, bins=[0, 1/3, 2/3, 1.01])[0].tolist()}")


if __name__ == "__main__":
    main()
