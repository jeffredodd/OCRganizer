"""Main Flask application for OCRganizer."""

import logging
import traceback
from pathlib import Path

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from werkzeug.utils import secure_filename

from src.ai_analyzer import AIAnalyzer
from src.config import get_config
from src.file_organizer import FileOrganizer, OrganizationStrategy
from src.pdf_processor import PDFProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load configuration
config = get_config()

# Initialize Flask app
app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = config.files.max_file_size_mb * 1024 * 1024
app.config["UPLOAD_FOLDER"] = config.files.input_dir
app.config["OUTPUT_FOLDER"] = config.files.output_dir
CORS(app)

# Ensure directories exist
Path(app.config["UPLOAD_FOLDER"]).mkdir(exist_ok=True)
Path(app.config["OUTPUT_FOLDER"]).mkdir(exist_ok=True)

# Initialize components
pdf_processor = PDFProcessor()

# Create organization strategy from config
org_strategy = OrganizationStrategy(
    structure_pattern=config.organization.structure_pattern,
    filename_pattern=config.organization.filename_pattern,
    date_format=config.organization.date_format,
)
file_organizer = FileOrganizer(
    Path(app.config["OUTPUT_FOLDER"]),
    org_strategy,
    enable_company_normalization=config.organization.enable_company_normalization,
    similarity_threshold=config.organization.company_similarity_threshold,
)

# Initialize AI analyzer
ai_analyzer = None
try:
    ai_analyzer = AIAnalyzer()
    logger.info(f"Initialized AI analyzer with provider: {ai_analyzer.provider}")
except Exception as e:
    logger.error(f"Failed to initialize AI analyzer: {e}")
    logger.warning("AI analysis will not be available")


@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload_files():
    """Handle file uploads."""
    if "files" not in request.files:
        return jsonify({"error": "No files provided"}), 400

    files = request.files.getlist("files")
    uploaded_files = []

    for file in files:
        if file and file.filename.endswith(".pdf"):
            filename = secure_filename(file.filename)
            filepath = Path(app.config["UPLOAD_FOLDER"]) / filename

            # Ensure unique filename
            counter = 1
            while filepath.exists():
                base = filepath.stem
                filepath = filepath.parent / f"{base}_{counter}.pdf"
                counter += 1

            file.save(filepath)
            uploaded_files.append(
                {
                    "filename": filepath.name,
                    "path": str(filepath),
                    "size": filepath.stat().st_size,
                }
            )

    return jsonify(
        {
            "message": f"Successfully uploaded {len(uploaded_files)} files",
            "files": uploaded_files,
        }
    )


