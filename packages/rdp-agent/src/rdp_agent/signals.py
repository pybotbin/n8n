"""UI signal extraction and heuristic detection."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

import numpy as np
from PIL import Image

try:  # pragma: no cover - optional dependency
    import cv2
except Exception:  # pragma: no cover
    cv2 = None


@dataclass
class Template:
    name: str
    path: str
    threshold: float = 0.85


class SignalExtractor:
    """Detect UI templates and compute binary signals."""

    def __init__(self, templates: Iterable[Template]) -> None:
        self.templates = list(templates)
        self._loaded: Dict[str, np.ndarray] = {}

    def detect(self, image: Image.Image) -> Dict[str, bool]:
        if cv2 is None:
            return {template.name: False for template in self.templates}

        result = {}
        screenshot = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2GRAY)

        for template in self.templates:
            tpl = self._load_template(template)
            res = cv2.matchTemplate(screenshot, tpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            result[template.name] = bool(max_val >= template.threshold)
        return result

    def _load_template(self, template: Template) -> np.ndarray:
        if template.name in self._loaded:
            return self._loaded[template.name]
        tpl = cv2.imread(template.path, cv2.IMREAD_GRAYSCALE)
        if tpl is None:
            raise FileNotFoundError(f"Template not found: {template.path}")
        self._loaded[template.name] = tpl
        return tpl

