"""
analysis.py
-----------
Pure-computation module.  Every function takes a DataFrame, returns a
clean summary DataFrame, and (optionally) saves a CSV to TABLE_DIR.

No plotting happens here – that lives in figures.py.

Functions
---------
scope_distribution        – in-scope vs out-of-scope counts
family_distribution        – taxonomy family counts & %
action_distribution        – action type counts & %
hv_distribution            – horizontal vs vertical counts & %
sector_distribution        – industry sector counts & %
id_format_distribution     – identifier format counts & %
mechanism_distribution     – exploit mechanism frequency
severity_distribution      – severity counts & %
temporal_distribution      – disclosure year counts
confidence_distribution    – confidence level counts & %
family_x_sector_crosstab   – family × sector cross-tabulation (raw counts)
family_x_severity_crosstab – family × severity cross-tabulation
run_all                    – runs every function and returns a dict of frames
"""

from __future__ import annotations
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import (
    TABLE_DIR, FAMILY_ORDER, ACTION_ORDER, HV_ORDER,
    SEVERITY_ORDER, SECTOR_ORDER, ID_FORMAT_ORDER,
    CONFIDENCE_ORDER, YEAR_ORDER,
    ID_FORMAT_LABELS, SEVERITY_LABELS, FAMILY_SHORT,
)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ordered_counts(
    series: pd.Series,
    order: list[str],
    label_map: dict[str, str] | None = None,
    total_col: str = "n_in_scope",
) -> pd.DataFrame:
    """
    Count occurrences of each value in `series`, enforce `order`,
    fill missing with 0, compute percentage.
    """
    counts = series.value_counts()
    out = (
        pd.DataFrame({"value": order})
        .assign(count=lambda d: d["value"].map(counts).fillna(0).astype(int))
    )
    total = out["count"].sum()
    out["pct"] = (out["count"] / total * 100).round(1)
    if label_map:
        out["label"] = out["value"].map(label_map).fillna(out["value"])
    else:
        out["label"] = out["value"]
    return out[["label", "count", "pct"]].reset_index(drop=True)


def _save_csv(df: pd.DataFrame, name: str, save: bool) -> None:
    if save:
        TABLE_DIR.mkdir(parents=True, exist_ok=True)
        out = TABLE_DIR / f"{name}.csv"
        df.to_csv(out, index=False)
        print(f"  [saved] {out.relative_to(TABLE_DIR.parent.parent)}")


# ---------------------------------------------------------------------------
# Public analysis functions
# ---------------------------------------------------------------------------

