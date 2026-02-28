---
description: Run the Python backend test suite with pytest
---

Run the backend test suite with coverage reporting.

!`cd backend && uv run pytest --cov=src/app --cov-report=term-missing -v`

Analyze the output:
- Report which tests passed and failed
- Show coverage percentages for each module
- For any failures, read the relevant source files and suggest fixes
- If no tests exist yet, suggest which tests should be written first based on the codebase
