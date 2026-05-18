"""
02_fetch_eligible_reports.py
----------------------------
Reads candidates_filtered.csv, filters to eligible=true rows, fetches the
fullest possible content for each report, and writes a single
combined_reports.json ready to pass directly to the classifier.

Fetch strategy (in priority order per report):
  1. GET /reports/{id}.json  — returns structured JSON including full
     vulnerability_information when the report is publicly disclosed.
     Requires a valid session cookie (same as Phase 1 in 01_fetch_candidates.py).
  2. HTML og:description fallback — if the .json endpoint returns no
     vulnerability_information (redacted or auth-gated), falls back to
     scraping the og:description meta tag from the report HTML page,
     identical to the enrichment phase in 01_fetch_candidates.py.

Output schema per report (classifier-ready):
  {
    "report_id":            "string",
    "source_url":           "string",
    "program_name":         "string",
    "severity":             "string | null",
    "weakness_name":        "string | null",
    "disclosed_at":         "string | null",
    "title":                "string",
    "vulnerability_info":   "string | null",   ← primary classification input
    "fetch_method":         "json_api | html_fallback | not_found"
  }

Resumable: skips report_ids already present in combined_reports.json.
1.5-second delay between every outbound request.
"""

import csv
import json
import os
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths  (adjust BASE_DIR if your layout differs)
# ---------------------------------------------------------------------------
BASE_DIR      = Path(__file__).resolve().parent.parent
ENV_FILE      = BASE_DIR / ".env"
FILTERED_CSV  = BASE_DIR / "data" / "candidates_filtered_manual.csv"
OUTPUT_FILE   = BASE_DIR / "data" / "consolidated_raw_reports.json"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
REQUEST_DELAY   = 1.5
H1_CSRF_URL     = "https://hackerone.com/hacktivity/overview"
H1_REPORT_JSON  = "https://hackerone.com/reports/{report_id}.json"
H1_REPORT_HTML  = "https://hackerone.com/reports/{report_id}"

# How much vulnerability text to keep (characters).
# Classifier context window is generous; 6 000 chars covers most reports fully.
MAX_VULN_CHARS = 6_000


# ---------------------------------------------------------------------------
# Session helpers (reused from 01_fetch_candidates.py)
# ---------------------------------------------------------------------------

def _get_csrf(session: requests.Session) -> str:
    resp = session.get(H1_CSRF_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tag  = soup.find("meta", {"name": "csrf-token"})
    if not tag:
        sys.exit("[ERROR] Could not find CSRF token. Session cookie may be expired.")
    return tag["content"]


def _build_session(cookie_raw: str) -> requests.Session:
    session = requests.Session()
    session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        "Cookie": cookie_raw,
    })
    return session


# ---------------------------------------------------------------------------
# Fetch strategies
# ---------------------------------------------------------------------------

