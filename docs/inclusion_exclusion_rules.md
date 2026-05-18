# Inclusion and Exclusion Rules

This document defines the operational criteria used to determine whether a publicly disclosed vulnerability report qualifies as an in-scope Broken Object Level Authorization (BOLA) case for inclusion in the dataset accompanying:

The purpose of these rules is to:
- reduce classification ambiguity,
- improve reproducibility,
- separate BOLA from adjacent vulnerability classes,
- and prevent overcounting caused by inconsistent practitioner labeling.

These rules were applied during:
- pre-filter screening,
- full classification,
- and manual review.

---

# Inclusion Philosophy

The dataset intentionally uses a strict operational definition of BOLA.

A report is included only when:
1. a concrete object boundary exists,
2. cross-boundary access or action occurs,
3. and the failure is fundamentally object-level authorization.

Reports tagged:
- IDOR,
- Improper Access Control,
- or Broken Access Control

are not automatically considered BOLA.

This distinction is important because public bug bounty tagging frequently conflates:
- BOLA,
- BFLA,
- authentication bypass,
- and general business logic flaws.

---

# Core Inclusion Criteria

A report must satisfy **all three** criteria to be considered in-scope.

---

# 1. Concrete Object Reference

## Requirement

The vulnerability must involve a specific identifiable object.

The object may represent:
- data,
- configuration,
- state,
- relationship,
- or resource ownership.

The object boundary must be technically meaningful rather than abstract.

---

## Valid Object Examples

- User account
- Invoice
- Support ticket
- API token
- Message
- File
- Organization
- Workspace
- Analytics record
- Customer profile
- Conversation history
- Payment object
- Storage configuration

---

## Included Examples

### Included

```http
GET /invoice/1042
```

```json
{
  "user_id": 5512
}
```

```http
GET /organizations/4421/reports
```

All involve concrete object references.

---

## Excluded Examples

### Excluded

- “Unauthorized access to sensitive data” without identifying the object boundary
- Generic admin panel exposure
- Arbitrary account takeover without object-level distinction

---

## Operational Rule

If the report cannot answer:

> “What specific object was improperly accessed or acted upon?”

the report is excluded.

---

# 2. Cross-Boundary Access or Action

## Requirement

The attacker must access or act upon an object belonging to a different authorization context.

The boundary may involve:
- another user,
- another tenant,
- another organization,
- or another privilege context.

The key requirement is:
- the attacker is not authorized for that specific object.

---

## Valid Boundary Types

### User-to-User

One user accesses another user's object.

### User-to-Admin (Vertical)

A lower-privileged user accesses an object owned by a higher-privileged role.

### Tenant-to-Tenant

One organization or workspace accesses another organization's objects.

### Cross-Context Ownership

Authorization scope changes improperly across ownership boundaries.

---

## Included Examples

### Horizontal

User A retrieves User B's invoice.

### Vertical

Standard user deletes an administrator-owned object using an endpoint they are legitimately allowed to call.

### Tenant Isolation

Organization A accesses Organization B's reports.

---

## Excluded Examples

### Excluded

- User modifies their own object in unintended ways
- Abuse entirely within owned resources
- Self-service business logic manipulation

---

## Operational Rule

The report must demonstrate:
- unauthorized access,
or
- unauthorized action

against an object outside the attacker's intended authorization scope.

---

# 3. Technical Evidence Requirement

## Requirement

The report must contain at least one technical detail sufficient to support reproducible classification.

This requirement exists to:
- reduce speculation,
- improve consistency,
- and prevent narrative-only classification.

---

## Acceptable Technical Evidence

At least one of the following must appear:

- endpoint path
- HTTP method
- parameter name
- request example
- response example
- object identifier
- identifier format
- reproduction steps
- workflow description
- code snippet
- API structure description

---

## Included Examples

### Included

```http
POST /tasks/482/archive
```

```json
{
  "organization_id": 5521
}
```

“Attacker changed another user's UUID in the request body.”

---

## Excluded Examples

### Excluded

- “Researchers could access unauthorized data” with no technical details
- High-level summaries lacking object or workflow description
- Advisory-only disclosures without exploit context

---

## Operational Rule

The report must contain enough technical detail to support:
- taxonomy assignment,
- exploit mechanism analysis,
- or authorization-boundary interpretation.

---

# Explicit Exclusion Rules

Reports meeting any of the following conditions are excluded from in-scope BOLA classification.

---

# 1. Pure BFLA / RBAC Failure

## Definition

