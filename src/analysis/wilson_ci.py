"""
wilson_ci.py
------------
Computes Wilson score confidence intervals for every key proportion
reported in the paper. Zero external dependencies beyond pandas and
whatever loader.py already needs.

Outputs
-------
  <out_dir>/<dimension>.csv   – one file per dimension
  Console summary             – formatted tables for all dimensions

Usage
-----
    python wilson_ci.py
    python wilson_ci.py --out results/wilson_cis/
    python wilson_ci.py --alpha 0.05          # default → 95% CIs
    python wilson_ci.py --no-save             # print only
    python wilson_ci.py --data path/to/file.json
"""

import argparse
import math
from pathlib import Path

import pandas as pd

from loader import load


# ───────────────────────────────────────────────────────────────────────────
# Wilson CI core – no external dependencies
# ───────────────────────────────────────────────────────────────────────────

def _norm_ppf(p: float) -> float:
    """
    Inverse standard-normal CDF for p in (0.5, 1) via the rational
    approximation in Abramowitz & Stegun §26.2.17.
    Error < 4.5 × 10⁻⁴, which is more than adequate for CI display.
    Verified: _norm_ppf(0.975) ≈ 1.9603  (exact 1.9600).
    """
    t   = math.sqrt(-2.0 * math.log(1.0 - p))
    num = 2.515517 + 0.802853 * t + 0.010328 * t ** 2
    den = 1.0 + 1.432788 * t + 0.189269 * t ** 2 + 0.001308 * t ** 3
    return t - num / den


def wilson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """
    Wilson score interval for a proportion k / n.

    Parameters
    ----------
    k     : number of successes (int ≥ 0)
    n     : number of trials   (int > 0)
    alpha : significance level  (float, default 0.05 → 95% CI)

    Returns
    -------
    (lower, upper) as floats in [0, 1].
    Returns (nan, nan) when n == 0.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    z  = _norm_ppf(1.0 - alpha / 2.0)
    z2 = z * z
    n_tilde = n + z2
    p_tilde = (k + z2 / 2.0) / n_tilde
    margin  = z * math.sqrt(p_tilde * (1.0 - p_tilde) / n_tilde)
    return (max(0.0, p_tilde - margin), min(1.0, p_tilde + margin))


# ───────────────────────────────────────────────────────────────────────────
# Table builder
# ───────────────────────────────────────────────────────────────────────────

def ci_table(
    counts: pd.Series,
    N: int,
    category_col: str = "category",
    alpha: float = 0.05,
) -> pd.DataFrame:
    """
    Build a proportion + Wilson CI DataFrame from a counts Series.

    Parameters
    ----------
    counts       : {category_label: count}  (pd.Series)
    N            : total / denominator for each proportion
    category_col : name of the first column in the output
    alpha        : significance level

    Returns
    -------
    DataFrame – columns: <category_col> | n | pct | ci_lower | ci_upper | ci_str
    Sorted descending by n.

    Notes
    -----
    pct / ci_lower / ci_upper are in percentage points (0–100), not [0, 1].
    ci_str is a ready-to-paste string, e.g. "[31.5%, 52.5%]".
    """
    rows = []
    for cat, k in counts.items():
        lo, hi = wilson_ci(int(k), N, alpha)
        rows.append({
            category_col: cat,
            "n":          int(k),
            "pct":        round(k / N * 100, 1),
            "ci_lower":   round(lo * 100, 1),
            "ci_upper":   round(hi * 100, 1),
            "ci_str":     f"[{lo * 100:.1f}%, {hi * 100:.1f}%]",
        })
    return (
        pd.DataFrame(rows)
        .sort_values("n", ascending=False)
        .reset_index(drop=True)
    )


# ───────────────────────────────────────────────────────────────────────────
# Per-dimension table functions
# ───────────────────────────────────────────────────────────────────────────

def tbl_label_noise(df_all: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """In-scope vs Unclassified out of all 107 classified reports."""
    counts = pd.Series({
        "In-scope BOLA": int(df_all["bola_in_scope"].sum()),
        "Unclassified":  int((~df_all["bola_in_scope"]).sum()),
    })
    return ci_table(counts, N=len(df_all), category_col="classification", alpha=alpha)


def tbl_family(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """BOLA family distribution (n = 84 in-scope)."""
    return ci_table(
        df["bola_family"].value_counts(),
        N=len(df),
        category_col="bola_family",
        alpha=alpha,
    )


def tbl_action_type(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Action type distribution."""
    return ci_table(
        df["action_type"].value_counts(),
        N=len(df),
        category_col="action_type",
        alpha=alpha,
    )


