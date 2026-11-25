"""E19 figure (2026-11-23): Blind − Aware gap against source length with the target position fixed.
Reads results/e19/e19_cells.csv (scripts/analyze_e19.py); nothing is typed in. Original prompts, primary set.
Colour carries the position together with marker and line style; filled marker = 95 % CI excludes 0.
Colours checked under protan / deutan / tritan simulation (OKLab dE >= 16 for every pair, >= 3:1 on white).
Output: figures/pakdd_fig_e19_length_position.(pdf|png)"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from pakdd_figures import GREY, GRID, INK, W, save  # noqa: E402  (also applies the rcParams)

ARMS = [("first", "Target first", "#16337A", "-", "o"), ("middle", "Target in the middle", "#D9480F", (0, (4, 2)), "s"),
        ("last", "Target last", "#2F9E9E", (0, (1, 1.5)), "^")]
X = {200: 0, 500: 1, 1000: 2}


def main(family="original"):
    C = pd.read_csv("results/e19/e19_cells.csv"); C = C[C.family == family]
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.25), sharey=True)
    fig.subplots_adjust(wspace=0.08, top=0.80)
    for ax, (out, title) in zip(axes, (("ELR", "ELR (final answer)"), ("WP", "WP (memory)"))):
        ax.axhline(0, color=GREY, lw=0.6, zorder=1)
        for k, (arm, lbl, col, ls, mk) in enumerate(ARMS):
            g = C[(C.outcome == out) & (C.arm == arm)].sort_values("level")
            xs = [X[l] + (k - 1) * 0.07 for l in g.level]
            ax.plot(xs, g.G, color=col, ls=ls, lw=1.2, zorder=3)
            ax.errorbar(xs, g.G, yerr=[g.G - g.G_lo, g.G_hi - g.G], fmt="none", ecolor=col, elinewidth=0.7, capsize=1.6, zorder=2)
            for x, r in zip(xs, g.itertuples()):
                sig = r.G_hi < 0 or r.G_lo > 0
                ax.plot([x], [r.G], marker=mk, ms=4.6, mfc=col if sig else "white", mec=col, mew=0.9, ls="none", zorder=4)
        ax.set_title(title, pad=3)
        ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["200", "500", "1,000"])
        ax.set_xlim(-0.35, 2.35); ax.set_ylim(-56, 8)
        ax.set_xlabel("Source length (tokens)")
        ax.grid(axis="y", color=GRID, lw=0.5); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0].set_ylabel("Blind − Aware (pp)")
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([], [], color=c, ls=ls, lw=1.2, marker=mk, ms=4.6, mfc=c, mec=c, label=lbl) for _, lbl, c, ls, mk in ARMS],
               loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 1.0), handlelength=2.6, columnspacing=1.4)
    save(fig, "pakdd_fig_e19_length_position" + ("" if family == "original" else f"_{family}"))


if __name__ == "__main__":
    main(*sys.argv[1:])
