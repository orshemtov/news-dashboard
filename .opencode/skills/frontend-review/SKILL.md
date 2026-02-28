---
name: frontend-review
description: Screenshot-driven UI review workflow using Playwright MCP to iteratively inspect, analyze, and improve the frontend
---

## What this skill does

Enables an iterative UI review loop: screenshot the running frontend, analyze what you see, suggest or apply fixes, re-screenshot to verify. This is the core workflow for being a good frontend engineering assistant on this project.

## Prerequisites

- The frontend dev server must be running at `http://localhost:5173` (start with `pnpm dev` in `frontend/` or `mise run dev` from the project root)
- The Playwright MCP server must be enabled (configured in `.opencode/opencode.json`)
- The backend should be running at `http://localhost:8000` if you need real data (start with `cd backend && mise run serve`)

## The review loop

### Step 1: Navigate and capture

Use Playwright MCP tools in this order:

```
browser_navigate -> http://localhost:5173/<route>
browser_snapshot  -> get the accessibility tree (structure, text, roles)
browser_take_screenshot -> get visual output
```

### Step 2: Analyze

Evaluate the screenshot and snapshot against these criteria:

- **Layout**: Is the grid/flex layout consistent? Are elements properly aligned?
- **Spacing**: Does it follow Tailwind's 4px spacing scale? Are margins/padding consistent?
- **Typography**: Is the type hierarchy clear? Are font sizes appropriate?
- **Color & Contrast**: Do text/background combinations meet WCAG AA (4.5:1 ratio)?
- **Components**: Are shadcn/ui primitives used correctly? Any custom components that should use primitives?
- **Responsiveness**: Does the layout work at different viewport sizes?
- **States**: Are loading, empty, and error states handled?
- **Accessibility**: Are interactive elements keyboard-accessible? Do images have alt text? Are ARIA roles correct?

### Step 3: Suggest or apply fixes

Reference specific files and components:

- Pages are in `frontend/src/pages/` (Feed.tsx, Search.tsx, Sources.tsx, Stats.tsx, Chat.tsx)
- Reusable components are in `frontend/src/components/` (organized by feature: feed/, search/, sources/, stats/, chat/)
- UI primitives are in `frontend/src/components/ui/` (shadcn/ui)
- Layout components are in `frontend/src/components/layout/`
- Use `cn()` from `frontend/src/lib/utils.ts` for conditional classes

### Step 4: Verify

After applying changes:

```
browser_navigate -> http://localhost:5173/<same-route>  (force reload)
browser_take_screenshot -> compare with before
```

Confirm the fix looks correct. If not, iterate.

## Route-specific guidance

| Route | Key components | What to look for |
|-------|---------------|-----------------|
| `/feed` | ArticleCard, filters, pagination | Card grid layout, image loading, tag badges, date formatting |
| `/search` | Search input, mode selector, results | Input focus states, mode toggle, result highlighting, empty state |
| `/sources` | Source list, add dialog, status badges | Table alignment, dialog form layout, status indicators |
| `/stats` | Stat cards, charts | Number formatting, chart responsiveness, card grid |
| `/chat` | Message list, input area, citations | Message bubble alignment, citation links, scroll behavior |

## Interaction testing

Use Playwright MCP tools to test interactive elements:

```
browser_click -> click buttons, links, tabs
browser_type  -> type in search fields, forms
browser_fill  -> fill form fields
```

Verify that interactions produce the expected UI changes by re-snapshotting after each action.
