"""OCR abstraction layer supporting multiple engines."""
from __future__ import annotations

import re
from typing import Iterable

from PIL import Image

from .config import OCREngineConfig

try:  # pragma: no cover - optional dependencies
    import pytesseract
except Exception:  # pragma: no cover
    pytesseract = None

try:  # pragma: no cover
    import easyocr
except Exception:  # pragma: no cover
    easyocr = None


class OCRProcessor:
    """Dispatch OCR requests to the configured engine."""

    def __init__(self, config: OCREngineConfig) -> None:
        self.config = config
        self._easyocr_reader = None

        if self.config.engine == "easyocr" and easyocr:
            self._easyocr_reader = easyocr.Reader(self.config.languages)

    def extract_text(self, image: Image.Image) -> str:
        if self.config.engine == "tesseract":
            return self._extract_with_tesseract(image)
        if self.config.engine == "easyocr":
            return self._extract_with_easyocr(image)
        raise ValueError(f"Unsupported OCR engine: {self.config.engine}")

    def _extract_with_tesseract(self, image: Image.Image) -> str:
        if pytesseract is None:
            raise RuntimeError("pytesseract is not installed")

        config = ""
        if self.config.page_seg_mode is not None:
            config += f" --psm {self.config.page_seg_mode}"

        text = pytesseract.image_to_string(
            image, lang="+".join(self.config.languages), config=config
        )
        return self._mask_sensitive_tokens(text)

    def _extract_with_easyocr(self, image: Image.Image) -> str:
        if self._easyocr_reader is None:
            raise RuntimeError("easyocr is not initialised")

        results = self._easyocr_reader.readtext(image, detail=0)
        return self._mask_sensitive_tokens("\n".join(results))

    def _mask_sensitive_tokens(self, text: str) -> str:
        masked = text
        for pattern, replacement in self._compiled_patterns:
            masked = pattern.sub(replacement, masked)
        return masked

    @property
    def _compiled_patterns(self) -> Iterable[tuple[re.Pattern[str], str]]:
        compiled = []
        for raw in self.config.text_mask_patterns:
            try:
                pattern, replacement = raw.split("=>", 1)
            except ValueError:
                pattern, replacement = raw, "***"
            compiled.append((re.compile(pattern, re.IGNORECASE), replacement))
        return compiled

