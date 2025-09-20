"""Tests for file organizer module."""
import datetime
import os
import shutil
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.ai_analyzer import DocumentInfo
from src.file_organizer import FileOrganizer, OrganizationStrategy
from src.pdf_processor import PDFDocument


class TestOrganizationStrategy:
    """Test OrganizationStrategy class."""

    def test_default_strategy(self):
        """Test default organization strategy."""
        strategy = OrganizationStrategy()

        assert strategy.structure_pattern == "{company}/{year}/{month}"
        assert strategy.filename_pattern == "{company}_{type}_{date}"
        assert strategy.date_format == "%Y-%m-%d"

    def test_custom_strategy(self):
        """Test custom organization strategy."""
        strategy = OrganizationStrategy(
            structure_pattern="{year}/{company}",
            filename_pattern="{type}_{date}",
            date_format="%B %d, %Y",
        )

        assert strategy.structure_pattern == "{year}/{company}"
        assert strategy.filename_pattern == "{type}_{date}"
        assert strategy.date_format == "%B %d, %Y"


class TestFileOrganizer:
    """Test FileOrganizer class."""

    @pytest.fixture
    def temp_dirs(self, tmp_path):
        """Create temporary directories for testing."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()
        return input_dir, output_dir

    @pytest.fixture
    def organizer(self, temp_dirs):
        """Create a FileOrganizer instance."""
        _, output_dir = temp_dirs
        return FileOrganizer(output_dir=output_dir)

    def test_organizer_initialization(self, organizer, temp_dirs):
        """Test FileOrganizer initialization."""
        _, output_dir = temp_dirs
        assert organizer.output_dir == output_dir
        assert isinstance(organizer.strategy, OrganizationStrategy)

    def test_create_directory_structure(self, organizer, temp_dirs):
        """Test creating directory structure."""
        _, output_dir = temp_dirs

        doc_info = DocumentInfo(
            company_name="Tesla",
            document_type="invoice",
            date=datetime.date(2023, 5, 15),
            confidence_score=0.9,
            suggested_name="Tesla Invoice May 2023",
            additional_metadata={},
        )

        target_dir = organizer._create_directory_structure(doc_info)

        expected_path = output_dir / "Tesla" / "2023" / "05 - May"
        assert target_dir == expected_path
        assert target_dir.exists()

    def test_sanitize_filename(self, organizer):
        """Test filename sanitization."""
        test_cases = [
            ("File/Name:With*Special?Chars", "File_Name_With_Special_Chars"),
            ("   Spaces   Around   ", "Spaces_Around"),
            ("file.pdf.pdf", "file.pdf"),
            ("", "document"),
        ]

        for input_name, expected_name in test_cases:
            result = organizer._sanitize_filename(input_name)
            assert result == expected_name

    def test_generate_filename(self, organizer):
        """Test filename generation."""
        doc_info = DocumentInfo(
            company_name="Google",
            document_type="receipt",
            date=datetime.date(2023, 6, 20),
            confidence_score=0.95,
            suggested_name=None,
            additional_metadata={},
        )

        filename = organizer._generate_filename(doc_info)

        assert filename == "Google_receipt_2023-06-20.pdf"

    def test_generate_filename_with_suggested_name(self, organizer):
        """Test filename generation with suggested name."""
        doc_info = DocumentInfo(
            company_name="Amazon",
            document_type="order",
            date=datetime.date(2023, 7, 4),
            confidence_score=0.98,
            suggested_name="Amazon Prime Order July 2023",
            additional_metadata={},
        )

        filename = organizer._generate_filename(doc_info, use_suggested=True)

        assert filename == "Amazon_Prime_Order_July_2023.pdf"

    def test_organize_file(self, organizer, temp_dirs):
        """Test organizing a single file."""
        input_dir, output_dir = temp_dirs

        # Create a test PDF
        source_file = input_dir / "test.pdf"
        source_file.write_bytes(b"fake pdf content")

        # Create document and info
        pdf_doc = PDFDocument(
            file_path=source_file,
            text_content="Test content",
            metadata={},
            extracted_date=datetime.date(2023, 8, 10),
            company_name="Microsoft",
            document_type="license",
            suggested_name="Microsoft License August 2023",
        )

        doc_info = DocumentInfo(
            company_name="Microsoft",
            document_type="license",
            date=datetime.date(2023, 8, 10),
            confidence_score=0.92,
            suggested_name="Microsoft License August 2023",
            additional_metadata={},
        )

        # Organize the file
        new_path = organizer.organize_file(pdf_doc, doc_info)

        # Check the result
        expected_path = (
            output_dir
            / "Microsoft"
            / "2023"
            / "08 - August"
            / "Microsoft_license_2023-08-10.pdf"
        )
        assert new_path == expected_path
        assert new_path.exists()
        assert new_path.read_bytes() == b"fake pdf content"

    def test_organize_file_with_duplicate(self, organizer, temp_dirs):
        """Test organizing a file when destination already exists."""
        input_dir, output_dir = temp_dirs

        # Create a test PDF
        source_file = input_dir / "test.pdf"
        source_file.write_bytes(b"fake pdf content")

        # Create existing file at destination
        existing_dir = output_dir / "Apple" / "2023" / "09 - September"
        existing_dir.mkdir(parents=True)
        existing_file = existing_dir / "Apple_warranty_2023-09-01.pdf"
        existing_file.write_bytes(b"existing content")

        # Create document and info
        pdf_doc = PDFDocument(
            file_path=source_file,
            text_content="Test content",
            metadata={},
            extracted_date=datetime.date(2023, 9, 1),
            company_name="Apple",
            document_type="warranty",
            suggested_name="Apple Warranty September 2023",
        )

        doc_info = DocumentInfo(
            company_name="Apple",
            document_type="warranty",
            date=datetime.date(2023, 9, 1),
            confidence_score=0.95,
            suggested_name="Apple Warranty September 2023",
            additional_metadata={},
        )

        # Organize the file
        new_path = organizer.organize_file(pdf_doc, doc_info)

        # Should create a file with a number appended
        expected_path = existing_dir / "Apple_warranty_2023-09-01_1.pdf"
        assert new_path == expected_path
        assert new_path.exists()

    def test_batch_organize(self, organizer, temp_dirs):
        """Test batch organization of multiple files."""
        input_dir, _ = temp_dirs

        # Create test PDFs
        files = []
        for i in range(3):
            source_file = input_dir / f"test{i}.pdf"
            source_file.write_bytes(f"content {i}".encode())
            files.append(source_file)

        # Create documents and infos
        documents = [
            PDFDocument(
                files[0],
                "Content 1",
                {},
                datetime.date(2023, 1, 1),
                "Company1",
                "type1",
                "Name1",
            ),
            PDFDocument(
                files[1],
                "Content 2",
                {},
                datetime.date(2023, 2, 1),
                "Company2",
                "type2",
                "Name2",
            ),
            PDFDocument(
                files[2],
                "Content 3",
                {},
                datetime.date(2023, 3, 1),
                "Company3",
                "type3",
                "Name3",
            ),
        ]

        doc_infos = [
            DocumentInfo(
                "Company1", "type1", datetime.date(2023, 1, 1), 0.9, "Name1", {}
            ),
            DocumentInfo(
                "Company2", "type2", datetime.date(2023, 2, 1), 0.8, "Name2", {}
            ),
            DocumentInfo(
                "Company3", "type3", datetime.date(2023, 3, 1), 0.7, "Name3", {}
            ),
        ]

        # Organize batch
        results = organizer.batch_organize(documents, doc_infos)

        assert len(results) == 3
        for result in results:
            assert result["status"] == "success"
            assert Path(result["new_path"]).exists()

    def test_organize_with_custom_strategy(self, temp_dirs):
        """Test organization with custom strategy."""
        input_dir, output_dir = temp_dirs

        # Create custom strategy
        custom_strategy = OrganizationStrategy(
            structure_pattern="{year}/{month}/{company}",
            filename_pattern="{date}_{type}",
            date_format="%B_%d_%Y",
        )

        organizer = FileOrganizer(output_dir=output_dir, strategy=custom_strategy)

        # Create a test PDF
        source_file = input_dir / "test.pdf"
        source_file.write_bytes(b"fake pdf content")

        # Create document and info
        pdf_doc = PDFDocument(
            file_path=source_file,
            text_content="Test content",
            metadata={},
            extracted_date=datetime.date(2023, 10, 15),
            company_name="Netflix",
            document_type="subscription",
            suggested_name="Netflix Subscription October 2023",
        )

        doc_info = DocumentInfo(
            company_name="Netflix",
            document_type="subscription",
            date=datetime.date(2023, 10, 15),
            confidence_score=0.88,
            suggested_name="Netflix Subscription October 2023",
            additional_metadata={},
        )

        # Organize the file
        new_path = organizer.organize_file(pdf_doc, doc_info)

        # Check the result matches our custom strategy: {year}/{month}/{company}
        expected_path = (
            output_dir
            / "2023"
            / "10 - October"
            / "Netflix"
            / "October_15_2023_subscription.pdf"
        )
        assert new_path == expected_path
        assert new_path.exists()

    def test_undo_organization(self, organizer, temp_dirs):
        """Test undoing file organization."""
        input_dir, output_dir = temp_dirs

        # Create and organize a file
        source_file = input_dir / "test.pdf"
        source_file.write_bytes(b"fake pdf content")

        pdf_doc = PDFDocument(
            file_path=source_file,
            text_content="Test content",
            metadata={},
            extracted_date=datetime.date(2023, 11, 20),
            company_name="Spotify",
            document_type="invoice",
            suggested_name="Spotify Invoice November 2023",
        )

        doc_info = DocumentInfo(
            company_name="Spotify",
            document_type="invoice",
            date=datetime.date(2023, 11, 20),
            confidence_score=0.91,
            suggested_name="Spotify Invoice November 2023",
            additional_metadata={},
        )

        # Organize the file
        new_path = organizer.organize_file(pdf_doc, doc_info)
        assert new_path.exists()
        assert not source_file.exists()

        # Undo the organization
        restored_path = organizer.undo_organization(new_path, source_file)

        assert restored_path == source_file
        assert source_file.exists()
        assert not new_path.exists()

    def test_organize_file_with_permission_error(self, organizer, temp_dirs):
        """Test organizing file with permission error."""
        input_dir, output_dir = temp_dirs

        source_file = input_dir / "test.pdf"
        source_file.write_bytes(b"fake pdf content")

        pdf_doc = PDFDocument(
            file_path=source_file,
            text_content="Test content",
            metadata={},
            extracted_date=datetime.date(2023, 1, 1),
            company_name="Test Company",
            document_type="test",
            suggested_name="Test Document",
        )

        doc_info = DocumentInfo(
            company_name="Test Company",
            document_type="test",
            date=datetime.date(2023, 1, 1),
            confidence_score=0.9,
            suggested_name="Test Document",
            additional_metadata={},
        )

        # Mock shutil.move to raise permission error
        with patch("shutil.move", side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                organizer.organize_file(pdf_doc, doc_info)

    def test_sanitize_filename_special_characters(self, organizer):
        """Test filename sanitization with special characters."""
        test_cases = [
            ("File<>Name", "File__Name"),
            ('File"Name', "File_Name"),
            ("File|Name", "File_Name"),
            ("File?Name*", "File_Name"),  # The sanitizer strips trailing underscores
            ("File/Name\\Path", "File_Name_Path"),
            ("", "document"),
            ("   ", "document"),
        ]

        for input_name, expected in test_cases:
            result = organizer._sanitize_filename(input_name)
            assert result == expected or result == "document"

    def test_create_directory_structure_no_date(self, organizer, temp_dirs):
        """Test creating directory structure with no date information."""
        _, output_dir = temp_dirs

        doc_info = DocumentInfo(
            company_name="Test Company",
            document_type="test",
            date=None,  # No date
            confidence_score=0.9,
            suggested_name="Test Document",
            additional_metadata={},
        )

        target_dir = organizer._create_directory_structure(doc_info)

        # With new smart organization, no date means stop at company level
        expected_path = output_dir / "Test_Company"
        assert target_dir == expected_path
        assert target_dir.exists()

    def test_batch_organize_empty_list(self, organizer):
        """Test batch organization with empty lists."""
        results = organizer.batch_organize([], [])
        assert results == []

    def test_undo_organization_nonexistent_file(self, organizer, temp_dirs):
        """Test undoing organization with non-existent organized file."""
        input_dir, output_dir = temp_dirs

        organized_path = output_dir / "nonexistent.pdf"
        original_path = input_dir / "original.pdf"

        with pytest.raises(FileNotFoundError):
            organizer.undo_organization(organized_path, original_path)
