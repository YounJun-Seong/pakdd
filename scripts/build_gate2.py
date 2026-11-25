"""Build the Gate 2 set: multi-ICO articles for question-blind compression.

Design (agreed 2026-09-04): each sample is an ARTICLE with one TARGET prompt
(ICO + unanimous gold label + its own evidence span) and 2-4 DISTRACTOR
prompts from the same article. Conditions built downstream:
  question-aware vs question-blind  x  single-ICO vs multi-ICO material.

Selection:
- train-split articles with >=3 usable unanimous prompts (same span filters as
  pilot v2); prefer articles that contain a NO_DIFFERENCE prompt
- target label stratified 100/100/100 across INCREASE/NO_DIFFERENCE/DECREASE
- targets drawn only from prompts whose span later passes the frozen-evaluator
  grounding check (scripts/verify_gate2_targets.py) — build emits candidates,
  verification prunes.

Output: data/gate2/gate2_candidates.jsonl
"""
import html
import json
import re
from pathlib import Path

import pandas as pd

SEED = 42
N_PER_LABEL = 120  # candidates per label; verification prunes to ~100
MAX_DISTRACTORS = 4

LABEL_MAP = {
    "significantly increased": "INCREASE",
    "no significant difference": "NO_DIFFERENCE",
    "significantly decreased": "DECREASE",
}

RAW = Path("data/raw")
OUT = Path("data/gate2")
OUT.mkdir(parents=True, exist_ok=True)


def prose_ratio(t: str) -> float:
    return sum(c.isalpha() or c in " ,.;:()%-" for c in t) / len(t) if t else 0.0


def main():
    ann = pd.read_csv(RAW / "annotations_merged.csv")
    prompts = pd.read_csv(RAW / "prompts_merged.csv")
    train_ids = set(int(x) for x in open(RAW / "train_article_ids.txt").read().split())

    ann = ann[(ann["Valid Label"] == True) & (ann["Valid Reasoning"] == True)]  # noqa: E712
    ann = ann[ann["PMCID"].isin(train_ids)]
    ann["Label"] = ann["Label"].str.strip().str.lower()
    ann = ann[ann["Label"].isin(LABEL_MAP)]
    ann["evidence"] = ann["Annotations"].fillna("").astype(str).map(
        lambda s: re.sub(r"\s+", " ", html.unescape(html.unescape(s))).strip())
    ann = ann[ann["evidence"].str.len().between(100, 1200)]
    ann = ann[ann["evidence"].map(prose_ratio) >= 0.60]
    agree = ann.groupby("PromptID")["Label"].nunique()
    ann = ann[ann["PromptID"].isin(agree[agree == 1].index)]
    per_prompt = (ann.sort_values("evidence", key=lambda s: s.str.len(), ascending=False)
                  .drop_duplicates("PromptID"))
    m = per_prompt.merge(prompts, on=["PromptID", "PMCID"])
    for c in ["Intervention", "Comparator", "Outcome"]:
        m[c] = m[c].fillna("").astype(str).str.strip()
    m = m[(m["Intervention"] != "") & (m["Comparator"] != "") & (m["Outcome"] != "")]
    m["gold_label"] = m["Label"].map(LABEL_MAP)

    counts = m.groupby("PMCID")["PromptID"].nunique()
    eligible = set(counts[counts >= 3].index)
    m = m[m["PMCID"].isin(eligible)]
    print(f"eligible articles: {len(eligible)}, prompts: {len(m)}")

    # one candidate per article: pick target stratified by label, prefer
    # articles containing a NO_DIFFERENCE prompt (negative results in the mix)
    rng_shuffled = m.sample(frac=1.0, random_state=SEED)
    by_art = {pmcid: g for pmcid, g in rng_shuffled.groupby("PMCID")}
    art_order = (rng_shuffled.drop_duplicates("PMCID")
                 .assign(has_nd=lambda d: d["PMCID"].map(
                     m[m["gold_label"] == "NO_DIFFERENCE"].groupby("PMCID").size()).notna())
                 .sort_values("has_nd", ascending=False)["PMCID"].tolist())

    picked, used = [], {"INCREASE": 0, "NO_DIFFERENCE": 0, "DECREASE": 0}
    for pmcid in art_order:
        g = by_art[pmcid]
        # choose the target whose label bucket is least filled
        g = g.assign(fill=g["gold_label"].map(used)).sort_values("fill")
        t = g.iloc[0]
        if used[t["gold_label"]] >= N_PER_LABEL:
            continue
        distractors = g[g["PromptID"] != t["PromptID"]].head(MAX_DISTRACTORS)
        if len(distractors) < 2:
            continue
        used[t["gold_label"]] += 1
        picked.append({
            "sample_id": f"G2-{len(picked):04d}",
            "pmcid": int(pmcid),
            "target": {
                "prompt_id": int(t["PromptID"]),
                "intervention": t["Intervention"], "comparator": t["Comparator"],
                "outcome": t["Outcome"], "evidence": t["evidence"],
                "gold_label": t["gold_label"],
            },
            "distractors": [
                {"prompt_id": int(r["PromptID"]),
                 "intervention": r["Intervention"], "comparator": r["Comparator"],
                 "outcome": r["Outcome"], "evidence": r["evidence"],
                 "gold_label": r["gold_label"]}
                for _, r in distractors.iterrows()
            ],
        })
        if all(v >= N_PER_LABEL for v in used.values()):
            break

    with open(OUT / "gate2_candidates.jsonl", "w") as f:
        for rec in picked:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"candidates: {len(picked)} articles; target labels: {used}")
    nd_present = sum(any(d["gold_label"] == "NO_DIFFERENCE" for d in r["distractors"])
                     or r["target"]["gold_label"] == "NO_DIFFERENCE" for r in picked)
    print(f"articles containing a NO_DIFFERENCE prompt: {nd_present}")
    n_span_tokens = pd.Series([
        (len(r["target"]["evidence"]) + sum(len(d["evidence"]) for d in r["distractors"])) / 4
        for r in picked])
    print(f"approx multi-ICO material tokens: mean={n_span_tokens.mean():.0f}, "
          f"p90={n_span_tokens.quantile(0.9):.0f}")


if __name__ == "__main__":
    main()
