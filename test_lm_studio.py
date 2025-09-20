#!/usr/bin/env python3
"""
Test script to verify LM Studio connectivity and functionality.
Run this after setting up LM Studio to ensure everything is working.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ai_analyzer import AIAnalyzer
from pdf_processor import PDFDocument


def test_lm_studio_connection():
    """Test connection to LM Studio."""
    print("🧪 Testing LM Studio Connection")
    print("=" * 40)

    # Check configuration
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY", "")
    model_name = os.getenv("LOCAL_MODEL_NAME", "local-model")

    print(f"Base URL: {base_url}")
    print(f"API Key: {'***' + api_key[-4:] if len(api_key) > 4 else 'Not set'}")
    print(f"Model Name: {model_name}")
    print()

    if "localhost" not in base_url and "127.0.0.1" not in base_url:
        print("⚠️  Warning: Not configured for local LM Studio")
        print("   Set OPENAI_BASE_URL=http://localhost:1234/v1 in your .env file")
        return False

    try:
        # Initialize analyzer
        print("🔧 Initializing AI Analyzer...")
        analyzer = AIAnalyzer(provider="openai")
        print("✅ AI Analyzer initialized successfully")

        # Create test document
        print("📄 Creating test document...")
        test_doc = PDFDocument(
            file_path=Path("test.pdf"),
            text_content="Invoice from Acme Corporation dated January 15, 2024 for services rendered.",
            metadata={},
            extracted_date=None,
            company_name=None,
            document_type=None,
            suggested_name=None,
        )

        # Test analysis
        print("🤖 Testing document analysis...")
        result = analyzer.analyze_document(test_doc)

        print("✅ Analysis completed successfully!")
        print(f"   Company: {result.company_name}")
        print(f"   Type: {result.document_type}")
        print(f"   Date: {result.date}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Suggested Name: {result.suggested_name}")

        if result.company_name != "Unknown" or result.document_type != "document":
            print("🎉 LM Studio is working correctly!")
            return True
        else:
            print("⚠️  LM Studio responded but may need prompt tuning")
            print(
                "   Try a different model or check the model's instruction-following capability"
            )
            return False

    except Exception as e:
        print(f"❌ Error testing LM Studio: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Ensure LM Studio is running with server enabled")
        print("   2. Check that a model is loaded in LM Studio")
        print("   3. Verify the port number (default: 1234)")
        print("   4. Check your .env configuration")
        return False


def main():
    """Main test function."""
    print("🚀 OCRganizer LM Studio Test")
    print("=" * 50)
    print()

    success = test_lm_studio_connection()

    print()
    print("=" * 50)
    if success:
        print("✅ LM Studio integration is working!")
        print("   You can now run: ./preview_pdfs.sh or ./process_pdfs.sh")
    else:
        print("❌ LM Studio integration needs attention")
        print("   Please check the troubleshooting steps above")
        print("   Or see LM_STUDIO_SETUP.md for detailed setup instructions")
    print()


if __name__ == "__main__":
    main()
