I need you to pre-filter a dataset of HackerOne vulnerability reports for a BOLA research project.



Read the file data/candidates_raw.json.



For each report, apply these three eligibility criteria:



ELIGIBLE if ALL THREE are true:

1. A specific object is referenced (order, account, document, record, profile, invoice, form) — not just "data" generically

2. Evidence that the attacker accessed an object belonging to ANOTHER user, tenant, or role — not just their own

3. At least ONE technical detail present: endpoint path, HTTP method, object identifier type, or exploitation steps



INELIGIBLE if:

- Pure business logic flaw with no cross-user object access (price manipulation, OTP bypass on own account)

- Authentication bypass with no object reference

- Too vague to determine cross-user boundary

- Different vuln class entirely (XSS, SQLi, SSRF etc.)



For each report output:

- report_id

- program_name  

- severity

- eligible: true or false

- confidence: high or low

- reason: one sentence



Do NOT build a framework or API pipeline 

Just use your own reasoning directly in agent mode for the classification Work through ALL 200 reports systematically. Do not stop early. Write the results to data/candidates_filtered.csv as you go, appending each row immediately so progress is saved if you hit a context limit.



Do not summarize or skip reports. Every report_id must appear in the output.