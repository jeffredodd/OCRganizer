"""AI-based document analysis module for categorizing and extracting information from PDFs.

This module provides a clean, professional interface for analyzing PDF documents
using various AI providers (OpenAI, Anthropic, local models) to extract
categorization information such as company names, document types, and dates.
"""

import json
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Protocol, Tuple

from dateutil import parser as date_parser

from .config import AIConfig, get_config
from .pdf_processor import PDFDocument

logger = logging.getLogger(__name__)


class AIProvider(Protocol):
    """Protocol defining the interface for AI providers."""

    def analyze_document_text(self, text: str, max_tokens: int = 800) -> str:
        """Analyze document text and return JSON response."""
        ...


@dataclass
class DocumentInfo:
    """Data class for document analysis results.

    Attributes:
        company_name: Name of the company/organization
        document_type: Type of document (e.g., 'bank statement', 'invoice')
        date: Primary date of the document
        confidence_score: AI confidence score (0.0-1.0)
        suggested_name: Suggested filename for the document
        additional_metadata: Additional extracted information
        year_only: Year if only year is known
        year_month_only: (year, month) tuple if only year/month known
    """

    company_name: str
    document_type: str
    date: Optional[date]
    confidence_score: float
    suggested_name: str
    additional_metadata: Dict[str, Any] = field(default_factory=dict)
    year_only: Optional[int] = None
    year_month_only: Optional[Tuple[int, int]] = None

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        # Ensure confidence score is within valid range
        self.confidence_score = max(0.0, min(1.0, self.confidence_score))

        # Clean up strings
        if self.company_name:
            self.company_name = self.company_name.strip()
        if self.document_type:
            self.document_type = self.document_type.lower().strip()

        # Set date-related fields
        if self.date:
            self.year_only = self.date.year
            self.year_month_only = (self.date.year, self.date.month)


class OpenAIProvider:
    """OpenAI API provider implementation."""

    def __init__(
        self,
        client,
        ai_config: AIConfig,
        credentials: Dict[str, Any],
        is_local: bool = False,
    ):
        self.client = client
        self.ai_config = ai_config
        self.credentials = credentials
        self.is_local = is_local

    def analyze_document_text(self, text: str, max_tokens: int = 800) -> str:
        """Analyze document text using OpenAI API."""
        try:
            model = self._get_model()
            max_tokens = min(max_tokens, self.ai_config.openai_max_tokens)

            logger.debug(f"Using OpenAI model: {model} (local: {self.is_local})")

            # Try chat completions first
            response = self._try_chat_completions(model, text, max_tokens)
            if response:
                return response

            # Fallback to completions for older models
            response = self._try_completions(model, text, max_tokens)
            return response or "{}"

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return "{}"

    def _get_model(self) -> str:
        """Get the appropriate model name."""
        model = self.ai_config.openai_model

        # For local models, use configured local model name if available
        if self.is_local and model == "gpt-3.5-turbo":
            return self.credentials.get("local_model_name", "gpt-oss-20b")

        return model

    def _try_chat_completions(
        self, model: str, text: str, max_tokens: int
    ) -> Optional[str]:
        """Try chat completions API."""
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a document analysis expert. Analyze documents and provide structured information for categorization.",
                    },
                    {"role": "user", "content": text},
                ],
                temperature=self.ai_config.openai_temperature,
                max_tokens=max_tokens,
            )

            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if (
                    hasattr(choice, "message")
                    and choice.message
                    and choice.message.content
                ):
                    return choice.message.content

            logger.warning("Empty response from OpenAI chat completions")
            return None

        except Exception as e:
            logger.warning(f"Chat completions failed: {e}")
            return None

    def _try_completions(self, model: str, text: str, max_tokens: int) -> Optional[str]:
        """Try legacy completions API."""
        try:
            response = self.client.completions.create(
                model=model,
                prompt=f"System: You are a document analysis expert.\n\nUser: {text}\n\nAssistant:",
                temperature=self.ai_config.openai_temperature,
                max_tokens=max_tokens,
            )

            if hasattr(response, "choices") and response.choices:
                return response.choices[0].text

            return None

        except Exception as e:
            logger.error(f"Completions API also failed: {e}")
            return None


