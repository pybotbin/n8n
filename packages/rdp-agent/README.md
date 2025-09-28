# RDP Agent

This package contains the Python implementation of the Windows-side agent
for the "Real-Time RDP Screen Analysis" system. It captures screen
frames, extracts OCR and UI signals, deduplicates frames using perceptual
hashing and streams structured payloads to the n8n orchestrator using
WebSockets.

## Features

- Configurable frame capture rate and region of interest.
- OCR abstraction with support for both Tesseract and EasyOCR.
- Template-based UI signal detection using OpenCV.
- Perceptual hashing for duplicate frame suppression.
- WebSocket transport with action downlink and metrics publishing.

## Usage

```bash
python -m rdp_agent.main --config agent.json --loop
```

The agent configuration file mirrors the fields defined in
`rdp_agent.config.AgentConfig`.

