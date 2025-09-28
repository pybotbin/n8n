# Real-Time RDP Screen Analysis System

This document summarises the system modules implemented in this
repository according to the technical specification.

## Components

- **Windows Agent (Python)** – Located in `packages/rdp-agent`. Captures
  frames, performs OCR, deduplicates, emits telemetry and applies
  downlink actions from the orchestrator.
- **n8n Workflow** – Located in `packages/rdp-workflow`. Provides
  ingestion, throttling, LLM prompt building, OpenAI integration, state
  management, logging and action streaming.
- **Documentation** – This folder consolidates architecture guidance and
  deployment steps.

## Data Flow

1. The agent captures frames (`rdp_agent.capture.ScreenCapturer`), runs
   OCR (`rdp_agent.ocr.OCRProcessor`) and computes perceptual hashes
   (`rdp_agent.hashing.HashingEngine`).
2. The payload is streamed through WebSockets using
   `rdp_agent.transport.AgentTransport` and processed by the n8n workflow
   (`workflow.json`).
3. n8n prepares context, calls ChatGPT and emits actions to the agent.
   Actions are executed via `rdp_agent.actions.ActionExecutor`.
4. Metrics and decisions are logged to Redis/PostgreSQL according to the
   workflow definitions.

