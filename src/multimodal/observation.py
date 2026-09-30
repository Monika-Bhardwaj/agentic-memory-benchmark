"""Multimodal observation interface.

Defines the common representation for multimodal observations that can include
images, text, and metadata. Ground truth is never included in metadata.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ImageReference:
    """Reference to a generated or stored image.

    Images are content-addressable: the hash uniquely identifies the image content.
    """
    path: str
    width: int = 64
    height: int = 64
    hash: str = ""

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "width": self.width,
            "height": self.height,
            "hash": self.hash,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ImageReference":
        return cls(
            path=d["path"],
            width=d.get("width", 64),
            height=d.get("height", 64),
            hash=d.get("hash", ""),
        )


@dataclass(frozen=True)
class Observation:
    """A single multimodal observation.

    Contains an image reference, textual description, timestamp, and metadata.
    Ground truth labels are NEVER included in metadata.
    """
    image: ImageReference | None
    text: str
    timestamp: int
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Validate: no ground truth keys in metadata
        forbidden_keys = {"ground_truth", "answer", "label", "success", "correct"}
        for key in forbidden_keys:
            if key in self.metadata:
                raise ValueError(f"Observation metadata cannot contain '{key}'")

    def to_dict(self) -> dict:
        return {
            "image": self.image.to_dict() if self.image else None,
            "text": self.text,
            "timestamp": self.timestamp,
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Observation":
        img = ImageReference.from_dict(d["image"]) if d.get("image") else None
        return cls(
            image=img,
            text=d["text"],
            timestamp=d["timestamp"],
            metadata=dict(d.get("metadata", {})),
        )


class ObservationSequence:
    """An ordered sequence of multimodal observations."""

    def __init__(self, observations: list[Observation]):
        self._observations = list(observations)
        # Validate timestamps are non-decreasing
        for i in range(1, len(self._observations)):
            if self._observations[i].timestamp < self._observations[i - 1].timestamp:
                raise ValueError("Observation timestamps must be non-decreasing")

    def __len__(self) -> int:
        return len(self._observations)

    def __getitem__(self, idx: int) -> Observation:
        return self._observations[idx]

    def __iter__(self):
        return iter(self._observations)

    @property
    def observations(self) -> list[Observation]:
        return list(self._observations)

    def to_dict(self) -> dict:
        return {"observations": [o.to_dict() for o in self._observations]}

    @classmethod
    def from_dict(cls, d: dict) -> "ObservationSequence":
        return cls([Observation.from_dict(o) for o in d["observations"]])
