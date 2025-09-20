"""PDF processing module for extracting text and metadata from PDF files."""
import datetime
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import pdfplumber
import pypdf
import pytesseract
from pdf2image import convert_from_path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Suppress specific pypdf encoding warnings that we handle gracefully
pypdf_logger = logging.getLogger("pypdf._cmap")
pypdf_logger.setLevel(
    logging.CRITICAL
)  # Only show critical errors, not encoding warnings


@dataclass
class PDFDocument:
    """Data class representing a processed PDF document."""

    file_path: Path
    text_content: str
    metadata: Dict[str, Any]
    extracted_date: Optional[datetime.date] = None
    company_name: Optional[str] = None
    document_type: Optional[str] = None
    suggested_name: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert PDFDocument to dictionary."""
        data = asdict(self)
        data["file_path"] = str(self.file_path)
        if self.extracted_date:
            data["extracted_date"] = self.extracted_date.isoformat()
        return data


class PDFProcessor:
    """Handles PDF file processing, text extraction, and metadata extraction."""

    def __init__(self):
        """Initialize the PDF processor."""
        self.supported_extensions = [".pdf"]

    def extract_text(self, pdf_path: Path) -> str:
        """
        Extract text from a PDF file using pypdf with robust encoding error handling.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        try:
            text = ""
            with open(pdf_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        # Handle specific encoding errors gracefully
                        error_msg = str(e).lower()
                        if "encoding" in error_msg or "90ms-rksj" in error_msg:
                            logger.warning(
                                f"Encoding error on page {page_num} of {pdf_path.name}: {e}"
                            )
                            logger.info(
                                f"Attempting alternative extraction methods for page {page_num}"
                            )
                            # Try to extract with error handling
                            try:
                                # Attempt to get text with encoding fallback
                                page_text = self._extract_text_with_encoding_fallback(
                                    page
                                )
                                if page_text:
                                    text += page_text + "\n"
                            except Exception as fallback_e:
                                logger.debug(
                                    f"Fallback extraction also failed for page {page_num}: {fallback_e}"
                                )
                        else:
                            logger.warning(
                                f"Error extracting text from page {page_num}: {e}"
                            )

            # If pypdf fails or returns empty, try pdfplumber
            if not text.strip():
                logger.info(
                    f"pypdf extraction yielded no text, trying pdfplumber for {pdf_path.name}"
                )
                text = self.extract_text_with_pdfplumber(pdf_path)

            return text.strip()

        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path}: {e}")
            # Try pdfplumber as final fallback
            logger.info(f"Attempting pdfplumber as final fallback for {pdf_path.name}")
            try:
                return self.extract_text_with_pdfplumber(pdf_path)
            except Exception as fallback_e:
                logger.error(
                    f"All text extraction methods failed for {pdf_path}: {fallback_e}"
                )
                return ""

    def extract_text_with_pdfplumber(self, pdf_path: Path) -> str:
        """
        Extract text using pdfplumber as a fallback method with encoding error handling.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    try:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                    except Exception as e:
                        error_msg = str(e).lower()
                        if "encoding" in error_msg or "90ms-rksj" in error_msg:
                            logger.warning(
                                f"pdfplumber encoding error on page {page_num} of {pdf_path.name}: {e}"
                            )
                            # Try alternative extraction methods with pdfplumber
                            try:
                                # Try extracting with different parameters
                                page_text = page.extract_text(
                                    layout=True, x_tolerance=3, y_tolerance=3
                                )
                                if page_text:
                                    text += page_text + "\n"
                            except Exception as fallback_e:
                                logger.debug(
                                    f"pdfplumber fallback also failed for page {page_num}: {fallback_e}"
                                )
                        else:
                            logger.warning(f"pdfplumber error on page {page_num}: {e}")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text with pdfplumber from {pdf_path}: {e}")
            return ""

    def extract_text_with_ocr(self, pdf_path: Path) -> str:
        """
        Extract text using OCR for scanned PDFs.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            OCR-extracted text content
        """
        try:
            logger.info(f"Attempting OCR extraction for {pdf_path}")

            # Try to convert PDF to images
            try:
                images = convert_from_path(pdf_path)
            except Exception as e:
                logger.warning(
                    f"PDF to image conversion failed (poppler may not be installed): {e}"
                )
                # Try alternative: extract embedded images from PDF
                return self._extract_text_from_pdf_images(pdf_path)

            text = ""
            for i, image in enumerate(images):
                try:
                    # Perform OCR on each page
                    page_text = pytesseract.image_to_string(image, config="--psm 6")
                    if page_text and page_text.strip():
                        text += page_text + "\n"
                        logger.debug(
                            f"OCR extracted {len(page_text)} chars from page {i+1}"
                        )
                except Exception as e:
                    logger.warning(f"OCR failed for page {i}: {e}")

            return text.strip()

        except Exception as e:
            logger.error(f"Error performing OCR on {pdf_path}: {e}")
            return ""

    def _extract_text_from_pdf_images(self, pdf_path: Path) -> str:
        """
        Fallback OCR method that extracts embedded images from PDF.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            OCR-extracted text content
        """
        try:
            import fitz  # PyMuPDF - alternative PDF library

            doc = fitz.open(pdf_path)
            text = ""

            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images()

                for img_index, img in enumerate(image_list):
                    try:
                        # Extract image
                        xref = img[0]
                        pix = fitz.Pixmap(doc, xref)

                        if pix.n - pix.alpha < 4:  # GRAY or RGB
                            # Convert to PIL Image for OCR
                            import io

                            from PIL import Image

                            img_data = pix.tobytes("ppm")
                            pil_image = Image.open(io.BytesIO(img_data))

                            # Perform OCR
                            page_text = pytesseract.image_to_string(pil_image)
                            if page_text and page_text.strip():
                                text += page_text + "\n"

                        pix = None

                    except Exception as e:
                        logger.warning(
                            f"Failed to OCR image {img_index} on page {page_num}: {e}"
                        )

            doc.close()
            return text.strip()

        except ImportError:
            logger.warning("PyMuPDF not available, OCR fallback not possible")
            return ""
        except Exception as e:
            logger.error(f"Error in fallback OCR method: {e}")
            return ""

    def extract_metadata(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract metadata from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Dictionary containing metadata
        """
        metadata = {}

        try:
            with open(pdf_path, "rb") as file:
                pdf_reader = pypdf.PdfReader(file)

                # Extract document info
                if pdf_reader.metadata:
                    metadata["title"] = pdf_reader.metadata.get("/Title", "")
                    metadata["author"] = pdf_reader.metadata.get("/Author", "")
                    metadata["subject"] = pdf_reader.metadata.get("/Subject", "")
                    metadata["creator"] = pdf_reader.metadata.get("/Creator", "")
                    metadata["producer"] = pdf_reader.metadata.get("/Producer", "")

                    # Extract creation date if available
                    creation_date = pdf_reader.metadata.get("/CreationDate", "")
                    if creation_date:
                        metadata["creation_date"] = str(creation_date)

                    mod_date = pdf_reader.metadata.get("/ModDate", "")
                    if mod_date:
                        metadata["modification_date"] = str(mod_date)

                # Get page count
                metadata["page_count"] = len(pdf_reader.pages)

                # Get file size
                metadata["file_size"] = pdf_path.stat().st_size

        except Exception as e:
            logger.error(f"Error extracting metadata from {pdf_path}: {e}")

        return metadata

    def process_pdf(self, pdf_path: Path) -> PDFDocument:
        """
        Process a single PDF file to extract text and metadata.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            PDFDocument object containing extracted information
        """
        logger.info(f"Processing PDF: {pdf_path}")

        # Extract text content
        text_content = self.extract_text(pdf_path)

        # If text extraction failed or returned minimal content, try OCR
        min_text_threshold = 100  # Increased threshold for better OCR triggering
        if not text_content or len(text_content.strip()) < min_text_threshold:
            logger.info(
                f"Text extraction returned minimal content ({len(text_content)} chars), attempting OCR for {pdf_path}"
            )
            ocr_text = self.extract_text_with_ocr(pdf_path)
            if ocr_text and len(ocr_text.strip()) > len(text_content.strip()):
                logger.info(
                    f"OCR provided better text extraction ({len(ocr_text)} chars vs {len(text_content)} chars)"
                )
                text_content = ocr_text
            elif ocr_text:
                # Combine both if we have some text from both methods
                text_content = text_content + "\n" + ocr_text

        # Extract metadata
        metadata = self.extract_metadata(pdf_path)

        # Create PDFDocument object
        document = PDFDocument(
            file_path=pdf_path, text_content=text_content, metadata=metadata
        )

        logger.info(f"Successfully processed {pdf_path}")
        return document

    def _extract_text_with_encoding_fallback(self, page) -> str:
        """
        Attempt to extract text from a page with encoding error handling.

        Args:
            page: pypdf page object

        Returns:
            Extracted text or empty string if all methods fail
        """
        try:
            # Try to access the page content with different approaches
            # Method 1: Try to get the raw content and decode manually
            if hasattr(page, "/Contents"):
                # This is a more direct approach that might bypass encoding issues
                return ""  # For now, return empty - this would need more complex implementation

            # Method 2: Try extracting with different parameters
            # Some pypdf versions have different extraction options
            try:
                return page.extract_text(extraction_mode="layout")
            except Exception:
                pass

            # Method 3: Try basic extraction with error suppression
            try:
                return page.extract_text() or ""
            except Exception:
                pass

        except Exception as e:
            logger.debug(f"All encoding fallback methods failed: {e}")

        return ""

    def batch_process(self, pdf_paths: List[Path]) -> List[PDFDocument]:
        """
        Process multiple PDF files.

        Args:
            pdf_paths: List of paths to PDF files

        Returns:
            List of PDFDocument objects
        """
        documents = []
        total = len(pdf_paths)

        for i, pdf_path in enumerate(pdf_paths, 1):
            logger.info(f"Processing {i}/{total}: {pdf_path.name}")
            try:
                document = self.process_pdf(pdf_path)
                documents.append(document)
            except Exception as e:
                logger.error(f"Failed to process {pdf_path}: {e}")

        return documents

    def is_valid_pdf(self, file_path: Path) -> bool:
        """
        Check if a file is a valid PDF.

        Args:
            file_path: Path to the file

        Returns:
            True if file is a valid PDF, False otherwise
        """
        if not file_path.exists():
            return False

        if file_path.suffix.lower() not in self.supported_extensions:
            return False

        try:
            with open(file_path, "rb") as file:
                # Check PDF header
                header = file.read(5)
                return header == b"%PDF-" or header.startswith(b"%PDF")
        except Exception:
            return False
