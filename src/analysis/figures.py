"""
figures.py
----------
Publication-quality figure generation for the BOLA meta-analysis.

Every function accepts the relevant summary DataFrame (output of
analysis.py) and returns the matplotlib Figure object.  Figures are
saved to FIG_DIR as both PNG (300 dpi) and SVG unless save=False.

Figures produced
----------------
fig_scope_pie            – donut: in-scope vs out-of-scope
fig_family_bar           – horizontal bar: family distribution
fig_action_bar           – horizontal bar: action type distribution
fig_hv_bar               – horizontal bar: H vs V direction
fig_sector_bar           – horizontal bar: industry sector
fig_id_format_bar        – horizontal bar: identifier format
fig_mechanism_bar        – horizontal bar: exploit mechanism frequency
fig_severity_bar         – horizontal bar: severity distribution
fig_temporal_bar         – vertical bar: year distribution
fig_confidence_pie       – donut: confidence distribution
fig_family_sector_heatmap – heatmap: family × sector crosstab
fig_family_severity_heatmap – heatmap: family × severity crosstab
fig_overview_dashboard   – 3×2 summary dashboard (key six panels)
save_all                 – saves every figure
"""

from __future__ import annotations
from pathlib import Path
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    FIG_DIR, MPL_RC, PALETTE, COLORS,
    FIG_WIDTH_SINGLE, FIG_WIDTH_DOUBLE, FIG_HEIGHT_BASE,
    ANNOT_FONTSIZE, FAMILY_SHORT,
)

# Apply global style
plt.rcParams.update(MPL_RC)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _apply_style() -> None:
    """Re-apply rcParams (call at start of each function for safety)."""
    plt.rcParams.update(MPL_RC)


def _watermark(ax: plt.Axes, text: str = "APIsec Research Labs") -> None:
    ax.text(
        0.99, 0.01, text,
        transform=ax.transAxes,
        ha="right", va="bottom",
        fontsize=7, color="#aaaaaa", style="italic",
    )


def _annotate_bars_h(ax: plt.Axes, counts: list[int], pcts: list[float]) -> None:
    """Annotate horizontal bars with count and percentage."""
    for i, (bar, cnt, pct) in enumerate(zip(ax.patches, counts, pcts)):
        w = bar.get_width()
        ax.text(
            w + max(counts) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{cnt}  ({pct:.1f}%)",
            va="center", ha="left",
            fontsize=ANNOT_FONTSIZE, color=COLORS["text"],
        )


def _save_fig(fig: plt.Figure, name: str, save: bool) -> None:
    if save:
        FIG_DIR.mkdir(parents=True, exist_ok=True)
        for ext in ("png", "svg"):
            out = FIG_DIR / f"{name}.{ext}"
            fig.savefig(out, format=ext)
        print(f"  [saved] figures/{name}.png + .svg")


