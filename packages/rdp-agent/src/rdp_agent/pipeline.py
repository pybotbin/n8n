"""Frame processing pipeline orchestrating capture, OCR and transport."""
from __future__ import annotations

import base64
import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from .capture import ScreenCapturer
from .config import AgentConfig
from .hashing import HashingEngine
from .metrics import MetricsReporter
from .ocr import OCRProcessor
from .signals import SignalExtractor
from .state import AgentState
from .transport import AgentTransport, FramePayload

LOGGER = logging.getLogger(__name__)


@dataclass
class FrameContext:
    frame_id: str
    hash_value: str


class ProcessingPipeline:
    """High level pipeline implementing specification requirements."""

    def __init__(self, config: AgentConfig, state_path: Optional[Path] = None) -> None:
        self.config = config
        self.capturer = ScreenCapturer()
        self.hashing = HashingEngine()
        self.ocr = OCRProcessor(config.ocr)
        self.signals = SignalExtractor([])
        self.transport = AgentTransport(config)
        self._state_path = state_path
        self.state = AgentState.load(state_path) if state_path else AgentState()
        self.metrics = MetricsReporter(config.metrics_push_endpoint)
        self._last_hash: Optional[str] = None

    async def start(self) -> None:
        await self.transport.connect()
        await self.metrics.start()

    async def stop(self) -> None:
        await self.metrics.stop()
        await self.transport.close()
        self._persist_state()

    async def run_once(self) -> Optional[FrameContext]:
        roi = None
        if self.config.roi.width and self.config.roi.height:
            roi = (
                self.config.roi.x,
                self.config.roi.y,
                self.config.roi.width,
                self.config.roi.height,
            )

        capture = self.capturer.capture(roi=roi)
        hash_result = self.hashing.compute(capture.image)

        if self._last_hash and HashingEngine.distance(self._last_hash, hash_result.value) < self.config.dedupe_threshold:
            LOGGER.debug("Frame %s skipped due to deduplication", hash_result.value)
            return None

        self._last_hash = hash_result.value
        frame_id = f"{self.config.agent_id}-{uuid.uuid4().hex[:8]}"

        ocr_text = self.ocr.extract_text(capture.image)
        signals = self.signals.detect(capture.image)

        payload = self._build_payload(frame_id, capture, hash_result.value, ocr_text, signals)
        await self.transport.send_frame(FramePayload(data=payload))

        metrics = self.metrics.snapshot(
            frame_id=frame_id,
            hash=hash_result.value,
            signals=signals,
        )
        await self.metrics.push(metrics)

        return FrameContext(frame_id=frame_id, hash_value=hash_result.value)

    def _build_payload(
        self,
        frame_id: str,
        capture,
        hash_value: str,
        ocr_text: str,
        signals: Dict[str, bool],
    ) -> Dict[str, object]:
        jpeg_bytes = capture.to_jpeg_bytes(self.config.jpeg_quality)
        return {
            "agent_id": self.config.agent_id,
            "ts": capture.timestamp,
            "frame_id": frame_id,
            "roi": list(capture.roi),
            "p_hash": hash_value,
            "ocr_text": ocr_text,
            "signals": signals,
            "img_b64": base64.b64encode(jpeg_bytes).decode("ascii"),
            "meta": {
                "screen": "unknown",
            },
        }

    def _persist_state(self) -> None:
        if self._state_path:
            self.state.save(self._state_path)

