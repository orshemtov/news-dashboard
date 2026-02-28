---
description: Run frontend linting, type checking, and tests
---

Run the frontend quality checks:

1. TypeScript type checking:
   !`cd frontend && pnpm tsc --noEmit`

2. ESLint:
   !`cd frontend && pnpm eslint src/`

Report all errors and warnings. For type errors, suggest specific fixes with file paths and line numbers. Group issues by severity.
