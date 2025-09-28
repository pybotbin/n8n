"""Configuration model for the Windows RDP agent.

This module centralises configuration handling so that the rest of the
agent can remain stateless. The configuration values are loaded from a
combination of environment variables, optional JSON/YAML files and
runtime overrides received from the orchestration backend.

The configuration surface mirrors the parameters defined in the
technical specification, covering frame capture, OCR, change detection
and networking behaviour.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import json
import os


@dataclass
class OCREngineConfig:
    """Runtime configuration for the OCR subsystem."""

    engine: str = "tesseract"
    languages: List[str] = field(default_factory=lambda: ["eng"])
    text_mask_patterns: List[str] = field(default_factory=list)
    page_seg_mode: Optional[int] = None


@dataclass
class ROIConfig:
    """Region of interest configuration."""

    x: int = 0
    y: int = 0
    width: Optional[int] = None
    height: Optional[int] = None


@dataclass
class TransportConfig:
    """Network transport options."""

    websocket_endpoint: str = "wss://localhost:5678/ws"
    websocket_actions_endpoint: Optional[str] = None
    http_fallback_endpoint: Optional[str] = None
    jwt_token: Optional[str] = None
    verify_tls: bool = True
    connect_timeout: float = 5.0
    request_timeout: float = 5.0
    max_retries: int = 2


@dataclass
class BackpressurePolicy:
    """Parameters controlling adaptive backpressure."""

    max_llm_calls_per_second: float = 2.0
    min_frame_interval_ms: int = 100
    image_mode_enabled: bool = True
    queue_limit: int = 50


@dataclass
class AgentConfig:
    """Top level configuration container for the RDP agent."""

    agent_id: str = "agent-unknown"
    capture_fps: float = 10.0
    roi: ROIConfig = field(default_factory=ROIConfig)
    jpeg_quality: int = 80
    capture_scale: float = 1.0
    dedupe_threshold: float = 6.0  # perceptual hash distance threshold
    crc_roi: bool = False
    enable_ui_detection: bool = True
    ocr: OCREngineConfig = field(default_factory=OCREngineConfig)
    transport: TransportConfig = field(default_factory=TransportConfig)
    backpressure: BackpressurePolicy = field(default_factory=BackpressurePolicy)
    metrics_push_endpoint: Optional[str] = None

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "AgentConfig":
        """Load configuration from environment and optional JSON file."""

        config = cls()

        # Load from JSON file if provided
        if path and path.exists():
            with path.open("r", encoding="utf8") as handle:
                raw = json.load(handle)
            config = cls.from_dict(raw)

        # Override with environment variables if present
        env_agent_id = os.getenv("RDP_AGENT_ID")
        if env_agent_id:
            config.agent_id = env_agent_id

        capture_fps = os.getenv("RDP_CAPTURE_FPS")
        if capture_fps:
            config.capture_fps = float(capture_fps)

        jwt_token = os.getenv("RDP_AGENT_JWT")
        if jwt_token:
            config.transport.jwt_token = jwt_token

        return config

    @classmethod
    def from_dict(cls, raw: Dict[str, object]) -> "AgentConfig":
        """Create a configuration object from a dictionary."""

        roi = ROIConfig(**raw.get("roi", {}))
        ocr = OCREngineConfig(**raw.get("ocr", {}))
        transport = TransportConfig(**raw.get("transport", {}))
        backpressure = BackpressurePolicy(**raw.get("backpressure", {}))

        return cls(
            agent_id=raw.get("agent_id", "agent-unknown"),
            capture_fps=float(raw.get("capture_fps", 10.0)),
            roi=roi,
            jpeg_quality=int(raw.get("jpeg_quality", 80)),
            capture_scale=float(raw.get("capture_scale", 1.0)),
            dedupe_threshold=float(raw.get("dedupe_threshold", 6.0)),
            crc_roi=bool(raw.get("crc_roi", False)),
            enable_ui_detection=bool(raw.get("enable_ui_detection", True)),
            ocr=ocr,
            transport=transport,
            backpressure=backpressure,
            metrics_push_endpoint=raw.get("metrics_push_endpoint"),
        )

    def to_dict(self) -> Dict[str, object]:
        """Serialise the configuration into a JSON-compatible dictionary."""

        return {
            "agent_id": self.agent_id,
            "capture_fps": self.capture_fps,
            "roi": self.roi.__dict__,
            "jpeg_quality": self.jpeg_quality,
            "capture_scale": self.capture_scale,
            "dedupe_threshold": self.dedupe_threshold,
            "crc_roi": self.crc_roi,
            "enable_ui_detection": self.enable_ui_detection,
            "ocr": self.ocr.__dict__,
            "transport": self.transport.__dict__,
            "backpressure": self.backpressure.__dict__,
            "metrics_push_endpoint": self.metrics_push_endpoint,
        }

