# Debug Prompt

Use this prompt when debugging the project with a coding agent.

```text
You are helping debug a Python 3.12 pandas project called mortgage-data-qa-utility.

Rules:
- Use synthetic/public-style data only.
- Do not claim the project is an official company tool.
- Do not invent financial conclusions.
- Keep changes simple and readable.
- Run pytest before finishing.

Task:
1. Reproduce the failure.
2. Identify the smallest relevant code path.
3. Patch the issue.
4. Add or update a focused test.
5. Report commands run and verification.
```

