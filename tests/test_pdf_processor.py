"""Tests for PDF processor module."""
import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.pdf_processor import PDFDocument, PDFProcessor


class TestPDFDocument:
    """Test PDFDocument data class."""

    def test_document_creation(self):
        """Test creating a PDFDocument."""
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            text_content="Sample text",
            metadata={"pages": 1},
            extracted_date=datetime.date(2023, 3, 15),
            company_name="Chase Bank",
            document_type="statement",
            suggested_name="Chase Bank Statement March 2023",
        )

        assert doc.file_path == Path("test.pdf")
        assert doc.text_content == "Sample text"
        assert doc.metadata["pages"] == 1
        assert doc.extracted_date == datetime.date(2023, 3, 15)
        assert doc.company_name == "Chase Bank"
        assert doc.document_type == "statement"
        assert doc.suggested_name == "Chase Bank Statement March 2023"

    def test_document_to_dict(self):
        """Test converting PDFDocument to dictionary."""
        doc = PDFDocument(
            file_path=Path("test.pdf"),
            text_content="Sample text",
            metadata={"pages": 1},
            extracted_date=datetime.date(2023, 3, 15),
            company_name="Chase Bank",
            document_type="statement",
            suggested_name="Chase Bank Statement March 2023",
        )

        doc_dict = doc.to_dict()
        assert doc_dict["file_path"] == "test.pdf"
        assert doc_dict["text_content"] == "Sample text"
        assert doc_dict["extracted_date"] == "2023-03-15"
        assert doc_dict["company_name"] == "Chase Bank"


