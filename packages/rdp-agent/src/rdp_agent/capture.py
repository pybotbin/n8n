"""Screen capture and preprocessing pipeline."""
from __future__ import annotations

import io
import time
from dataclasses import dataclass
from typing import Optional, Tuple

from PIL import Image

try:  # pragma: no cover - optional dependency at runtime
    import mss
except Exception:  # pragma: no cover - the module is optional during tests
    mss = None


@dataclass
class CaptureResult:
    """Represents a captured frame and metadata."""

    image: Image.Image
    timestamp: float
    roi: Tuple[int, int, int, int]

    def to_jpeg_bytes(self, quality: int = 80) -> bytes:
        """Encode the captured image to JPEG."""

        buffer = io.BytesIO()
        self.image.save(buffer, format="JPEG", quality=quality)
        return buffer.getvalue()


class ScreenCapturer:
    """Capture frames from the active display or RDP session."""

    def __init__(self, monitor: int = 0):
        self._monitor_index = monitor

    def capture(self, roi: Optional[Tuple[int, int, int, int]] = None) -> CaptureResult:
        if mss is None:
            raise RuntimeError(
                "mss library is required for screen capture but is not installed"
            )

        with mss.mss() as sct:
            monitor = sct.monitors[self._monitor_index]
            if roi:
                monitor = {
                    "left": roi[0],
                    "top": roi[1],
                    "width": roi[2],
                    "height": roi[3],
                }

            raw = sct.grab(monitor)
            image = Image.frombytes("RGB", raw.size, raw.rgb)
            timestamp = time.time()
            return CaptureResult(image=image, timestamp=timestamp, roi=(
                monitor["left"],
                monitor["top"],
                monitor["width"],
                monitor["height"],
            ))

