# Data QA Prompt

Use this prompt to ask an agent to review a synthetic mortgage-style CSV.

```text
Review this synthetic/public-style mortgage CSV for data quality only.

Check:
- Required columns.
- Missing values.
- Duplicate loan_id values.
- Malformed origination dates.
- Invalid FICO, LTV, and DTI ranges.
- Invalid loan purpose values.
- Negative balances.
- Suspicious coupon values.

Return:
- A short QA status.
- Findings by severity.
- Rows and columns affected.
- Suggested remediation steps.

Do not make credit, valuation, trading, or investment conclusions.
Do not use confidential company data.
```

