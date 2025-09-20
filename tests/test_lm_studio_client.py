"""Tests for LM Studio client module."""
from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from src.lm_studio_client import LMStudioClient


class TestLMStudioClient:
    """Test LMStudioClient class."""

    def test_initialization(self):
        """Test LMStudioClient initialization."""
        client = LMStudioClient("http://localhost:1234/v1", "test-model")

        assert client.base_url == "http://localhost:1234"
        assert client.model_name == "test-model"

    def test_initialization_strips_v1(self):
        """Test that /v1 is stripped from base URL."""
        client = LMStudioClient("http://localhost:1234/v1/", "test-model")
        assert client.base_url == "http://localhost:1234"

    @patch("src.lm_studio_client.requests.post")
    def test_generate_response_success(self, mock_post):
        """Test successful response generation."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"response": "Test AI response"}
        mock_post.return_value = mock_response

        client = LMStudioClient("http://localhost:1234", "test-model")
        result = client.generate_response("Test prompt")

        assert result == "Test AI response"
        mock_post.assert_called_once()

    @patch("src.lm_studio_client.requests.post")
    def test_generate_response_text_field(self, mock_post):
        """Test response with 'text' field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"text": "Response in text field"}
        mock_post.return_value = mock_response

        client = LMStudioClient("http://localhost:1234", "test-model")
        result = client.generate_response("Test prompt")

        assert result == "Response in text field"

    @patch("src.lm_studio_client.requests.post")
    def test_generate_response_choices_field(self, mock_post):
        """Test response with 'choices' field."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"choices": [{"text": "Response in choices"}]}
        mock_post.return_value = mock_response

        client = LMStudioClient("http://localhost:1234", "test-model")
        result = client.generate_response("Test prompt")

        assert result == "Response in choices"

    @patch("src.lm_studio_client.requests.post")
    def test_generate_response_http_error(self, mock_post):
        """Test response with HTTP error."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response

        # Mock the alternative endpoints method
        client = LMStudioClient("http://localhost:1234", "test-model")
        with patch.object(
            client, "_try_alternative_endpoints", return_value="fallback response"
        ):
            result = client.generate_response("Test prompt")
            assert result == "fallback response"

    @patch("src.lm_studio_client.requests.post")
    def test_generate_response_exception(self, mock_post):
        """Test response with exception."""
        mock_post.side_effect = requests.RequestException("Connection error")

        client = LMStudioClient("http://localhost:1234", "test-model")
        result = client.generate_response("Test prompt")

        assert result == ""

    @patch("src.lm_studio_client.requests.post")
    def test_try_alternative_endpoints_completions(self, mock_post):
        """Test alternative completions endpoint."""
        # First call fails, second succeeds
        mock_post.side_effect = [
            MagicMock(status_code=404),  # First endpoint fails
            MagicMock(
                status_code=200,
                json=lambda: {"choices": [{"text": "Alternative response"}]},
            ),
        ]

        client = LMStudioClient("http://localhost:1234", "test-model")
        result = client._try_alternative_endpoints("Test prompt")

        assert result == "Alternative response"
        assert mock_post.call_count == 2

    @patch("src.lm_studio_client.requests.post")
    def test_try_alternative_endpoints_chat(self, mock_post):
        """Test alternative chat endpoint."""
        # First two calls fail, third succeeds
        mock_post.side_effect = [
            MagicMock(status_code=404),  # completions fails
            MagicMock(
                status_code=200,
                json=lambda: {"choices": [{"message": {"content": "Chat response"}}]},
            ),
        ]

        client = LMStudioClient("http://localhost:1234", "test-model")
        result = client._try_alternative_endpoints("Test prompt")

        assert result == "Chat response"
        assert mock_post.call_count == 2

    @patch("src.lm_studio_client.requests.post")
    def test_try_alternative_endpoints_all_fail(self, mock_post):
        """Test when all alternative endpoints fail."""
        mock_post.return_value = MagicMock(status_code=404)

        client = LMStudioClient("http://localhost:1234", "test-model")
        result = client._try_alternative_endpoints("Test prompt")

        assert result == ""
        # Should try both alternative endpoints (completions and chat)
        assert mock_post.call_count >= 2

    def test_payload_structure(self):
        """Test that the request payload has correct structure."""
        with patch("src.lm_studio_client.requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"response": "test"}
            mock_post.return_value = mock_response

            client = LMStudioClient("http://localhost:1234", "test-model")
            client.generate_response("Test prompt")

            # Check the payload structure
            call_args = mock_post.call_args
            payload = call_args[1]["json"]

            assert payload["model"] == "test-model"
            assert payload["prompt"] == "Test prompt"
            assert payload["max_tokens"] == 500
            assert payload["temperature"] == 0.3
            assert "stop" in payload

    def test_url_construction(self):
        """Test URL construction for different endpoints."""
        client = LMStudioClient("http://localhost:1234", "test-model")

        with patch("src.lm_studio_client.requests.post") as mock_post:
            mock_post.return_value = MagicMock(status_code=404)

            client.generate_response("test")

            # Should call the generate endpoint first
            first_call_url = mock_post.call_args_list[0][0][0]
            assert first_call_url == "http://localhost:1234/api/generate"

    @patch("src.lm_studio_client.requests.post")
    def test_timeout_parameter(self, mock_post):
        """Test that timeout is set correctly."""
        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: {"response": "test"}
        )

        client = LMStudioClient("http://localhost:1234", "test-model")
        client.generate_response("Test prompt")

        # Check that timeout was set
        call_kwargs = mock_post.call_args[1]
        assert call_kwargs["timeout"] == 30
