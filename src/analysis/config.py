"""
config.py
---------
Central configuration for the BOLA meta-analysis pipeline.
All brand colors, canonical label orders, path roots, and
plot style settings live here so every module stays in sync.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Repository roots
# ---------------------------------------------------------------------------
REPO_ROOT   = Path(__file__).resolve().parents[1]
DATA_DIR    = REPO_ROOT / "data"
OUT_DIR     = REPO_ROOT / "outputs"
FIG_DIR     = OUT_DIR  / "figures"
TABLE_DIR   = OUT_DIR  / "tables"

DEFAULT_DATA_FILE = DATA_DIR / "classified_manually_verified.json"

# ---------------------------------------------------------------------------
# Brand palette  (primary #025C7A + complementary blue/teal/green tones)
# ---------------------------------------------------------------------------
COLORS = {
    "primary":   "#025C7A",   # deep teal
    "c2":        "#0A7EA4",   # mid-blue
    "c3":        "#1FA8C7",   # sky teal
    "c4":        "#4DC4D8",   # light teal
    "c5":        "#2E9E6E",   # green
    "c6":        "#66BB9A",   # mint
    "c7":        "#A8D8C8",   # pale mint
    "neutral":   "#E8F4F7",   # very light teal (backgrounds)
    "accent":    "#F47B20",   # warm orange for highlights/callouts
    "text":      "#1A2E35",   # near-black
    "gridline":  "#D0E5EC",   # muted teal grid
}

# Ordered palette list for sequential use in bar charts etc.
PALETTE = [
    COLORS["primary"], COLORS["c2"], COLORS["c3"], COLORS["c4"],
    COLORS["c5"],      COLORS["c6"], COLORS["c7"],
]

# ---------------------------------------------------------------------------
# Canonical label ordering for every categorical dimension
# ---------------------------------------------------------------------------
FAMILY_ORDER = [
    "Direct Object Reference BOLA",
    "Action-Level Object BOLA",
    "Tenant Isolation BOLA",
    "Workflow-Context BOLA",
    "Chained Disclosure BOLA",
    "Object Rebinding BOLA",
]

FAMILY_SHORT = {
    "Direct Object Reference BOLA": "Direct Object\nReference",
    "Action-Level Object BOLA":     "Action-Level\nObject",
    "Tenant Isolation BOLA":        "Tenant\nIsolation",
    "Workflow-Context BOLA":        "Workflow-\nContext",
    "Chained Disclosure BOLA":      "Chained\nDisclosure",
    "Object Rebinding BOLA":        "Object\nRebinding",
}

ACTION_ORDER     = ["Read", "Modify", "Delete", "Trigger", "Enumerate", "Unclear"]
HV_ORDER         = ["Horizontal", "Vertical", "Unclear"]
SEVERITY_ORDER   = ["critical", "high", "medium", "low", "None"]
SEVERITY_LABELS  = {"critical": "Critical", "high": "High",
                    "medium": "Medium",   "low": "Low", "None": "N/A"}

SECTOR_ORDER = [
    "SaaS & Productivity",
    "Social & Consumer Platforms",
    "E-commerce & Marketplace",
    "Government & Public Sector",
    "Enterprise & Infrastructure",
    "Fintech & Financial Services",
]

ID_FORMAT_ORDER = [
    "sequential_int", "unclear", "encoded_id",
    "username", "email", "uuid", "hash",
]
ID_FORMAT_LABELS = {
    "sequential_int": "Sequential integer",
    "unclear":        "Unclear / not specified",
    "encoded_id":     "Encoded ID (GraphQL GID, base64)",
    "username":       "Username",
    "email":          "Email",
    "uuid":           "UUID",
    "hash":           "Hash",
}

CONFIDENCE_ORDER = ["High", "Medium", "Low"]

YEAR_ORDER = ["2023", "2024", "2025", "2026"]

# ---------------------------------------------------------------------------
# Matplotlib / figure defaults
# ---------------------------------------------------------------------------
MPL_RC = {
    "figure.facecolor":       "white",
    "axes.facecolor":         "white",
    "axes.edgecolor":         COLORS["text"],
    "axes.labelcolor":        COLORS["text"],
    "axes.titlesize":         13,
    "axes.titleweight":       "bold",
    "axes.labelsize":         11,
    "axes.grid":              True,
    "axes.grid.axis":         "x",
    "grid.color":             COLORS["gridline"],
    "grid.linewidth":         0.7,
    "xtick.color":            COLORS["text"],
    "ytick.color":            COLORS["text"],
    "xtick.labelsize":        9,
    "ytick.labelsize":        9,
    "font.family":            "DejaVu Sans",
    "text.color":             COLORS["text"],
    "figure.dpi":             150,
    "savefig.dpi":            300,
    "savefig.bbox":           "tight",
    "savefig.facecolor":      "white",
}

FIG_WIDTH_SINGLE = 8    # inches, single-panel figure
FIG_WIDTH_DOUBLE = 14   # inches, side-by-side panels
FIG_HEIGHT_BASE  = 5    # default height

# Bar annotation font size
ANNOT_FONTSIZE = 9