"""Canonical evaluator results (2026-09-29).

Problem: cache/classifier_scoring.jsonl holds duplicate keys with conflicting verdicts
(two scoring processes wrote the same item), so re-reading the cache can change a verdict
that a committed results/*_scored.csv already reports. Decision (user, 2026-09-29): the
COMMITTED verdict files are the canonical record; nothing is re-scored.

What this script does (read-only with respect to the evaluator; no model call):
  1. joins every committed verdict row with the text the evaluator judged and rebuilds its
     cache keys;
  2. keeps every committed verdict EXACTLY as committed (no number changes). The evaluator is
     stochastic, so the same item (ICO + text) was sometimes judged differently in two rows
     or files; those rows stay as committed and are flagged, never harmonised;
  3. selects, for every key, ONE cached evaluator response — the one that reproduces the
     committed verdict of the first row that refers to it (files in priority order: the
     paper's primary grid first, then by mtime) — and writes a duplicate-free cache;
  4. writes results/canonical_results.csv (one row per committed verdict row, with
     `cache_verdict` / `cache_reproducible`), results/canonical_manifest.json (evaluator
     spec, file hashes, counts, evaluator test-retest agreement) and
     results/canonical_cache_mismatch.csv (rows the duplicate-free cache would judge
     differently if they were ever re-scored — they must NOT be re-scored).

  --apply   additionally installs the duplicate-free cache as cache/classifier_scoring.jsonl
            (the old cache is kept as cache/classifier_scoring.pre_canonical_20260929.jsonl).
            No results/*_scored.csv file is modified.
"""
import argparse
import glob
import hashlib
import json
import os
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from supdrift.classifier import PROMPT_VERSION, SYSTEM_PROMPT, parse_response  # noqa: E402
from supdrift.llm import MODELS as LLM_MODELS, full_cache_key  # noqa: E402

OLD = "cache/classifier_scoring.jsonl"
KEEP = "cache/classifier_scoring.pre_canonical_20260929.jsonl"
NEW = "cache/classifier_canonical.jsonl"
PRIMARY = ["extra_hard_", "extra_hardmem_"]          # the paper's main enforced-25 grid
DESIGN = ["sample_id", "prompt_id", "mode", "cond", "icoset", "budget", "depth", "step", "seed", "run", "role",
          "kind", "fmt", "K", "stage", "position"]


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def source_of(csv):
    stem = csv[:-4]
    for p in (stem.replace("_final_scored", "_ok") + ".jsonl", stem.replace("_final_scored", "") + ".jsonl",
              stem.replace("_scored", "") + ".jsonl", stem.replace("results/scored_", "results/chains_") + ".jsonl",
              stem.replace("_scored_", "_chains_") + ".jsonl"):
        if p != csv and os.path.exists(p):
            return p
    return None