def _fetch_via_json_api(
    session: requests.Session, csrf: str, report_id: str
) -> dict | None:
    """
    GET /reports/{id}.json with session cookie + CSRF header.
    Returns a normalised report dict on success, None on failure.

    The endpoint returns the full vulnerability_information field for
    publicly disclosed reports when a valid session is present.
    """
    url = H1_REPORT_JSON.format(report_id=report_id)
    try:
        resp = session.get(
            url,
            headers={
                "Accept":       "application/json",
                "X-CSRF-Token": csrf,
                "Referer":      H1_CSRF_URL,
            },
            timeout=30,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        data = resp.json()
    except Exception as exc:
        print(f"      [json_api error] {exc}")
        return None

    # The .json response nests data differently depending on H1 version.
    # Try both the top-level dict and a nested 'report' key.
    payload = data if "title" in data else data.get("report", data)

    vuln_info = (
        payload.get("vulnerability_information")
        or payload.get("vulnerability_info")
        or ""
    ).strip()

    if not vuln_info:
        return None  # trigger HTML fallback

    return {
        "title":            payload.get("title", ""),
        "program_name":     (payload.get("team") or {}).get("name", "")
                            or payload.get("team_handle", ""),
        "severity":         (payload.get("severity") or {}).get("rating")
                            or payload.get("severity_rating"),
        "weakness_name":    (payload.get("weakness") or {}).get("name"),
        "disclosed_at":     payload.get("disclosed_at"),
        "vulnerability_info": vuln_info[:MAX_VULN_CHARS],
        "fetch_method":     "json_api",
    }


def _fetch_via_html(session: requests.Session, report_id: str) -> dict | None:
    """
    Scrape the public report page and extract og:description.
    Returns a normalised report dict on success, None on failure.
    """
    url = H1_REPORT_HTML.format(report_id=report_id)
    try:
        resp = session.get(
            url,
            headers={"Accept": "text/html", "Referer": "https://hackerone.com/"},
            timeout=30,
        )
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
    except Exception as exc:
        print(f"      [html error] {exc}")
        return None

    # og:description
    vuln_info = ""
    for meta in soup.find_all("meta"):
        prop = meta.get("property") or meta.get("name") or ""
        if prop in ("og:description", "description"):
            vuln_info = (meta.get("content") or "").strip()
            if vuln_info:
                break

    # Title from <title> tag as fallback
    page_title = ""
    title_tag = soup.find("title")
    if title_tag:
        page_title = title_tag.get_text(strip=True)

    return {
        "title":            page_title,
        "program_name":     "",   # not reliably available from HTML without JS
        "severity":         None,
        "weakness_name":    None,
        "disclosed_at":     None,
        "vulnerability_info": vuln_info[:MAX_VULN_CHARS] if vuln_info else None,
        "fetch_method":     "html_fallback",
    }


# ---------------------------------------------------------------------------
# CSV reader
# ---------------------------------------------------------------------------

def _load_eligible_ids(csv_path: Path) -> list[dict]:
    """
    Return list of dicts for rows where eligible == 'true' (case-insensitive).
    Preserves program_name, severity, reason from the pre-filter CSV so we
    can use them as fallback metadata if the fetch returns sparse data.
    """
    rows = []
    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if row.get("eligible", "").strip().lower() == "true":
                rows.append({
                    "report_id":    row.get("report_id", "").strip(),
                    "program_name": row.get("program_name", "").strip(),
                    "severity":     row.get("severity", "").strip() or None,
                    "reason":       row.get("reason", "").strip(),
                })
    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv(ENV_FILE)
    cookie_raw = os.getenv("H1_SESSION_COOKIE", "").strip()
    if not cookie_raw:
        sys.exit("[ERROR] H1_SESSION_COOKIE not set in .env")

    if not FILTERED_CSV.exists():
        sys.exit(f"[ERROR] Filtered CSV not found: {FILTERED_CSV}")

    # Load already-fetched report IDs for resumability
    existing: list[dict] = []
    fetched_ids: set[str] = set()
    if OUTPUT_FILE.exists():
        try:
            existing = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
            fetched_ids = {r["report_id"] for r in existing}
            print(f"Resuming — {len(fetched_ids)} reports already in {OUTPUT_FILE.name}")
        except json.JSONDecodeError:
            print("[WARN] combined_reports.json is malformed — starting fresh.")
            existing = []

    eligible_rows = _load_eligible_ids(FILTERED_CSV)
    to_fetch = [r for r in eligible_rows if r["report_id"] not in fetched_ids]

    print(f"Eligible reports in CSV : {len(eligible_rows)}")
    print(f"Already fetched         : {len(fetched_ids)}")
    print(f"To fetch this run       : {len(to_fetch)}\n")

    if not to_fetch:
        print("Nothing to do. combined_reports.json is up to date.")
        return

    session = _build_session(cookie_raw)

    print("Fetching CSRF token …")
    csrf = _get_csrf(session)
    print("CSRF OK\n")

    results = list(existing)
    errors  = []

    for idx, meta in enumerate(to_fetch, 1):
        report_id = meta["report_id"]
        print(f"  [{idx:>3}/{len(to_fetch)}] {report_id}", end="  ")

        # ── Strategy 1: JSON API ──────────────────────────────────────────
        fetched = _fetch_via_json_api(session, csrf, report_id)
        time.sleep(REQUEST_DELAY)

        # ── Strategy 2: HTML fallback ─────────────────────────────────────
        if fetched is None:
            print("(json→html fallback)", end="  ")
            fetched = _fetch_via_html(session, report_id)
            time.sleep(REQUEST_DELAY)

        if fetched is None:
            print("NOT FOUND")
            errors.append(report_id)
            # Still write a skeleton so check_coverage doesn't re-attempt forever
            results.append({
                "report_id":        report_id,
                "source_url":       f"https://hackerone.com/reports/{report_id}",
                "program_name":     meta["program_name"],
                "severity":         meta["severity"],
                "weakness_name":    None,
                "disclosed_at":     None,
                "title":            "",
                "vulnerability_info": None,
                "fetch_method":     "not_found",
            })
        else:
            # Prefer richer metadata from CSV if fetch returned blanks
            record = {
                "report_id":     report_id,
                "source_url":    f"https://hackerone.com/reports/{report_id}",
                "program_name":  fetched["program_name"] or meta["program_name"],
                "severity":      fetched["severity"]     or meta["severity"],
                "weakness_name": fetched["weakness_name"],
                "disclosed_at":  fetched["disclosed_at"],
                "title":         fetched["title"],
                "vulnerability_info": fetched["vulnerability_info"],
                "fetch_method":  fetched["fetch_method"],
            }
            results.append(record)
            vuln_len = len(record["vulnerability_info"] or "")
            print(f"OK via {record['fetch_method']}  ({vuln_len} chars)")

        # Write after every report — crash-safe
        OUTPUT_FILE.write_text(
            json.dumps(results, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ---------------------------------------------------------------------------
    # Summary
    # ---------------------------------------------------------------------------
    print(f"\n── Done ──────────────────────────────────────────")
    print(f"Total records in {OUTPUT_FILE.name} : {len(results)}")

    from collections import Counter
    method_dist = Counter(r["fetch_method"] for r in results)
    for method, count in method_dist.most_common():
        print(f"  {count:>4}  {method}")

    with_content = sum(1 for r in results if r.get("vulnerability_info"))
    print(f"\nReports with vulnerability text : {with_content}/{len(results)}")

    if errors:
        print(f"\nFailed to fetch ({len(errors)}) — written as 'not_found' skeletons:")
        for rid in errors:
            print(f"  https://hackerone.com/reports/{rid}")


if __name__ == "__main__":
    main()