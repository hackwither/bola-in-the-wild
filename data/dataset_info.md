# Dataset Information

## Dataset Title

BOLA in the Wild: Taxonomy and Meta-Analysis of 100+ HackerOne Disclosures

# Description

This dataset contains manually reviewed public HackerOne disclosures related to Broken Object Level Authorization (BOLA).

The dataset was constructed to support empirical analysis of real-world API authorization failures and to develop an operational BOLA taxonomy grounded in observed disclosures.

# Source

Public HackerOne disclosures collected from the Hacktivity dataset.

Query criteria:

- Weakness tags:
  - IDOR
  - Improper Access Control
- Disclosure period:
  - January 2021 – January 2026
- Sorted by:
  - Upvotes descending
- Sample size:
  - First 200 results

---

# Final Dataset Statistics

| Metric | Value |
|---|---|
| Candidates sampled | 200 |
| Fully classified | 108 |
| Confirmed in-scope BOLA | 86 |
| Out-of-scope / Unclassified | 22 |

---

# Intended Use

This dataset is intended for:

- API security research
- Authorization testing research
- BOLA detection benchmarking
- Taxonomy development
- Security education
- LLM-assisted vulnerability classification research

---

# Limitations

- Public-disclosure bias
- Overrepresentation of mature bug bounty programs
- Sparse disclosure details in some reports
- Potential classifier subjectivity despite review

See `docs/limitations.md` for full discussion.

---

# Citation

Please cite the accompanying paper and repository when using this dataset.