def scope_distribution(df_all: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """In-scope vs out-of-scope breakdown."""
    total = len(df_all)
    in_s  = int(df_all["bola_in_scope"].sum())
    out_s = total - in_s
    result = pd.DataFrame({
        "label":  ["In-scope BOLA", "Unclassified / Out-of-scope"],
        "count":  [in_s, out_s],
        "pct":    [round(in_s / total * 100, 1), round(out_s / total * 100, 1)],
    })
    _save_csv(result, "scope_distribution", save)
    return result


def family_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """BOLA taxonomy family counts (in-scope reports only)."""
    result = _ordered_counts(df["bola_family"], FAMILY_ORDER)
    result.rename(columns={"label": "family"}, inplace=True)
    _save_csv(result, "family_distribution", save)
    return result


def action_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """Action type counts (in-scope)."""
    result = _ordered_counts(df["action_type"], ACTION_ORDER)
    result.rename(columns={"label": "action_type"}, inplace=True)
    _save_csv(result, "action_distribution", save)
    return result


def hv_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """Horizontal vs vertical authorization failure direction (in-scope)."""
    # Normalise the 'unclear' / 'Unclear' inconsistency
    hv = df["horizontal_vertical"].str.strip().str.capitalize()
    result = _ordered_counts(hv, HV_ORDER)
    result.rename(columns={"label": "direction"}, inplace=True)
    _save_csv(result, "hv_distribution", save)
    return result


def sector_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """Industry sector counts (in-scope)."""
    result = _ordered_counts(df["industry_sector"], SECTOR_ORDER)
    result.rename(columns={"label": "sector"}, inplace=True)
    _save_csv(result, "sector_distribution", save)
    return result


def id_format_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """Identifier format counts (in-scope)."""
    result = _ordered_counts(df["id_format"], ID_FORMAT_ORDER, ID_FORMAT_LABELS)
    result.rename(columns={"label": "id_format"}, inplace=True)
    _save_csv(result, "id_format_distribution", save)
    return result


def mechanism_distribution(df_mechs: pd.DataFrame, n_in_scope: int, save: bool = True) -> pd.DataFrame:
    """
    Exploit mechanism frequency.

    Because one report can have multiple mechanisms, counts are over
    distinct report_id occurrences per mechanism, and `pct_of_reports`
    expresses mechanism prevalence as a share of in-scope reports.
    """
    if df_mechs.empty:
        result = pd.DataFrame(columns=["mechanism", "count", "pct_of_reports"])
        _save_csv(result, "mechanism_distribution", save)
        return result

    counts = (
        df_mechs.groupby("mechanism")["report_id"]
        .nunique()
        .reset_index()
        .rename(columns={"report_id": "count"})
        .sort_values("count", ascending=False)
    )
    counts["pct_of_reports"] = (counts["count"] / n_in_scope * 100).round(1)
    counts = counts.reset_index(drop=True)
    _save_csv(counts, "mechanism_distribution", save)
    return counts


def severity_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    severity = df["severity"].fillna("N/A")

    result = _ordered_counts(
        severity,
        SEVERITY_ORDER,
        SEVERITY_LABELS
    )

    result.rename(columns={"label": "severity"}, inplace=True)

    _save_csv(result, "severity_distribution", save)

    return result


def temporal_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """Disclosure year counts for reports with a known year (in-scope)."""
    known = df["year_disclosed"].dropna().astype(int).astype(str)
    result = _ordered_counts(known, YEAR_ORDER)
    result.rename(columns={"label": "year"}, inplace=True)
    result["n_redacted"] = int(df["year_disclosed"].isna().sum())
    _save_csv(result, "temporal_distribution", save)
    return result


def confidence_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """Confidence level breakdown (in-scope)."""
    result = _ordered_counts(df["confidence"], CONFIDENCE_ORDER)
    result.rename(columns={"label": "confidence"}, inplace=True)
    _save_csv(result, "confidence_distribution", save)
    return result


def family_x_sector_crosstab(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """
    Cross-tabulation: BOLA family (rows) × industry sector (columns).
    Returns raw counts.  Missing combinations are 0.
    """
    ct = (
        pd.crosstab(df["bola_family"], df["industry_sector"])
        .reindex(index=FAMILY_ORDER, columns=SECTOR_ORDER, fill_value=0)
    )
    # Short column labels for readability
    ct.columns = [c.split(" &")[0] for c in ct.columns]
    ct.index   = [FAMILY_SHORT.get(i, i).replace("\n", " ") for i in ct.index]
    ct.index.name   = "BOLA Family"
    ct.columns.name = "Sector"
    # Add row totals
    ct["Total"] = ct.sum(axis=1)
    _save_csv(ct.reset_index(), "family_x_sector_crosstab", save)
    return ct


def family_x_severity_crosstab(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """
    Cross-tabulation: BOLA family (rows) × severity (columns).
    Returns raw counts.
    """
    # 1. Clean data slice against all text-string and object null variations
    null_variants = ["null", "None", "nan", "NaN", "", "unrated", "N/A", None]
    df_clean = df.copy()
    df_clean["severity"] = df_clean["severity"].astype(str).str.strip().replace(null_variants, "N/A")
    df_clean["severity"] = df_clean["severity"].fillna("N/A")
    
    # 2. Handle case-sensitivity matching dynamically
    local_order = list(SEVERITY_ORDER) if hasattr(SEVERITY_ORDER, "__iter__") else SEVERITY_ORDER.copy()
    is_lowercase = len(local_order) > 0 and local_order[0].islower()
    na_key = "na" if is_lowercase else "N/A"
    
    if na_key not in local_order:
        local_order.append(na_key)
        
    if is_lowercase:
        df_clean["severity"] = df_clean["severity"].replace({"N/A": "na"})
        
    # 3. Isolate present categories and generate the cross-tabulation matrix
    sev_order_present = [s for s in local_order if s in df_clean["severity"].unique()]
    
    ct = (
        pd.crosstab(df_clean["bola_family"], df_clean["severity"])
        .reindex(index=FAMILY_ORDER, columns=sev_order_present, fill_value=0)
    )
    
    # 4. Standardize output formatting structures for figures.py
    ct.columns = [SEVERITY_LABELS.get(c, "N/A" if c == na_key else c) for c in ct.columns]
    ct.index   = [FAMILY_SHORT.get(i, i).replace("\n", " ") for i in ct.index]
    ct.index.name   = "BOLA Family"
    ct.columns.name = "Severity"
    ct["Total"] = ct.sum(axis=1)
    _save_csv(ct.reset_index(), "family_x_severity_crosstab", save)
    return ct

# ---------------------------------------------------------------------------
# Program-weighted analysis  (addresses single-program concentration bias)
# ---------------------------------------------------------------------------

def _program_weights(df: pd.DataFrame) -> pd.Series:
    """
    Per-report weight = 1 / (reports from that program in this slice).
    Each program therefore contributes a total weight of 1.0 regardless
    of how many reports it has, neutralising concentration bias.
    """
    counts = df["program_name"].map(df["program_name"].value_counts())
    return (1.0 / counts).rename("weight")


def program_concentration(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """
    Raw report counts per program, share of dataset, and the weight
    each program would carry in a program-weighted analysis.
    Useful for quantifying the limitation directly in the paper.
    """
    counts = (
        df["program_name"]
        .value_counts()
        .reset_index()
        .rename(columns={"program_name": "program", "count": "n_reports"})
    )
    total = counts["n_reports"].sum()
    counts["pct_of_dataset"] = (counts["n_reports"] / total * 100).round(1)
    counts["program_weight"] = (1.0 / counts["n_reports"]).round(4)
    counts = counts.sort_values("n_reports", ascending=False).reset_index(drop=True)
    _save_csv(counts, "program_concentration", save)
    return counts


def _weighted_counts(
    df: pd.DataFrame,
    col: str,
    order: list[str],
    label_map: dict[str, str] | None = None,
) -> pd.DataFrame:
    """
    Compute program-weighted distribution for a single categorical column.

    Steps
    -----
    1. Attach per-report weights (1 / program report count).
    2. Sum weights per category  →  each program contributes weight 1.0 total.
    3. Normalise to percentages.
    4. Enforce `order`, fill missing categories with 0.
    """
    weights = _program_weights(df)
    weighted = (
        df.assign(weight=weights)
        .groupby(col)["weight"]
        .sum()
        .reindex(order, fill_value=0.0)
        .reset_index()
        .rename(columns={col: "value", "weight": "weighted_count"})
    )
    total_weight = weighted["weighted_count"].sum()
    weighted["pct"] = (weighted["weighted_count"] / total_weight * 100).round(1)
    weighted["label"] = (
        weighted["value"].map(label_map) if label_map
        else weighted["value"]
    ).fillna(weighted["value"])
    return weighted[["label", "weighted_count", "pct"]].reset_index(drop=True)


def program_weighted_family_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """
    BOLA family distribution re-weighted so every program contributes equally.
    Compare against `family_distribution` to assess concentration bias.
    """
    result = _weighted_counts(df, "bola_family", FAMILY_ORDER)
    result.rename(columns={"label": "family"}, inplace=True)
    _save_csv(result, "pw_family_distribution", save)
    return result


def program_weighted_sector_distribution(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """
    Industry sector distribution re-weighted so every program contributes equally.
    """
    result = _weighted_counts(df, "industry_sector", SECTOR_ORDER)
    result.rename(columns={"label": "sector"}, inplace=True)
    _save_csv(result, "pw_sector_distribution", save)
    return result


def program_weighted_family_x_sector_crosstab(df: pd.DataFrame, save: bool = True) -> pd.DataFrame:
    """
    Family × sector cross-tab using program weights instead of raw counts.
    Each cell is the sum of weights for reports in that (family, sector) cell,
    so a program with 13 reports in one cell counts the same as one with 1.
    """
    weights = _program_weights(df)
    ct = (
        df.assign(weight=weights)
        .pivot_table(
            index="bola_family",
            columns="industry_sector",
            values="weight",
            aggfunc="sum",
            fill_value=0.0,
        )
        .reindex(index=FAMILY_ORDER, columns=SECTOR_ORDER, fill_value=0.0)
    )
    ct = ct.round(3)
    ct.columns = [c.split(" &")[0] for c in ct.columns]
    ct.index   = [FAMILY_SHORT.get(i, i).replace("\n", " ") for i in ct.index]
    ct.index.name   = "BOLA Family"
    ct.columns.name = "Sector"
    ct["Total"] = ct.sum(axis=1).round(3)
    _save_csv(ct.reset_index(), "pw_family_x_sector_crosstab", save)
    return ct

# ---------------------------------------------------------------------------
# Convenience: run everything at once
# ---------------------------------------------------------------------------

def run_all(
    df_all: pd.DataFrame,
    df: pd.DataFrame,
    df_mechs: pd.DataFrame,
    save: bool = True,
) -> dict[str, pd.DataFrame]:
    """
    Compute every distribution table and return them in a named dict.

    Parameters
    ----------
    df_all   : full classified dataset (all rows)
    df       : in-scope rows only
    df_mechs : exploded mechanism table (from loader.load())
    save     : whether to write CSV files to outputs/tables/

    Returns
    -------
    dict mapping table name → DataFrame
    """
    print("Computing distributions …")
    tables = {}
    tables["scope"]               = scope_distribution(df_all, save)
    tables["family"]              = family_distribution(df, save)
    tables["action"]              = action_distribution(df, save)
    tables["hv"]                  = hv_distribution(df, save)
    tables["sector"]              = sector_distribution(df, save)
    tables["id_format"]           = id_format_distribution(df, save)
    tables["mechanism"]           = mechanism_distribution(df_mechs, len(df), save)
    tables["severity"]            = severity_distribution(df, save)
    tables["temporal"]            = temporal_distribution(df, save)
    tables["confidence"]          = confidence_distribution(df, save)
    tables["family_x_sector"]     = family_x_sector_crosstab(df, save)
    tables["family_x_severity"]   = family_x_severity_crosstab(df, save)
    tables["program_concentration"]      = program_concentration(df, save)
    tables["pw_family"]                  = program_weighted_family_distribution(df, save)
    tables["pw_sector"]                  = program_weighted_sector_distribution(df, save)
    tables["pw_family_x_sector"]         = program_weighted_family_x_sector_crosstab(df, save)
    print(f"  → {len(tables)} tables computed, {sum(1 for _ in TABLE_DIR.glob('*.csv'))} CSVs saved.")
    return tables