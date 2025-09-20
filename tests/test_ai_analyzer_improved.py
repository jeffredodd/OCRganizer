"""Improved tests for the AI analyzer module."""

import json
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from src.ai_analyzer import AIAnalyzer, AnthropicProvider, DocumentInfo, OpenAIProvider
from src.config import AIConfig
from src.pdf_processor import PDFDocument


class TestDocumentInfo:
    """Test DocumentInfo data class."""

    def test_initialization(self):
        """Test DocumentInfo initialization."""
        doc_info = DocumentInfo(
            company_name="Test Company",
            document_type="invoice",
            date=date(2023, 3, 15),
            confidence_score=0.95,
            suggested_name="Test Invoice",
            additional_metadata={"amount": "$100"},
        )

        assert doc_info.company_name == "Test Company"
        assert doc_info.document_type == "invoice"
        assert doc_info.date == date(2023, 3, 15)
        assert doc_info.confidence_score == 0.95
        assert doc_info.suggested_name == "Test Invoice"
        assert doc_info.additional_metadata == {"amount": "$100"}

    def test_post_init_validation(self):
        """Test post-initialization validation and cleanup."""
        doc_info = DocumentInfo(
            company_name="  Test Company  ",
            document_type="  INVOICE  ",
            date=date(2023, 3, 15),
            confidence_score=1.5,  # Should be clamped to 1.0
            suggested_name="Test",
            additional_metadata={},
        )

        assert doc_info.company_name == "Test Company"
        assert doc_info.document_type == "invoice"
        assert doc_info.confidence_score == 1.0
        assert doc_info.year_only == 2023
        assert doc_info.year_month_only == (2023, 3)

    def test_post_init_negative_confidence(self):
        """Test that negative confidence scores are clamped to 0."""
        doc_info = DocumentInfo(
            company_name="Test",
            document_type="test",
            date=None,
            confidence_score=-0.5,
            suggested_name="Test",
            additional_metadata={},
        )

        assert doc_info.confidence_score == 0.0


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        return Mock()

    @pytest.fixture
    def ai_config(self):
        """AI configuration fixture."""
        return AIConfig(
            openai_model="gpt-3.5-turbo", openai_temperature=0.3, openai_max_tokens=800
        )

    @pytest.fixture
    def openai_provider(self, mock_openai_client, ai_config):
        """OpenAI provider fixture."""
        return OpenAIProvider(
            client=mock_openai_client,
            ai_config=ai_config,
            credentials={},
            is_local=False,
        )

    def test_analyze_document_text_success(self, openai_provider, mock_openai_client):
        """Test successful document analysis."""
        # Mock successful chat completion response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message = Mock()
        mock_response.choices[0].message.content = '{"company_name": "Test Corp"}'

        mock_openai_client.chat.completions.create.return_value = mock_response

        result = openai_provider.analyze_document_text("Test document text")

        assert result == '{"company_name": "Test Corp"}'
        mock_openai_client.chat.completions.create.assert_called_once()

    def test_analyze_document_text_fallback_to_completions(
        self, openai_provider, mock_openai_client
    ):
        """Test fallback to completions API when chat fails."""
        # Mock chat completions failure
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "Chat failed"
        )

        # Mock successful completions response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].text = '{"company_name": "Test Corp"}'

        mock_openai_client.completions.create.return_value = mock_response

        result = openai_provider.analyze_document_text("Test document text")

        assert result == '{"company_name": "Test Corp"}'
        mock_openai_client.completions.create.assert_called_once()

    def test_analyze_document_text_complete_failure(
        self, openai_provider, mock_openai_client
    ):
        """Test when both API calls fail."""
        mock_openai_client.chat.completions.create.side_effect = Exception(
            "Chat failed"
        )
        mock_openai_client.completions.create.side_effect = Exception(
            "Completions failed"
        )

        result = openai_provider.analyze_document_text("Test document text")

        assert result == "{}"

    def test_get_model_local(self, ai_config):
        """Test model selection for local setup."""
        provider = OpenAIProvider(
            client=Mock(),
            ai_config=ai_config,
            credentials={"local_model_name": "local-model"},
            is_local=True,
        )

        model = provider._get_model()
        assert model == "local-model"

    def test_get_model_cloud(self, ai_config):
        """Test model selection for cloud setup."""
        provider = OpenAIProvider(
            client=Mock(), ai_config=ai_config, credentials={}, is_local=False
        )

        model = provider._get_model()
        assert model == "gpt-3.5-turbo"


