---
description: Screenshot the running frontend and review the UI
agent: ui-reviewer
---

Review the frontend UI by navigating to the running dev server and taking screenshots.

If $ARGUMENTS specifies a route (e.g., "/feed", "/search", "/sources"), navigate to that route.
Otherwise, start with the main feed page at http://localhost:5173/feed.

Use the Playwright MCP tools to:
1. Navigate to the target page
2. Take a snapshot and screenshot (always save screenshots with the `.opencode/screenshots/` prefix, e.g. `.opencode/screenshots/feed-review.png`)
3. Analyze the UI for layout, spacing, accessibility, and component usage
4. Suggest specific improvements with file paths and Tailwind classes

After analysis, ask if I should apply any suggested changes and re-screenshot to verify.