def _hbar_figure(
    labels: list[str],
    counts: list[int],
    pcts: list[float],
    title: str,
    xlabel: str = "Number of reports",
    colors: list[str] | None = None,
    fig_h: float | None = None,
) -> plt.Figure:
    """Reusable horizontal bar chart builder."""
    _apply_style()
    n = len(labels)
    h = fig_h or max(FIG_HEIGHT_BASE, n * 0.55 + 1.2)
    fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, h))
    bar_colors = colors or [PALETTE[i % len(PALETTE)] for i in range(n)]
    bars = ax.barh(
        labels, counts,
        color=bar_colors, height=0.6, edgecolor="white", linewidth=0.5,
    )
    ax.set_xlabel(xlabel, fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold", pad=12)
    ax.invert_yaxis()
    ax.set_xlim(0, max(counts) * 1.28)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_color(COLORS["gridline"])
    _annotate_bars_h(ax, counts, pcts)
    _watermark(ax)
    fig.tight_layout()
    return fig


# ---------------------------------------------------------------------------
# Individual figure functions
# ---------------------------------------------------------------------------

def fig_scope_pie(scope_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Donut chart: in-scope vs out-of-scope."""
    _apply_style()
    labels = scope_df["label"].tolist()
    sizes  = scope_df["count"].tolist()
    colors = [COLORS["primary"], COLORS["c4"]]

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        sizes,
        labels=None,
        colors=colors,
        autopct="%1.1f%%",
        startangle=90,
        pctdistance=0.72,
        wedgeprops=dict(width=0.5, edgecolor="white", linewidth=2),
    )
    for at in autotexts:
        at.set_fontsize(11)
        at.set_color("white")
        at.set_fontweight("bold")

    ax.legend(
        handles=[mpatches.Patch(color=c, label=l) for c, l in zip(colors, labels)],
        loc="lower center", bbox_to_anchor=(0.5, -0.08),
        fontsize=10, frameon=False, ncol=2,
    )
    ax.set_title(
        f"Dataset Composition\n(n = {sum(sizes)} classified reports)",
        fontsize=13, fontweight="bold", pad=10,
    )
    # Centre annotation
    ax.text(0, 0, f"{sizes[0]}\nin-scope", ha="center", va="center",
            fontsize=12, fontweight="bold", color=COLORS["primary"])
    _watermark(ax)
    fig.tight_layout()
    _save_fig(fig, "fig_scope_pie", save)
    return fig


def fig_family_bar(family_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Horizontal bar: BOLA family distribution."""
    labels  = family_df["family"].tolist()
    counts  = family_df["count"].tolist()
    pcts    = family_df["pct"].tolist()
    # Use short labels for readability on figure
    short   = [FAMILY_SHORT.get(l, l).replace("\n", " ") for l in labels]
    bar_colors = [PALETTE[i] for i in range(len(labels))]

    fig = _hbar_figure(
        short, counts, pcts,
        title="BOLA Taxonomy Family Distribution\n(confirmed in-scope reports)",
        colors=bar_colors,
    )
    _save_fig(fig, "fig_family_bar", save)
    return fig


def fig_action_bar(action_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Horizontal bar: action type distribution."""
    labels = action_df["action_type"].tolist()
    counts = action_df["count"].tolist()
    pcts   = action_df["pct"].tolist()
    # Colour state-changing actions differently
    state_changing = {"Modify", "Delete", "Trigger"}
    colors = [COLORS["accent"] if l in state_changing else COLORS["primary"] for l in labels]

    fig = _hbar_figure(
        labels, counts, pcts,
        title="Action Type Distribution\n(in-scope reports)",
        colors=colors,
    )
    # Legend
    ax = fig.axes[0]
    ax.legend(
        handles=[
            mpatches.Patch(color=COLORS["primary"], label="Read / Enumerate / Unclear"),
            mpatches.Patch(color=COLORS["accent"],  label="State-changing (Modify / Delete / Trigger)"),
        ],
        loc="lower right", fontsize=8, frameon=True, framealpha=0.9,
    )
    _save_fig(fig, "fig_action_bar", save)
    return fig


def fig_hv_bar(hv_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Horizontal bar: horizontal vs vertical authorization failure."""
    labels = hv_df["direction"].tolist()
    counts = hv_df["count"].tolist()
    pcts   = hv_df["pct"].tolist()
    colors = [COLORS["primary"], COLORS["accent"], COLORS["c4"]]

    fig = _hbar_figure(
        labels, counts, pcts,
        title="Authorization Failure Direction\n(in-scope reports)",
        colors=colors[:len(labels)],
        fig_h=3.8,
    )
    _save_fig(fig, "fig_hv_bar", save)
    return fig


def fig_sector_bar(sector_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Horizontal bar: industry sector distribution."""
    labels = sector_df["sector"].tolist()
    counts = sector_df["count"].tolist()
    pcts   = sector_df["pct"].tolist()

    fig = _hbar_figure(
        labels, counts, pcts,
        title="Industry Sector Distribution\n(in-scope reports)",
        colors=[PALETTE[i % len(PALETTE)] for i in range(len(labels))],
    )
    _save_fig(fig, "fig_sector_bar", save)
    return fig


def fig_id_format_bar(id_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Horizontal bar: identifier format distribution."""
    labels = id_df["id_format"].tolist()
    counts = id_df["count"].tolist()
    pcts   = id_df["pct"].tolist()
    # Sequential int highlighted
    colors = [
        COLORS["accent"] if "Sequential" in l else PALETTE[i % len(PALETTE)]
        for i, l in enumerate(labels)
    ]

    fig = _hbar_figure(
        labels, counts, pcts,
        title="Object Identifier Format Distribution\n(in-scope reports)",
        colors=colors,
    )
    _save_fig(fig, "fig_id_format_bar", save)
    return fig


def fig_mechanism_bar(mech_df: pd.DataFrame, n_in_scope: int, save: bool = True) -> plt.Figure:
    """Horizontal bar: exploit mechanism frequency."""
    if mech_df.empty:
        fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, 3))
        ax.text(0.5, 0.5, "No mechanism data", ha="center", va="center")
        _save_fig(fig, "fig_mechanism_bar", save)
        return fig

    labels = mech_df["mechanism"].tolist()
    counts = mech_df["count"].tolist()
    pcts   = mech_df["pct_of_reports"].tolist()

    fig = _hbar_figure(
        labels, counts, pcts,
        title="Exploit Mechanism Frequency\n(% of in-scope reports; multi-mechanism reports counted once per mechanism)",
        xlabel=f"Reports (n = {n_in_scope} in-scope total)",
        colors=[PALETTE[i % len(PALETTE)] for i in range(len(labels))],
    )
    _save_fig(fig, "fig_mechanism_bar", save)
    return fig


def fig_severity_bar(sev_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Horizontal bar: severity distribution."""
    labels = sev_df["severity"].tolist()
    counts = sev_df["count"].tolist()
    pcts   = sev_df["pct"].tolist()
    sev_colors = {
        "Critical": "#C0392B", "High": "#E67E22",
        "Medium":   COLORS["primary"], "Low": COLORS["c4"], "N/A": "#AAAAAA",
    }
    colors = [sev_colors.get(l, COLORS["primary"]) for l in labels]

    fig = _hbar_figure(
        labels, counts, pcts,
        title="Severity Distribution\n(in-scope reports, HackerOne triage ratings)",
        colors=colors, fig_h=4.0,
    )
    _save_fig(fig, "fig_severity_bar", save)
    return fig


def fig_temporal_bar(temp_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Vertical bar: temporal distribution by year."""
    _apply_style()
    known = temp_df[temp_df["count"] > 0].copy()
    years  = known["year"].tolist()
    counts = known["count"].tolist()

    n_redacted = int(temp_df["n_redacted"].iloc[0]) if "n_redacted" in temp_df.columns else 0

    fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, FIG_HEIGHT_BASE))
    bars = ax.bar(
        years, counts,
        color=COLORS["primary"], width=0.55, edgecolor="white", linewidth=0.8,
    )
    ax.set_xlabel("Disclosure Year", fontsize=11)
    ax.set_ylabel("Number of reports", fontsize=11)
    ax.set_title(
        f"Temporal Distribution of Disclosed Reports\n"
        f"(reports with known year = {sum(counts)}; {n_redacted} redacted / undated)",
        fontsize=13, fontweight="bold", pad=10,
    )
    ax.yaxis.set_major_locator(mticker.MaxNLocator(integer=True))
    ax.spines[["top", "right"]].set_visible(False)
    # Annotate bars
    for bar, cnt in zip(bars, counts):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.2,
            str(cnt), ha="center", va="bottom",
            fontsize=ANNOT_FONTSIZE + 1, fontweight="bold", color=COLORS["primary"],
        )
    # Note on partial year if 2026 present
    if "2026" in years:
        ax.annotate(
            "* 2026 partial year",
            xy=(years.index("2026"), counts[years.index("2026")]),
            xytext=(years.index("2026") - 0.3, counts[years.index("2026")] + 1.2),
            fontsize=8, color="#888888",
        )
    _watermark(ax)
    fig.tight_layout()
    _save_fig(fig, "fig_temporal_bar", save)
    return fig


