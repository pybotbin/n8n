"""Action execution layer for applying LLM decisions."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Optional

try:  # pragma: no cover - optional dependency
    import pyautogui
except Exception:  # pragma: no cover
    pyautogui = None

LOGGER = logging.getLogger(__name__)


@dataclass
class Action:
    type: str
    target: Optional[str] = None
    value: Optional[str] = None


class ActionExecutor:
    """Execute actions received from the orchestration layer."""

    def __init__(self) -> None:
        if pyautogui:
            pyautogui.FAILSAFE = False

    async def execute(self, action: Action) -> None:
        handler = getattr(self, f"_handle_{action.type}", None)
        if not handler:
            LOGGER.warning("No handler for action type %s", action.type)
            return
        await handler(action)

    async def _handle_click(self, action: Action) -> None:
        if not pyautogui:
            LOGGER.warning("pyautogui not installed; cannot click")
            return
        if not action.target:
            LOGGER.warning("Click action missing target coordinates")
            return
        x, y = map(int, action.target.split(","))
        pyautogui.click(x, y)

    async def _handle_type(self, action: Action) -> None:
        if not pyautogui:
            LOGGER.warning("pyautogui not installed; cannot type")
            return
        text = action.value or ""
        pyautogui.typewrite(text)

    async def _handle_hotkey(self, action: Action) -> None:
        if not pyautogui:
            LOGGER.warning("pyautogui not installed; cannot send hotkey")
            return
        if not action.value:
            LOGGER.warning("Hotkey action missing value")
            return
        keys = [key.strip() for key in action.value.split("+")]
        pyautogui.hotkey(*keys)

