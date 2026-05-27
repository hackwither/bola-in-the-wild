"""
loader.py
---------
Loads, validates, and normalises the BOLA classification JSON into two
clean DataFrames:
    df_all   – all 107 rows (in-scope + out-of-scope)
    df       – 84 confirmed in-scope BOLA rows only

Normalisation applied:
  * severity / horizontal_vertical lowercased and stripped
  * year_disclosed cast to nullable Int64
  * exploit_mechanisms kept as Python lists (one row per mechanism in
    df_mechs, which is also returned for convenience)
  * bola_family == "Unclassified" always maps to bola_in_scope == False

Raises clear errors if expected columns are missing so the pipeline
fails loudly on schema drift rather than silently producing wrong tables.
"""

import json
import sys
from pathlib import Path

import pandas as pd

# Allow running this file directly from repo root
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DEFAULT_DATA_FILE, FAMILY_ORDER


# ---------------------------------------------------------------------------
# Required columns (subset that the analysis actively uses)
# ---------------------------------------------------------------------------
REQUIRED_COLS = {
    "report_id", "program_name", "severity", "industry_sector",
    "http_method", "id_format", "year_disclosed", "bola_family",
    "bola_in_scope", "horizontal_vertical", "action_type",
    "exploit_mechanisms", "confidence",
}


def load(path: Path | str = DEFAULT_DATA_FILE) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Load and normalise the JSON classification file.

    Parameters
    ----------
    path : path-like
        Path to the JSON export (list of report objects).

    Returns
    -------
    df_all   : DataFrame – all records including Unclassified
    df       : DataFrame – confirmed in-scope BOLA only
    df_mechs : DataFrame – one row per (report_id, mechanism) for in-scope reports
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(
            f"Dataset not found at {path}.\n"
            "Place classified_manually_verified.json in data/ or pass an explicit path."
        )

    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)

    if not isinstance(raw, list):
        raise ValueError("Expected a JSON array at the top level.")

    df_all = pd.DataFrame(raw)

    # ------------------------------------------------------------------
    # Schema check
    # ------------------------------------------------------------------
    missing = REQUIRED_COLS - set(df_all.columns)
    if missing:
        raise ValueError(
            f"Missing expected columns in dataset: {sorted(missing)}\n"
            f"Found: {sorted(df_all.columns)}"
        )

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------
    # Strings: strip whitespace, normalise case where appropriate
    df_all["severity"] = df_all["severity"].apply(
        lambda x: "N/A" if (x is None or (isinstance(x, float) and pd.isna(x)) or str(x).strip().lower() in ("none", "null", "nan", ""))
        else str(x).strip().lower()
    )    
    df_all["horizontal_vertical"] = df_all["horizontal_vertical"].fillna("Unclear").astype(str).str.strip().str.capitalize()
    df_all["action_type"]         = df_all["action_type"].fillna("Unclear").astype(str).str.strip()
    df_all["id_format"]           = df_all["id_format"].fillna("unclear").astype(str).str.strip()
    df_all["confidence"]          = df_all["confidence"].fillna("Low").astype(str).str.strip()
    df_all["bola_family"]         = df_all["bola_family"].fillna("Unclassified").astype(str).str.strip()
    df_all["industry_sector"]     = df_all["industry_sector"].fillna("Unknown").astype(str).str.strip()
    df_all["program_name"]        = df_all["program_name"].fillna("Unknown").astype(str).str.strip()

    # Coerce year to nullable integer
    df_all["year_disclosed"] = pd.to_numeric(df_all["year_disclosed"], errors="coerce").astype("Int64")

    # Ensure bola_in_scope is boolean; Unclassified family always → False
    df_all["bola_in_scope"] = df_all["bola_in_scope"].fillna(False).astype(bool)
    df_all.loc[df_all["bola_family"] == "Unclassified", "bola_in_scope"] = False

    # exploit_mechanisms: ensure it's always a list
    df_all["exploit_mechanisms"] = df_all["exploit_mechanisms"].apply(
        lambda x: x if isinstance(x, list) else []
    )

    # ------------------------------------------------------------------
    # In-scope subset
    # ------------------------------------------------------------------
    df = df_all[df_all["bola_in_scope"]].copy().reset_index(drop=True)

    # ------------------------------------------------------------------
    # Mechanism explode table (for frequency analysis)
    # ------------------------------------------------------------------
    mech_rows = []
    for _, row in df.iterrows():
        for mech in row["exploit_mechanisms"]:
            mech_rows.append({"report_id": row["report_id"], "mechanism": mech})
    df_mechs = pd.DataFrame(mech_rows) if mech_rows else pd.DataFrame(columns=["report_id", "mechanism"])

    return df_all, df, df_mechs


def dataset_summary(df_all: pd.DataFrame, df: pd.DataFrame) -> dict:
    """Return a plain-dict summary of dataset composition for printing."""
    return {
        "total_classified":  len(df_all),
        "in_scope":          int(df_all["bola_in_scope"].sum()),
        "out_of_scope":      int((~df_all["bola_in_scope"]).sum()),
        "in_scope_pct":      round(df_all["bola_in_scope"].mean() * 100, 1),
        "confidence_high":   int((df["confidence"] == "High").sum()),
        "confidence_medium": int((df["confidence"] == "Medium").sum()),
        "confidence_low":    int((df["confidence"] == "Low").sum()),
        "unique_programs":   df_all["program_name"].nunique(),
        "unique_sectors":    df_all["industry_sector"].nunique(),
        "years_with_data":   sorted(df["year_disclosed"].dropna().astype(int).unique().tolist()),
    }