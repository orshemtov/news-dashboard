---
description: Trigger the Kafka ingestion worker and monitor article processing
---

Manage the news ingestion pipeline.

If $ARGUMENTS is "start" or empty, start the Kafka consumer worker:
!`cd backend && uv run python -m app.workers.consumer`

If $ARGUMENTS is "status", check the current state:
1. Use the Kafka MCP tools to list topics and describe consumer groups
2. Use the Postgres MCP to query recent article counts:
   - Total articles in the database
   - Articles ingested in the last hour
   - Articles by source

If $ARGUMENTS is "sources", trigger ingestion from all active sources:
!`cd backend && uv run python -c "import asyncio; from app.services.ingestion import IngestionService; asyncio.run(IngestionService().ingest_all_sources())"`

Report the status of the pipeline and any errors encountered.