def fig_confidence_pie(conf_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Donut chart: classifier confidence distribution."""
    _apply_style()
    labels = conf_df["confidence"].tolist()
    sizes  = conf_df["count"].tolist()
    colors = [COLORS["primary"], COLORS["c3"], COLORS["c6"]]

    fig, ax = plt.subplots(figsize=(6, 5))
    wedges, texts, autotexts = ax.pie(
        sizes, labels=None, colors=colors,
        autopct="%1.1f%%", startangle=90, pctdistance=0.72,
        wedgeprops=dict(width=0.5, edgecolor="white", linewidth=2),
    )
    for at in autotexts:
        at.set_fontsize(11)
        at.set_color("white")
        at.set_fontweight("bold")
    ax.legend(
        handles=[mpatches.Patch(color=c, label=l) for c, l in zip(colors, labels)],
        loc="lower center", bbox_to_anchor=(0.5, -0.08),
        fontsize=10, frameon=False, ncol=3,
    )
    ax.set_title("Classifier Confidence Distribution\n(in-scope reports)",
                 fontsize=13, fontweight="bold", pad=10)
    _watermark(ax)
    fig.tight_layout()
    _save_fig(fig, "fig_confidence_pie", save)
    return fig


def fig_family_sector_heatmap(ct: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Heatmap: BOLA family × industry sector cross-tabulation."""
    _apply_style()
    # Drop Total column for the colour map
    plot_ct = ct.drop(columns="Total", errors="ignore")

    fig, ax = plt.subplots(figsize=(FIG_WIDTH_DOUBLE, max(4.5, len(plot_ct) * 0.85 + 1.5)))
    data = plot_ct.values.astype(float)
    # Custom colormap from white → primary
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "bola_cmap", ["#F0F9FC", COLORS["c3"], COLORS["primary"]], N=256
    )
    im = ax.imshow(data, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(plot_ct.columns)))
    ax.set_xticklabels(plot_ct.columns, rotation=25, ha="right", fontsize=9)
    ax.set_yticks(range(len(plot_ct.index)))
    ax.set_yticklabels(plot_ct.index, fontsize=9)
    ax.set_title("BOLA Family × Industry Sector Cross-tabulation\n(raw counts, in-scope reports)",
                 fontsize=13, fontweight="bold", pad=12)
    # Annotate cells
    thresh = data.max() / 2.0
    for r in range(data.shape[0]):
        for c in range(data.shape[1]):
            v = int(data[r, c])
            ax.text(c, r, str(v), ha="center", va="center",
                    fontsize=10, fontweight="bold",
                    color="white" if data[r, c] > thresh else COLORS["text"])
    # Add total column as text annotation outside grid
    totals = ct["Total"].tolist() if "Total" in ct.columns else []
    if totals:
        for r, t in enumerate(totals):
            ax.text(len(plot_ct.columns) + 0.15, r, f"= {t}",
                    va="center", ha="left", fontsize=9, color=COLORS["text"])
    plt.colorbar(im, ax=ax, shrink=0.6, label="Report count")
    ax.grid(False)
    fig.tight_layout()
    _save_fig(fig, "fig_family_sector_heatmap", save)
    return fig


