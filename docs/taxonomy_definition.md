# BOLA Taxonomy Definitions

This document defines the operational taxonomy used throughout the dataset and accompanying paper:

> *Broken Object Level Authorization in the Wild: A Taxonomy and Quantitative Meta-Analysis of 100+ HackerOne Disclosures*

The taxonomy was derived empirically from publicly disclosed bug bounty reports and refined iteratively through manual review.

A report is assigned the family that best explains *why* authorization failed.

The taxonomy is intended to:
- reduce classification ambiguity,
- support reproducible empirical analysis,
- and provide operational guidance for API security testing.

---

# Taxonomy Design Principles

The taxonomy is organized around the *primary authorization failure mechanism*, not:
- exploit severity,
- HTTP method,
- endpoint type,
- or programming framework.

Several reports contain multiple exploit behaviors simultaneously. In such cases, classification prioritizes:
1. the dominant authorization boundary crossed,
2. the mechanism enabling the boundary failure,
3. and the primary attacker action.

Each family is therefore mutually exclusive at the top-level classification layer, even if reports contain overlapping mechanics.

---

# 1. Direct Object Reference BOLA

## Definition

The attacker directly references another user's object identifier in a single request without requiring a prior acquisition step.

The identifier may be:
- sequential,
- opaque,
- encoded,
- user-derived,
- or otherwise externally referenceable.

The defining property is not predictability itself, but that:
- the identifier is already known,
- directly observable,
- or trivially derivable
before exploitation begins.

---

## Core Authorization Failure

The server validates:
- authentication,
but fails to validate:
- ownership of the referenced object.

---

## Typical Behaviors

- Sequential ID incrementing
- UUID substitution
- Username substitution
- Email substitution
- GraphQL node ID substitution
- Hash-based object reference swapping

---

## Typical Example

```http
GET /invoice/1042
```

The attacker changes:
```text
1041 → 1042
```

and retrieves another user's invoice because object ownership is never validated.

---

## Included Cases

- Single-request object substitution
- Read-only unauthorized access
- Direct object retrieval
- Direct object modification when ownership reassignment is NOT the core mechanism

---

## Excluded Cases

- Multi-step identifier harvesting
- Cross-tenant isolation failures
- Ownership reassignment attacks
- Pure RBAC/BFLA endpoint access failures

---

## Common Confusion Cases

### Direct Object Reference vs Chained Disclosure

Direct Object Reference:
- attacker already possesses or predicts identifier

Chained Disclosure:
- attacker first harvests identifier from another workflow step before exploitation

---

# 2. Action-Level Object BOLA

## Definition

The attacker performs an unauthorized state-changing action on another user's object.

The attacker is legitimately permitted to access the endpoint itself, but:
- authorization is not enforced for the specific target object.

---

## Core Authorization Failure

Function access is valid.

Object ownership validation is absent.

---

## Typical Behaviors

- Delete
- Modify
- Approve
- Trigger
- Transfer
- Archive
- Workflow execution

---

## Typical Example

```http
POST /tasks/482/archive
```

The attacker substitutes another user's task ID and archives their task because the server validates endpoint access but not task ownership.

---

## Included Cases

- Unauthorized modification
- Unauthorized deletion
- Unauthorized triggering
- Unauthorized workflow execution
- Unauthorized state changes

---

## Excluded Cases

- Pure read-only access
- Endpoint privilege escalation
- Admin-only endpoint exposure

---

## Common Confusion Cases

### Action-Level Object vs BFLA

Action-Level Object:
- attacker is allowed to call endpoint
- object ownership validation missing

BFLA:
- attacker should never access endpoint itself

---

### Action-Level Object vs Direct Object Reference

Direct Object Reference:
- primary impact is object retrieval/access

Action-Level Object:
- primary impact is state-changing action

If both occur simultaneously, classification prioritizes the dominant attacker action.

---

# 3. Tenant Isolation BOLA

## Definition

The attacker crosses an organizational, workspace, or tenant boundary to access another tenant's objects.

The violated boundary is organizational membership rather than individual user ownership alone.

---

## Core Authorization Failure

The application validates:
- authenticated session existence,
but fails to validate:
- tenant membership alignment with the referenced object.

---

## Typical Behaviors

- Cross-workspace access
- Cross-organization object retrieval
- Cross-account SaaS exposure
- Multi-tenant identifier swapping

---

## Typical Example

```http
POST /bugs.json
{
  "organization_id": 4421
}
```

The attacker supplies another organization's identifier and retrieves objects belonging to a different tenant.

---

## Included Cases

- Multi-tenant SaaS isolation failures
- Cross-organization report access
- Cross-workspace object access

---

## Excluded Cases

- Individual user-to-user access within same tenant
- Pure role escalation
- Generic object substitution without tenant boundary crossing

---

## Common Confusion Cases

### Tenant Isolation vs Direct Object Reference

Direct Object Reference:
- boundary crossed is user ownership

Tenant Isolation:
- boundary crossed is organizational/tenant membership

---

