"""Tests for PyMuPDF PDF extractor."""
import unittest
from pathlib import Path
from services.pdf_extractor import PDFExtractor, PDFExtractionResult


class TestPDFExtractor(unittest.TestCase):
    def setUp(self):
        self.sample_pdf_path = Path("data/sample_resumes/Alex_Rivera_Senior_Python_Backend.pdf")

    def test_extract_text_from_valid_pdf_file(self):
        if not self.sample_pdf_path.exists():
            self.skipTest("Sample PDF not found.")
        result = PDFExtractor.extract_text(self.sample_pdf_path)
        self.assertTrue(result.success)
        self.assertFalse(result.is_empty)
        self.assertGreaterEqual(result.page_count, 1)
        self.assertIn("Alex Rivera", result.text)
        self.assertIn("Python", result.text)

    def test_extract_text_from_bytes(self):
        if not self.sample_pdf_path.exists():
            self.skipTest("Sample PDF not found.")
        with open(self.sample_pdf_path, "rb") as f:
            data = f.read()
        result = PDFExtractor.extract_text(data, file_name="alex_bytes.pdf")
        self.assertTrue(result.success)
        self.assertEqual(result.file_name, "alex_bytes.pdf")
        self.assertIn("FastAPI", result.text)

    def test_extract_text_from_nonexistent_file(self):
        result = PDFExtractor.extract_text("non_existent_file_123.pdf")
        self.assertFalse(result.success)
        self.assertIn("not found", result.error_message.lower())

    def test_extract_text_from_corrupted_bytes(self):
        corrupted = b"not a valid pdf content at all"
        result = PDFExtractor.extract_text(corrupted, file_name="corrupt.pdf")
        self.assertFalse(result.success)
        self.assertIsNotNone(result.error_message)

    def test_clean_text_normalization(self):
        raw = "Line 1\r\n\r\n\r\n\r\nLine 2   \n\x0cLine 3"
        cleaned = PDFExtractor.clean_text(raw)
        self.assertIn("Line 1", cleaned)
        self.assertIn("Line 2", cleaned)
        self.assertIn("Line 3", cleaned)


if __name__ == "__main__":
    unittest.main()