The attacker is not authorized to access the endpoint itself.

The failure concerns:
- function-level access,
not
- object ownership validation.

---

## Excluded Example

```http
GET /admin/deleteUser
```

Standard user accesses administrator-only endpoint.

---

## Why Excluded

The vulnerability concerns:
- endpoint authorization,
not
- object-level authorization.

---

## Clarification

If:
- the attacker is legitimately allowed to call the endpoint,
but
- ownership validation on the target object is missing,

the case is included as BOLA.

---

# 2. Generic Authentication Bypass

## Definition

Authentication itself fails independently of object ownership.

---

## Excluded Examples

- Missing authentication
- Session fixation
- MFA bypass
- Token forgery without object boundary
- Unauthenticated admin access

---

## Why Excluded

The failure concerns:
- authentication,
not
- object authorization.

---

# 3. Business Logic Abuse on Owned Resources

## Definition

The attacker abuses application logic using resources they legitimately own.

No cross-object authorization boundary is crossed.

---

## Excluded Examples

- Unlimited coupon redemption
- Self-referral abuse
- Purchasing workflow abuse
- Race conditions on owned objects
- Manipulating personal quotas

---

## Why Excluded

The attacker remains within their authorized ownership scope.

---

# 4. Generic Information Disclosure

## Definition

Sensitive information becomes exposed without meaningful object-boundary violation.

---

## Excluded Examples

- Stack traces
- Environment variable leakage
- Public configuration exposure
- Debug endpoint disclosure

---

## Why Excluded

No object-level authorization failure exists.

---

# 5. Insufficient Technical Detail

## Definition

The report lacks enough evidence to support reliable classification.

---

## Excluded Examples

- Acknowledgment-only disclosures
- Advisory links without exploit details
- One-sentence summaries with no technical context

---

## Clarification

Sparse disclosures may still be included if:
- object boundaries,
- authorization failure,
- and exploit semantics
remain reasonably inferable.

Such reports receive:
- Medium
or
- Low confidence classifications.

---

# Vertical BOLA Clarification

Vertical BOLA is included only when:

1. the attacker is legitimately allowed to call the endpoint,
2. the missing control concerns ownership of the specific object,
3. and the issue is not pure role-gated endpoint access.

---

## Included Vertical Example

Standard user modifies administrator-owned object through shared endpoint.

---

## Excluded Vertical Example

Standard user accesses `/admin/users/delete`.

This is BFLA, not BOLA.

---

# Workflow-Context Clarification

Workflow-Context BOLA requires:
- the object's lifecycle state itself
to enable exploitation.

---

## Included Example

Access persists after employee removal from organization.

---

## Excluded Example

Generic stale session unrelated to object state.

---

# Chained Disclosure Clarification

Chained Disclosure requires:
- a distinct prior acquisition step.

---

## Included Example

1. Identifier leaked from endpoint A
2. Identifier exploited at endpoint B

---

## Excluded Example

Attacker directly guesses sequential ID.

This is Direct Object Reference BOLA instead.

---

# Confidence Assignment Rules

Confidence reflects:
- evidentiary quality,
not
- exploit severity.

---

# High Confidence

Requirements typically include:
- explicit endpoint,
- request structure,
- reproduction steps,
- or direct cross-boundary proof.

---

# Medium Confidence

Cross-boundary access is clear but:
- some technical details are absent.

---

# Low Confidence

Cross-boundary behavior implied but:
- disclosure content sparse,
- partially redacted,
- or technically incomplete.

---

# Null and Unknown Handling

Missing fields do not imply absence of vulnerability properties.

Examples:
- unknown identifier format,
- missing endpoint,
- absent disclosure year.

Public disclosures frequently redact implementation details.

Unknown values are therefore preserved rather than inferred.

---

# Manual Review Rules

Manual review was triggered for:
- low-confidence classifications,
- sparse disclosures,
- taxonomy ambiguity,
- classifier disagreement,
- and uncertain inclusion status.

Override decisions were documented through rationale fields.

---

# Final Operational Definition

A report is considered in-scope BOLA when:

1. a concrete object exists,
2. an unauthorized cross-boundary interaction occurs,
3. the failure is fundamentally object-level authorization,
4. sufficient technical evidence exists,
5. and the issue is not better explained as:
   - BFLA,
   - authentication bypass,
   - or business logic abuse on owned resources.

These rules were designed to prioritize:
- reproducibility,
- analytical consistency,
- and operational clarity
over broad or informal practitioner interpretations of “IDOR.”