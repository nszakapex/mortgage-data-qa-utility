# Limitations

- The validation thresholds are generic review bands, not policy rules.
- The project does not determine whether any loan, pool, security, or strategy is attractive.
- The report does not produce credit, valuation, or investment conclusions.
- The tool does not produce financial models, risk ratings, pricing views, or model conclusions.
- Sample rows are synthetic and should not be treated as representative market data.
- The utility validates flat loan-level CSV files and selected pool/research Excel sheet layouts; it is not a full production data platform.
- Date parsing relies on pandas and may need stricter formatting rules in a production setting.
- Research workbook sheet detection is heuristic and may classify unusual column naming as unknown.
- Additional checks may be needed for pool-level fields, remittance data, delinquency statuses, geography, documentation type, occupancy, servicer data, or performance history.
- This is not production-ready validation software and is not an official AD&Co tool.
