"""Phase-6 E16 (filler validation) and E17 (WP-ELR disagreement audit): samples and blind sheets
(docs/phase6_prereg.md, 2026-11-23). No generation, no scoring.

E16  100 filler spans of the E14 length-matched control (constructible sources only), stratified:
       home_own   40  span sits in the HOME article's block, prose from the home article
       other_own  30  span sits in another trial's block, prose from that trial's article
       borrowed   30  span contains prose borrowed from another trial of the same source
     at most one span per source inside a stratum; seed "e16-sample".
     Deterministic checks on ALL filler spans: target position (filler vs E13 long source), lexical
     similarity to the gold evidence span (token Jaccard, ROUGE-L recall), statistical-marker regex.
E17  150 E13 truncation-free chains, Multi (long) cells, budgets 100 / 200, both models:
       WP0_ELR1  80  (20 per model x budget; Blind first, Aware only to fill a short stratum)
       WP0_ELR0  36  ( 9 per model x budget, Blind)
       WP1_ELR1  34  (9 / 9 / 8 / 8, Blind)
     seed "e17-sample".

Blind sheets (what a rater sees): data/audit/e16_sheet_{A,B}.jsonl, data/audit/e17_sheet_{A,B}.jsonl
(same items, different shuffled order per rater; no gold label, no automatic verdict, no condition).
Keys (never shown to raters): data/audit/e16_key.csv, data/audit/e17_key.csv
Full-coverage deterministic checks: results/e16/e16_filler_spans_all.csv
"""
import json
import random
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_longsource import ntok, render  # noqa: E402
from build_phase4_materials import filler_sentences  # noqa: E402
from run_phase4 import load_samples  # noqa: E402

AUD = Path("data/audit"); AUD.mkdir(parents=True, exist_ok=True)
Path("results/e16").mkdir(parents=True, exist_ok=True)
Path("results/e17").mkdir(parents=True, exist_ok=True)
STAT_RE = re.compile(r"\bp\s*[<>=≤]\s*0?\.\d|\b95\s*%\s*(CI|confidence)|\b(OR|HR|RR)\s*[=:]?\s*\d|\bsignificant(ly)?\b|\bvs\.?\b.*\d", re.I)
W = re.compile(r"[a-z0-9]+")


def toks(x):
    return W.findall(x.lower())


def lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b, 1):
            cur.append(prev[j - 1] + 1 if x == y else max(prev[j], cur[-1]))
        prev = cur
    return prev[-1]


def e16(samples):
    F = [json.loads(l) for l in open("data/longsource/longfiller_v1.jsonl")]
    L = {json.loads(l)["sample_id"]: json.loads(l) for l in open("data/longsource/longsource_v1.jsonl")}
    own = {}
    rows = []
    for f in F:
        if not f["constructible"]:
            continue
        s = samples[f["sample_id"]]; tgt = s["target"]["evidence"]; t = s["target"]
        mat_f, mat_l = render(f["blocks"]), render(L[f["sample_id"]]["blocks"])
        # target position = reference tokens before the target's own slot (first home-block span equal to the target);
        # string search is not used: the target sentence can recur inside other spans of the E13 long source
        def before(blocks):
            for bi_, b_ in enumerate(blocks):
                for si_, sp_ in enumerate(b_["spans"]):
                    if b_["sample_id"] == f["sample_id"] and sp_ == tgt:
                        return (bi_, si_), ntok(render(blocks[:bi_] + [{**b_, "spans": b_["spans"][:si_]}]))
        (slot_f, pos_f), (slot_l, pos_l) = before(f["blocks"]), before(L[f["sample_id"]]["blocks"])
        assert slot_f == slot_l
        dup_f, dup_l = mat_f.count(tgt), mat_l.count(tgt)
        tt = toks(tgt)
        for bi, (b, bl) in enumerate(zip(f["blocks"], L[f["sample_id"]]["blocks"])):
            if b["pmcid"] not in own:
                own[b["pmcid"]] = sorted(set(filler_sentences(b["pmcid"])), key=len, reverse=True)
            for si, (sp, orig) in enumerate(zip(b["spans"], bl["spans"])):
                if b["sample_id"] == f["sample_id"] and sp == tgt:
                    continue
                rest = sp
                for sent in own[b["pmcid"]]:
                    if sent in rest:
                        rest = rest.replace(sent, "", 1)
                borrowed = bool(rest.strip())
                home = b["sample_id"] == f["sample_id"]
                st = toks(sp)
                rows.append(dict(sample_id=f["sample_id"], block=bi, span=si, block_pmcid=b["pmcid"], home_block=home,
                                 borrowed=borrowed, stratum="borrowed" if borrowed else ("home_own" if home else "other_own"),
                                 n_tokens=ntok(sp), replaced_tokens=ntok(orig),
                                 jaccard_gold=len(set(st) & set(tt)) / max(1, len(set(st) | set(tt))),
                                 rougeL_recall_gold=lcs(tt, st) / max(1, len(tt)),
                                 stat_marker=bool(STAT_RE.search(sp)),
                                 target_tokens_before_filler=pos_f, target_tokens_before_long=pos_l,
                                 target_occurrences_filler=dup_f, target_occurrences_long=dup_l,
                                 intervention=t["intervention"], comparator=t["comparator"], outcome=t["outcome"],
                                 gold_label=t["gold_label"], gold_evidence=tgt, text=sp))
    A = pd.DataFrame(rows)
    A.drop(columns=["gold_evidence", "text"]).round(4).to_csv("results/e16/e16_filler_spans_all.csv", index=False)
    rng = random.Random("e16-sample")
    pick = []
    for stratum, n in (("home_own", 40), ("other_own", 30), ("borrowed", 30)):
        g = A[A.stratum == stratum]
        sids = sorted(g.sample_id.unique()); rng.shuffle(sids)
        for sid in sids[:n]:
            idx = sorted(g[g.sample_id == sid].index)
            pick.append(rng.choice(idx))
        assert len(sids) >= n, (stratum, len(sids))
    S = A.loc[pick].reset_index(drop=True)
    S.insert(0, "item_id", [f"F{i + 1:03d}" for i in range(len(S))])
    S.to_csv(AUD / "e16_key.csv", index=False)
    for rater in "AB":
        order = list(range(len(S))); random.Random(f"e16-order-{rater}").shuffle(order)
        with open(AUD / f"e16_sheet_{rater}.jsonl", "w") as fh:
            for i in order:
                r = S.loc[i]
                fh.write(json.dumps(dict(item_id=r.item_id, intervention=r.intervention, comparator=r.comparator, outcome=r.outcome,
                                         target_evidence_sentence=r.gold_evidence, passage=r.text), ensure_ascii=False) + "\n")
    print(f"E16: {len(A)} filler spans in {A.sample_id.nunique()} sources; strata {A.stratum.value_counts().to_dict()}; "
          f"sampled {S.stratum.value_counts().to_dict()}")
    src = A.groupby("sample_id").first()
    dpos = src.target_tokens_before_filler - src.target_tokens_before_long
    print(f"     target slot identical in all sources; tokens before target, filler - long: mean {dpos.mean():+.1f}, max |diff| {dpos.abs().max():.0f}")
    print(f"     target sentence occurs more than once: filler {(src.target_occurrences_filler > 1).mean():.1%}, long {(src.target_occurrences_long > 1).mean():.1%} of sources")
    src[["target_tokens_before_filler", "target_tokens_before_long", "target_occurrences_filler", "target_occurrences_long"]].to_csv("results/e16/e16_target_position.csv")
    print(f"     stat-marker regex hits: {A.stat_marker.mean():.2%} of spans; ROUGE-L recall vs gold >= 0.5: {(A.rougeL_recall_gold >= 0.5).mean():.2%}; "
          f"Jaccard >= 0.3: {(A.jaccard_gold >= 0.3).mean():.2%}")


