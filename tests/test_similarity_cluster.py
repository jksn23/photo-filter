import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from src.core.similarity.similarity_cluster import cluster_paths_by_hash


class SimilarityClusterTests(unittest.TestCase):
    def test_near_duplicate_goes_to_same_cluster_and_different_scene_does_not(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            first = base / "first.jpg"
            second = base / "second.jpg"
            different = base / "different.jpg"

            image = np.zeros((96, 96, 3), dtype=np.uint8)
            cv2.rectangle(image, (20, 20), (76, 76), (255, 255, 255), -1)
            cv2.imwrite(str(first), image)
            cv2.imwrite(str(second), image.copy())
            cv2.imwrite(str(different), np.full((96, 96, 3), 80, dtype=np.uint8))

            clusters = cluster_paths_by_hash([first, second, different], threshold=4)
            grouped = [set(paths) for paths in clusters.values()]

            self.assertTrue(any({first, second}.issubset(group) for group in grouped))
            self.assertFalse(any({first, different}.issubset(group) for group in grouped))


if __name__ == "__main__":
    unittest.main()

