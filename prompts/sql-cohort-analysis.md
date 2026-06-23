# SQL Cohort Analysis Prompt

Use this prompt for generic SQL cohort exploration on synthetic/public-style mortgage data.

```text
Write SQL for a synthetic mortgage loan table named mortgage_loans.

Fields:
- loan_id
- agency
- product_type
- vintage
- origination_date
- loan_purpose
- fico
- ltv
- dti
- coupon
- current_balance
- loan_age_months

Create cohort summaries by vintage, agency, product_type, and loan_purpose.
Include row counts, average FICO, average LTV, average DTI, average coupon, and total current balance.

Rules:
- Use neutral data summaries only.
- Do not infer market performance or investment conclusions.
- Do not assume the data is confidential or official.
```