def tbl_auth_direction(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Horizontal vs Vertical vs Unclear."""
    return ci_table(
        df["horizontal_vertical"].value_counts(),
        N=len(df),
        category_col="direction",
        alpha=alpha,
    )


def tbl_severity(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Severity in canonical order (critical → none)."""
    order = ["critical", "high", "medium", "low", "none"]
    raw   = df["severity"].str.lower().value_counts()
    # Reindex to canonical order; drop any values not in order (shouldn't exist)
    counts = raw.reindex([s for s in order if s in raw.index], fill_value=0)
    return ci_table(counts, N=len(df), category_col="severity", alpha=alpha)


def tbl_industry(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Industry sector distribution."""
    return ci_table(
        df["industry_sector"].value_counts(),
        N=len(df),
        category_col="industry_sector",
        alpha=alpha,
    )


def tbl_id_format(df: pd.DataFrame, alpha: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns two tables:
      (a) all_formats  – denominator = n (including 'unclear')
      (b) known_formats – denominator = known-format subset only

    The known-format table matches the paper's "55.4% of known-format cases"
    framing rather than the "36.9% of n=84" framing.
    """
    all_counts   = df["id_format"].value_counts()
    tbl_all      = ci_table(all_counts, N=len(df), category_col="id_format", alpha=alpha)

    known        = df[df["id_format"].str.lower() != "unclear"]
    known_counts = known["id_format"].value_counts()
    tbl_known    = ci_table(known_counts, N=len(known), category_col="id_format", alpha=alpha)

    return tbl_all, tbl_known


def tbl_mechanisms(df_mechs: pd.DataFrame, n_reports: int, alpha: float) -> pd.DataFrame:
    """
    Each mechanism's proportion is:
        k reports mentioning that mechanism / n_reports total

    Proportions are NOT mutually exclusive and do not sum to 100%.
    The denominator is always n_reports (= 84 in-scope reports).
    """
    if df_mechs.empty:
        return pd.DataFrame(
            columns=["mechanism", "n", "pct", "ci_lower", "ci_upper", "ci_str"]
        )
    counts = df_mechs["mechanism"].value_counts()
    return ci_table(counts, N=n_reports, category_col="mechanism", alpha=alpha)


def tbl_confidence(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """Classifier confidence distribution (High / Medium / Low)."""
    order  = ["High", "Medium", "Low"]
    raw    = df["confidence"].value_counts()
    counts = raw.reindex([c for c in order if c in raw.index], fill_value=0)
    return ci_table(counts, N=len(df), category_col="confidence", alpha=alpha)


# ───────────────────────────────────────────────────────────────────────────
# Vertical-only sub-table (for the 11.9% claim)
# ───────────────────────────────────────────────────────────────────────────

def tbl_vertical_rate(df: pd.DataFrame, alpha: float) -> pd.DataFrame:
    """
    Single-row table: vertical escalation rate out of all in-scope reports.
    Useful for the '11.9% of confirmed cases are vertical' claim.
    """
    k = int((df["horizontal_vertical"].str.lower() == "vertical").sum())
    lo, hi = wilson_ci(k, len(df), alpha)
    return pd.DataFrame([{
        "category": "Vertical escalation",
        "n":        k,
        "N":        len(df),
        "pct":      round(k / len(df) * 100, 1),
        "ci_lower": round(lo * 100, 1),
        "ci_upper": round(hi * 100, 1),
        "ci_str":   f"[{lo * 100:.1f}%, {hi * 100:.1f}%]",
    }])


# ───────────────────────────────────────────────────────────────────────────
# Console output helper
# ───────────────────────────────────────────────────────────────────────────

def _print_section(title: str, tbl: pd.DataFrame, note: str = "") -> None:
    sep = "─" * 72
    print(f"\n{sep}")
    print(f"  {title}")
    if note:
        print(f"  ⚠  {note}")
    print(sep)
    print(tbl.to_string(index=False))


# ───────────────────────────────────────────────────────────────────────────
# Main
# ───────────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compute Wilson CIs for all key proportions in the BOLA paper."
    )
    parser.add_argument(
        "--data",    default=None,
        help="Path to classified JSON dataset (default: config.DEFAULT_DATA_FILE)",
    )
    parser.add_argument(
        "--out",     default="results/wilson_cis",
        help="Output directory for CSVs (default: results/wilson_cis/)",
    )
    parser.add_argument(
        "--alpha",   default=0.05, type=float,
        help="Significance level; 0.05 → 95%% CIs (default: 0.05)",
    )
    parser.add_argument(
        "--no-save", action="store_true",
        help="Print tables to console only; do not write CSVs",
    )
    args = parser.parse_args()

    # ── Load ──────────────────────────────────────────────────────────────
    load_kwargs = {"path": args.data} if args.data else {}
    df_all, df, df_mechs = load(**load_kwargs)

    N_all   = len(df_all)   # 107
    N       = len(df)       # 84
    ci_pct  = int(round((1.0 - args.alpha) * 100))

    print(f"\n{'═' * 72}")
    print(f"  Wilson {ci_pct}% Confidence Intervals — BOLA paper proportions")
    print(f"{'═' * 72}")
    print(f"  Total classified  : {N_all}")
    print(f"  In-scope BOLA     : {N}")
    print(f"  Alpha             : {args.alpha}  →  {ci_pct}% CIs")

    tables: dict[str, pd.DataFrame] = {}

    # 1. Label noise
    tables["label_noise"] = tbl_label_noise(df_all, args.alpha)
    _print_section(
        f"Label Noise  (N = {N_all} classified reports)",
        tables["label_noise"],
    )

    # 2. Family distribution  ← the headline finding
    tables["family"] = tbl_family(df, args.alpha)
    _print_section(
        f"BOLA Family Distribution  (N = {N} in-scope reports)",
        tables["family"],
        note="Action-Level vs Direct Object CI overlap signals co-dominance; "
             "see robustness analysis.",
    )

    # 3. Action type
    tables["action_type"] = tbl_action_type(df, args.alpha)
    _print_section(f"Action Type  (N = {N})", tables["action_type"])

    # 4. Authorization direction
    tables["auth_direction"] = tbl_auth_direction(df, args.alpha)
    _print_section(f"Authorization Direction  (N = {N})", tables["auth_direction"])

    # 5. Vertical escalation rate (single-row summary for the 11.9% claim)
    tables["vertical_rate"] = tbl_vertical_rate(df, args.alpha)
    _print_section(
        f"Vertical Escalation Rate  (N = {N})",
        tables["vertical_rate"],
    )

    # 6. Severity
    tables["severity"] = tbl_severity(df, args.alpha)
    _print_section(f"Severity  (N = {N})", tables["severity"])

    # 7. Industry sector
    tables["industry"] = tbl_industry(df, args.alpha)
    _print_section(f"Industry Sector  (N = {N})", tables["industry"])

    # 8. Identifier format – two denominators
    fmt_all, fmt_known = tbl_id_format(df, args.alpha)
    tables["id_format_all"]   = fmt_all
    tables["id_format_known"] = fmt_known
    n_known = int(fmt_known["n"].sum())
    _print_section(
        f"Identifier Format — all reports  (N = {N})",
        fmt_all,
        note="'unclear' = insufficient report detail to determine format",
    )
    _print_section(
        f"Identifier Format — known-format subset  (N = {n_known})",
        fmt_known,
        note="proportions here match the paper's 'of known-format cases' framing",
    )

    # 9. Exploit mechanisms  (non-exclusive proportions)
    tables["mechanisms"] = tbl_mechanisms(df_mechs, N, args.alpha)
    _print_section(
        f"Exploit Mechanisms  (N = {N} reports; non-exclusive)",
        tables["mechanisms"],
        note="proportions do NOT sum to 100%; each is k_reports / {N}".format(N=N),
    )

    # 10. Classifier confidence
    tables["confidence"] = tbl_confidence(df, args.alpha)
    _print_section(f"Classifier Confidence  (N = {N})", tables["confidence"])

    print(f"\n{'═' * 72}\n")

    # ── Save CSVs ─────────────────────────────────────────────────────────
    if not args.no_save:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, tbl in tables.items():
            dest = out_dir / f"{name}.csv"
            tbl.to_csv(dest, index=False)
            print(f"  saved → {dest}")
        print(f"\nAll tables written to  {out_dir}/\n")


if __name__ == "__main__":
    main()