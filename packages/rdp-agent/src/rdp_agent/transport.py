"""Networking utilities for communicating with the orchestration layer."""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, Optional

import websockets

from .config import AgentConfig

LOGGER = logging.getLogger(__name__)


@dataclass
class FramePayload:
    data: Dict[str, Any]


@dataclass
class ActionPayload:
    frame_id: str
    intent: str
    action: Dict[str, Any]
    confidence: float
    state_delta: Optional[Dict[str, Any]] = None


class AgentTransport:
    """Maintains WebSocket connections for frames and actions."""

    def __init__(self, config: AgentConfig) -> None:
        self.config = config
        self._frame_ws: Optional[websockets.WebSocketClientProtocol] = None
        self._action_ws: Optional[websockets.WebSocketClientProtocol] = None

    async def connect(self) -> None:
        headers = {}
        if self.config.transport.jwt_token:
            headers["Authorization"] = f"Bearer {self.config.transport.jwt_token}"

        LOGGER.info("Connecting to frame websocket %s", self.config.transport.websocket_endpoint)
        self._frame_ws = await websockets.connect(
            self.config.transport.websocket_endpoint,
            extra_headers=headers,
            ping_interval=10,
            ping_timeout=10,
            max_queue=None,
        )

        actions_endpoint = (
            self.config.transport.websocket_actions_endpoint
            or self.config.transport.websocket_endpoint.replace("frames", "actions")
        )

        LOGGER.info("Connecting to action websocket %s", actions_endpoint)
        self._action_ws = await websockets.connect(
            actions_endpoint,
            extra_headers=headers,
            ping_interval=10,
            ping_timeout=10,
            max_queue=None,
        )

    async def send_frame(self, payload: FramePayload) -> None:
        if not self._frame_ws:
            raise RuntimeError("Frame websocket not connected")
        await self._frame_ws.send(json.dumps(payload.data))

    async def iter_actions(self) -> AsyncGenerator[ActionPayload, None]:
        if not self._action_ws:
            raise RuntimeError("Action websocket not connected")

        async for raw in self._action_ws:
            data = json.loads(raw)
            yield ActionPayload(
                frame_id=data.get("frame_id", ""),
                intent=data.get("intent", "noop"),
                action=data.get("action", {}),
                confidence=float(data.get("confidence", 0.0)),
                state_delta=data.get("state_delta"),
            )

    async def close(self) -> None:
        if self._frame_ws and not self._frame_ws.closed:
            await self._frame_ws.close()
        if self._action_ws and not self._action_ws.closed:
            await self._action_ws.close()

