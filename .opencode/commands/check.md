---
description: Run all linters and type checkers across backend and frontend
---

Run the full quality check suite for the entire project.

**Backend checks:**

1. Ruff linting:
   !`cd backend && uv run ruff check src/`

2. Ruff formatting check:
   !`cd backend && uv run ruff format --check src/`

3. Type checking (ty):
   !`cd backend && uv run ty check src/app/`

**Frontend checks:**

4. TypeScript type checking:
   !`cd frontend && pnpm tsc --noEmit`

5. ESLint:
   !`cd frontend && pnpm eslint src/`

Summarize all issues found, grouped by:
- Errors (must fix)
- Warnings (should fix)
- Style issues (nice to fix)

Suggest fixes for the most critical issues first.
