import tempfile
import unittest
from pathlib import Path

import cv2
import numpy as np

from src.core.culling.culling_engine import run_core_culling_engine


class CullingEngineTests(unittest.TestCase):
    def test_pipeline_end_to_end_returns_selected_rejected_and_reasons(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_dir = root / "input"
            cache_dir = root / "cache"
            input_dir.mkdir()
            image = np.zeros((96, 96, 3), dtype=np.uint8)
            cv2.rectangle(image, (20, 20), (76, 76), (255, 255, 255), -1)
            cv2.imwrite(str(input_dir / "a.jpg"), image)
            cv2.imwrite(str(input_dir / "b.jpg"), image.copy())

            result = run_core_culling_engine(input_dir, mode="aggressive", cache_root=cache_dir, enable_body_scoring=False)

            self.assertEqual(result.summary.total_photos, 2)
            self.assertGreaterEqual(len(result.selected), 1)
            self.assertGreaterEqual(len(result.clusters), 1)
            self.assertTrue(any(item.reasons for item in result.selected + result.rejected))


if __name__ == "__main__":
    unittest.main()

