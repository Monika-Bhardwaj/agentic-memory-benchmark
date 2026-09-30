"""Procedural multimodal scene generator.

Generates deterministic visual scenes with objects, colors, positions, and
spatial relationships. All scenes are synthetic with invented entities to
prevent pretraining prior leakage.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field


# Frozen color palette (invented names to avoid real-world associations)
_COLORS = [
    "crimson", "azure", "amber", "verdant", "violet",
    "coral", "indigo", "scarlet", "teal", "golden",
]

# Frozen shape types
_SHAPES = ["circle", "square", "triangle", "diamond", "pentagon"]

# Frozen spatial relationships
_RELATIONSHIPS = ["above", "below", "left_of", "right_of", "inside", "outside"]


@dataclass(frozen=True)
class SceneObject:
    """An object in a visual scene."""
    object_id: str
    shape: str
    color: str
    size: int  # 1-5
    x: int  # 0-100
    y: int  # 0-100

    def describe(self) -> str:
        return f"a {self.color} {self.shape} (size {self.size}) at position ({self.x}, {self.y})"


@dataclass(frozen=True)
class Scene:
    """A complete visual scene with objects and relationships."""
    scene_id: str
    objects: tuple[SceneObject, ...]
    relationships: tuple[tuple[str, str, str], ...]  # (obj1_id, relationship, obj2_id)
    timestamp: int
    description: str = ""

    def describe(self) -> str:
        parts = ["The scene contains:"]
        for obj in self.objects:
            parts.append(f"  - {obj.describe()}")
        if self.relationships:
            parts.append("Relationships:")
            for obj1, rel, obj2 in self.relationships:
                parts.append(f"  - {obj1} is {rel.replace('_', ' ')} {obj2}")
        return "\n".join(parts)


class SceneGenerator:
    """Deterministic procedural scene generator.

    Given a seed, generates identical scenes. All entities are invented.
    """

    def __init__(self, seed: int):
        self._rng = random.Random(seed)
        self._seed = seed

    def generate_scene(
        self,
        n_objects: int = 3,
        n_distractors: int = 0,
        timestamp: int = 0,
    ) -> Scene:
        """Generate a scene with the specified number of objects and distractors."""
        scene_id = f"scene_{self._seed}_{timestamp}"

        # Generate main objects
        objects = []
        used_positions = set()
        for i in range(n_objects):
            obj = self._generate_object(f"obj_{i}", used_positions)
            objects.append(obj)

        # Generate distractor objects
        for i in range(n_distractors):
            obj = self._generate_object(f"dist_{i}", used_positions)
            objects.append(obj)

        # Generate relationships between main objects
        relationships = []
        if n_objects >= 2:
            n_rel = min(self._rng.randint(1, 3), n_objects * (n_objects - 1) // 2)
            for _ in range(n_rel):
                i, j = self._rng.sample(range(n_objects), 2)
                rel = self._rng.choice(_RELATIONSHIPS)
                relationships.append((objects[i].object_id, rel, objects[j].object_id))

        # Generate description
        description = self._generate_description(objects[:n_objects], relationships)

        return Scene(
            scene_id=scene_id,
            objects=tuple(objects),
            relationships=tuple(relationships),
            timestamp=timestamp,
            description=description,
        )

    def _generate_object(self, obj_id: str, used_positions: set) -> SceneObject:
        """Generate a single object with a unique position."""
        max_attempts = 100
        for _ in range(max_attempts):
            x = self._rng.randint(5, 95)
            y = self._rng.randint(5, 95)
            if (x, y) not in used_positions:
                used_positions.add((x, y))
                return SceneObject(
                    object_id=obj_id,
                    shape=self._rng.choice(_SHAPES),
                    color=self._rng.choice(_COLORS),
                    size=self._rng.randint(1, 5),
                    x=x,
                    y=y,
                )
        # Fallback: use a position based on attempt count
        return SceneObject(
            object_id=obj_id,
            shape=self._rng.choice(_SHAPES),
            color=self._rng.choice(_COLORS),
            size=self._rng.randint(1, 5),
            x=self._rng.randint(5, 95),
            y=self._rng.randint(5, 95),
        )

    def _generate_description(
        self,
        objects: list[SceneObject],
        relationships: list[tuple[str, str, str]],
    ) -> str:
        """Generate a textual description of the scene."""
        parts = ["In the scene:"]
        for obj in objects:
            parts.append(f"There is {obj.describe()}.")
        for obj1, rel, obj2 in relationships:
            parts.append(f"The {obj1} is {rel.replace('_', ' ')} the {obj2}.")
        return " ".join(parts)

    def generate_temporal_sequence(
        self,
        n_steps: int = 3,
        n_objects: int = 3,
        n_distractors: int = 0,
    ) -> list[Scene]:
        """Generate a temporal sequence of scenes with controlled changes."""
        scenes = []
        for t in range(n_steps):
            scene = self.generate_scene(
                n_objects=n_objects,
                n_distractors=n_distractors,
                timestamp=t,
            )
            scenes.append(scene)
        return scenes