class TestAnthropicProvider:
    """Test Anthropic provider implementation."""

    @pytest.fixture
    def mock_anthropic_client(self):
        """Mock Anthropic client."""
        return Mock()

    @pytest.fixture
    def ai_config(self):
        """AI configuration fixture."""
        return AIConfig(
            anthropic_model="claude-3-haiku-20240307",
            anthropic_temperature=0.3,
            anthropic_max_tokens=800,
        )

    @pytest.fixture
    def anthropic_provider(self, mock_anthropic_client, ai_config):
        """Anthropic provider fixture."""
        return AnthropicProvider(client=mock_anthropic_client, ai_config=ai_config)

    def test_analyze_document_text_success(
        self, anthropic_provider, mock_anthropic_client
    ):
        """Test successful document analysis with Anthropic."""
        # Mock successful response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = '{"company_name": "Test Corp"}'

        mock_anthropic_client.messages.create.return_value = mock_response

        result = anthropic_provider.analyze_document_text("Test document text")

        assert result == '{"company_name": "Test Corp"}'
        mock_anthropic_client.messages.create.assert_called_once()

    def test_analyze_document_text_failure(
        self, anthropic_provider, mock_anthropic_client
    ):
        """Test API failure handling."""
        mock_anthropic_client.messages.create.side_effect = Exception("API failed")

        result = anthropic_provider.analyze_document_text("Test document text")

        assert result == "{}"


