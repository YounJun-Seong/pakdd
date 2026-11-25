"""PAKDD 2027 figures (2026-11-22). Three figures, LNCS text width (12.2 cm). Colour carries identity
together with line style and marker, never alone (the figures stay readable in greyscale print).
Colours: Aware blue / Blind orange (Fig. 1); ELR violet / WP teal (Fig. 2); in Fig. 3 the truncation-free
ELR keeps its violet from Fig. 2 and the enforced protocol is red. Pairs checked for separation under
protan / deutan / tritan simulation (OKLab dE >= 12) and >= 3:1 contrast on white.

  Fig. 1  figures/pakdd_fig1_framework.(pdf|png)    Future-Query Blindness framework (schematic, no data)
  Fig. 2  figures/pakdd_fig2_compression.(pdf|png)  E13, truncation-free, judge-based ELR and WP DiD vs compression
  Fig. 3  figures/pakdd_fig3_truncation.(pdf|png)   E13, judge-based ELR DiD, enforced vs truncation-free

Every plotted number is read from results/ratio_summary.csv (scripts/analyze_ratio.py); nothing is typed in.
Filled marker = 95 % CI excludes 0, hollow marker = CI includes 0.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("figures")
W = 4.8                                  # LNCS text width in inches
INK, GREY, LIGHT, GRID = "#111111", "#6E6E6E", "#F1F1EF", "#D9D9D9"
C_AWARE, C_BLIND = "#2A78D6", "#EB6834"
T_AWARE, T_BLIND = "#E4EEFA", "#FCE9E0"          # light tints of the two condition colours
C_ELR, C_WP, C_ENF = "#6250D6", "#149A6B", "#E34948"
MODELS = [("qwen3-8b", "Qwen3-8B"), ("qwen3-14b", "Qwen3-14B")]
BUDGETS = [100, 200, 400, 800]
LW, MS = 1.2, 4.6

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Liberation Sans", "DejaVu Sans"], "font.size": 7.5,
    "axes.titlesize": 8, "axes.labelsize": 7.5, "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.8,
    "axes.edgecolor": INK, "axes.linewidth": 0.6, "xtick.color": INK, "ytick.color": INK, "text.color": INK,
    "axes.labelcolor": INK, "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.facecolor": "white",
})


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=400, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)
    print("wrote", OUT / f"{name}.pdf")


# ------------------------------------------------------------------------------- Fig. 1
def fig1():
    fig, ax = plt.subplots(figsize=(W, 4.05))
    ax.set_xlim(0, 100); ax.set_ylim(0, 100); ax.axis("off")

    def box(x, y, w, h, text="", fc="white", ls="-", bold=False, fs=7.2, ec=INK, lw=0.8):
        ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0,rounding_size=1.6",
                                    fc=fc, ec=ec, lw=lw, ls=ls))
        if text:
            ax.text(x, y, text, ha="center", va="center", fontsize=fs, fontweight="bold" if bold else "normal", linespacing=1.25)

    def arrow(x0, y0, x1, y1, ls="-", color=INK):
        ax.add_patch(FancyArrowPatch((x0, y0), (x1, y1), arrowstyle="-|>", mutation_scale=7, lw=0.8, ls=ls,
                                     color=color, shrinkA=0, shrinkB=0))

    xa, xb, bw = 23.5, 76.5, 43
    ax.text(50, 97.6, "Factorial design:  Query Awareness (Aware / Blind)  ×  Evidence Competition (Single / Multi)",
            ha="center", va="center", fontsize=6.0, fontweight="bold")
    box(50, 88.5, 96, 10.5, "Medical evidence source $M_0$  (length $L$)\nSingle-ICO: target finding only   |   Multi-ICO: target + competing findings",
        fc=LIGHT, fs=6.9)
    arrow(xa, 83.25, xa, 80.2, color=C_AWARE); arrow(xb, 83.25, xb, 80.2, color=C_BLIND)
    ax.text(xa, 77.8, "(a) Query-Aware", ha="center", va="center", fontsize=8, fontweight="bold", color=C_AWARE)
    ax.text(xb, 77.8, "(b) Query-Blind", ha="center", va="center", fontsize=8, fontweight="bold", color=C_BLIND)
    box(xa, 69.5, bw, 10, "Future query $q$ available\nwriter at step $t$ receives $M_{t-1}$ + $q$", ec=C_AWARE, lw=1.1, fs=6.9)
    box(xb, 69.5, bw, 10, "Future query $q$ unavailable\nwriter at step $t$ receives $M_{t-1}$ only", ec=C_BLIND, lw=1.1, fs=6.9)
    arrow(xa, 64.5, xa, 60.2, color=C_AWARE); arrow(xb, 64.5, xb, 60.2, color=C_BLIND)
    for x, tint, ec in ((xa, T_AWARE, C_AWARE), (xb, T_BLIND, C_BLIND)):
        box(x, 52, bw, 16, fc=tint, ec=ec, lw=1.1)
        ax.text(x, 56.6, "Memory writing × 4", ha="center", va="center", fontsize=7.2)
        ax.text(x, 52.0, "$M_0 \\rightarrow M_1 \\rightarrow M_2 \\rightarrow M_3 \\rightarrow M_4$", ha="center", va="center", fontsize=6.3)
        ax.text(x, 47.4, "memory budget $B$ per write", ha="center", va="center", fontsize=6.9)
    ax.annotate("", xy=(xb - bw / 2 - 0.4, 52), xytext=(xa + bw / 2 + 0.4, 52),
                arrowprops=dict(arrowstyle="<|-|>", lw=0.7, color=GREY, mutation_scale=6, shrinkA=0, shrinkB=0))
    ax.text(50, 55.4, "same", ha="center", va="center", fontsize=6.3, color=GREY)
    ax.text(50, 48.6, "$B$", ha="center", va="center", fontsize=6.6, color=GREY)
    arrow(xa, 44, xa, 39.7, color=C_AWARE); arrow(xb, 44, xb, 39.7, color=C_BLIND)
    box(xa, 34.7, bw, 10, "Target warrant may be retained\nin $M_4$", ec=C_AWARE, lw=1.1)
    box(xb, 34.7, bw, 10, "Potential warrant loss\nin $M_4$", ls=(0, (4, 2)), ec=C_BLIND, lw=1.1)
    arrow(xa, 29.7, xa, 25.4, color=C_AWARE); arrow(xb, 29.7, xb, 25.4, color=C_BLIND)
    box(50, 19, 96, 12.4, "Final reader:  query $q$ + memory $M_4$  →  answer\n ", fc=LIGHT)
    ax.text(xa, 16.4, "$q$ already known to the writer", ha="center", va="center", fontsize=6.3, color=GREY)
    ax.text(xb, 16.4, "$q$ revealed only at this step", ha="center", va="center", fontsize=6.3, color=INK, fontweight="bold")
    arrow(50, 12.8, 50, 8.7)
    box(50, 4.4, 96, 8.4, "ELR (final answer)  ·  WP (memory $M_4$)  ·  Blindness × Competition DiD", bold=True, fs=6.9)
    save(fig, "pakdd_fig1_framework")


# ------------------------------------------------------------------------------- Fig. 2 / 3
def series(df, model, protocol, outcome):
    d = df[(df.model == model) & (df.protocol == protocol) & (df.outcome == outcome) & df.budget.isin(BUDGETS)]
    d = d.set_index("budget").loc[BUDGETS]
    return d.DiD.to_numpy(), d.DiD_lo.to_numpy(), d.DiD_hi.to_numpy()


def draw(ax, x, y, lo, hi, *, color, ls, marker, dx):
    xs = [v + dx for v in x]
    ax.plot(xs, y, color=color, ls=ls, lw=LW, zorder=3)
    ax.errorbar(xs, y, yerr=[y - lo, hi - y], fmt="none", ecolor=color, elinewidth=0.8, capsize=2, capthick=0.8, zorder=3)
    for xi, yi, l, h in zip(xs, y, lo, hi):
        ax.plot(xi, yi, marker=marker, ms=MS, mec=color, mew=0.9, mfc=color if (h < 0 or l > 0) else "white", zorder=4)


def panel_axes(ylabel, ylim):
    fig, axes = plt.subplots(1, 2, figsize=(W, 2.45), sharey=True)
    fig.subplots_adjust(wspace=0.07)
    for ax, (_, name), tag in zip(axes, MODELS, "ab"):
        ax.axhline(0, color=INK, lw=0.7, zorder=2)
        ax.set_title(f"({tag}) {name}", pad=4)
        ax.set_xticks(range(4)); ax.set_xticklabels([f"{b // 10}%\n({b})" for b in BUDGETS])
        ax.set_xlim(-0.35, 3.35); ax.set_ylim(*ylim)
        ax.grid(axis="y", color=GRID, lw=0.5, zorder=0); ax.set_axisbelow(True)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        ax.tick_params(length=2.5, width=0.6)
    axes[0].set_ylabel(ylabel)
    fig.supxlabel("Memory budget (% of 1,000-token source)", fontsize=7.5, y=-0.07)
    return fig, axes


def handles(specs):
    h = [Line2D([], [], color=c, ls=ls, lw=LW, marker=m, ms=MS, mfc=c, mec=c, label=lab) for lab, c, ls, m in specs]
    h.append(Line2D([], [], color="none", marker="o", ms=MS, mfc="white", mec=INK, mew=0.9, label="hollow: CI includes 0"))
    return h


def top_legend(fig, specs):
    fig.legend(handles=handles(specs), loc="upper center", bbox_to_anchor=(0.5, 1.045), ncol=3, frameon=False,
               handlelength=2.3, columnspacing=0.9, handletextpad=0.45, fontsize=6.3)


def fig2(df):
    fig, axes = panel_axes("Blindness × Competition DiD (pp)", (-56, 12))
    for ax, (m, _) in zip(axes, MODELS):
        draw(ax, range(4), *series(df, m, "notrunc", "ELR"), color=C_ELR, ls="-", marker="o", dx=-0.06)
        draw(ax, range(4), *series(df, m, "notrunc", "WP"), color=C_WP, ls=(0, (4, 2)), marker="s", dx=0.06)
    top_legend(fig, [("ELR (final answer)", C_ELR, "-", "o"), ("WP (memory)", C_WP, (0, (4, 2)), "s")])
    save(fig, "pakdd_fig2_compression")


def fig3(df):
    fig, axes = panel_axes("Judge-based ELR DiD (pp)", (-62, 14))
    for ax, (m, _) in zip(axes, MODELS):
        draw(ax, range(4), *series(df, m, "enforced", "ELR"), color=C_ENF, ls="-", marker="^", dx=-0.06)
        draw(ax, range(4), *series(df, m, "notrunc", "ELR"), color=C_ELR, ls=(0, (4, 2)), marker="o", dx=0.06)
    top_legend(fig, [("Enforced cap (truncation permitted)", C_ENF, "-", "^"), ("Truncation-free", C_ELR, (0, (4, 2)), "o")])
    save(fig, "pakdd_fig3_truncation")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    df = pd.read_csv("results/ratio_summary.csv")
    fig1(); fig2(df); fig3(df)
    t = df[df.model.isin([m for m, _ in MODELS]) & df.budget.isin(BUDGETS) & df.outcome.isin(["ELR", "WP"])]
    print(t[["model", "protocol", "outcome", "budget", "DiD", "DiD_lo", "DiD_hi"]].round(1).to_string(index=False))
