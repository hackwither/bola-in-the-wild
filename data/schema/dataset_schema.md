# Dataset Schema

This document defines the schema for `classified_manually_verified.json`.

Each JSON object represents one publicly disclosed HackerOne report evaluated for inclusion in the BOLA dataset.

---

# Schema Overview

```json
{
  "report_id": "3543475",
  "program_name": "Basecamp",
  "severity": "low",
  "industry_sector": "SaaS & Productivity",
  "http_method": "POST",
  "endpoint_pattern": "/account/imports",
  "id_format": "encoded_id",
  "year_disclosed": 2026,
  "bola_family": "Tenant Isolation BOLA",
  "bola_in_scope": true,
  "horizontal_vertical": "Horizontal",
  "action_type": "Read",
  "exploit_mechanisms": [
    "Cross-endpoint identifier leakage",
    "Multi-tenant context confusion"
  ],
  "confidence": "High",
  "rationale": "..."
}
```

---

# Field Definitions

| Field | Type | Description |
|---|---|---|
| report_id | string | HackerOne report ID |
| program_name | string | Program or organization name |
| severity | string/null | HackerOne severity rating |
| industry_sector | string | Program sector classification |
| http_method | string/null | Primary HTTP method involved |
| endpoint_pattern | string/null | Normalized vulnerable endpoint pattern |
| id_format | string | Identifier format used in exploitation |
| year_disclosed | integer/null | Disclosure year if publicly visible |
| bola_family | string | Assigned BOLA taxonomy family |
| bola_in_scope | boolean | Final inclusion determination |
| horizontal_vertical | string | Authorization direction classification |
| action_type | string | Primary unauthorized operation |
| exploit_mechanisms | array[string] | Observed exploitation techniques |
| confidence | string | Classification confidence level |
| rationale | string | Structured classification explanation |

---

# BOLA Family Values

Valid `bola_family` values:

- Direct Object Reference BOLA
- Action-Level Object BOLA
- Tenant Isolation BOLA
- Workflow-Context BOLA
- Chained Disclosure BOLA
- Object Rebinding BOLA
- Unclassified

---

# Authorization Direction Values

Valid `horizontal_vertical` values:

- Horizontal
- Vertical
- Unclear

These describe the ownership relationship between attacker and victim objects, not endpoint-level RBAC permissions.

---

# Action Type Values

Valid `action_type` values:

- Read
- Modify
- Delete
- Trigger
- Enumerate
- Unclear

---

# Identifier Format Values

Valid `id_format` values:

- sequential_integer
- encoded_id
- username
- email
- uuid
- hash
- unclear

Opaque identifiers are treated as exploitable if authorization enforcement remains absent.

---

# Exploit Mechanism Values

`exploit_mechanisms` is a multi-label field.

Observed values include:

- Sequential integer enumeration
- Cross-endpoint identifier leakage
- State confusion
- Encoded ID manipulation
- Multi-tenant context confusion
- GraphQL global ID leakage
- Object reassignment
- UUID reuse
- Email-based object binding
- Relationship/association abuse

Multiple mechanisms may apply to a single report.

---

# Confidence Levels

## High

Confirmed cross-boundary access with detailed technical evidence.

Typically includes:
- endpoint paths,
- request examples,
- PoC steps,
- or direct exploitation evidence.

## Medium

Cross-boundary access is clear but some technical details are absent.

## Low

Cross-boundary behavior is implied but disclosure detail is sparse.

---

# Notes

- `null` values reflect missing disclosure information rather than negative evidence.
- Sparse disclosures are common in public bug bounty ecosystems.
- All classifications are derived from publicly available evidence only.
- Manual review was applied to low-confidence and disputed classifications.