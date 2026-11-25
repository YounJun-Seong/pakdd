"""Phase-6 E18 one-pass vs recursive memory, analysis (docs/phase6_prereg.md, 2026-11-23).
One-pass (results/e18_qwen3-14b*) against the four-pass chains of the same articles: original prompts = committed
E13 / E14 verdicts, matched prompt = E15 verdicts. Outputs: results/e18/e18_summary.csv, results/e18/e18_report.md"""
import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_e15 import comps, load_matched, wide  # noqa: E402
from analyze_lencontrol import fmt, load as load_orig  # noqa: E402
from analyze_phase4 import boot_ci  # noqa: E402

M, B = "qwen3-14b", 200
KEY = ["family", "sample_id", "mode", "cond", "budget"]
CONDS = ("single", "filler", "multi")


def main():
    Path("results/e18").mkdir(parents=True, exist_ok=True)
    raw = pd.DataFrame([{k: r.get(k) for k in KEY + ["failed", "memory_tokens", "attempts"]} for r in map(json.loads, open(f"results/e18_{M}.jsonl"))])
    for stem, col in (("ok", "elr"), ("mem", "wp")):
        s = pd.read_csv(f"results/e18_{M}_{stem}_scored.csv")
        assert not s.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any()
        raw = raw.merge(s[KEY + ["supported"]].rename(columns={"supported": col}), on=KEY, how="left", validate="1:1")
    raw[["elr", "wp"]] = raw[["elr", "wp"]].astype(float)
    four = {"original": load_orig(M)[0], "matched": load_matched(M, B)}
    # the first write must be the same generation as in the four-pass chain: compare first-write attempt counts
    chk = []
    for fam, path, mm, cc in (("original", f"results/ratio_notrunc_{M}.jsonl", {"aware": "aware", "blind": "blind"}, {"single": "single", "long": "multi"}),
                              ("original", f"results/lenctrl_{M}.jsonl", {"aware": "aware", "blind": "blind"}, {"filler": "filler"}),
                              ("matched", f"results/e15b{B}_{M}.jsonl", {"aware_m": "aware", "blind_m": "blind"}, {c: c for c in CONDS})):
        for r in map(json.loads, open(path)):
            if r["budget"] == B and r["mode"] in mm and r["cond"] in cc and not r["failed"]:
                chk.append(dict(family=fam, sample_id=r["sample_id"], mode=mm[r["mode"]], cond=cc[r["cond"]], a4=r["attempts"][0]))
    c = raw.merge(pd.DataFrame(chk), on=["family", "sample_id", "mode", "cond"], how="inner")
    same = (c.attempts.map(lambda a: a[0]) == c.a4).mean()
    md = ["# E18 One-pass vs recursive memory — analysis", "",
          f"Qwen3-14B, B = {B}, truncation-free, judge-based outcomes. One-pass = the chain stopped after the first write (M1);",
          "four-pass = the existing chains (M4). `*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples).",
          "G = Blind − Aware; LENGTH = G_Filler − G_Single; COMPETITION = G_Multi − G_Filler; RECURSION = four-pass − one-pass.",
          f"First write identical to the four-pass chain's (same first-write attempt count): {same:.1%} of {len(c)} chains. "
          f"Failed one-pass chains: {int(raw.failed.sum())}.", ""]
    rows = []
    for fam in ("original", "matched"):
        d1 = raw[raw.family == fam]
        mem1 = d1.groupby(["mode", "cond"]).memory_tokens.mean()
        md += [f"## {fam} prompt{'s (primary)' if fam == 'original' else ' (secondary)'}", "",
               "M1 length (model tokens): " + ", ".join(f"{mo}/{c_} {mem1[(mo, c_)]:.0f}" for mo in ("aware", "blind") for c_ in CONDS) + ".", ""]
        for col, lbl in (("elr", "ELR"), ("wp", "WP")):
            p1, p4 = wide(d1, col, B), wide(four[fam], col, B)
            idx = p1.index.intersection(p4.index); p1, p4 = p1.loc[idx], p4.loc[idx]
            md += [f"### {lbl}  (n = {len(idx)})", "", "| Memory | A-Single | B-Single | A-Filler | B-Filler | A-Multi | B-Multi |", "|---|---|---|---|---|---|---|"]
            for name, p in (("one-pass (M1)", p1), ("four-pass (M4)", p4)):
                md.append(f"| {name} | " + " | ".join(f"{p[(mo, c_)].mean():.1f}" for c_ in CONDS for mo in ("aware", "blind")) + " |")
            md.append("| RECURSION (M4 − M1) | " + " | ".join(fmt(boot_ci((p4[(mo, c_)] - p1[(mo, c_)]).to_numpy())) for c_ in CONDS for mo in ("aware", "blind")) + " |")
            for c_ in CONDS:
                for mo in ("aware", "blind"):
                    t = boot_ci((p4[(mo, c_)] - p1[(mo, c_)]).to_numpy())
                    rows.append(dict(family=fam, outcome=lbl, estimand=f"cell_{mo}_{c_}", n=len(idx), one_pass=p1[(mo, c_)].mean(), four_pass=p4[(mo, c_)].mean(),
                                     recursion=t[0], recursion_lo=t[1], recursion_hi=t[2]))
            c1, c4 = comps(p1), comps(p4)
            md += ["", "| Estimand | One-pass | Four-pass | RECURSION |", "|---|---|---|---|"]
            for k in c1:
                a, o, dl = boot_ci(c1[k].to_numpy()), boot_ci(c4[k].to_numpy()), boot_ci((c4[k] - c1[k]).to_numpy())
                md.append(f"| {k} | {'**' + fmt(a) + '**' if k == 'LENGTH' else fmt(a)} | {fmt(o)} | {fmt(dl)} |")
                rows.append(dict(family=fam, outcome=lbl, estimand=k, n=len(idx), one_pass=a[0], one_pass_lo=a[1], one_pass_hi=a[2],
                                 four_pass=o[0], four_pass_lo=o[1], four_pass_hi=o[2], recursion=dl[0], recursion_lo=dl[1], recursion_hi=dl[2]))
                if k == "LENGTH":
                    v = ("present after one write" if a[2] < 0 else "not present after one write") + ("; aggravated by rewriting" if dl[2] < 0 else "; not aggravated by rewriting")
                    md += [] if False else []
                    rows[-1]["verdict"] = v
            md.append("")
    S = pd.DataFrame(rows)
    S.round(3).to_csv("results/e18/e18_summary.csv", index=False)
    md += ["## Reading rule (pre-registered; primary = ELR, original prompts)", ""]
    for r in S[S.estimand == "LENGTH"].itertuples():
        md.append(f"- {r.family}, {r.outcome}: LENGTH one-pass {r.one_pass:+.1f} [{r.one_pass_lo:+.1f}, {r.one_pass_hi:+.1f}], four-pass {r.four_pass:+.1f}; "
                  f"RECURSION {r.recursion:+.1f} [{r.recursion_lo:+.1f}, {r.recursion_hi:+.1f}] -> **{r.verdict}**")
    Path("results/e18/e18_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
