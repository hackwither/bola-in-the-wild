"""
01_fetch_candidates.py
----------------------
Queries the HackerOne internal GraphQL API for publicly disclosed reports
where the weakness name contains "IDOR" or "Improper Access Control",
disclosed between 2021 and 2026.

For each report retrieves:
  - report_id (numeric, decoded from base64 global ID)
  - title
  - program_name
  - severity_rating
  - bounty_amount  (sum of all bounty nodes, or null)
  - weakness_name
  - disclosed_at
  - vulnerability_info (first 1000 chars of description)
  - source_url

Two-phase execution
-------------------
Phase 1 — GraphQL pagination
  Bulk-collects structured fields (title, severity, weakness, program,
  bounty, disclosed_at) for up to TARGET_COUNT reports.
  `vulnerability_information` is gated server-side to program members /
  reporter for this session type and always returns null in bulk queries.

Phase 2 — HTML enrichment
  For each collected report, GETs the individual report page and extracts
  the `og:description` <meta> tag.  This tag is server-rendered in the
  <head> (no JavaScript required) and always contains the public
  vulnerability description for disclosed reports — the same text shown
  on the report page.  First 1000 characters are stored as
  vulnerability_info.

Auth: reads H1_SESSION_COOKIE from bola_research/.env and passes it in
the Cookie header.  A fresh CSRF token is obtained from the hacktivity
overview page before Phase 1 and reused for all GraphQL calls.
1.5-second delay between every outbound request.  Progress printed
every 50 reports in each phase.
"""

import base64
import json
import os
import sys
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"
OUTPUT_FILE = BASE_DIR / "data" / "candidates_raw.json"

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
TARGET_COUNT = 200
PAGE_SIZE = 50          # reports per GraphQL request
REQUEST_DELAY = 1.5     # seconds between page fetches
DATE_GT = "2020-12-31T23:59:59Z"  # disclosed_at > this → 2021 onwards
DATE_LT = "2027-01-01T00:00:00Z"  # disclosed_at < this → up to end of 2026

H1_GRAPHQL = "https://hackerone.com/graphql"
H1_CSRF_URL = "https://hackerone.com/hacktivity/overview"

