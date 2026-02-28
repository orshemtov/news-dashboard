---
description: Check ingestion status and trigger article ingestion from sources
---

Manage the news ingestion pipeline.

If $ARGUMENTS is "status" or empty, check the current state:
1. Use the Postgres MCP to query recent article counts:
   - Total articles in the database
   - Articles ingested in the last hour
   - Articles by source
2. Check if the real-time Telegram listener is connected

If $ARGUMENTS is "sources", trigger ingestion from all active sources by calling the `/api/articles` endpoint or checking the backend logs.

Report the status of the pipeline and any errors encountered.