def keys_for(t, text):
    return [full_cache_key("qwen3-32b", {"task": "ico_classify", "v": PROMPT_VERSION, "i": t["intervention"],
                                         "c": t["comparator"], "o": t["outcome"], "t": text, "a": a}) for a in (0, 1, 2)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    src_cache = KEEP if os.path.exists(KEEP) else OLD

    ico = {}
    for l in open("data/gate2/gate2_candidates.jsonl"):
        r = json.loads(l); ico[r["sample_id"]] = r["target"]
    for l in open("data/pilot/pilot_v2.jsonl"):
        r = json.loads(l); ico[r["sample_id"]] = r

    writes = defaultdict(list)                        # key -> [(label, direction, certainty, response)]
    n_lines = 0
    for l in open(src_cache):
        n_lines += 1
        r = json.loads(l)
        p = parse_response(r["response"])
        writes[r["key"]].append((p["claim_label"], p["direction"], p["certainty"], r["response"]))
    print(f"cache {src_cache}: {n_lines} lines, {len(writes)} keys, "
          f"{sum(1 for w in writes.values() if len({x[0] for x in w}) > 1)} keys with conflicting verdicts", flush=True)

    csvs = [c for c in sorted(glob.glob("results/*scored*.csv"))]
    first_seen = {c: os.path.getmtime(c) for c in csvs}
    csvs.sort(key=lambda c: (0 if any(os.path.basename(c).startswith(p) for p in PRIMARY) else 1, first_seen[c], c))

    chosen = {}            # key -> response index kept in the canonical cache
    item = {}              # (i, c, o, text) -> (label, direction, certainty, file)
    out, changes, files = [], [], []
    stat = Counter()
    for c in csvs:
        src = source_of(c)
        df = pd.read_csv(c, low_memory=False)
        if src is None:
            print(f"  {c}: no source jsonl — skipped"); continue
        rows = [json.loads(l) for l in open(src)]
        if "error" in rows[0] or any("error" in r for r in rows[:50]):
            rows = [r for r in rows if "error" not in r]
        if len(rows) != len(df):                     # gate2 chains: scored subset = cohort articles
            keep = set(df["sample_id"])
            rows = [r for r in rows if r["sample_id"] in keep and r.get("text") is not None]
        assert len(rows) == len(df), (c, len(rows), len(df))
        if [r["sample_id"] for r in rows] != df["sample_id"].tolist():   # row order differs: align on the design
            kc = [k for k in DESIGN if k in df.columns and k in rows[0]]
            by = {tuple(r[k] for k in kc): r for r in rows}
            assert len(by) == len(rows), (c, kc)
            rows = [by[tuple(v)] for v in df[kc].itertuples(index=False, name=None)]
        has_dir = "direction" in df.columns
        new_lab, new_dir, new_cer = [], [], []
        n_changed = 0
        for r, v in zip(rows, df.itertuples(index=False)):
            t = r if "intervention" in r else ico[r["sample_id"]]
            text = r["text"]
            committed = v.claim_label
            ik = (t["intervention"], t["comparator"], t["outcome"], text)
            ks = keys_for(t, text)
            reason = ""
            if ik in item:
                lab, d, ce, owner = item[ik]
                if lab != committed:
                    reason = f"same item judged {lab} in {os.path.basename(owner)}"
            else:
                # find the cached response chain that reproduces the committed verdict
                sel, ok = {}, False
                for k in ks:
                    w = writes.get(k, [])
                    hit = [i for i, x in enumerate(w) if x[0] == committed and
                           (not has_dir or (x[1] == v.direction and x[2] == v.certainty))] or \
                          [i for i, x in enumerate(w) if x[0] == committed]
                    if hit and committed not in ("PARSE_ERROR", "EVAL_ERROR"):
                        sel[k] = hit[-1]; ok = True; break
                    pe = [i for i, x in enumerate(w) if x[0] == "PARSE_ERROR"]
                    if pe:
                        sel[k] = pe[-1]              # unparsable attempt, the evaluator moved on
                    elif w:
                        break                        # a valid different verdict sits here: not reproducible
                if ok:
                    k = [k for k in ks if k in sel][-1]
                    x = writes[k][sel[k]]
                    lab, d, ce = x[0], x[1], x[2]
                    stat["reproduced"] += 1
                else:                                # fall back to what the cache resolves to (last write)
                    sel, lab, d, ce = {}, "MISSING", "MISSING", "MISSING"
                    for k in ks:
                        w = writes.get(k, [])
                        if not w:
                            continue
                        sel[k] = len(w) - 1
                        lab, d, ce = w[-1][0], w[-1][1], w[-1][2]
                        if lab != "PARSE_ERROR":
                            break
                    if lab == "MISSING":             # never cached: keep the committed verdict, flag it
                        lab, d, ce = committed, getattr(v, "direction", ""), getattr(v, "certainty", "")
                        stat["not_in_cache"] += 1
                        reason = "not in cache (committed verdict kept)"
                    else:
                        stat["not_reproducible"] += 1
                        reason = f"cache cannot reproduce {committed}; resolves to {lab}"
                for k, i in sel.items():
                    chosen.setdefault(k, i)
                item[ik] = (lab, d, ce, c)
            gold = v.gold_label
            rec = {"file": os.path.basename(c), "model_file": os.path.basename(src)}
            rec.update({k: getattr(v, k) for k in DESIGN if hasattr(v, k)})
            rec.update(intervention=t["intervention"], comparator=t["comparator"], outcome=t["outcome"],
                       text_sha16=hashlib.sha256(text.encode()).hexdigest()[:16], gold_label=gold,
                       direction=getattr(v, "direction", ""), certainty=getattr(v, "certainty", ""),
                       claim_label=committed, supported=(committed == gold),
                       cache_verdict=lab, cache_reproducible=(lab == committed), note=reason)
            out.append(rec)
            if lab != committed:
                n_changed += 1
                changes.append(rec)
            new_lab.append(lab); new_dir.append(d); new_cer.append(ce)
        files.append({"file": c, "source": src, "rows": len(df), "cache_mismatch": n_changed, "sha256": sha(c)})
        stat["rows"] += len(df); stat["changed"] += n_changed
        if n_changed:
            print(f"  {os.path.basename(c)}: {n_changed} of {len(df)} rows not reproducible from the duplicate-free cache", flush=True)

    can = pd.DataFrame(out)
    can.to_csv("results/canonical_results.csv", index=False, escapechar="\\")
    pd.DataFrame(changes).to_csv("results/canonical_cache_mismatch.csv", index=False, escapechar="\\")
    n_ref = len(chosen)
    with open(NEW, "w") as f:
        for k, w in writes.items():
            i = chosen.get(k, len(w) - 1)            # keys no committed row refers to: last write, as before
            f.write(json.dumps({"key": k, "response": w[i][3]}, ensure_ascii=False) + "\n")
    dup = sum(len(w) - 1 for w in writes.values())
    dis = sum(sum(1 for a, b in zip(w, w[1:]) if a[0] != b[0]) for w in writes.values())
    man = {"created": "2026-09-29", "rule": "committed verdict files are canonical and unchanged; rows are never "
           "re-scored; new experiments append new keys to the duplicate-free cache",
           "evaluator_test_retest": {"repeated_judgments": dup, "different_verdict": dis,
                                     "agreement_pct": round(100 * (1 - dis / max(dup, 1)), 2)},
           "evaluator": {"model": LLM_MODELS["qwen3-32b"]["model"], "prompt_version": PROMPT_VERSION,
                         "system_prompt_sha256_16": hashlib.sha256(SYSTEM_PROMPT.encode()).hexdigest()[:16],
                         "decoding": "attempts 0-1 thinking (temperature 0.6, top_p 0.95, seeds 42/43, max 2500/3500, "
                                     "repetition_penalty 1.05), attempt 2 no-think (max 600)"},
           "source_cache": {"path": src_cache, "lines": n_lines, "keys": len(writes), "sha256": sha(src_cache)},
           "canonical_cache": {"path": "cache/classifier_scoring.jsonl" if args.apply else NEW, "keys": len(writes),
                               "keys_pinned_by_committed_rows": n_ref, "sha256": sha(NEW)},
           "counts": dict(stat), "priority": [os.path.basename(c) for c in csvs], "files": files}
    json.dump(man, open("results/canonical_manifest.json", "w"), indent=1)
    print(f"evaluator test-retest: {dup} repeated judgments, {dis} with a different verdict "
          f"({100 * (1 - dis / max(dup, 1)):.1f}% agreement)")
    print(f"rows {stat['rows']}, items pinned from cache {stat['reproduced']}, rows the cache would judge differently {stat['changed']} "
          f"(not reproducible {stat['not_reproducible']}, not in cache {stat['not_in_cache']}); "
          f"canonical cache: {len(writes)} keys, {n_ref} pinned")
    if args.apply:
        if not os.path.exists(KEEP):
            os.rename(OLD, KEEP)
        shutil.copy2(NEW, OLD)
        print(f"installed {OLD}; previous cache kept as {KEEP}")


if __name__ == "__main__":
    main()
