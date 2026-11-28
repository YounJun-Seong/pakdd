"""Phase-6 E20 full-source reading and loss stage, analysis (docs/phase6_prereg.md, 2026-11-27).
New: the final answer straight from the uncompressed Single / Filler source (results/e20_answers_*); Multi = the E13
`full_long` answers. Everything else is the committed E13 / E14 (four writes) and E18 (first write) verdicts.
Outputs: results/e20/e20_summary.csv, results/e20/e20_stage.csv, results/e20/e20_report.md"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_lencontrol import BUDGETS, MODELS, fmt, load as load_orig  # noqa: E402
from analyze_phase4 import boot_ci  # noqa: E402

CONDS = ("single", "filler", "multi")
STAGES = (("retained_used", 1, 1), ("write_loss", 0, 0), ("read_failure", 1, 0), ("answer_without_memory", 0, 1))
PRIMARY = ("qwen3-14b", 200, "filler")


def wilson(k, n, z=1.96):
    if n == 0:
        return np.nan, np.nan, np.nan
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return 100 * p, 100 * (c - h), 100 * (c + h)


def full(m, ids):
    out = {}
    a = pd.read_csv(f"results/e20_answers_{m}_scored.csv")
    assert not a.claim_label.isin(["EVAL_ERROR", "PARSE_ERROR"]).any()
    for src, cond in (("full_single", "single"), ("full_filler", "filler")):
        out[cond] = a[a.source == src].set_index("sample_id").supported.astype(float)
    r = pd.read_csv(f"results/ratio_answers_{m}_scored.csv")
    out["multi"] = r[(r.source == "full_long") & r.sample_id.isin(ids)].set_index("sample_id").supported.astype(float)
    F = pd.DataFrame(out) * 100
    assert len(F) == len(ids) and not F.isna().any().any()
    return F


def stage_rows(g, F, tag):
    """g: one mode x cond x budget cell (sample_id, elr, wp); F: full-source correctness of that cond (0 / 100)."""
    g = g.set_index("sample_id").join(F.rename("full"), how="inner").dropna(subset=["elr", "wp"])
    ok = g[g.full == 100]
    row = dict(tag, n=len(g), full_correct=len(ok))
    for name, wp, elr in STAGES:
        row[name] = int(((ok.wp == wp) & (ok.elr == elr)).sum())
    wrong = ok[ok.elr == 0]
    row["final_wrong"] = len(wrong)
    row["write_share"], row["write_share_lo"], row["write_share_hi"] = wilson(int((wrong.wp == 0).sum()), len(wrong))
    return row


def main():
    Path("results/e20").mkdir(parents=True, exist_ok=True)
    md = ["# E20 Full-source reading and loss stage — analysis", "",
          "FULL = the reader's answer straight from the uncompressed source (same reader prompt and settings as every final",
          "answer). M4 cells are the committed truncation-free chains of E13 / E14. `*` = 95 % CI excludes 0 (paired article",
          "bootstrap, 2,000 resamples). Stage table: over articles whose full-source answer is correct; memory evidence = the",
          "evaluator's WP verdict (label recoverability).", ""]
    S, T = [], []
    for m in MODELS:
        d, _ = load_orig(m)
        ids = sorted(d.sample_id.unique())
        F = full(m, ids)
        md += [f"## {m}  (n = {len(ids)})", "", "### Full-source ELR (%)", "", "| Source | FULL | vs Single |", "|---|---|---|"]
        for c in CONDS:
            t = boot_ci(F[c].to_numpy()); dd = boot_ci((F[c] - F["single"]).to_numpy()) if c != "single" else None
            md.append(f"| {c} | {t[0]:.1f} [{t[1]:.1f}, {t[2]:.1f}] | {fmt(dd) if dd else '—'} |")
            S.append(dict(model=m, budget=0, cond=c, quantity="FULL", est=t[0], lo=t[1], hi=t[2]))
            if dd:
                S.append(dict(model=m, budget=0, cond=c, quantity="FULL - FULL(single)", est=dd[0], lo=dd[1], hi=dd[2]))
        md += ["", "### M4 against the full source (ELR)", "",
               "| B | Source | Aware M4 | Blind M4 | Aware M4 − FULL | Blind M4 − FULL |", "|---|---|---|---|---|---|"]
        for b in BUDGETS:
            g = d[d.budget == b]
            g = g[~g.sample_id.isin(g[g.failed.astype(bool)].sample_id.unique())]
            p = g.pivot_table(index="sample_id", columns=["mode", "cond"], values="elr", aggfunc="first").dropna() * 100
            for c in CONDS:
                f = F.loc[p.index, c]
                da, db = boot_ci((p[("aware", c)] - f).to_numpy()), boot_ci((p[("blind", c)] - f).to_numpy())
                md.append(f"| {b} | {c} | {p[('aware', c)].mean():.1f} | {p[('blind', c)].mean():.1f} | {fmt(da)} | {fmt(db)} |")
                for q, t in (("Aware M4 - FULL", da), ("Blind M4 - FULL", db)):
                    S.append(dict(model=m, budget=b, cond=c, quantity=q, est=t[0], lo=t[1], hi=t[2]))
                for mode in ("aware", "blind"):
                    T.append(stage_rows(g[(g["mode"] == mode) & (g.cond == c)][["sample_id", "elr", "wp"]], F[c],
                                        dict(model=m, memory="M4", budget=b, mode=mode, cond=c)))
        md.append("")
    # first-write memories (E18, Qwen3-14B, B = 200, original prompts): descriptive
    if Path("results/e18_qwen3-14b_ok_scored.csv").exists():
        m = "qwen3-14b"; K = ["family", "sample_id", "mode", "cond", "budget"]
        e = pd.read_csv(f"results/e18_{m}_ok_scored.csv")[K + ["supported"]].rename(columns={"supported": "elr"}).merge(
            pd.read_csv(f"results/e18_{m}_mem_scored.csv")[K + ["supported"]].rename(columns={"supported": "wp"}), on=K, validate="1:1")
        e = e[e.family == "original"]; e[["elr", "wp"]] = e[["elr", "wp"]].astype(float)
        F = full(m, sorted(load_orig(m)[0].sample_id.unique()))
        for c in CONDS:
            for mode in ("aware", "blind"):
                T.append(stage_rows(e[(e["mode"] == mode) & (e.cond == c)][["sample_id", "elr", "wp"]], F[c],
                                    dict(model=m, memory="M1", budget=200, mode=mode, cond=c)))
    T = pd.DataFrame(T); S = pd.DataFrame(S)
    md += ["## Loss stage (articles with a correct full-source answer)", "",
           "retained = WP 1 & ELR 1; write loss = WP 0 & ELR 0; read failure = WP 1 & ELR 0; answer without memory = WP 0 & ELR 1.",
           "Write share = WP 0 among wrong final answers (Wilson 95 % CI).", "",
           "| Model | Memory | B | Mode | Source | n full-correct | retained | write loss | read failure | answer w/o memory | wrong finals | write share of wrong finals |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in T.itertuples():
        pc = lambda k: f"{k} ({100 * k / r.full_correct:.1f}%)"  # noqa: E731
        md.append(f"| {r.model} | {r.memory} | {r.budget} | {r.mode} | {r.cond} | {r.full_correct} | {pc(r.retained_used)} | {pc(r.write_loss)} | "
                  f"{pc(r.read_failure)} | {pc(r.answer_without_memory)} | {r.final_wrong} | "
                  + (f"{r.write_share:.1f} [{r.write_share_lo:.1f}, {r.write_share_hi:.1f}]" if r.final_wrong else "—") + " |")
    md += ["", "## Reading rule (pre-registered)", ""]
    for m in MODELS:
        for b in BUDGETS:
            for c in ("filler", "multi"):
                s = S[(S.model == m) & (S.budget == b) & (S.cond == c) & (S.quantity == "Blind M4 - FULL")].iloc[0]
                t = T[(T.model == m) & (T.memory == "M4") & (T.budget == b) & (T["mode"] == "blind") & (T.cond == c)].iloc[0]
                i, ii = bool(s.hi < 0), bool(t.final_wrong > 0 and t.write_share_lo > 50)
                md.append(f"- {m}, B = {b}, {c}{' (PRIMARY)' if (m, b, c) == PRIMARY else ''}: Blind M4 − FULL {fmt((s.est, s.lo, s.hi))}; "
                          f"write share {t.write_share:.1f} [{t.write_share_lo:.1f}, {t.write_share_hi:.1f}] of {t.final_wrong} wrong finals "
                          f"-> {'write-stage loss' if (i and ii) else 'NOT established as write-stage loss'} (i {i}, ii {ii}).")
    md.append("")
    for m in MODELS:
        for c in ("filler", "multi"):
            s = S[(S.model == m) & (S.cond == c) & (S.quantity == "FULL - FULL(single)")].iloc[0]
            md.append(f"- {m}: FULL({c}) − FULL(single) {fmt((s.est, s.lo, s.hi))} -> source-reading difficulty "
                      f"{'contributes' if s.hi < 0 else 'not shown'}.")
    S.round(3).to_csv("results/e20/e20_summary.csv", index=False)
    T.round(3).to_csv("results/e20/e20_stage.csv", index=False)
    Path("results/e20/e20_report.md").write_text("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    main()