# 4. Workflow-Context BOLA

## Definition

Authorization fails because the target object exists in a specific lifecycle or workflow state.

The object state itself is the enabling condition for exploitation.

The same request would typically be rejected against the object in a normal state.

---

## Core Authorization Failure

Authorization is:
- evaluated incompletely,
- cached incorrectly,
- or not re-evaluated
after object state changes.

---

## Typical States

- Archived
- Removed
- Deactivated
- Disabled
- Deleted
- Transferred
- Soft-deleted

---

## Typical Behaviors

- Access persists after employee removal
- Archived objects remain accessible
- Deactivated accounts continue exposing data
- Post-privacy-change object leakage

---

## Typical Example

A removed employee retains access to customer records because the application validates session existence but does not re-evaluate access rights after organizational dissociation.

---

## Included Cases

- Lifecycle-state-dependent authorization bypass
- Post-removal access persistence
- Stale access control tied to object state

---

## Excluded Cases

- Generic stale sessions unrelated to object state
- Pure tenant isolation failures
- General authorization omissions without lifecycle dependency

---

## Common Confusion Cases

### Workflow-Context vs Tenant Isolation

Workflow-Context:
- lifecycle state enables access

Tenant Isolation:
- tenant boundary itself is the primary failure

---

# 5. Chained Disclosure BOLA

## Definition

The attacker must first harvest an identifier or authorization-relevant reference from one workflow step before exploiting it at another endpoint.

Exploitation requires a multi-step sequence.

---

## Core Authorization Failure

One endpoint leaks an identifier scoped to another user's object.

A second endpoint accepts that identifier without ownership validation.

---

## Typical Behaviors

- Identifier leakage
- Token harvesting
- Cross-endpoint exploitation
- Multi-step object retrieval

---

## Typical Example

1. Attacker receives leaked document ID from a preview endpoint
2. Attacker supplies ID to download endpoint
3. Download endpoint validates ID existence but not ownership

---

## Included Cases

- Cross-endpoint identifier reuse
- Multi-step exploitation chains
- Identifier acquisition workflows

---

## Excluded Cases

- Direct one-step object substitution
- Predictable sequential IDs already known beforehand

---

## Common Confusion Cases

### Chained Disclosure vs Direct Object Reference

Direct Object Reference:
- identifier already available

Chained Disclosure:
- identifier must first be harvested

---

# 6. Object Rebinding BOLA

## Definition

The attacker modifies an ownership-defining field that determines authorization scope or object ownership.

The exploit targets:
- who owns the object,
rather than:
- which object is accessed.

---

## Core Authorization Failure

The server trusts client-supplied ownership context.

---

## Typical Fields

- owner_id
- account_id
- user_id
- sender
- tenant_id
- creator_id

---

## Typical Behaviors

- Ownership reassignment
- Sender impersonation
- Cross-account object rebinding
- Authorization context rewriting

---

## Typical Example

```json
{
  "owner_id": 5521
}
```

The attacker replaces the ownership field with another user's identifier, causing authorization scope to shift.

---

## Included Cases

- Ownership reassignment
- Sender spoofing through trusted metadata
- Account-context rebinding

---

## Excluded Cases

- Simple object retrieval
- Generic identifier swapping
- Tenant-only boundary crossing without ownership mutation

---

## Common Confusion Cases

### Object Rebinding vs Direct Object Reference

Direct Object Reference:
- attacker references another object

Object Rebinding:
- attacker changes ownership relationship itself

---

# 7. Unclassified

## Definition

The report lacks sufficient evidence for confident BOLA classification or falls outside strict inclusion criteria.

---

## Common Reasons

- Pure BFLA / RBAC failure
- Generic authentication bypass
- Business logic abuse on owned resources
- Insufficient technical detail
- Ambiguous object boundary
- Sparse disclosure content

---

# Vertical vs Horizontal Clarification

The taxonomy distinguishes between:
- taxonomy family,
and
- authorization direction.

These are separate dimensions.

## Horizontal

Attacker accesses object belonging to peer-level user.

## Vertical

Attacker accesses object belonging to higher-privileged role.

Vertical BOLA is included only when:
- the attacker is legitimately allowed to call the endpoint,
and
- the missing control concerns ownership of the specific object.

Vertical BOLA is NOT equivalent to BFLA.

---

# Confidence Definitions

## High Confidence

- explicit technical evidence,
- confirmed cross-boundary access,
- clear exploit mechanics.

Typically includes:
- endpoints,
- requests,
- PoC steps,
- or direct reproduction details.

---

## Medium Confidence

- cross-boundary behavior clear,
- but one or more technical details absent.

---

## Low Confidence

- boundary crossing implied,
- sparse disclosure detail,
- or incomplete technical evidence.

Low confidence does NOT imply false positive classification.

---

# Notes

- Taxonomy assignment reflects the dominant observed authorization failure mechanism.
- Some reports contain multiple valid interpretations.
- The taxonomy is operational rather than ontological.
- Future work may refine, merge, or expand families as larger datasets become available.