def fig_family_severity_heatmap(ct: pd.DataFrame, save: bool = True) -> plt.Figure:
    """Heatmap: BOLA family × severity cross-tabulation."""
    _apply_style()
    plot_ct = ct.drop(columns="Total", errors="ignore")
    sev_colors_order = ["#C0392B", "#E67E22", COLORS["primary"], COLORS["c4"]]

    fig, ax = plt.subplots(figsize=(9, max(4, len(plot_ct) * 0.85 + 1.5)))
    from matplotlib.colors import LinearSegmentedColormap
    cmap = LinearSegmentedColormap.from_list(
        "bola_sev", ["#F0F9FC", COLORS["c3"], COLORS["primary"]], N=256
    )
    data = plot_ct.values.astype(float)
    im   = ax.imshow(data, cmap=cmap, aspect="auto")
    ax.set_xticks(range(len(plot_ct.columns)))
    ax.set_xticklabels(plot_ct.columns, fontsize=10)
    ax.set_yticks(range(len(plot_ct.index)))
    ax.set_yticklabels(plot_ct.index, fontsize=9)
    ax.set_title("BOLA Family × Severity Cross-tabulation\n(raw counts, in-scope reports)",
                 fontsize=13, fontweight="bold", pad=12)
    thresh = data.max() / 2.0
    for r in range(data.shape[0]):
        for c in range(data.shape[1]):
            v = int(data[r, c])
            ax.text(c, r, str(v), ha="center", va="center",
                    fontsize=11, fontweight="bold",
                    color="white" if data[r, c] > thresh else COLORS["text"])
    plt.colorbar(im, ax=ax, shrink=0.6, label="Report count")
    ax.grid(False)
    fig.tight_layout()
    _save_fig(fig, "fig_family_severity_heatmap", save)
    return fig