class TestAIAnalyzer:
    """Test main AI analyzer class."""

    @pytest.fixture
    def mock_config(self):
        """Mock configuration."""
        config = Mock()
        config.ai = AIConfig()
        config.processing = Mock()
        config.processing.max_text_for_ai = 4000
        config.processing.confidence_threshold = 0.7
        config.get_ai_credentials.return_value = {
            "openai_api_key": "test_key",
            "openai_base_url": None,
            "anthropic_api_key": None,
            "local_model_name": None,
        }
        return config

    @patch("src.ai_analyzer.get_config")
    @patch("openai.OpenAI")
    def test_initialization_openai(
        self, mock_openai_client, mock_get_config, mock_config
    ):
        """Test AIAnalyzer initialization with OpenAI."""
        mock_get_config.return_value = mock_config
        mock_openai_client.return_value = Mock()

        analyzer = AIAnalyzer(provider="openai")

        assert analyzer.provider == "openai"
        assert isinstance(analyzer.client, OpenAIProvider)

    @patch("src.ai_analyzer.get_config")
    @patch("anthropic.Anthropic")
    def test_initialization_anthropic(
        self, mock_anthropic_client, mock_get_config, mock_config
    ):
        """Test AIAnalyzer initialization with Anthropic."""
        mock_config.get_ai_credentials.return_value = {
            "openai_api_key": None,
            "openai_base_url": None,
            "anthropic_api_key": "test_key",
            "local_model_name": None,
        }
        mock_get_config.return_value = mock_config
        mock_anthropic_client.return_value = Mock()

        analyzer = AIAnalyzer(provider="anthropic")

        assert analyzer.provider == "anthropic"
        assert isinstance(analyzer.client, AnthropicProvider)

    @patch("src.ai_analyzer.get_config")
    def test_initialization_invalid_provider(self, mock_get_config, mock_config):
        """Test initialization with invalid provider."""
        mock_get_config.return_value = mock_config

        with pytest.raises(ValueError, match="Unsupported AI provider"):
            AIAnalyzer(provider="invalid")

    @patch("src.ai_analyzer.get_config")
    def test_analyze_document_success(self, mock_get_config, mock_config):
        """Test successful document analysis."""
        mock_get_config.return_value = mock_config

        # Create mock PDF document
        pdf_doc = PDFDocument(
            file_path=Path("test.pdf"),
            text_content="Test document content",
            metadata={},
        )

        # Mock AI client
        mock_client = Mock()
        mock_client.analyze_document_text.return_value = json.dumps(
            {
                "company_name": "Test Company",
                "document_type": "invoice",
                "date": "2023-03-15",
                "confidence_score": 0.95,
                "suggested_name": "Test Invoice",
                "additional_metadata": {},
            }
        )

        with patch("openai.OpenAI"):
            analyzer = AIAnalyzer(provider="openai")
            analyzer.client = mock_client

            result = analyzer.analyze_document(pdf_doc)

            assert isinstance(result, DocumentInfo)
            assert result.company_name == "Test Company"
            assert result.document_type == "invoice"
            assert result.date == date(2023, 3, 15)
            assert result.confidence_score == 0.95

    @patch("src.ai_analyzer.get_config")
    def test_analyze_document_empty_text(self, mock_get_config, mock_config):
        """Test analysis with empty document text."""
        mock_get_config.return_value = mock_config

        pdf_doc = PDFDocument(file_path=Path("empty.pdf"), text_content="", metadata={})

        with patch("openai.OpenAI"):
            analyzer = AIAnalyzer(provider="openai")

            result = analyzer.analyze_document(pdf_doc)

            assert isinstance(result, DocumentInfo)
            assert result.company_name == "Unknown"
            assert result.confidence_score == 0.0

    @patch("src.ai_analyzer.get_config")
    def test_analyze_document_ai_failure(self, mock_get_config, mock_config):
        """Test analysis when AI fails."""
        mock_get_config.return_value = mock_config

        pdf_doc = PDFDocument(
            file_path=Path("test.pdf"), text_content="Test content", metadata={}
        )

        # Mock AI client that fails
        mock_client = Mock()
        mock_client.analyze_document_text.side_effect = Exception("AI failed")

        with patch("openai.OpenAI"):
            analyzer = AIAnalyzer(provider="openai")
            analyzer.client = mock_client

            result = analyzer.analyze_document(pdf_doc)

            assert isinstance(result, DocumentInfo)
            assert result.company_name == "Unknown"
            assert result.confidence_score == 0.0

    def test_extract_json_from_response(self):
        """Test JSON extraction from AI response."""
        analyzer = AIAnalyzer.__new__(AIAnalyzer)  # Create without __init__

        # Test with clean JSON
        response = '{"company_name": "Test Corp"}'
        result = analyzer._extract_json_from_response(response)
        assert result == '{"company_name": "Test Corp"}'

        # Test with extra text
        response = 'Here is the analysis: {"company_name": "Test Corp"} Done.'
        result = analyzer._extract_json_from_response(response)
        assert result == '{"company_name": "Test Corp"}'

    def test_clean_json_string(self):
        """Test JSON string cleaning."""
        analyzer = AIAnalyzer.__new__(AIAnalyzer)  # Create without __init__

        # Test removing extra text
        json_str = 'prefix {"company_name": "Test"} suffix'
        result = analyzer._clean_json_string(json_str)
        assert result == '{"company_name": "Test"}'

        # Test fixing unmatched braces
        json_str = '{"company_name": "Test", "incomplete":'
        result = analyzer._clean_json_string(json_str)
        assert result.endswith("}")

    def test_parse_date_from_data(self):
        """Test date parsing from various formats."""
        analyzer = AIAnalyzer.__new__(AIAnalyzer)  # Create without __init__

        # Test ISO format
        result = analyzer._parse_date_from_data("2023-03-15")
        assert result == date(2023, 3, 15)

        # Test None
        result = analyzer._parse_date_from_data(None)
        assert result is None

        # Test invalid format
        result = analyzer._parse_date_from_data("invalid")
        assert result is None

    def test_extract_date_from_text(self):
        """Test date extraction from text."""
        analyzer = AIAnalyzer.__new__(AIAnalyzer)  # Create without __init__

        # Test MM/DD/YYYY format
        text = "Statement date: 03/15/2023"
        result = analyzer._extract_date_from_text(text)
        assert result is not None
        assert result.year == 2023
        assert result.month == 3
        assert result.day == 15

    def test_extract_date_from_filename(self):
        """Test date extraction from filename."""
        analyzer = AIAnalyzer.__new__(AIAnalyzer)  # Create without __init__

        # Test YYYY_MM_DD format
        filename = "document_2023_03_15.pdf"
        result = analyzer._extract_date_from_filename(filename)
        assert result == date(2023, 3, 15)

        # Test no date
        filename = "document.pdf"
        result = analyzer._extract_date_from_filename(filename)
        assert result is None

    def test_generate_suggested_name(self):
        """Test suggested name generation."""
        analyzer = AIAnalyzer.__new__(AIAnalyzer)  # Create without __init__

        doc_info = DocumentInfo(
            company_name="Test Company",
            document_type="bank statement",
            date=date(2023, 3, 15),
            confidence_score=0.95,
            suggested_name="",
            additional_metadata={},
        )

        result = analyzer._generate_suggested_name(doc_info)
        assert "Test Company" in result
        assert "Bank Statement" in result
        assert "March 2023" in result

    @patch("src.ai_analyzer.get_config")
    def test_batch_analyze(self, mock_get_config, mock_config):
        """Test batch document analysis."""
        mock_get_config.return_value = mock_config

        # Create mock documents
        docs = [
            PDFDocument(Path("doc1.pdf"), "Content 1", {}),
            PDFDocument(Path("doc2.pdf"), "Content 2", {}),
        ]

        with patch("openai.OpenAI"):
            analyzer = AIAnalyzer(provider="openai")

            # Mock the analyze_document method
            mock_results = [
                DocumentInfo("Company 1", "type1", None, 0.9, "Name 1", {}),
                DocumentInfo("Company 2", "type2", None, 0.8, "Name 2", {}),
            ]

            with patch.object(analyzer, "analyze_document", side_effect=mock_results):
                results = analyzer.batch_analyze(docs)

                assert len(results) == 2
                assert all(isinstance(r, DocumentInfo) for r in results)