class TestPDFProcessor:
    """Test PDFProcessor class."""

    @pytest.fixture
    def processor(self):
        """Create a PDFProcessor instance."""
        return PDFProcessor()

    def test_processor_initialization(self, processor):
        """Test PDFProcessor initialization."""
        assert processor is not None
        assert hasattr(processor, "extract_text")
        assert hasattr(processor, "extract_metadata")

    @patch("src.pdf_processor.pypdf.PdfReader")
    def test_extract_text_from_pdf(self, mock_pdf_reader, processor, tmp_path):
        """Test extracting text from a PDF file."""
        # Create a mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        # Setup mock
        mock_reader = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Sample PDF text content"
        mock_reader.pages = [mock_page]
        mock_pdf_reader.return_value = mock_reader

        # Test extraction
        text = processor.extract_text(pdf_file)

        assert text == "Sample PDF text content"
        mock_pdf_reader.assert_called_once()

    @patch("src.pdf_processor.pdfplumber.open")
    def test_extract_text_with_pdfplumber(self, mock_pdfplumber, processor, tmp_path):
        """Test extracting text using pdfplumber as fallback."""
        # Create a mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        # Setup mock
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Text from pdfplumber"
        mock_pdf.pages = [mock_page]
        mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
        mock_pdf.__exit__ = MagicMock(return_value=None)
        mock_pdfplumber.return_value = mock_pdf

        # Test extraction with pdfplumber
        text = processor.extract_text_with_pdfplumber(pdf_file)

        assert text == "Text from pdfplumber"
        mock_pdfplumber.assert_called_once_with(pdf_file)

    def test_extract_metadata(self, processor, tmp_path):
        """Test extracting metadata from PDF."""
        # Create a mock PDF file
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        with patch("src.pdf_processor.pypdf.PdfReader") as mock_reader:
            mock_pdf = MagicMock()
            mock_pdf.metadata = {
                "/Title": "Test Document",
                "/Author": "Test Author",
                "/CreationDate": "D:20230315120000",
            }
            mock_pdf.pages = [MagicMock()]
            mock_reader.return_value = mock_pdf

            metadata = processor.extract_metadata(pdf_file)

            assert metadata["title"] == "Test Document"
            assert metadata["author"] == "Test Author"
            assert metadata["page_count"] == 1

    def test_ocr_extraction(self, processor, tmp_path):
        """Test OCR extraction from scanned PDF."""
        # Create a mock PDF file
        pdf_file = tmp_path / "scanned.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        # Mock the OCR dependencies within the processor module
        with patch("src.pdf_processor.convert_from_path") as mock_convert:
            with patch("src.pdf_processor.pytesseract.image_to_string") as mock_ocr:
                # Setup mocks
                mock_image = MagicMock()
                mock_convert.return_value = [mock_image]
                mock_ocr.return_value = "OCR extracted text"

                # Test OCR extraction
                text = processor.extract_text_with_ocr(pdf_file)

                assert text == "OCR extracted text"
        mock_convert.assert_called_once_with(pdf_file)
        mock_ocr.assert_called_once_with(mock_image, config="--psm 6")

    def test_process_pdf(self, processor, tmp_path):
        """Test processing a complete PDF file."""
        # Create a mock PDF file
        pdf_file = tmp_path / "document.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        with patch.object(processor, "extract_text", return_value="Extracted text"):
            with patch.object(processor, "extract_metadata", return_value={"pages": 1}):
                document = processor.process_pdf(pdf_file)

                assert document.file_path == pdf_file
                assert document.text_content == "Extracted text"
                assert document.metadata == {"pages": 1}

    def test_process_pdf_with_empty_text(self, processor, tmp_path):
        """Test processing PDF with no extractable text (triggers OCR)."""
        # Create a mock PDF file
        pdf_file = tmp_path / "scanned.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        with patch.object(processor, "extract_text", return_value=""):
            with patch.object(
                processor, "extract_text_with_ocr", return_value="OCR text"
            ):
                with patch.object(
                    processor, "extract_metadata", return_value={"pages": 1}
                ):
                    document = processor.process_pdf(pdf_file)

                    assert document.text_content == "OCR text"

    def test_batch_process(self, processor, tmp_path):
        """Test batch processing multiple PDFs."""
        # Create mock PDF files
        pdf1 = tmp_path / "doc1.pdf"
        pdf2 = tmp_path / "doc2.pdf"
        pdf1.write_bytes(b"fake pdf 1")
        pdf2.write_bytes(b"fake pdf 2")

        with patch.object(processor, "process_pdf") as mock_process:
            mock_process.side_effect = [
                PDFDocument(pdf1, "Text 1", {}, None, None, None, None),
                PDFDocument(pdf2, "Text 2", {}, None, None, None, None),
            ]

            documents = processor.batch_process([pdf1, pdf2])

            assert len(documents) == 2
            assert documents[0].file_path == pdf1
            assert documents[1].file_path == pdf2

    def test_extract_text_empty_pdf(self, processor, tmp_path):
        """Test extracting text from empty PDF."""
        pdf_file = tmp_path / "empty.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        with patch("src.pdf_processor.pypdf.PdfReader") as mock_reader:
            mock_pdf = MagicMock()
            mock_pdf.pages = []
            mock_reader.return_value = mock_pdf

            text = processor.extract_text(pdf_file)
            assert text == ""

    def test_extract_text_corrupted_pdf(self, processor, tmp_path):
        """Test extracting text from corrupted PDF."""
        pdf_file = tmp_path / "corrupted.pdf"
        pdf_file.write_bytes(b"not a pdf")

        with patch("src.pdf_processor.pypdf.PdfReader") as mock_reader:
            mock_reader.side_effect = Exception("Corrupted PDF")

            text = processor.extract_text(pdf_file)
            assert text == ""

    def test_extract_metadata_no_metadata(self, processor, tmp_path):
        """Test extracting metadata from PDF with no metadata."""
        pdf_file = tmp_path / "no_metadata.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        with patch("src.pdf_processor.pypdf.PdfReader") as mock_reader:
            mock_pdf = MagicMock()
            mock_pdf.metadata = None
            mock_pdf.pages = [MagicMock()]
            mock_reader.return_value = mock_pdf

            metadata = processor.extract_metadata(pdf_file)
            assert metadata["page_count"] == 1
            assert metadata["file_size"] > 0

    def test_ocr_extraction_failure(self, processor, tmp_path):
        """Test OCR extraction when conversion fails."""
        pdf_file = tmp_path / "scanned.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        with patch("src.pdf_processor.convert_from_path") as mock_convert:
            mock_convert.side_effect = Exception("Poppler not found")

            text = processor.extract_text_with_ocr(pdf_file)
            assert text == ""

    def test_ocr_extraction_partial_failure(self, processor, tmp_path):
        """Test OCR extraction when some pages fail."""
        pdf_file = tmp_path / "scanned.pdf"
        pdf_file.write_bytes(b"fake pdf content")

        with patch("src.pdf_processor.convert_from_path") as mock_convert:
            with patch("src.pdf_processor.pytesseract.image_to_string") as mock_ocr:
                # Setup mocks - first page succeeds, second fails
                mock_image1 = MagicMock()
                mock_image2 = MagicMock()
                mock_convert.return_value = [mock_image1, mock_image2]
                mock_ocr.side_effect = ["Page 1 text", Exception("OCR failed")]

                text = processor.extract_text_with_ocr(pdf_file)
                assert text == "Page 1 text"

    def test_is_valid_pdf_nonexistent_file(self, processor, tmp_path):
        """Test PDF validation with non-existent file."""
        pdf_file = tmp_path / "nonexistent.pdf"
        assert not processor.is_valid_pdf(pdf_file)

    def test_is_valid_pdf_wrong_extension(self, processor, tmp_path):
        """Test PDF validation with wrong extension."""
        text_file = tmp_path / "document.txt"
        text_file.write_text("Not a PDF")
        assert not processor.is_valid_pdf(text_file)

    def test_is_valid_pdf_invalid_content(self, processor, tmp_path):
        """Test PDF validation with invalid PDF content."""
        pdf_file = tmp_path / "invalid.pdf"
        pdf_file.write_bytes(b"Not a real PDF")
        assert not processor.is_valid_pdf(pdf_file)

    def test_batch_process_with_failures(self, processor, tmp_path):
        """Test batch processing with some failures."""
        pdf1 = tmp_path / "doc1.pdf"
        pdf2 = tmp_path / "doc2.pdf"
        pdf1.write_bytes(b"fake pdf 1")
        pdf2.write_bytes(b"fake pdf 2")

        with patch.object(processor, "process_pdf") as mock_process:
            mock_process.side_effect = [
                PDFDocument(pdf1, "Text 1", {}, None, None, None, None),
                Exception("Processing failed"),
            ]

            documents = processor.batch_process([pdf1, pdf2])

            # Should only return successful documents
            assert len(documents) == 1
            assert documents[0].file_path == pdf1