def fig_overview_dashboard(
    family_df: pd.DataFrame,
    action_df: pd.DataFrame,
    hv_df: pd.DataFrame,
    sector_df: pd.DataFrame,
    sev_df: pd.DataFrame,
    id_df: pd.DataFrame,
    n_in_scope: int,
    n_total: int,
    save: bool = True,
) -> plt.Figure:
    """
    6-panel summary dashboard combining the six key single-variable
    distributions on one publication page.
    """
    _apply_style()
    fig = plt.figure(figsize=(18, 14))
    fig.suptitle(
        "BOLA in the Wild: Key Distribution Summary\n"
        f"(n = {n_in_scope} confirmed in-scope BOLA reports, {n_total} classified total)",
        fontsize=15, fontweight="bold", y=0.98,
    )

    gs = fig.add_gridspec(3, 2, hspace=0.52, wspace=0.38)
    axes = [
        fig.add_subplot(gs[0, 0]),
        fig.add_subplot(gs[0, 1]),
        fig.add_subplot(gs[1, 0]),
        fig.add_subplot(gs[1, 1]),
        fig.add_subplot(gs[2, 0]),
        fig.add_subplot(gs[2, 1]),
    ]

    def _mini_hbar(ax, labels, counts, pcts, title, color_list):
        bars = ax.barh(labels, counts, color=color_list, height=0.6,
                       edgecolor="white", linewidth=0.5)
        ax.invert_yaxis()
        ax.set_title(title, fontsize=11, fontweight="bold", pad=6)
        ax.set_xlim(0, max(counts) * 1.32)
        ax.spines[["top", "right"]].set_visible(False)
        ax.spines["left"].set_color(COLORS["gridline"])
        ax.tick_params(labelsize=8)
        for bar, cnt, pct in zip(bars, counts, pcts):
            ax.text(bar.get_width() + max(counts) * 0.015,
                    bar.get_y() + bar.get_height() / 2,
                    f"{cnt} ({pct:.0f}%)", va="center", ha="left",
                    fontsize=7.5, color=COLORS["text"])

    # 1 – Family
    short_fam = [FAMILY_SHORT.get(l, l).replace("\n", " ") for l in family_df["family"]]
    _mini_hbar(axes[0], short_fam, family_df["count"].tolist(),
               family_df["pct"].tolist(), "Family Distribution",
               PALETTE[:len(family_df)])

    # 2 – Action type
    state = {"Modify", "Delete", "Trigger"}
    act_colors = [COLORS["accent"] if l in state else COLORS["primary"]
                  for l in action_df["action_type"]]
    _mini_hbar(axes[1], action_df["action_type"].tolist(),
               action_df["count"].tolist(), action_df["pct"].tolist(),
               "Action Type", act_colors)

    # 3 – Horizontal / Vertical
    _mini_hbar(axes[2], hv_df["direction"].tolist(),
               hv_df["count"].tolist(), hv_df["pct"].tolist(),
               "Auth Failure Direction",
               [COLORS["primary"], COLORS["accent"], COLORS["c4"]][:len(hv_df)])

    # 4 – Severity
    sev_colors_map = {"Critical": "#C0392B", "High": "#E67E22",
                      "Medium": COLORS["primary"], "Low": COLORS["c4"], "N/A": "#AAAAAA"}
    sev_col = [sev_colors_map.get(l, COLORS["primary"]) for l in sev_df["severity"]]
    _mini_hbar(axes[3], sev_df["severity"].tolist(),
               sev_df["count"].tolist(), sev_df["pct"].tolist(),
               "Severity Distribution", sev_col)

    # 5 – Sector
    _mini_hbar(axes[4], sector_df["sector"].tolist(),
               sector_df["count"].tolist(), sector_df["pct"].tolist(),
               "Industry Sector", PALETTE[:len(sector_df)])

    # 6 – ID format
    id_col = [
        COLORS["accent"] if "Sequential" in l else PALETTE[i % len(PALETTE)]
        for i, l in enumerate(id_df["id_format"])
    ]
    _mini_hbar(axes[5], id_df["id_format"].tolist(),
               id_df["count"].tolist(), id_df["pct"].tolist(),
               "Identifier Format", id_col)

    # Shared footer watermark
    fig.text(0.99, 0.005, "APIsec Research Labs", ha="right", va="bottom",
             fontsize=7, color="#aaaaaa", style="italic")
    _save_fig(fig, "fig_overview_dashboard", save)
    return fig

