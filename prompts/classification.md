You are classifying HackerOne vulnerability reports for a BOLA taxonomy research. Do NOT build a framework or API pipeline 
Just use your own reasoning directly in agent mode for the classification.

You will receive raw report content from bola_research/data/consolidated_raw_reports.json. 

Return ONLY valid JSON to data/classified_reports.json. No preamble. No explanation outside the JSON.

Be conservative. If a report does not clearly demonstrate Broken Object Level Authorization, classify bola_family as "Unclassified" and bola_in_scope as false.

---

EXPLICIT EXCLUSION RULES
Do NOT classify as BOLA if the report describes:
- An attacker manipulating only their own objects (own account, own order, own subscription)
- Pure privilege escalation via role/permission assignment with no specific object reference (RBAC/BFLA without object-level context)
- Feature gating bypass where no cross-user object boundary is crossed
- Authentication bypass (2FA, SSO, password reset) affecting only the attacker's own account
- Generic information disclosure not tied to a specific owned object
- Business logic flaws (price manipulation, quantity abuse, reward abuse) where the attacker does not access another user's object

INCLUSION RULE
A report qualifies as BOLA only if: an attacker accessed, read, modified, deleted, or triggered an action on an object that belongs to or is associated with another user, tenant, or organizational boundary — without proper authorization at the object level.

---

BOLA FAMILY
Select EXACTLY ONE.

"Direct Object Reference BOLA"
Attacker directly supplies an object identifier in a request and receives another user's object without authorization. The identifier can be ANY type: sequential integer, UUID, hash, encoded ID, email, phone number, username. The defining characteristic is direct reference — one request, one object, no multi-step identifier acquisition required.

"Tenant Isolation BOLA"
Attacker crosses a tenant/organization/workspace boundary to access or modify objects belonging to a different tenant. The authorization failure is at the tenant boundary specifically, not just user-to-user. Common in SaaS multi-tenant architectures.
Note: if the violation is also role-based (admin vs user), only classify as Tenant Isolation if the primary boundary crossed is organizational/tenant, not role-based.

"Action-Level Object BOLA"
Attacker performs an unauthorized STATE-CHANGING action on another user's object: delete, approve, modify, transfer, accept, reject, assign. Read-only access to another user's object is Direct Object Reference BOLA, not this category. The key signal is an action verb in the vulnerability description.

"Chained Disclosure BOLA"
Exploitation requires a distinct prior step to obtain the object identifier or context — from a separate endpoint, API response, or workflow step. Multi-step by definition. The identifier used in the final attack was not predictable independently; it had to be harvested first.

"Object Rebinding BOLA"
Attacker reassigns or rebinds object ownership by supplying or modifying an ownership field in a request body or parameter: owner_id, account_id, user_id, tenant_id, assigned_to. The object changes hands or context as a result.

"Workflow-Context BOLA"
Ownership or authorization enforcement is bypassed specifically because of object state or lifecycle position: draft, pending, archived, deactivated, deleted, transferred. The same request would be rejected for an active/normal-state object. Scope is intentionally narrow — state-of-object enabling access, not general workflow skipping.

"Unclassified"
Insufficient evidence, not clearly BOLA, ambiguous, or excluded by the rules above.

---

HORIZONTAL VS VERTICAL
Select EXACTLY ONE.

"Horizontal": attacker accesses an object belonging to another user at the same privilege level (user-to-user)
"Vertical": attacker accesses an object belonging to a higher-privilege role (user-to-admin, tenant-to-superadmin)
"Unclear": insufficient information to determine

---

ACTION TYPE
Select EXACTLY ONE — the primary unauthorized action the attacker performs.

"Read": attacker retrieves/views data they shouldn't access
"Modify": attacker changes/updates another user's object
"Delete": attacker deletes another user's object
"Trigger": attacker initiates an action or state change on another user's object (send, accept, approve, assign)
"Enumerate": attacker iterates over objects to discover their existence or metadata without necessarily reading full content
"Unclear": cannot be determined

---

EXPLOIT MECHANISMS
Select ZERO OR MORE — only if explicitly evidenced or strongly implied.

"Sequential integer enumeration"
"UUID reuse"
"GraphQL global ID leakage"
"Email-based object binding"
"Phone-number binding"
"Parameter pollution"
"State confusion"
"Cross-endpoint identifier leakage"
"Object reassignment"
"Multi-tenant context confusion"
"Relationship/association abuse"
"Encoded ID manipulation"

---

INDUSTRY SECTOR
Select EXACTLY ONE.

"Fintech & Financial Services"
"E-commerce & Marketplace"
"SaaS & Productivity"
"Social & Consumer Platforms"
"Healthcare & Life Sciences"
"Enterprise & Infrastructure"
"Government & Public Sector"
"Other"

---

CONFIDENCE DEFINITIONS
Apply exactly one using these operational rules:

"High": report contains endpoint path OR request/response example AND clearly demonstrates cross-user object access AND exclusion rules clearly do not apply
"Medium": cross-user object access is evident but one of the following is missing: endpoint path, request example, or object identifier type
"Low": cross-user access is implied but not demonstrated, OR description is too sparse to confirm the inclusion rule is met, OR exclusion rules may apply but cannot be confirmed

---

ENDPOINT NORMALIZATION RULES
- Replace all numeric IDs with {id}: /api/orders/12345 → /api/orders/{id}
- Replace all UUIDs with {uuid}: /users/550e8400-e29b-41d4-a716-446655440000 → /users/{uuid}
- Replace all encoded IDs with {encoded_id}
- Replace email addresses with {email}
- Keep query parameter names but replace values: ?user_id=123 → ?user_id={id}
- If multiple endpoints are involved, use the primary vulnerable endpoint
- If endpoint is not determinable, use null

---

OUTPUT SCHEMA

{
  "report_id": "",
  "program_name": "",
  "severity": "",
  "industry_sector": "",
  "http_method": "GET | POST | PUT | PATCH | DELETE | unclear",
  "endpoint_pattern": "",
  "id_format": "sequential_int | uuid | hash | email | phone | username | encoded_id | unclear",
  "year_disclosed": null,
  "bola_family": "",
  "bola_in_scope": true or false,
  "horizontal_vertical": "Horizontal | Vertical | Unclear",
  "action_type": "Read | Modify | Delete | Trigger | Enumerate | Unclear",
  "exploit_mechanisms": [],
  "confidence": "High | Medium | Low",
  "rationale": ""
}

Rationale must briefly state: (1) why inclusion rule is met or not, (2) why the selected family fits over alternatives considered, (3) why confidence level was assigned.

---

REPORT CONTENT:
{report_content}