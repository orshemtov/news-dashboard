---
description: Start the full development environment (infrastructure + backend + frontend)
---

Start the full development environment for the news-dashboard project.

Run the following steps in order:

1. Start infrastructure services (PostgreSQL):
   !`mise run infra`

2. Wait a few seconds for services to be healthy, then start the backend:
   !`cd backend && mise run serve`

3. In parallel, start the frontend:
   !`cd frontend && mise run serve`

Or use the combined command from the project root:
   !`mise run dev`

Report the status of each service and any errors encountered.
The backend runs at http://localhost:8000 and the frontend at http://localhost:5173.