# ---------------------------------------------------------------------------
# Program-weighted figures  (addresses single-program concentration bias)
# ---------------------------------------------------------------------------

def fig_program_concentration(conc_df: pd.DataFrame, save: bool = True) -> plt.Figure:
    """
    Horizontal bar: reports per program, descending.
    Annotates share of dataset so the limitation can be cited directly.
    """
    _apply_style()
    df = conc_df.sort_values("n_reports", ascending=True)   # ascending → largest at top after invert
    labels = df["program"].tolist()
    counts = df["n_reports"].tolist()
    pcts   = df["pct_of_dataset"].tolist()

    # Colour top-2 contributors in accent to call them out
    max_c  = max(counts)
    colors = [
        COLORS["accent"] if c == max(counts) or c == sorted(set(counts))[-2]
        else COLORS["c3"]
        for c in counts
    ]

    fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, max(FIG_HEIGHT_BASE, len(labels) * 0.5 + 1.5)))
    ax.barh(labels, counts, color=colors, height=0.6, edgecolor="white", linewidth=0.5)
    ax.invert_yaxis()
    ax.set_xlabel("Number of in-scope reports", fontsize=11)
    ax.set_title(
        "Report Concentration by Program\n"
        "(each bar = one bug-bounty program; top contributors highlighted)",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.set_xlim(0, max_c * 1.35)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_color(COLORS["gridline"])

    for bar, cnt, pct in zip(ax.patches, counts, pcts):
        ax.text(
            bar.get_width() + max_c * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{cnt}  ({pct:.1f}%)",
            va="center", ha="left", fontsize=ANNOT_FONTSIZE, color=COLORS["text"],
        )
    _watermark(ax)
    fig.tight_layout()
    _save_fig(fig, "fig_program_concentration", save)
    return fig


def fig_pw_family_comparison(
    family_raw: pd.DataFrame,
    family_pw: pd.DataFrame,
    save: bool = True,
) -> plt.Figure:
    """
    Grouped horizontal bar: raw count % vs program-weighted % per BOLA family.
    The visual robustness check for the concentration limitation.
    If bars align closely, findings hold regardless of program skew.
    """
    _apply_style()
    labels  = [FAMILY_SHORT.get(l, l).replace("\n", " ") for l in family_raw["family"]]
    raw_pct = family_raw["pct"].tolist()

    # pw_family uses 'weighted_count' not 'count'; pct column is shared name
    pw_pct  = family_pw["pct"].tolist()

    n       = len(labels)
    y       = np.arange(n)
    height  = 0.36

    fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, max(FIG_HEIGHT_BASE, n * 0.9 + 1.5)))
    bars_raw = ax.barh(y + height / 2, raw_pct, height=height,
                       color=COLORS["primary"], label="Raw %", edgecolor="white")
    bars_pw  = ax.barh(y - height / 2, pw_pct,  height=height,
                       color=COLORS["accent"],  label="Program-weighted %", edgecolor="white",
                       alpha=0.85)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Share of reports (%)", fontsize=11)
    ax.set_title(
        "BOLA Family: Raw vs Program-Weighted Distribution\n"
        "(convergence = finding robust to concentration bias)",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.set_xlim(0, max(raw_pct + pw_pct) * 1.35)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_color(COLORS["gridline"])

    for bar, v in zip(bars_raw, raw_pct):
        ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", ha="left",
                fontsize=ANNOT_FONTSIZE - 1, color=COLORS["primary"])
    for bar, v in zip(bars_pw, pw_pct):
        ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", ha="left",
                fontsize=ANNOT_FONTSIZE - 1, color=COLORS["accent"])

    ax.legend(loc="lower right", fontsize=9, frameon=True, framealpha=0.9)
    _watermark(ax)
    fig.tight_layout()
    _save_fig(fig, "fig_pw_family_comparison", save)
    return fig