@app.route("/api/process", methods=["POST"])
def process_pdfs():
    """Process uploaded PDFs."""
    if not ai_analyzer:
        return (
            jsonify({"error": "AI analyzer not configured. Please set API keys."}),
            500,
        )

    try:
        # Get list of PDFs to process
        input_dir = Path(app.config["UPLOAD_FOLDER"])
        pdf_files = list(input_dir.glob("*.pdf"))

        if not pdf_files:
            return jsonify({"error": "No PDF files found to process"}), 400

        results = []
        total_files = len(pdf_files)

        # Process each PDF
        for i, pdf_path in enumerate(pdf_files, 1):
            try:
                logger.info(f"Processing {i}/{total_files}: {pdf_path.name}")

                # Extract text and metadata
                pdf_doc = pdf_processor.process_pdf(pdf_path)

                # Analyze with AI
                doc_info = ai_analyzer.analyze_document(pdf_doc)

                # Organize the file
                new_path = file_organizer.organize_file(pdf_doc, doc_info)

                results.append(
                    {
                        "original_filename": pdf_path.name,
                        "new_path": str(
                            new_path.relative_to(Path(app.config["OUTPUT_FOLDER"]))
                        ),
                        "company": doc_info.company_name,
                        "document_type": doc_info.document_type,
                        "date": doc_info.date.isoformat() if doc_info.date else None,
                        "confidence": doc_info.confidence_score,
                        "suggested_name": doc_info.suggested_name,
                        "status": "success",
                    }
                )

            except Exception as e:
                logger.error(f"Error processing {pdf_path.name}: {e}")
                logger.error(traceback.format_exc())
                results.append(
                    {
                        "original_filename": pdf_path.name,
                        "status": "error",
                        "error": str(e),
                    }
                )

        # Get summary
        summary = file_organizer.get_organization_summary()

        return jsonify(
            {
                "message": f"Processed {len(results)} files",
                "results": results,
                "summary": summary,
            }
        )

    except Exception as e:
        logger.error(f"Processing error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500


@app.route("/api/process_single", methods=["POST"])
def process_single_pdf():
    """Process a single PDF with custom settings."""
    if not ai_analyzer:
        return jsonify({"error": "AI analyzer not configured"}), 500

    try:
        data = request.json
        pdf_path = Path(data["path"])

        if not pdf_path.exists():
            return jsonify({"error": "File not found"}), 404

        # Process the PDF
        pdf_doc = pdf_processor.process_pdf(pdf_path)

        # Check if custom categorization is provided
        if data.get("custom_category"):
            from datetime import datetime

            from src.ai_analyzer import DocumentInfo

            doc_info = DocumentInfo(
                company_name=data["custom_category"].get("company", "Unknown"),
                document_type=data["custom_category"].get("type", "document"),
                date=datetime.fromisoformat(data["custom_category"]["date"]).date()
                if data["custom_category"].get("date")
                else None,
                confidence_score=1.0,
                suggested_name=data["custom_category"].get("name", ""),
                additional_metadata={},
            )
        else:
            # Use AI to analyze
            doc_info = ai_analyzer.analyze_document(pdf_doc)

        # Organize the file
        new_path = file_organizer.organize_file(pdf_doc, doc_info)

        return jsonify(
            {
                "success": True,
                "original_path": str(pdf_path),
                "new_path": str(new_path),
                "doc_info": {
                    "company": doc_info.company_name,
                    "type": doc_info.document_type,
                    "date": doc_info.date.isoformat() if doc_info.date else None,
                    "confidence": doc_info.confidence_score,
                    "suggested_name": doc_info.suggested_name,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error processing single PDF: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/files", methods=["GET"])
def list_files():
    """List uploaded files waiting to be processed."""
    try:
        input_dir = Path(app.config["UPLOAD_FOLDER"])
        files = []

        for pdf_path in input_dir.glob("*.pdf"):
            files.append(
                {
                    "name": pdf_path.name,
                    "path": str(pdf_path),
                    "size": pdf_path.stat().st_size,
                    "modified": pdf_path.stat().st_mtime,
                }
            )

        return jsonify({"files": files})

    except Exception as e:
        logger.error(f"Error listing files: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/organized", methods=["GET"])
def list_organized():
    """List organized files."""
    try:
        output_dir = Path(app.config["OUTPUT_FOLDER"])
        organized_files = []

        for pdf_path in output_dir.rglob("*.pdf"):
            rel_path = pdf_path.relative_to(output_dir)
            organized_files.append(
                {
                    "name": pdf_path.name,
                    "path": str(rel_path),
                    "full_path": str(pdf_path),
                    "size": pdf_path.stat().st_size,
                }
            )

        return jsonify({"files": organized_files})

    except Exception as e:
        logger.error(f"Error listing organized files: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get current configuration."""
    return jsonify(
        {
            "ai_provider": ai_analyzer.provider if ai_analyzer else None,
            "input_dir": app.config["UPLOAD_FOLDER"],
            "output_dir": app.config["OUTPUT_FOLDER"],
            "max_file_size": app.config["MAX_CONTENT_LENGTH"],
            "organization_strategy": {
                "structure": file_organizer.strategy.structure_pattern,
                "filename": file_organizer.strategy.filename_pattern,
            },
        }
    )


@app.route("/api/config", methods=["POST"])
def update_config():
    """Update configuration."""
    try:
        data = request.json

        if "organization_strategy" in data:
            strategy_data = data["organization_strategy"]
            file_organizer.strategy = OrganizationStrategy(
                structure_pattern=strategy_data.get(
                    "structure", file_organizer.strategy.structure_pattern
                ),
                filename_pattern=strategy_data.get(
                    "filename", file_organizer.strategy.filename_pattern
                ),
                date_format=strategy_data.get(
                    "date_format", file_organizer.strategy.date_format
                ),
            )

        return jsonify({"message": "Configuration updated successfully"})

    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/preview", methods=["POST"])
def preview_organization():
    """Preview how a file would be organized without actually moving it."""
    if not ai_analyzer:
        return jsonify({"error": "AI analyzer not configured"}), 500

    try:
        data = request.json
        pdf_path = Path(data["path"])

        if not pdf_path.exists():
            return jsonify({"error": "File not found"}), 404

        # Process and analyze the PDF
        pdf_doc = pdf_processor.process_pdf(pdf_path)
        doc_info = ai_analyzer.analyze_document(pdf_doc)

        # Generate preview without moving the file
        target_dir = file_organizer._create_directory_structure(doc_info)
        filename = file_organizer._generate_filename(doc_info)
        preview_path = target_dir / filename

        return jsonify(
            {
                "original_path": str(pdf_path),
                "preview_path": str(
                    preview_path.relative_to(Path(app.config["OUTPUT_FOLDER"]))
                ),
                "doc_info": {
                    "company": doc_info.company_name,
                    "type": doc_info.document_type,
                    "date": doc_info.date.isoformat() if doc_info.date else None,
                    "confidence": doc_info.confidence_score,
                    "suggested_name": doc_info.suggested_name,
                },
            }
        )

    except Exception as e:
        logger.error(f"Error generating preview: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify(
        {
            "status": "healthy",
            "ai_configured": ai_analyzer is not None,
            "version": "1.0.0",
        }
    )


def main():
    """Main entry point for the web application."""
    app.run(host=config.web.host, port=config.web.port, debug=config.web.debug)


if __name__ == "__main__":
    main()
