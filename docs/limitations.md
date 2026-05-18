# Limitations

This document outlines the primary methodological and interpretive limitations affecting the dataset and findings presented in:

The goal of this section is transparency. The dataset was designed to maximize reproducibility and operational clarity, but several constraints inherent to public vulnerability disclosures affect generalizability.

---

# 1. Public Disclosure Selection Bias

The dataset is derived exclusively from publicly disclosed HackerOne reports.

As a result, it represents the publicly visible BOLA disclosure ecosystem rather than the true global prevalence of Broken Object Level Authorization vulnerabilities.

Organizations that:
- operate public bug bounty programs,
- permit public disclosure,
- and maintain mature vulnerability response processes

are substantially overrepresented relative to:
- private enterprise APIs,
- internal corporate systems,
- healthcare environments,
- regulated financial infrastructure,
- and closed government systems.

The findings therefore characterize the subset of BOLA vulnerabilities that become publicly observable through disclosure platforms.

---

# 2. Program Representation Bias

Certain programs contribute disproportionately to the final dataset.

For example:
- HackerOne itself,
- U.S. Department of Defense (DoD) programs,
- GitHub,
- GitLab,
- Shopify,
- and other SaaS platforms

appear frequently due to:
- active bug bounty participation,
- high disclosure transparency,
- and large researcher engagement.

This concentration may inflate the prevalence of:
- GraphQL-related patterns,
- SaaS tenant-isolation failures,
- and developer-platform authorization workflows

relative to sectors with limited disclosure practices.

---

# 3. Disclosure Depth Heterogeneity

Public bug bounty disclosures vary significantly in technical depth.

Some reports include:
- full endpoints,
- request bodies,
- exploitation walkthroughs,
- and proof-of-concept scripts.

Others contain only:
- high-level summaries,
- minimal reproduction details,
- or generalized descriptions.

This inconsistency affects:
- confidence assignment,
- exploit mechanism classification,
- and identifier-format attribution.

The dataset therefore includes confidence scoring to distinguish evidentiary strength from analytical interpretation.

---

# 4. Sparse Disclosure Ambiguity

Certain reports imply cross-user access without explicitly demonstrating it.

For example:
- a disclosure may state that another user's object was accessible,
- but omit the exact request sequence,
- endpoint path,
- or ownership relationship.

Such cases required interpretive classification.

Low-confidence entries were retained because excluding all sparse disclosures would systematically bias the dataset toward unusually detailed reports and distort the observable ecosystem.

However, inclusion of sparse disclosures introduces uncertainty into:
- family distributions,
- exploit mechanism frequencies,
- and action-type prevalence.

---

# 5. LLM-Assisted Classification Limitations

The classification pipeline used structured LLM-assisted analysis combined with human review.

While operational rules reduced ambiguity, several limitations remain:

- adjacent taxonomy families occasionally overlap,
- some reports describe multiple authorization failures simultaneously,
- and sparse disclosures may produce multiple defensible interpretations.

Particularly difficult distinctions included:
- Direct Object Reference vs. Chained Disclosure,
- Action-Level Object vs. BFLA,
- and Workflow-Context vs. stale authorization state.

Manual review mitigated many errors but does not eliminate subjective interpretation entirely.

The dataset should therefore be understood as:
- operationally structured,
- manually reviewed,
- and reproducible,
rather than perfectly objective.

---

# 6. Taxonomy Subjectivity

The proposed taxonomy reflects one operational interpretation of real-world BOLA behavior.

Alternative researchers may:
- merge certain families,
- split others differently,
- or prioritize exploit mechanics over authorization semantics.

For example:
- Action-Level Object BOLA could reasonably be modeled as a subfamily of Direct Object Reference,
- while Workflow-Context BOLA could be interpreted as a lifecycle-specific authorization failure category.

The taxonomy is therefore intended as:
- an empirical analytical framework,
not
- a canonical or exhaustive ontology.

Future work may refine or restructure these categories as larger datasets become available.

---

# 7. Temporal Incompleteness

A substantial portion of reports lacked publicly visible disclosure dates due to HackerOne redaction behavior.