def fig_pw_sector_comparison(
    sector_raw: pd.DataFrame,
    sector_pw: pd.DataFrame,
    save: bool = True,
) -> plt.Figure:
    """
    Grouped horizontal bar: raw % vs program-weighted % per industry sector.
    Same robustness logic as fig_pw_family_comparison.
    """
    _apply_style()
    labels  = sector_raw["sector"].tolist()
    raw_pct = sector_raw["pct"].tolist()
    pw_pct  = sector_pw["pct"].tolist()

    n      = len(labels)
    y      = np.arange(n)
    height = 0.36

    fig, ax = plt.subplots(figsize=(FIG_WIDTH_SINGLE, max(FIG_HEIGHT_BASE, n * 0.9 + 1.5)))
    bars_raw = ax.barh(y + height / 2, raw_pct, height=height,
                       color=COLORS["primary"], label="Raw %", edgecolor="white")
    bars_pw  = ax.barh(y - height / 2, pw_pct,  height=height,
                       color=COLORS["accent"],  label="Program-weighted %", edgecolor="white",
                       alpha=0.85)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Share of reports (%)", fontsize=11)
    ax.set_title(
        "Industry Sector: Raw vs Program-Weighted Distribution\n"
        "(convergence = finding robust to concentration bias)",
        fontsize=13, fontweight="bold", pad=12,
    )
    ax.set_xlim(0, max(raw_pct + pw_pct) * 1.35)
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines["left"].set_color(COLORS["gridline"])

    for bar, v in zip(bars_raw, raw_pct):
        ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", ha="left",
                fontsize=ANNOT_FONTSIZE - 1, color=COLORS["primary"])
    for bar, v in zip(bars_pw, pw_pct):
        ax.text(bar.get_width() + 0.4, bar.get_y() + bar.get_height() / 2,
                f"{v:.1f}%", va="center", ha="left",
                fontsize=ANNOT_FONTSIZE - 1, color=COLORS["accent"])

    ax.legend(loc="lower right", fontsize=9, frameon=True, framealpha=0.9)
    _watermark(ax)
    fig.tight_layout()
    _save_fig(fig, "fig_pw_sector_comparison", save)
    return fig
# ---------------------------------------------------------------------------
# Save-all convenience
# ---------------------------------------------------------------------------

def save_all(tables: dict, save: bool = True) -> dict[str, plt.Figure]:
    """
    Generate and save every figure.

    Parameters
    ----------
    tables : dict returned by analysis.run_all()
    save   : whether to write files to disk

    Returns
    -------
    dict mapping figure name → Figure object
    """
    print("Generating figures …")
    figs = {}
    figs["scope_pie"]          = fig_scope_pie(tables["scope"], save)
    figs["family_bar"]         = fig_family_bar(tables["family"], save)
    figs["action_bar"]         = fig_action_bar(tables["action"], save)
    figs["hv_bar"]             = fig_hv_bar(tables["hv"], save)
    figs["sector_bar"]         = fig_sector_bar(tables["sector"], save)
    figs["id_format_bar"]      = fig_id_format_bar(tables["id_format"], save)
    figs["severity_bar"]       = fig_severity_bar(tables["severity"], save)
    figs["temporal_bar"]       = fig_temporal_bar(tables["temporal"], save)
    figs["confidence_pie"]     = fig_confidence_pie(tables["confidence"], save)

    n_in_scope = tables["scope"].loc[tables["scope"]["label"] == "In-scope BOLA", "count"].values[0]
    figs["mechanism_bar"]       = fig_mechanism_bar(
        tables["mechanism"], int(n_in_scope), save
    )
    figs["family_sector_heatmap"]   = fig_family_sector_heatmap(tables["family_x_sector"], save)
    figs["family_severity_heatmap"] = fig_family_severity_heatmap(tables["family_x_severity"], save)
    figs["overview_dashboard"]      = fig_overview_dashboard(
        tables["family"], tables["action"], tables["hv"],
        tables["sector"], tables["severity"], tables["id_format"],
        n_in_scope=int(n_in_scope),
        n_total=int(tables["scope"]["count"].sum()),
        save=save,
    )
    figs["program_concentration"]  = fig_program_concentration(tables["program_concentration"], save)
    figs["pw_family_comparison"]   = fig_pw_family_comparison(tables["family"], tables["pw_family"], save)
    figs["pw_sector_comparison"]   = fig_pw_sector_comparison(tables["sector"], tables["pw_sector"], save)
    print(f"  → {len(figs)} figures generated.")
    for fig in figs.values():
        plt.close(fig)
    return figs