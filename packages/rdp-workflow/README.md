# n8n Workflow: Real-Time RDP Screen Analysis

This package documents the n8n workflow orchestrating the end-to-end
pipeline described in the technical specification. The workflow file
`workflow.json` can be imported into an n8n instance to provision all
required triggers, queues, OpenAI interactions and decision logic.

## Workflow Topology

1. **WebSocket Ingest (Custom Node)** – Accepts frame payloads from
   agents, performs authentication and forwards them to Redis Streams.
2. **Deduplication & Throttle** – Drops repeated frames and enforces
   rate limits per agent.
3. **Context Builder** – Assembles the ChatGPT prompt with OCR text,
   signals, agent state and optional image references.
4. **OpenAI Chat** – Calls the Chat Completions API with structured
   system prompts enforcing JSON output.
5. **Decision Parser** – Validates the JSON response and determines the
   resulting intent/action/state delta.
6. **Redis State Update** – Persists the state delta for future frames.
7. **WebSocket Egress (Custom Node)** – Streams resulting actions back to
   the originating agent.
8. **Logging & Metrics** – Writes frame/decision metadata to PostgreSQL
   and emits Prometheus metrics.

## Import Instructions

1. Open the n8n UI and navigate to *Workflows → Import*.
2. Upload `workflow.json` located in this directory.
3. Configure credentials for Redis, PostgreSQL and OpenAI using n8n’s
   credential store.
4. Deploy the workflow in *Active* mode.

