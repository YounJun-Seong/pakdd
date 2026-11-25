"""Phase-6 E6 Contextual Evidence Robustness, analysis (docs/phase6_prereg.md, 2026-11-22).

Writes results/e6/e6_elr_summary.csv, e6_wp_summary.csv, e6_length_summary.csv and e6_analysis.md.
(e6_context_manifest.csv and e6_input_audit.csv are written by build_e6_context.py.)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_phase4 import boot_ci, did_boot  # noqa: E402

M = "qwen3-14b"
BUDGETS = [100, 200, 400]
CELLS = [("aware", "single"), ("blind", "single"), ("aware", "multi"), ("blind", "multi")]
KEY = ["sample_id", "mode", "cond", "budget"]
RES = Path("results/e6")
AGAINST = {("blind", "multi"): 1.0, ("aware", "single"): 1.0, ("aware", "multi"): 0.0, ("blind", "single"): 0.0}


def jl(p):
    return [json.loads(l) for l in open(p)]


def fmt(t):
    return f"{t[0]:+.1f} [{t[1]:+.1f}, {t[2]:+.1f}]"


def star(t):
    return "*" if (t[1] > 0 or t[2] < 0) else ""


def scored(path, keys):
    sc = pd.read_csv(path)
    assert not sc.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any(), path
    return sc[keys + ["supported"]]


def load():
    from run_phase4 import tokenizers
    enc, _ = tokenizers()
    rows = jl(f"results/e6_{M}.jsonl")
    df = pd.DataFrame([{**{k: r.get(k) for k in KEY + ["arm", "failed", "source_tokens", "memory_tokens", "mean_attempts"]},
                        "first_ok": np.mean(r["first_try_compliant"]) if r.get("first_try_compliant") else np.nan,
                        "first_write_attempts": r["attempts"][0] if r.get("attempts") else np.nan} for r in rows])
    k2 = KEY + ["arm"]
    df = df.merge(scored(f"results/e6_{M}_ok_scored.csv", k2).rename(columns={"supported": "sup_final"}), on=k2, how="left", validate="1:1")
    df = df.merge(scored(f"results/e6_{M}_mem_scored.csv", k2).rename(columns={"supported": "sup_mem"}), on=k2, how="left", validate="1:1")
    # span-only Single = the E13 truncation-free Single chains (identical cells; committed verdicts reused)
    r13 = [r for r in jl(f"results/ratio_notrunc_{M}.jsonl") if r["cond"] == "single" and r["budget"] in BUDGETS]
    s = pd.DataFrame([{**{k: r.get(k) for k in KEY + ["failed", "source_tokens", "mean_attempts"]}, "arm": "span",
                       "memory_tokens": len(enc(M, r["memory"])) if r.get("memory") else np.nan,
                       "first_ok": np.mean(r["first_try_compliant"]) if r.get("first_try_compliant") else np.nan,
                       "first_write_attempts": r["attempts"][0] if r.get("attempts") else np.nan} for r in r13])
    s = s.merge(scored(f"results/ratio_notrunc_{M}_ok_scored.csv", KEY).rename(columns={"supported": "sup_final"}), on=KEY, how="left", validate="1:1")
    s = s.merge(scored(f"results/ratio_notrunc_{M}_mem_scored.csv", KEY).rename(columns={"supported": "sup_mem"}), on=KEY, how="left", validate="1:1")
    df = pd.concat([df, s], ignore_index=True)
    for c in ("sup_final", "sup_mem"):
        df[c] = df[c].astype(float)
    return df


def per_article(d, col):
    piv = d.pivot_table(index="sample_id", columns=["mode", "cond"], values=col, aggfunc="first").dropna()
    return ((piv[("blind", "multi")] - piv[("aware", "multi")]) - (piv[("blind", "single")] - piv[("aware", "single")])) * 100


def cell_row(d, col):
    """Complete-case cells + DiD, Blind − Aware | Multi, conservative bound on all articles."""
    okid = d.groupby("sample_id").failed.sum()
    okid = okid[okid == 0].index
    cc = d[d.sample_id.isin(okid)]
    c4 = [cc[(cc["mode"] == mo) & (cc.cond == c)][col].mean() * 100 for mo, c in CELLS]
    t = did_boot(cc, col)
    am = cc[(cc["mode"] == "aware") & (cc.cond == "multi")].set_index("sample_id")[col]
    bm = cc[(cc["mode"] == "blind") & (cc.cond == "multi")].set_index("sample_id")[col]
    asg = cc[(cc["mode"] == "aware") & (cc.cond == "single")].set_index("sample_id")[col]
    bs = cc[(cc["mode"] == "blind") & (cc.cond == "single")].set_index("sample_id")[col]
    g = boot_ci((bm - am.reindex(bm.index)).to_numpy() * 100)
    gs = boot_ci((bs - asg.reindex(bs.index)).to_numpy() * 100)
    imp = d.copy()
    imp[col] = [AGAINST[(mo, c)] if f else v for mo, c, f, v in zip(imp["mode"], imp.cond, imp.failed, imp[col])]
    tb = did_boot(imp, col)
    return dict(AS=c4[0], BS=c4[1], AM=c4[2], BM=c4[3], DiD=t[0], DiD_lo=t[1], DiD_hi=t[2], n=t[3],
                BmA_multi=g[0], BmA_multi_lo=g[1], BmA_multi_hi=g[2], BmA_single=gs[0], BmA_single_lo=gs[1], BmA_single_hi=gs[2],
                bound=tb[0], bound_lo=tb[1], bound_hi=tb[2], n_all=d.sample_id.nunique()), cc


def main():
    df = load()
    audit = pd.read_csv(RES / "e6_input_audit.csv")
    a1 = audit[audit.cond == "single"].set_index("sample_id")
    subsets = {
        "all": set(a1.index),
        "single_no_annotated_contamination": set(a1.index[~a1.single_contam_annotated]),
        "single_no_contamination": set(a1.index[~(a1.single_contam_annotated | a1.single_contam_stat_sentence)]),
        "target_located": set(a1.index[a1.target_located]),
    }
    md = ["# E6 Contextual Evidence Robustness — analysis", "",
          f"Model {M}; truncation-free protocol; budgets 100 / 200 / 400; n = 294 articles per cell; frozen evaluator.",
          "Design, exclusion rules and reading rule: `docs/phase6_prereg.md` (E6, frozen before generation).",
          "This is a local-context experiment (span + up to two neighbouring sentences per side + ICO provenance); it is not a whole-document validation.",
          "`*` = 95 % CI excludes 0 (paired article bootstrap, 2,000 resamples, seed 42).", ""]

    # ---------------------------------------------------------------- input audit
    md += ["## Input audit", "", "| Condition | Candidates | Unique spans | Input tokens (14B) | Span-only tokens (14B) | Context tokens (ref) |", "|---|---|---|---|---|---|"]
    for c in ("single", "multi"):
        a = audit[audit.cond == c]
        md.append(f"| {c} | {a.n_candidates.mean():.2f} | {a.n_unique_spans.mean():.2f} | {a.input_tokens_qwen14b.mean():.0f} "
                  f"(p10–p90 {a.input_tokens_qwen14b.quantile(.1):.0f}–{a.input_tokens_qwen14b.quantile(.9):.0f}) | "
                  f"{a.span_only_tokens_qwen14b.mean():.0f} | {a.context_tokens_ref.mean():.0f} |")
    man = pd.read_csv(RES / "e6_context_manifest.csv")
    am_ = audit[audit.cond == "multi"]
    md += ["", f"- Spans located in the full text: {man.located.mean():.1%} of candidates ({man[man.role == 'target'].located.mean():.1%} of targets); "
               f"{man.in_body.mean():.1%} in a body section, the rest in the abstract. Unlocated candidates keep span + ICO provenance only.",
           f"- Single contamination (recorded, not removed): another annotated finding inside the target context {a1.single_contam_annotated.mean():.1%}; "
           f"a sentence with statistical language {a1.single_contam_stat_sentence.mean():.1%}; either {(a1.single_contam_annotated | a1.single_contam_stat_sentence).mean():.1%}.",
           f"- Multi overlap: identical evidence across candidates in {(am_.n_identical_evidence > 0).mean():.1%} of articles; a context overlapping another candidate in "
           f"{(am_.n_ctx_overlapping_candidate > 0).mean():.1%}; the target finding repeated inside a distractor context in {am_.target_repeated_in_distractor_ctx.mean():.1%}; "
           f"an unlocated candidate in {(am_.n_unlocated > 0).mean():.1%}.", ""]

    # ---------------------------------------------------------------- lengths / compliance
    L = (df.groupby(["arm", "budget", "mode", "cond"])
           .agg(n=("failed", "size"), failed_pct=("failed", lambda s: s.mean() * 100),
                first_attempt_compliance_pct=("first_ok", lambda s: s.mean() * 100),
                attempts_per_write=("mean_attempts", "mean"), first_write_attempts=("first_write_attempts", "mean"),
                source_tokens=("source_tokens", "mean"), memory_tokens=("memory_tokens", "mean"),
                memory_tokens_p90=("memory_tokens", lambda s: s.quantile(.9)), memory_tokens_max=("memory_tokens", "max"))
           .reset_index())
    L["realized_ratio_pct"] = L.memory_tokens / L.source_tokens * 100
    L.round(2).to_csv(RES / "e6_length_summary.csv", index=False)
    md += ["## Budget compliance, failures, realized memory length", "",
           "| Arm | B | Cell | Failed % | First-attempt compliance % | Attempts / write | Source tokens | Memory tokens (p90) | Realized ratio % |", "|---|---|---|---|---|---|---|---|---|"]
    for r in L.itertuples():
        md.append(f"| {r.arm} | {r.budget} | {r.mode}/{r.cond} | {r.failed_pct:.1f} | {r.first_attempt_compliance_pct:.1f} | {r.attempts_per_write:.2f} | "
                  f"{r.source_tokens:.0f} | {r.memory_tokens:.0f} ({r.memory_tokens_p90:.0f}) | {r.realized_ratio_pct:.0f} |")
    md.append("")

    # ---------------------------------------------------------------- outcomes
    verdict = {}
    for col, lbl, fname in (("sup_final", "ELR", "e6_elr_summary.csv"), ("sup_mem", "WP", "e6_wp_summary.csv")):
        out = []
        md += [f"## {lbl} — four cells and DiD (complete cases)", "",
               "| Arm | B | A-S | B-S | A-M | B-M | Blind − Aware, Single | Blind − Aware, Multi | DiD | n | Conservative bound |", "|---|---|---|---|---|---|---|---|---|---|---|"]
        pa = {}
        for arm in ("context", "span"):
            for b in BUDGETS:
                d = df[(df.arm == arm) & (df.budget == b)]
                r, cc = cell_row(d, col)
                pa[(arm, b)] = per_article(cc, col)
                out.append(dict(arm=arm, subset="all", budget=b, **r))
                t, g, gs, tb = (r["DiD"], r["DiD_lo"], r["DiD_hi"]), (r["BmA_multi"], r["BmA_multi_lo"], r["BmA_multi_hi"]), \
                    (r["BmA_single"], r["BmA_single_lo"], r["BmA_single_hi"]), (r["bound"], r["bound_lo"], r["bound_hi"])
                md.append(f"| {arm} | {b} | {r['AS']:.1f} | {r['BS']:.1f} | {r['AM']:.1f} | {r['BM']:.1f} | {fmt(gs)}{star(gs)} | {fmt(g)}{star(g)} | "
                          f"**{fmt(t)}{star(t)}** | {r['n']} | {fmt(tb)}{star(tb)} |")
                verdict[(lbl, arm, b)] = t
        md += ["", f"### {lbl} — does context change the interaction? Delta = DiD(context) − DiD(span-only)", "", "| B | DiD context | DiD span-only | Delta |", "|---|---|---|---|"]
        for b in BUDGETS:
            j = pa[("context", b)].index.intersection(pa[("span", b)].index)
            c = boot_ci((pa[("context", b)].loc[j] - pa[("span", b)].loc[j]).to_numpy())
            out.append(dict(arm="context_minus_span", subset="all", budget=b, DiD=c[0], DiD_lo=c[1], DiD_hi=c[2], n=len(j)))
            verdict[(lbl, "delta", b)] = c
            md.append(f"| {b} | {fmt(verdict[(lbl, 'context', b)])}{star(verdict[(lbl, 'context', b)])} | {fmt(verdict[(lbl, 'span', b)])}{star(verdict[(lbl, 'span', b)])} | "
                      f"**{fmt(c)}{star(c)}** (n={len(j)}) |")
        md += ["", f"### {lbl} — pre-registered secondary subsets (context arm)", "", "| Subset | n articles | B=100 | B=200 | B=400 |", "|---|---|---|---|---|"]
        for name, ids in subsets.items():
            cellsb = []
            for b in BUDGETS:
                d = df[(df.arm == "context") & (df.budget == b) & df.sample_id.isin(ids)]
                r, _ = cell_row(d, col)
                if name != "all":
                    out.append(dict(arm="context", subset=name, budget=b, **r))
                t = (r["DiD"], r["DiD_lo"], r["DiD_hi"])
                cellsb.append(f"{fmt(t)}{star(t)}")
            md.append(f"| {name} | {len(ids)} | " + " | ".join(cellsb) + " |")
        md.append("")
        pd.DataFrame(out).round(3).to_csv(RES / fname, index=False)

    # ---------------------------------------------------------------- references
    ans = pd.read_csv(f"results/e6_answers_{M}_scored.csv")
    md += ["## References", "", "Final answer straight from the uncompressed context input (no memory step), judged ELR: " +
           "; ".join(f"{c} {fmt(boot_ci(ans[ans.cond == c].supported.astype(float).to_numpy() * 100))}" for c in ("single", "multi")) + ".", "",
           "Existing evidence-span results for the same model (not re-scored; DiD in pp):", "",
           "| Experiment | Input | Protocol | Budget | ELR DiD | WP DiD |", "|---|---|---|---|---|---|"]
    nt = pd.read_csv("results/rev_notrunc_summary.csv"); nt = nt[nt.model == M]
    for r in nt.itertuples():
        md.append(f"| E3b | span-only (~294 tok) | truncation-free | {r.budget} | {r.ELR_DiD:+.1f} [{r.ELR_DiD_lo:+.1f}, {r.ELR_DiD_hi:+.1f}] (n={r.n_complete}) | "
                  f"{r.WP_DiD:+.1f} [{r.WP_DiD_lo:+.1f}, {r.WP_DiD_hi:+.1f}] |")
    bb = pd.read_csv("results/rev_bigbudget_summary.csv"); bb = bb[(bb.model == M) & bb.budget.isin([150, 256, 512])]
    for r in bb.itertuples():
        md.append(f"| E1 | span-only (~294 tok) | enforced | {r.budget} | {r.ELR_DiD:+.1f} [{r.ELR_DiD_lo:+.1f}, {r.ELR_DiD_hi:+.1f}] | "
                  f"{r.WP_DiD:+.1f} [{r.WP_DiD_lo:+.1f}, {r.WP_DiD_hi:+.1f}] |")
    rs = pd.read_csv("results/ratio_summary.csv"); rs = rs[(rs.model == M) & (rs.protocol == "notrunc") & rs.budget.isin(BUDGETS)]
    for b in BUDGETS:
        e, w = rs[(rs.budget == b) & (rs.outcome == "ELR")].iloc[0], rs[(rs.budget == b) & (rs.outcome == "WP")].iloc[0]
        md.append(f"| E13 | multi-trial spans (~1,121 tok) | truncation-free | {b} | {e.DiD:+.1f} [{e.DiD_lo:+.1f}, {e.DiD_hi:+.1f}] | {w.DiD:+.1f} [{w.DiD_lo:+.1f}, {w.DiD_hi:+.1f}] |")
    md.append("")

    # ---------------------------------------------------------------- reading rule
    md += ["## Reading rule (pre-registered)", ""]
    for lbl in ("ELR", "WP"):
        for b in BUDGETS:
            t, c = verdict[(lbl, "context", b)], verdict[(lbl, "delta", b)]
            pers = "persists" if t[2] < 0 else "does not persist"
            chg = ("context changes the effect (" + ("larger" if c[0] < 0 else "smaller") + " interaction)") if (c[1] > 0 or c[2] < 0) \
                else "no detectable change relative to span-only"
            md.append(f"- {lbl}, B={b}: interaction {pers} with context ({fmt(t)}); {chg} (Delta {fmt(c)}).")
    md.append("")
    (RES / "e6_analysis.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
