"""Agent metrics collection and publishing."""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import aiohttp

LOGGER = logging.getLogger(__name__)


@dataclass
class MetricsSample:
    timestamp: float
    payload: Dict[str, Any]


@dataclass
class MetricsReporter:
    endpoint: Optional[str]
    _session: Optional[aiohttp.ClientSession] = field(default=None, init=False)

    async def start(self) -> None:
        if self.endpoint and not self._session:
            self._session = aiohttp.ClientSession()

    async def stop(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    async def push(self, sample: MetricsSample) -> None:
        if not self.endpoint or not self._session:
            return
        try:
            async with self._session.post(
                self.endpoint,
                json={"timestamp": sample.timestamp, **sample.payload},
                timeout=5,
            ) as response:
                if response.status >= 400:
                    LOGGER.warning("Metrics push failed with status %s", response.status)
        except Exception as exc:  # pragma: no cover - network errors runtime only
            LOGGER.debug("Metrics push failed: %s", exc)

    def snapshot(self, **values: Any) -> MetricsSample:
        return MetricsSample(timestamp=time.time(), payload=values)