class AnthropicProvider:
    """Anthropic Claude API provider implementation."""

    def __init__(self, client, ai_config: AIConfig):
        self.client = client
        self.ai_config = ai_config

    def analyze_document_text(self, text: str, max_tokens: int = 800) -> str:
        """Analyze document text using Anthropic API."""
        try:
            response = self.client.messages.create(
                model=self.ai_config.anthropic_model,
                max_tokens=min(max_tokens, self.ai_config.anthropic_max_tokens),
                temperature=self.ai_config.anthropic_temperature,
                system="You are a document analysis expert. Analyze documents and provide structured information for categorization.",
                messages=[{"role": "user", "content": text}],
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            return "{}"


class AIAnalyzer:
    """Main AI analyzer class for document categorization.

    This class coordinates AI analysis of PDF documents, handling provider
    initialization, text processing, and result parsing.
    """

    def __init__(self, provider: Optional[str] = None):
        """Initialize the AI analyzer.

        Args:
            provider: AI provider to use ('openai' or 'anthropic').
                     If None, uses config default.
        """
        self.config = get_config()
        self.credentials = self.config.get_ai_credentials()

        # Determine provider
        self.provider = (provider or self.config.ai.preferred_provider).lower()

        if self.provider not in ["openai", "anthropic"]:
            raise ValueError(f"Unsupported AI provider: {self.provider}")

        # Initialize the appropriate client
        self.client = self._initialize_client()
        logger.info(f"Initialized AI analyzer with provider: {self.provider}")

    def _initialize_client(self) -> AIProvider:
        """Initialize the appropriate AI client."""
        if self.provider == "openai":
            return self._init_openai_client()
        elif self.provider == "anthropic":
            return self._init_anthropic_client()
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")

    def _init_openai_client(self) -> OpenAIProvider:
        """Initialize OpenAI client."""
        try:
            import openai
        except ImportError:
            raise ImportError("OpenAI package not installed. Run: pip install openai")

        api_key = self.credentials["openai_api_key"]
        base_url = self.credentials["openai_base_url"] or "https://api.openai.com/v1"

        # Detect local setup
        is_local = any(
            host in base_url for host in ["localhost", "127.0.0.1", "192.168."]
        )

        if is_local:
            logger.info(f"Using local LM Studio instance at {base_url}")
            api_key = api_key or "lm-studio"
        elif not api_key:
            raise ValueError("OpenAI API key not found in environment variables")

        client = openai.OpenAI(api_key=api_key, base_url=base_url)
        return OpenAIProvider(client, self.config.ai, self.credentials, is_local)

    def _init_anthropic_client(self) -> AnthropicProvider:
        """Initialize Anthropic client."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "Anthropic package not installed. Run: pip install anthropic"
            )

        api_key = self.credentials["anthropic_api_key"]
        if not api_key:
            raise ValueError("Anthropic API key not found in environment variables")

        client = anthropic.Anthropic(api_key=api_key)
        return AnthropicProvider(client, self.config.ai)

    def analyze_document(self, pdf_document: PDFDocument) -> DocumentInfo:
        """Analyze a PDF document using AI to extract categorization information.

        Args:
            pdf_document: PDFDocument object to analyze

        Returns:
            DocumentInfo object with analysis results
        """
        logger.info(f"Analyzing document: {pdf_document.file_path}")

        try:
            # Prepare text for analysis
            text_limit = self._get_text_limit()
            text_content = pdf_document.text_content[:text_limit]

            if not text_content.strip():
                logger.warning("No text content found in document")
                return self._create_fallback_document_info(pdf_document)

            # Create analysis prompt
            prompt = self._create_analysis_prompt(text_content)

            # Get AI response
            response = self.client.analyze_document_text(
                prompt, self.config.ai.openai_max_tokens
            )

            # Parse and enhance the response
            doc_info = self._parse_ai_response(response)
            doc_info = self._enhance_document_info(doc_info, pdf_document)

            logger.info(
                f"Analysis complete: {doc_info.company_name} - {doc_info.document_type} (confidence: {doc_info.confidence_score:.2f})"
            )
            return doc_info

        except Exception as e:
            logger.error(f"Error analyzing document {pdf_document.file_path}: {e}")
            return self._create_fallback_document_info(pdf_document)

    def _get_text_limit(self) -> int:
        """Determine appropriate text limit based on provider and configuration."""
        base_limit = self.config.processing.max_text_for_ai

        # For local models, be more conservative with context
        if (
            self.provider == "openai"
            and hasattr(self.client, "is_local")
            and self.client.is_local
        ):
            return min(base_limit, 1500)

        return base_limit

    def _create_analysis_prompt(self, text_content: str) -> str:
        """Create a prompt for AI analysis."""
        is_local = (
            self.provider == "openai"
            and hasattr(self.client, "is_local")
            and self.client.is_local
        )

        if is_local:
            return self._create_simple_prompt(text_content)
        else:
            return self._create_detailed_prompt(text_content)

    def _create_simple_prompt(self, text_content: str) -> str:
        """Create a simple prompt optimized for local models."""
        return f"""Extract information from this document and respond with ONLY valid JSON:

Document text:
{text_content}

Required JSON format:
{{
    "company_name": "company name or null",
    "document_type": "document type or null", 
    "date": "YYYY-MM-DD or null",
    "confidence_score": 0.8,
    "suggested_name": "descriptive name"
}}

JSON:"""

    def _create_detailed_prompt(self, text_content: str) -> str:
        """Create a detailed prompt for cloud AI models."""
        return f"""Analyze the following document text and extract key information for categorization.

Document text:
{text_content}

Please provide the following information in JSON format:
1. company_name: The company or organization that issued this document
2. document_type: Type of document (e.g., "bank statement", "invoice", "bill", "receipt", "tax document", "insurance", "contract", "letter", etc.)
3. date: The primary date of the document in YYYY-MM-DD format
4. confidence_score: Your confidence in this categorization (0.0 to 1.0)
5. suggested_name: A descriptive filename for this document
6. additional_metadata: Any other relevant information (account numbers, amounts, etc.)

Respond ONLY with valid JSON. Example:
{{
    "company_name": "Chase Bank",
    "document_type": "bank statement",
    "date": "2023-03-15",
    "confidence_score": 0.95,
    "suggested_name": "Chase Bank Statement March 2023",
    "additional_metadata": {{
        "account_type": "checking",
        "statement_period": "March 2023"
    }}
}}"""

    def _parse_ai_response(self, response: str) -> DocumentInfo:
        """Parse AI response into DocumentInfo object."""
        try:
            if not response or response.strip() == "":
                raise ValueError("Empty response")

            # Extract JSON from response
            json_str = self._extract_json_from_response(response)
            json_str = self._clean_json_string(json_str)

            data = json.loads(json_str)

            # Parse date
            doc_date = self._parse_date_from_data(data.get("date"))

            return DocumentInfo(
                company_name=data.get("company_name", "Unknown") or "Unknown",
                document_type=data.get("document_type", "document") or "document",
                date=doc_date,
                confidence_score=float(data.get("confidence_score", 0.0)),
                suggested_name=data.get("suggested_name", "") or "",
                additional_metadata=data.get("additional_metadata", {}),
            )

        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            logger.debug(f"Raw response: {response[:500]}...")
            return DocumentInfo(
                company_name="Unknown",
                document_type="document",
                date=None,
                confidence_score=0.0,
                suggested_name="",
                additional_metadata={"parsing_error": str(e)},
            )

    def _extract_json_from_response(self, response: str) -> str:
        """Extract JSON from AI response text."""
        # Look for JSON object in the response
        json_match = re.search(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", response, re.DOTALL)
        if json_match:
            return json_match.group()

        # If no JSON found, return the response as-is and let JSON parsing handle it
        return response.strip()

    def _clean_json_string(self, json_str: str) -> str:
        """Clean and fix common JSON formatting issues."""
        # Remove any text before first { and after last }
        start_idx = json_str.find("{")
        end_idx = json_str.rfind("}")

        if start_idx >= 0 and end_idx > start_idx:
            json_str = json_str[start_idx : end_idx + 1]

        # Clean up whitespace
        json_str = re.sub(r"\s+", " ", json_str)

        # Try to fix unmatched braces
        open_braces = json_str.count("{")
        close_braces = json_str.count("}")
        if open_braces > close_braces:
            json_str += "}" * (open_braces - close_braces)

        return json_str

    def _parse_date_from_data(self, date_str: Any) -> Optional[date]:
        """Parse date from AI response data."""
        if not date_str:
            return None

        try:
            if isinstance(date_str, str):
                # Try ISO format first
                if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                # Try general parsing
                return date_parser.parse(date_str).date()
            return None
        except Exception:
            return None

    def _enhance_document_info(
        self, doc_info: DocumentInfo, pdf_document: PDFDocument
    ) -> DocumentInfo:
        """Enhance document info with additional extraction methods."""
        # Try fallback date extraction if AI didn't find one
        if not doc_info.date:
            doc_info.date = self._extract_date_from_text(
                pdf_document.text_content
            ) or self._extract_date_from_filename(pdf_document.file_path.name)

        # Generate suggested name if not provided
        if not doc_info.suggested_name:
            doc_info.suggested_name = self._generate_suggested_name(doc_info)

        return doc_info

    def _extract_date_from_text(self, text: str) -> Optional[date]:
        """Extract date from document text using regex patterns."""
        patterns = [
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",  # MM/DD/YYYY
            r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",  # YYYY-MM-DD
            r"\b(\w+)\s+(\d{1,2}),?\s+(\d{4})\b",  # Month DD, YYYY
            r"\b(\d{1,2})\s+(\w+)\s+(\d{4})\b",  # DD Month YYYY
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return date_parser.parse(match.group()).date()
                except Exception:
                    continue

        # Look for month-year patterns (e.g., "January 2023")
        month_year_pattern = r"\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})\b"
        match = re.search(month_year_pattern, text, re.IGNORECASE)
        if match:
            try:
                # Use the first day of the month as default
                return date_parser.parse(f"{match.group(1)} 1, {match.group(2)}").date()
            except Exception:
                pass

        return None

    def _extract_date_from_filename(self, filename: str) -> Optional[date]:
        """Extract date from filename patterns."""
        patterns = [
            r"(\d{4})_(\d{2})_(\d{2})",  # YYYY_MM_DD
            r"(\d{4})(\d{2})(\d{2})",  # YYYYMMDD
            r"(\d{4})-(\d{2})-(\d{2})",  # YYYY-MM-DD
        ]

        for pattern in patterns:
            match = re.search(pattern, filename)
            if match:
                try:
                    year, month, day = map(int, match.groups())
                    if 1900 <= year <= 2030 and 1 <= month <= 12 and 1 <= day <= 31:
                        return date(year, month, day)
                except Exception:
                    continue

        return None

    def _generate_suggested_name(self, doc_info: DocumentInfo) -> str:
        """Generate a suggested filename based on document information."""
        parts = []

        if doc_info.company_name and doc_info.company_name != "Unknown":
            parts.append(doc_info.company_name)

        if doc_info.document_type and doc_info.document_type != "document":
            parts.append(
                " ".join(word.capitalize() for word in doc_info.document_type.split())
            )

        if doc_info.date:
            parts.append(doc_info.date.strftime("%B %Y"))

        return " ".join(parts) if parts else "Unnamed Document"

    def _create_fallback_document_info(self, pdf_document: PDFDocument) -> DocumentInfo:
        """Create fallback document info when AI analysis fails."""
        # Try basic date extraction
        extracted_date = self._extract_date_from_filename(
            pdf_document.file_path.name
        ) or self._extract_date_from_text(pdf_document.text_content[:1000])

        return DocumentInfo(
            company_name="Unknown",
            document_type="document",
            date=extracted_date,
            confidence_score=0.0,
            suggested_name=pdf_document.file_path.stem,
            additional_metadata={"fallback": True},
        )

    def batch_analyze(self, documents: List[PDFDocument]) -> List[DocumentInfo]:
        """Analyze multiple documents in batch.

        Args:
            documents: List of PDFDocument objects to analyze

        Returns:
            List of DocumentInfo objects with analysis results
        """
        results = []
        total = len(documents)

        for i, document in enumerate(documents, 1):
            logger.info(f"Analyzing document {i}/{total}: {document.file_path.name}")
            try:
                doc_info = self.analyze_document(document)
                results.append(doc_info)
            except Exception as e:
                logger.error(f"Failed to analyze {document.file_path}: {e}")
                results.append(self._create_fallback_document_info(document))

        return results
