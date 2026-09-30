"""Image renderer for procedural scenes.

Renders scenes to PNG images using only stdlib (no external dependencies).
Images are deterministic given the scene specification.
"""

from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path

from src.multimodal.scene_generator import Scene


class ImageRenderer:
    """Renders scenes to PNG images using stdlib only.

    Uses a simple encoding: each scene is rendered as a colored grid where
    objects are represented by their color at their position.
    """

    def __init__(self, output_dir: str | Path = "results/images"):
        self._output_dir = Path(output_dir)
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def render(self, scene: Scene, width: int = 64, height: int = 64) -> str:
        """Render a scene to a PNG image and return the file path.

        The image is a simple grid where each object is represented by
        a colored cell at its position. The color is derived from the
        object's color name (deterministic mapping).
        """
        # Create pixel grid
        grid = [[(255, 255, 255) for _ in range(width)] for _ in range(height)]

        # Place objects on grid
        for obj in scene.objects:
            px = int(obj.x * width / 100)
            py = int(obj.y * height / 100)
            color = self._color_to_rgb(obj.color)
            size = max(1, obj.size)
            for dx in range(-size, size + 1):
                for dy in range(-size, size + 1):
                    nx, ny = px + dx, py + dy
                    if 0 <= nx < width and 0 <= ny < height:
                        grid[ny][nx] = color

        # Generate deterministic hash
        scene_str = f"{scene.scene_id}_{width}_{height}"
        img_hash = hashlib.sha256(scene_str.encode()).hexdigest()[:16]

        # Write PNG
        filename = f"{scene.scene_id}_{img_hash}.png"
        filepath = self._output_dir / filename
        self._write_png(filepath, grid, width, height)

        return str(filepath)

    def _color_to_rgb(self, color_name: str) -> tuple[int, int, int]:
        """Map color name to RGB (deterministic)."""
        color_map = {
            "crimson": (220, 20, 60),
            "azure": (0, 127, 255),
            "amber": (255, 191, 0),
            "verdant": (34, 139, 34),
            "violet": (238, 130, 238),
            "coral": (255, 127, 80),
            "indigo": (75, 0, 130),
            "scarlet": (255, 36, 0),
            "teal": (0, 128, 128),
            "golden": (255, 215, 0),
        }
        return color_map.get(color_name, (128, 128, 128))

    def _write_png(self, filepath: Path, grid: list[list[tuple[int, int, int]]], width: int, height: int) -> None:
        """Write a PNG file using only stdlib."""
        # PNG signature
        signature = b'\x89PNG\r\n\x1a\n'

        # IHDR chunk
        ihdr_data = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
        ihdr = self._make_chunk(b'IHDR', ihdr_data)

        # IDAT chunk (compressed image data)
        raw_data = b''
        for row in grid:
            raw_data += b'\x00'  # filter byte
            for r, g, b in row:
                raw_data += bytes([r, g, b])

        compressed = zlib.compress(raw_data)
        idat = self._make_chunk(b'IDAT', compressed)

        # IEND chunk
        iend = self._make_chunk(b'IEND', b'')

        # Write file
        with open(filepath, 'wb') as f:
            f.write(signature + ihdr + idat + iend)

    def _make_chunk(self, chunk_type: bytes, data: bytes) -> bytes:
        """Create a PNG chunk."""
        chunk = chunk_type + data
        crc = zlib.crc32(chunk) & 0xffffffff
        return struct.pack('>I', len(data)) + chunk + struct.pack('>I', crc)
