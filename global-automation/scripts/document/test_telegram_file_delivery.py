import unittest

from PIL import Image
from pypdf import PdfWriter

from telegram_file_delivery import detect_format, prepare_delivery, validate_pdf


class TelegramFileDeliveryTests(unittest.TestCase):
    def test_pdf_is_not_relabelled(self):
        writer = PdfWriter()
        writer.add_blank_page(width=595, height=842)
        import io
        raw = io.BytesIO()
        writer.write(raw)
        data = raw.getvalue()
        result = prepare_delivery(data, "letter.pdf", "application/pdf")
        self.assertEqual(result["source_format"], "pdf")
        self.assertEqual(result["delivery_format"], "pdf")
        self.assertFalse(result["converted"])
        self.assertEqual(validate_pdf(result["data"]), 1)

    def test_jpeg_is_converted_to_real_pdf(self):
        import io
        raw = io.BytesIO()
        Image.new("RGB", (300, 400), "white").save(raw, format="JPEG")
        result = prepare_delivery(raw.getvalue(), "telegram-photo.jpg", "image/jpeg")
        self.assertEqual(result["source_format"], "jpeg")
        self.assertEqual(result["delivery_format"], "pdf")
        self.assertTrue(result["converted"])
        self.assertEqual(validate_pdf(result["data"]), 1)
        self.assertTrue(result["data"].startswith(b"%PDF-"))

    def test_fake_pdf_name_is_not_accepted_as_pdf(self):
        self.assertEqual(detect_format(b"not a pdf", "letter.pdf", "application/pdf"), "unknown")
        with self.assertRaises(ValueError):
            validate_pdf(b"not a pdf")


if __name__ == "__main__":
    unittest.main()