def e17():
    KEY = ["sample_id", "mode", "cond", "budget"]
    items = []
    for m in ("qwen3-8b", "qwen3-14b"):
        chains = {(r["sample_id"], r["mode"], r["cond"], r["budget"]): r for r in map(json.loads, open(f"results/ratio_notrunc_{m}.jsonl"))}
        f = pd.read_csv(f"results/ratio_notrunc_{m}_ok_scored.csv")[KEY + ["gold_label", "claim_label", "supported"]].rename(
            columns={"claim_label": "ans_eval", "supported": "elr"})
        w = pd.read_csv(f"results/ratio_notrunc_{m}_mem_scored.csv")[KEY + ["claim_label", "supported"]].rename(
            columns={"claim_label": "mem_eval", "supported": "wp"})
        d = f.merge(w, on=KEY, validate="1:1")
        d = d[(d.cond == "long") & d.budget.isin([100, 200]) & d["mode"].isin(["aware", "blind"])]
        d["cls"] = ["WP%d_ELR%d" % (int(a), int(b)) for a, b in zip(d.wp, d.elr)]
        d["model"] = m
        for b in (100, 200):
            for cls, n in (("WP0_ELR1", 20), ("WP0_ELR0", 9), ("WP1_ELR1", 9 if b == 100 else 8)):
                rng = random.Random(f"e17-sample-{m}-{b}-{cls}")
                g = d[(d.budget == b) & (d.cls == cls)]
                blind = sorted(g[g["mode"] == "blind"].index); rng.shuffle(blind)
                aware = sorted(g[g["mode"] == "aware"].index); rng.shuffle(aware)
                take = (blind + (aware if cls == "WP0_ELR1" else []))[:n]
                assert len(take) == n, (m, b, cls, len(take))
                for i in take:
                    r = d.loc[i]; c = chains[(r.sample_id, r["mode"], r.cond, r.budget)]
                    items.append(dict(model=m, sample_id=r.sample_id, mode=r["mode"], cond="multi", budget=int(r.budget), cls=cls,
                                      gold_label=r.gold_label, mem_eval=r.mem_eval, ans_eval=r.ans_eval,
                                      intervention=c["intervention"], comparator=c["comparator"], outcome=c["outcome"],
                                      memory=c["memory"], answer=c["text"]))
    S = pd.DataFrame(items)
    S.insert(0, "item_id", [f"D{i + 1:03d}" for i in range(len(S))])
    S.to_csv(AUD / "e17_key.csv", index=False)
    for rater in "AB":
        order = list(range(len(S))); random.Random(f"e17-order-{rater}").shuffle(order)
        with open(AUD / f"e17_sheet_{rater}.jsonl", "w") as fh:
            for i in order:
                r = S.loc[i]
                fh.write(json.dumps(dict(item_id=r.item_id, intervention=r.intervention, comparator=r.comparator, outcome=r.outcome,
                                         memory_notes=r.memory, final_answer=r.answer), ensure_ascii=False) + "\n")
    print(f"E17: {len(S)} chains; " + str(S.groupby(["cls", "mode"]).size().to_dict()))


if __name__ == "__main__":
    samples = {s["sample_id"]: s for s in load_samples()}
    e16(samples); e17()
