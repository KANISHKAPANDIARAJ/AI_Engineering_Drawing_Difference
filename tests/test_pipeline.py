import unittest
from unittest.mock import patch, MagicMock
import numpy as np

from modules.ocr_extractor import OCRExtractor
from modules.llm_analyzer import LLMAnalyzer
from config import ProjectConfig


class TestPipeline(unittest.TestCase):
    def setUp(self):
        # Ensure grid configurations are present
        ProjectConfig.GRID_ROWS = ["A", "B", "C", "D", "E", "F", "G", "H"]
        ProjectConfig.GRID_COLUMNS = ["1", "2", "3", "4", "5", "6", "7", "8"]

    def test_grid_coordinate_mapping(self):
        """Verify bounding boxes map correctly to drawing grid zones."""
        extractor = OCRExtractor()
        
        # Test box in the top-left (center at 120, 67.5) -> A1
        box_a1 = {"x": 10, "y": 10, "w": 220, "h": 115}
        grid_a1 = extractor._map_to_grid(box_a1, 1920, 1080)
        self.assertEqual(grid_a1, "A1")

        # Test box in the center (center at 960, 540) -> E5
        # 1920 / 8 = 240. Center cx = 960 -> col_idx = 4 (col 5)
        # 1080 / 8 = 135. Center cy = 540 -> row_idx = 4 (row E)
        box_center = {"x": 900, "y": 500, "w": 120, "h": 80}
        grid_center = extractor._map_to_grid(box_center, 1920, 1080)
        self.assertEqual(grid_center, "E5")

        # Test box in the bottom-right corner -> H8
        box_h8 = {"x": 1800, "y": 1000, "w": 100, "h": 70}
        grid_h8 = extractor._map_to_grid(box_h8, 1920, 1080)
        self.assertEqual(grid_h8, "H8")

    @patch("modules.ocr_extractor.OCRExtractor._available")
    def test_ocr_extraction_fallback(self, mock_available):
        """Verify grid mapping still runs even if Tesseract is not available."""
        mock_available.return_value = False
        extractor = OCRExtractor()

        img = np.ones((1080, 1920, 3), dtype=np.uint8) * 255
        boxes = [
            {"x": 100, "y": 100, "w": 50, "h": 50}
        ]

        result = extractor.extract_all(img, img, boxes)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["grid"], "A1")
        self.assertIsNone(result[0]["before_text"])
        self.assertIsNone(result[0]["after_text"])
        self.assertIsNone(result[0]["text_changed"])

    def test_preprocess_float_input(self):
        """Verify _preprocess converts float32 normalized image to uint8 before thresholding."""
        extractor = OCRExtractor()
        float_crop = np.ones((100, 100, 3), dtype=np.float32)
        processed = extractor._preprocess(float_crop)
        self.assertEqual(processed.dtype, np.uint8)
        self.assertEqual(processed.shape, (200, 200)) # upscaled 2x

    @patch("urllib.request.urlopen")
    def test_llm_report_generation(self, mock_urlopen):
        """Verify LLMAnalyzer constructs valid REST request payload and parses the markdown response."""
        # Mock API Response
        mock_response = MagicMock()
        mock_response.read.return_value = b"""{
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "{\\"report\\": \\"# Engineering Revision Analysis & Impact Report\\\\n\\\\nRevision report details.\\", \\"regions\\": [{\\"id\\": 1, \\"type\\": \\"Modified\\", \\"description\\": \\"Dimension updated from 25 mm to 29 mm\\"}]}"
                            }
                        ]
                    }
                }
            ]
        }"""
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Mock API Key presence
        analyzer = LLMAnalyzer()
        analyzer._get_api_key = MagicMock(return_value="mock_api_key")

        stats = {
            "ssim_score": 0.985,
            "num_regions": 1,
            "average_region_area": 500,
            "severity": "LOW"
        }
        regions = [
            {"grid": "B4", "change_type": "Modified", "before_text": "25 mm", "after_text": "29 mm"}
        ]

        report = analyzer.generate_report(stats, regions)
        self.assertTrue(report.startswith("# Engineering Revision Analysis"))
        self.assertIn("Revision report details.", report)


if __name__ == "__main__":
    unittest.main()
