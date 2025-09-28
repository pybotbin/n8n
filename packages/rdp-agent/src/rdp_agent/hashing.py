"""Utilities for detecting frame changes using perceptual hashes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from PIL import Image

try:  # pragma: no cover - optional dependency at runtime
    import imagehash
except Exception:  # pragma: no cover
    imagehash = None


@dataclass
class HashResult:
    """Container describing perceptual hash information."""

    value: str
    distance: Optional[int] = None


class HashingEngine:
    """Wrapper around the imagehash library with safe fallbacks."""

    def __init__(self, algorithm: str = "phash") -> None:
        self.algorithm = algorithm

    def compute(self, image: Image.Image) -> HashResult:
        if imagehash is None:
            raise RuntimeError(
                "imagehash library is required for perceptual hashing but is not installed"
            )

        hash_func = getattr(imagehash, f"{self.algorithm}")
        value = str(hash_func(image))
        return HashResult(value=value)

    @staticmethod
    def distance(hash_a: str, hash_b: str) -> int:
        if imagehash is None:
            raise RuntimeError("imagehash library is not available")
        return imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_b)