GRAPHQL_QUERY = """
query CandidateFetch($cursor: String, $count: Int!, $date_gt: DateTime!, $date_lt: DateTime!) {
  reports(
    first: $count
    after: $cursor
    where: {
      _or: [
        { weakness: { name: { _ilike: "%idor%" } } }
        { weakness: { name: { _ilike: "%improper access control%" } } }
      ]
      disclosed_at: { _gt: $date_gt, _lt: $date_lt }
    }
  ) {
    total_count
    pageInfo {
      hasNextPage
      endCursor
    }
    edges {
      node {
        id
        title
        disclosed_at
        vulnerability_information
        bounties {
          nodes {
            amount
          }
        }
        severity {
          rating
        }
        weakness {
          name
        }
        team {
          name
        }
      }
    }
  }
}
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _decode_report_id(global_id: str) -> str:
    """
    Decode a HackerOne base64 global ID to its numeric report ID.
    e.g. Z2lkOi8v...  →  gid://hackerone/Report/3604288  →  '3604288'
    """
    try:
        padding = "=" * (-len(global_id) % 4)
        decoded = base64.b64decode(global_id + padding).decode("utf-8")
        return decoded.split("/")[-1]
    except Exception:
        return global_id  # fallback: return raw GID


def _sum_bounty(nodes: list) -> str | None:
    """Return total bounty as a decimal string, or None if no paid bounties."""
    if not nodes:
        return None
    total = sum(float(n.get("amount", 0) or 0) for n in nodes)
    return f"{total:.2f}" if total > 0 else None


def _parse_node(node: dict) -> dict:
    report_id = _decode_report_id(node.get("id", ""))
    vuln_info = node.get("vulnerability_information") or ""
    if vuln_info:
        vuln_info = vuln_info[:1000]

    return {
        "report_id": report_id,
        "title": node.get("title", ""),
        "program_name": (node.get("team") or {}).get("name", ""),
        "severity_rating": (node.get("severity") or {}).get("rating", None),
        "bounty_amount": _sum_bounty((node.get("bounties") or {}).get("nodes", [])),
        "weakness_name": (node.get("weakness") or {}).get("name", ""),
        "disclosed_at": node.get("disclosed_at", ""),
        "vulnerability_info": vuln_info or None,
        "source_url": f"https://hackerone.com/reports/{report_id}",
    }


def _fetch_og_description(session: requests.Session, url: str) -> str | None:
    """
    GET a single HackerOne report page and return the first 1000 characters
    of its og:description meta tag.

    The tag is server-rendered in the HTML <head> for all publicly disclosed
    reports and is not gated by session permissions — it is identical to the
    vulnerability description shown on the report page.

    Returns None on any network / parsing error so the caller can skip
    gracefully and keep whatever value was already stored.
    """
    try:
        resp = session.get(
            url,
            headers={"Accept": "text/html", "Referer": "https://hackerone.com/"},
            timeout=30,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Prefer og:description; fall back to name="description"
        for meta in soup.find_all("meta"):
            prop = meta.get("property") or meta.get("name") or ""
            if prop in ("og:description", "description"):
                text = (meta.get("content") or "").strip()
                if text:
                    return text[:1000]
    except Exception:
        pass
    return None


def _get_csrf(session: requests.Session) -> str:
    resp = session.get(H1_CSRF_URL, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    tag = soup.find("meta", {"name": "csrf-token"})
    if not tag:
        sys.exit("[ERROR] Could not find CSRF token on page. Session may be expired.")
    return tag["content"]


def _graphql(
    session: requests.Session,
    csrf: str,
    cursor: str | None,
) -> dict:
    variables = {
        "count": PAGE_SIZE,
        "cursor": cursor,
        "date_gt": DATE_GT,
        "date_lt": DATE_LT,
    }
    resp = session.post(
        H1_GRAPHQL,
        json={"query": GRAPHQL_QUERY, "variables": variables},
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-CSRF-Token": csrf,
            "Referer": H1_CSRF_URL,
        },
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()

    errors = payload.get("errors")
    if errors and not payload.get("data"):
        raise RuntimeError(f"GraphQL error: {errors[0]['message']}")

    return payload["data"]["reports"]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    load_dotenv(ENV_FILE)
    cookie_raw = os.getenv("H1_SESSION_COOKIE", "").strip()
    if not cookie_raw:
        sys.exit("[ERROR] H1_SESSION_COOKIE not set in .env")

    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Cookie": cookie_raw,
        }
    )

    print("Fetching CSRF token …")
    csrf = _get_csrf(session)
    print(f"CSRF OK\n")

    results: list[dict] = []
    seen_ids: set[str] = set()
    cursor: str | None = None
    page = 0
    total_available: int | None = None

    while len(results) < TARGET_COUNT:
        page += 1
        print(f"  Page {page} (cursor={cursor or 'start'}) …", end=" ", flush=True)

        try:
            data = _graphql(session, csrf, cursor)
        except Exception as exc:
            print(f"\n[ERROR] {exc}")
            break

        if total_available is None:
            total_available = data.get("total_count", 0)
            print(
                f"\n  Total matching reports on HackerOne: {total_available}"
                f"  (collecting up to {TARGET_COUNT})\n"
            )
        else:
            print()

        edges = data.get("edges", [])
        if not edges:
            print("  No more results.")
            break

        for edge in edges:
            if len(results) >= TARGET_COUNT:
                break
            node = edge.get("node", {})
            parsed = _parse_node(node)
            rid = parsed["report_id"]
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            results.append(parsed)

            n = len(results)
            if n % 50 == 0:
                print(f"  ── {n} reports collected ──")

        page_info = data.get("pageInfo", {})
        if not page_info.get("hasNextPage"):
            print("  Reached last page.")
            break

        cursor = page_info.get("endCursor")
        time.sleep(REQUEST_DELAY)

    # ------------------------------------------------------------------
    # Phase 2: HTML enrichment — fetch og:description for each report
    # ------------------------------------------------------------------
    print(f"\n── Phase 2: fetching vulnerability descriptions ({len(results)} reports) ──\n")

    for idx, report in enumerate(results, 1):
        # Skip if Phase 1 somehow already populated the field
        if report.get("vulnerability_info"):
            continue

        desc = _fetch_og_description(session, report["source_url"])
        report["vulnerability_info"] = desc

        if idx % 50 == 0:
            filled = sum(1 for r in results[:idx] if r.get("vulnerability_info"))
            print(f"  ── {idx}/{len(results)} fetched  ({filled} with description) ──")

        if idx < len(results):
            time.sleep(REQUEST_DELAY)

    # ------------------------------------------------------------------
    # Save output
    # ------------------------------------------------------------------
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\nDone. {len(results)} report(s) saved → {OUTPUT_FILE.relative_to(BASE_DIR)}")

    # Summary
    from collections import Counter
    severity_dist = Counter(r["severity_rating"] or "none" for r in results)
    print("\nSeverity distribution:")
    for sev, count in severity_dist.most_common():
        print(f"  {count:4d}  {sev}")

    with_desc = sum(1 for r in results if r["vulnerability_info"])
    print(f"\nvulnerability_info present : {with_desc}/{len(results)}")


if __name__ == "__main__":
    main()
