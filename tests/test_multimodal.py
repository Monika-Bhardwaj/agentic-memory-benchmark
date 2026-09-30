"""Tests for multimodal observation interface and scene generation."""

import pytest

from src.multimodal.observation import ImageReference, Observation, ObservationSequence
from src.multimodal.scene_generator import SceneGenerator


class TestImageReference:
    def test_create(self):
        img = ImageReference(path="test.png", width=64, height=64, hash="abc123")
        assert img.path == "test.png"
        assert img.width == 64
        assert img.height == 64
        assert img.hash == "abc123"

    def test_to_dict(self):
        img = ImageReference(path="test.png", width=64, height=64, hash="abc123")
        d = img.to_dict()
        assert d["path"] == "test.png"
        assert d["width"] == 64
        assert d["hash"] == "abc123"

    def test_from_dict(self):
        d = {"path": "test.png", "width": 64, "height": 64, "hash": "abc123"}
        img = ImageReference.from_dict(d)
        assert img.path == "test.png"
        assert img.width == 64


class TestObservation:
    def test_create_text_only(self):
        obs = Observation(image=None, text="Hello", timestamp=1)
        assert obs.image is None
        assert obs.text == "Hello"
        assert obs.timestamp == 1

    def test_create_with_image(self):
        img = ImageReference(path="test.png")
        obs = Observation(image=img, text="Hello", timestamp=1)
        assert obs.image is not None
        assert obs.image.path == "test.png"

    def test_no_ground_truth_in_metadata(self):
        with pytest.raises(ValueError, match="ground_truth"):
            Observation(image=None, text="Hello", timestamp=1, metadata={"ground_truth": "answer"})

    def test_serialization_roundtrip(self):
        img = ImageReference(path="test.png", hash="abc")
        obs = Observation(image=img, text="Hello", timestamp=1, metadata={"source": "test"})
        d = obs.to_dict()
        obs2 = Observation.from_dict(d)
        assert obs2.text == "Hello"
        assert obs2.timestamp == 1
        assert obs2.metadata["source"] == "test"


class TestObservationSequence:
    def test_create(self):
        obs1 = Observation(image=None, text="First", timestamp=1)
        obs2 = Observation(image=None, text="Second", timestamp=2)
        seq = ObservationSequence([obs1, obs2])
        assert len(seq) == 2
        assert seq[0].text == "First"
        assert seq[1].text == "Second"

    def test_non_decreasing_timestamps(self):
        obs1 = Observation(image=None, text="First", timestamp=2)
        obs2 = Observation(image=None, text="Second", timestamp=1)
        with pytest.raises(ValueError, match="non-decreasing"):
            ObservationSequence([obs1, obs2])


class TestSceneGenerator:
    def test_determinism(self):
        gen1 = SceneGenerator(seed=42)
        gen2 = SceneGenerator(seed=42)
        scene1 = gen1.generate_scene(n_objects=3, timestamp=0)
        scene2 = gen2.generate_scene(n_objects=3, timestamp=0)
        assert scene1.scene_id == scene2.scene_id
        assert len(scene1.objects) == len(scene2.objects)

    def test_different_seeds(self):
        gen1 = SceneGenerator(seed=42)
        gen2 = SceneGenerator(seed=43)
        scene1 = gen1.generate_scene(n_objects=3, timestamp=0)
        scene2 = gen2.generate_scene(n_objects=3, timestamp=0)
        # Different seeds should produce different scenes (with high probability)
        assert scene1.scene_id != scene2.scene_id

    def test_object_count(self):
        gen = SceneGenerator(seed=42)
        scene = gen.generate_scene(n_objects=5, n_distractors=2, timestamp=0)
        assert len(scene.objects) == 7  # 5 main + 2 distractors

    def test_temporal_sequence(self):
        gen = SceneGenerator(seed=42)
        scenes = gen.generate_temporal_sequence(n_steps=3, n_objects=3)
        assert len(scenes) == 3
        assert scenes[0].timestamp == 0
        assert scenes[1].timestamp == 1
        assert scenes[2].timestamp == 2