As a result:
- temporal trend analysis is incomplete,
- longitudinal conclusions are limited,
- and year-over-year comparisons should be interpreted cautiously.

The absence of observable decline from 2023–2026 may reflect:
- persistent authorization weaknesses,
- disclosure lag,
- or incomplete metadata availability.

---

# 8. Upvote-Based Sampling Bias

The initial sampling frame was sorted by upvote count.

This improves:
- report readability,
- disclosure completeness,
- and validation confidence,

but may bias the dataset toward:
- unusually impactful vulnerabilities,
- highly visible programs,
- or reports written by well-known researchers.

Lower-visibility BOLA patterns may therefore be underrepresented.

---

# 9. Severity Rating Inconsistency

Severity ratings were assigned by individual programs using HackerOne conventions and were not normalized independently.

Different organizations apply severity criteria differently depending on:
- business context,
- internal risk models,
- and disclosure policy.

A “Medium” severity report in one ecosystem may receive a “High” rating elsewhere.

Severity distributions should therefore be interpreted as:
- disclosure-platform severity patterns,
rather than
- universal impact measurements.

---

# 10. Multi-Mechanism Classification Complexity

Many reports involve multiple exploit mechanisms simultaneously.

For example:
- GraphQL global ID decoding,
- sequential integer enumeration,
- and cross-endpoint identifier leakage

may all appear within a single exploit chain.

Mechanism frequencies therefore:
- are multi-label,
- may exceed dataset totals,
- and do not represent mutually exclusive categories.

This reflects real-world exploit complexity but complicates strict statistical independence.

---

# 11. Endpoint Visibility Limitations

Some disclosures intentionally redact:
- endpoint paths,
- parameter names,
- object identifiers,
- or workflow structure.

As a result:
- endpoint normalization may be incomplete,
- exploit mechanics may be partially obscured,
- and identifier formats may remain unknown.

The relatively high proportion of:
- `unclear` identifier formats,
- missing endpoints,
- and sparse mechanisms

should therefore not be interpreted as absence of those properties in the underlying vulnerabilities.

---

# 12. Ecosystem Generalizability

The dataset is heavily API-centric because:
- HackerOne disclosures disproportionately involve web APIs,
- modern SaaS architectures expose object references through APIs,
- and OWASP API Top 10 terminology shaped the sampling frame.

The findings may not generalize cleanly to:
- desktop software,
- embedded systems,
- thick-client enterprise applications,
- or non-HTTP authorization models.

---

# 13. Researcher Behavior Effects

Bug bounty ecosystems shape vulnerability discovery incentives.

Researchers are more likely to report vulnerabilities that are:
- reproducible,
- demonstrable,
- and financially rewarded.

This may inflate observable prevalence of:
- direct object reference flaws,
- enumeration weaknesses,
- and easily reproducible cross-user access bugs,

while underrepresenting:
- subtle authorization logic flaws,
- long exploit chains,
- or context-dependent lifecycle vulnerabilities.

The dataset therefore reflects both:
- underlying vulnerability prevalence,
and
- disclosure ecosystem incentives.

---

# 14. Interpretation of “In-Scope”

“In-scope BOLA” within this dataset reflects the operational criteria defined in:

- `schema/inclusion_exclusion_rules.md`
- `schema/taxonomy_definition.md`

This definition is intentionally strict.

Reports tagged IDOR, or Improper Access Control may still be excluded if they:
- lack concrete object boundaries,
- represent pure BFLA,
- involve business logic abuse on owned resources,
- or contain insufficient technical evidence.

The dataset therefore measures:
- rigorously operationalized BOLA behavior,
not
- the broader practitioner usage of “IDOR” terminology.

---

# Summary

Despite these limitations, the dataset provides:

- one of the first operationally structured empirical analyses of BOLA,
- a reproducible taxonomy-driven classification framework,
- a manually reviewed public disclosure corpus,
- and a foundation for future authorization-security measurement research.

The dataset is best understood as:
- an empirical measurement artifact,
- grounded in publicly observable disclosures,
- designed to support future refinement rather than claim finality.