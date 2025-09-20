"""Tests for AI analyzer module."""
import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.ai_analyzer import AIAnalyzer, DocumentInfo
from src.pdf_processor import PDFDocument


class TestDocumentInfo:
    """Test DocumentInfo data class."""

    def test_document_info_creation(self):
        """Test creating a DocumentInfo object."""
        info = DocumentInfo(
            company_name="Wells Fargo",
            document_type="bank statement",
            date=datetime.date(2023, 5, 15),
            confidence_score=0.95,
            suggested_name="Wells Fargo Bank Statement May 2023",
            additional_metadata={"account_type": "checking"},
        )

        assert info.company_name == "Wells Fargo"
        assert info.document_type == "bank statement"
        assert info.date == datetime.date(2023, 5, 15)
        assert info.confidence_score == 0.95
        assert info.suggested_name == "Wells Fargo Bank Statement May 2023"
        assert info.additional_metadata["account_type"] == "checking"


class TestAIAnalyzer:
    """Test AIAnalyzer class."""

    @pytest.fixture
    def analyzer(self, mock_env_vars):
        """Create an AIAnalyzer instance."""
        return AIAnalyzer(provider="openai")

    def test_analyzer_initialization_openai(self):
        """Test AIAnalyzer initialization with OpenAI."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            with patch("openai.OpenAI") as mock_openai:
                mock_client = MagicMock()
                mock_openai.return_value = mock_client
                analyzer = AIAnalyzer(provider="openai")
                assert analyzer.provider == "openai"
                assert analyzer.credentials["openai_api_key"] == "test-key"

    def test_analyzer_initialization_anthropic(self):
        """Test AIAnalyzer initialization with Anthropic."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("anthropic.Anthropic") as mock_anthropic:
                mock_client = MagicMock()
                mock_anthropic.return_value = mock_client
                analyzer = AIAnalyzer(provider="anthropic")
                assert analyzer.provider == "anthropic"
                assert analyzer.credentials["anthropic_api_key"] == "test-key"

    def test_analyzer_initialization_no_api_key(self):
        """Test AIAnalyzer initialization without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key not found"):
                AIAnalyzer(provider="openai")

    @patch("openai.OpenAI")
    def test_analyze_document_openai(self, mock_openai_client, analyzer):
        """Test document analysis with OpenAI."""
        # Mock the provider's analyze_document_text method
        mock_response = """{
            "company_name": "Chase Bank",
            "document_type": "credit card statement",
            "date": "2023-06-15",
            "confidence_score": 0.92,
            "suggested_name": "Chase Bank Credit Card Statement June 2023"
        }"""

        # Replace the analyzer's client with our mock
        analyzer.client = MagicMock()
        analyzer.client.analyze_document_text.return_value = mock_response

        # Create test document
        pdf_doc = PDFDocument(
            file_path=Path("test.pdf"),
            text_content="Chase Bank credit card statement for June 2023",
            metadata={},
            extracted_date=None,
            company_name=None,
            document_type=None,
            suggested_name=None,
        )

        # Analyze
        result = analyzer.analyze_document(pdf_doc)

        assert result.company_name == "Chase Bank"
        assert result.document_type == "credit card statement"
        assert result.date == datetime.date(2023, 6, 15)
        assert result.confidence_score == 0.92

    @patch("anthropic.Anthropic")
    def test_analyze_document_anthropic(self, mock_anthropic):
        """Test document analysis with Anthropic."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            analyzer = AIAnalyzer(provider="anthropic")

            # Mock the provider's analyze_document_text method
            mock_response = """{
                "company_name": "Verizon",
                "document_type": "phone bill",
                "date": "2023-07-01",
                "confidence_score": 0.88,
                "suggested_name": "Verizon Phone Bill July 2023"
            }"""

            # Replace the analyzer's client with our mock
            analyzer.client = MagicMock()
            analyzer.client.analyze_document_text.return_value = mock_response

            # Create test document
            pdf_doc = PDFDocument(
                file_path=Path("test.pdf"),
                text_content="Verizon Wireless bill for July 2023",
                metadata={},
                extracted_date=None,
                company_name=None,
                document_type=None,
                suggested_name=None,
            )

            # Analyze
            result = analyzer.analyze_document(pdf_doc)

            assert result.company_name == "Verizon"
            assert result.document_type == "phone bill"
            assert result.date == datetime.date(2023, 7, 1)

    def test_parse_ai_response(self, analyzer):
        """Test parsing AI response."""
        response = """{
            "company_name": "AT&T",
            "document_type": "internet bill",
            "date": "2023-08-10",
            "confidence_score": 0.95,
            "suggested_name": "AT&T Internet Bill August 2023",
            "additional_metadata": {
                "account_number": "XXX-1234",
                "amount_due": "$75.00"
            }
        }"""

        result = analyzer._parse_ai_response(response)

        assert result.company_name == "AT&T"
        assert result.document_type == "internet bill"
        assert result.date == datetime.date(2023, 8, 10)
        assert result.confidence_score == 0.95
        assert result.additional_metadata["account_number"] == "XXX-1234"

    def test_parse_ai_response_invalid_json(self, analyzer):
        """Test parsing invalid JSON response."""
        response = "This is not valid JSON"

        result = analyzer._parse_ai_response(response)

        assert result.company_name == "Unknown"
        assert result.document_type == "document"
        assert result.confidence_score == 0.0

    def test_extract_date_patterns(self, analyzer):
        """Test date extraction from text."""
        test_cases = [
            ("Statement Date: March 15, 2023", datetime.date(2023, 3, 15)),
            ("Invoice dated 06/20/2023", datetime.date(2023, 6, 20)),
            ("Bill for 2023-04-01", datetime.date(2023, 4, 1)),
            ("January 2023 Statement", datetime.date(2023, 1, 1)),
        ]

        for text, expected_date in test_cases:
            date = analyzer._extract_date_from_text(text)
            assert date == expected_date

    def test_generate_suggested_name(self, analyzer):
        """Test suggested name generation."""
        info = DocumentInfo(
            company_name="PG&E",
            document_type="utility bill",
            date=datetime.date(2023, 9, 15),
            confidence_score=0.9,
            suggested_name=None,
            additional_metadata={},
        )

        name = analyzer._generate_suggested_name(info)
        assert name == "PG&E Utility Bill September 2023"

    def test_batch_analyze(self, analyzer):
        """Test batch analysis of multiple documents."""
        # Create test documents
        docs = [
            PDFDocument(
                file_path=Path(f"test{i}.pdf"),
                text_content=f"Test document {i}",
                metadata={},
                extracted_date=None,
                company_name=None,
                document_type=None,
                suggested_name=None,
            )
            for i in range(3)
        ]

        with patch.object(analyzer, "analyze_document") as mock_analyze:
            mock_analyze.side_effect = [
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

            results = analyzer.batch_analyze(docs)

            assert len(results) == 3
            assert results[0].company_name == "Company1"
            assert results[1].company_name == "Company2"
            assert results[2].company_name == "Company3"

    def test_analyze_document_api_error(self, analyzer):
        """Test document analysis with API error."""
        # Mock API error
        analyzer.client = MagicMock()
        analyzer.client.analyze_document_text.side_effect = Exception("API Error")

        pdf_doc = PDFDocument(
            file_path=Path("test.pdf"),
            text_content="Test content",
            metadata={},
            extracted_date=None,
            company_name=None,
            document_type=None,
            suggested_name=None,
        )

        result = analyzer.analyze_document(pdf_doc)

        # Should return default values on error
        assert result.company_name == "Unknown"
        assert result.document_type == "document"
        assert result.confidence_score == 0.0

    def test_analyze_document_empty_response(self, analyzer):
        """Test document analysis with empty API response."""
        # Mock empty response
        analyzer.client = MagicMock()
        analyzer.client.analyze_document_text.return_value = ""

        pdf_doc = PDFDocument(
            file_path=Path("test.pdf"),
            text_content="Test content",
            metadata={},
            extracted_date=None,
            company_name=None,
            document_type=None,
            suggested_name=None,
        )

        result = analyzer.analyze_document(pdf_doc)

        assert result.company_name == "Unknown"
        assert result.document_type == "document"
        assert result.confidence_score == 0.0

    def test_analyze_document_malformed_json(self, analyzer):
        """Test document analysis with malformed JSON response."""
        # Mock malformed JSON response
        analyzer.client = MagicMock()
        analyzer.client.analyze_document_text.return_value = (
            '{"company_name": "Test", invalid json'
        )

        pdf_doc = PDFDocument(
            file_path=Path("test.pdf"),
            text_content="Test content",
            metadata={},
            extracted_date=None,
            company_name=None,
            document_type=None,
            suggested_name=None,
        )

        result = analyzer.analyze_document(pdf_doc)

        assert result.company_name == "Unknown"
        assert result.document_type == "document"
        assert result.confidence_score == 0.0

    def test_extract_date_from_text_no_date(self, analyzer):
        """Test date extraction from text with no dates."""
        text = "This is a document with no dates in it at all."
        result = analyzer._extract_date_from_text(text)
        assert result is None

    def test_extract_date_from_text_invalid_date(self, analyzer):
        """Test date extraction from text with invalid dates."""
        text = "This document is dated February 30, 2023"  # Invalid date
        result = analyzer._extract_date_from_text(text)
        # Should handle gracefully and return None or a valid fallback
        assert result is None or isinstance(result, datetime.date)

    def test_generate_suggested_name_minimal_info(self, analyzer):
        """Test name generation with minimal information."""
        info = DocumentInfo(
            company_name="Unknown",
            document_type="document",
            date=None,
            confidence_score=0.1,
            suggested_name=None,
            additional_metadata={},
        )

        name = analyzer._generate_suggested_name(info)
        assert "Unknown" in name or "Document" in name

    def test_batch_analyze_with_failures(self, analyzer):
        """Test batch analysis with some failures."""
        docs = [
            PDFDocument(
                file_path=Path("test1.pdf"),
                text_content="Test document 1",
                metadata={},
                extracted_date=None,
                company_name=None,
                document_type=None,
                suggested_name=None,
            ),
            PDFDocument(
                file_path=Path("test2.pdf"),
                text_content="Test document 2",
                metadata={},
                extracted_date=None,
                company_name=None,
                document_type=None,
                suggested_name=None,
            ),
        ]

        with patch.object(analyzer, "analyze_document") as mock_analyze:
            mock_analyze.side_effect = [
                DocumentInfo(
                    "Company1", "type1", datetime.date(2023, 1, 1), 0.9, "Name1", {}
                ),
                Exception("Analysis failed"),
            ]

            results = analyzer.batch_analyze(docs)

            assert len(results) == 2
            assert results[0].company_name == "Company1"
            assert results[1].company_name == "Unknown"  # Fallback for failed analysis

    def test_parse_ai_response_missing_fields(self, analyzer):
        """Test parsing AI response with missing required fields."""
        response = '{"company_name": "Test Company"}'  # Missing other fields

        result = analyzer._parse_ai_response(response)

        assert result.company_name == "Test Company"
        assert result.document_type == "document"  # Default value
        assert result.date is None
        assert result.confidence_score == 0.0  # Default value

    def test_parse_ai_response_extra_fields(self, analyzer):
        """Test parsing AI response with extra fields."""
        response = """{
            "company_name": "Test Company",
            "document_type": "invoice",
            "date": "2023-05-15",
            "confidence_score": 0.95,
            "suggested_name": "Test Invoice",
            "extra_field": "ignored",
            "another_field": 123
        }"""

        result = analyzer._parse_ai_response(response)

        assert result.company_name == "Test Company"
        assert result.document_type == "invoice"
        assert result.date == datetime.date(2023, 5, 15)
        assert result.confidence_score == 0.95
