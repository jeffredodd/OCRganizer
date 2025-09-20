"""File organization module for organizing PDFs into structured directories."""
import calendar
import logging
import re
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.ai_analyzer import DocumentInfo
from src.company_normalizer import CompanyNormalizer
from src.pdf_processor import PDFDocument

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class OrganizationStrategy:
    """Defines the organization strategy for files."""

    structure_pattern: str = "{company}/{year}/{month}"
    filename_pattern: str = "{company}_{type}_{date}"
    date_format: str = "%Y-%m-%d"


class FileOrganizer:
    """Handles file organization and renaming based on document information."""

    def __init__(
        self,
        output_dir: Path,
        strategy: Optional[OrganizationStrategy] = None,
        enable_company_normalization: bool = True,
        similarity_threshold: float = 0.8,
    ):
        """
        Initialize the file organizer.

        Args:
            output_dir: Base directory for organized files
            strategy: Organization strategy to use
            enable_company_normalization: Enable company name normalization
            similarity_threshold: Threshold for fuzzy company name matching (0.0-1.0)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.strategy = strategy or OrganizationStrategy()

        # Initialize company normalizer
        self.enable_company_normalization = enable_company_normalization
        if enable_company_normalization:
            self.company_normalizer = CompanyNormalizer(
                output_dir=self.output_dir, similarity_threshold=similarity_threshold
            )
            logger.info(
                f"Company normalization enabled with threshold {similarity_threshold}"
            )
        else:
            self.company_normalizer = None
            logger.info("Company normalization disabled")

        # Track organized files for potential undo
        self.organization_history = []

    def organize_file(
        self, pdf_document: PDFDocument, doc_info: DocumentInfo, copy_file: bool = False
    ) -> Path:
        """
        Organize a single PDF file based on its information.

        Args:
            pdf_document: PDFDocument object
            doc_info: DocumentInfo with categorization data
            copy_file: If True, copy file instead of moving

        Returns:
            Path to the organized file
        """
        logger.info(f"Organizing file: {pdf_document.file_path}")

        # Create directory structure
        target_dir = self._create_directory_structure(doc_info)

        # Generate filename
        filename = self._generate_filename(doc_info)

        # Ensure unique filename if file already exists
        target_path = target_dir / filename
        if target_path.exists():
            target_path = self._ensure_unique_path(target_path)

        # Move or copy the file
        try:
            if copy_file:
                shutil.copy2(pdf_document.file_path, target_path)
                logger.info(f"Copied file to: {target_path}")
            else:
                shutil.move(str(pdf_document.file_path), str(target_path))
                logger.info(f"Moved file to: {target_path}")

            # Track the organization
            self.organization_history.append(
                {
                    "original_path": pdf_document.file_path,
                    "new_path": target_path,
                    "doc_info": doc_info,
                }
            )

            return target_path

        except Exception as e:
            logger.error(f"Error organizing file {pdf_document.file_path}: {e}")
            raise

    def _format_month_folder(self, month: int) -> str:
        """
        Format month number into folder name like '01 - January'.

        Args:
            month: Month number (1-12)

        Returns:
            Formatted month string
        """
        month_name = calendar.month_name[month]
        return f"{month:02d} - {month_name}"

    def _create_directory_structure(self, doc_info: DocumentInfo) -> Path:
        """
        Create directory structure based on document information and strategy pattern.
        Uses smart nesting - only creates folders for known information.

        Args:
            doc_info: DocumentInfo object

        Returns:
            Path to the target directory
        """
        # Normalize company name if normalization is enabled
        if self.enable_company_normalization and self.company_normalizer:
            canonical_name = self.company_normalizer.normalize_company_name(
                doc_info.company_name or "Unknown"
            )
            company_folder = self.company_normalizer.get_folder_name(canonical_name)
            logger.debug(
                f"Normalized '{doc_info.company_name}' -> '{canonical_name}' -> folder '{company_folder}'"
            )
        else:
            company_folder = self._sanitize_dirname(doc_info.company_name or "Unknown")

        # Build path based on strategy pattern
        path_parts = []
        pattern_parts = self.strategy.structure_pattern.split("/")
        for part in pattern_parts:
            if part == "{company}":
                path_parts.append(company_folder)
            elif part == "{year}" and doc_info.date:
                path_parts.append(str(doc_info.date.year))
            elif part == "{year}" and doc_info.year_month_only:
                year, _ = doc_info.year_month_only
                path_parts.append(str(year))
            elif part == "{year}" and doc_info.year_only:
                path_parts.append(str(doc_info.year_only))
            elif part == "{month}" and doc_info.date:
                path_parts.append(self._format_month_folder(doc_info.date.month))
            elif part == "{month}" and doc_info.year_month_only:
                _, month = doc_info.year_month_only
                path_parts.append(self._format_month_folder(month))
            elif part == "{day}" and doc_info.date:
                path_parts.append(f"{doc_info.date.day:02d}")
            elif part == "{type}":
                path_parts.append(
                    self._sanitize_dirname(doc_info.document_type or "document")
                )
            # Skip parts that don't have data available
        # Create the full path
        target_dir = self.output_dir
        for part in path_parts:
            target_dir = target_dir / part

        target_dir.mkdir(parents=True, exist_ok=True)
        return target_dir

    def _generate_filename(
        self, doc_info: DocumentInfo, use_suggested: bool = False
    ) -> str:
        """
        Generate a filename based on document information.

        Args:
            doc_info: DocumentInfo object
            use_suggested: Use the AI-suggested name if available

        Returns:
            Generated filename with .pdf extension
        """
        if use_suggested and doc_info.suggested_name:
            filename = self._sanitize_filename(doc_info.suggested_name)
        else:
            # Use the filename pattern
            pattern = self.strategy.filename_pattern

            replacements = {
                "{company}": self._sanitize_filename(
                    doc_info.company_name or "Unknown"
                ),
                "{type}": self._sanitize_filename(doc_info.document_type or "document"),
            }

            if doc_info.date:
                replacements["{date}"] = doc_info.date.strftime(
                    self.strategy.date_format
                )
            else:
                replacements["{date}"] = "Unknown_Date"

            filename = pattern
            for placeholder, value in replacements.items():
                filename = filename.replace(placeholder, value)

            filename = self._sanitize_filename(filename)

        # Ensure .pdf extension
        if not filename.endswith(".pdf"):
            filename += ".pdf"

        return filename

    def _sanitize_filename(self, filename: str) -> str:
        """
        Sanitize filename to remove invalid characters.

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        if not filename:
            return "document"

        # Remove file extension if present
        if filename.endswith(".pdf"):
            filename = filename[:-4]

        # Replace invalid characters with underscores
        invalid_chars = r'[<>:"/\\|?*]'
        filename = re.sub(invalid_chars, "_", filename)

        # Replace multiple spaces with single underscore
        filename = re.sub(r"\s+", "_", filename)

        # Remove leading/trailing spaces and underscores
        filename = filename.strip("_").strip()

        # Ensure filename is not empty
        if not filename:
            filename = "document"

        # Limit length
        if len(filename) > 200:
            filename = filename[:200]

        return filename

    def _sanitize_dirname(self, dirname: str) -> str:
        """
        Sanitize directory name to remove invalid characters.

        Args:
            dirname: Original directory name

        Returns:
            Sanitized directory name
        """
        if not dirname:
            return "Unknown"

        # Replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        dirname = re.sub(invalid_chars, "_", dirname)

        # Replace multiple spaces with single underscore
        dirname = re.sub(r"\s+", "_", dirname)

        # Remove leading/trailing spaces and underscores
        dirname = dirname.strip("_").strip()

        # Ensure dirname is not empty
        if not dirname:
            dirname = "Unknown"

        return dirname

    def _ensure_unique_path(self, path: Path) -> Path:
        """
        Ensure the path is unique by adding a number suffix if needed.

        Args:
            path: Original path

        Returns:
            Unique path
        """
        if not path.exists():
            return path

        base = path.stem
        extension = path.suffix
        parent = path.parent
        counter = 1

        while True:
            new_path = parent / f"{base}_{counter}{extension}"
            if not new_path.exists():
                return new_path
            counter += 1

    def batch_organize(
        self,
        documents: List[PDFDocument],
        doc_infos: List[DocumentInfo],
        copy_files: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Organize multiple PDF files.

        Args:
            documents: List of PDFDocument objects
            doc_infos: List of corresponding DocumentInfo objects
            copy_files: If True, copy files instead of moving

        Returns:
            List of organization results
        """
        if len(documents) != len(doc_infos):
            raise ValueError("Documents and doc_infos lists must have the same length")

        results = []

        for document, doc_info in zip(documents, doc_infos):
            try:
                new_path = self.organize_file(document, doc_info, copy_files)
                results.append(
                    {
                        "original_path": str(document.file_path),
                        "new_path": str(new_path),
                        "status": "success",
                        "company": doc_info.company_name,
                        "type": doc_info.document_type,
                        "date": doc_info.date.isoformat() if doc_info.date else None,
                    }
                )
            except Exception as e:
                logger.error(f"Failed to organize {document.file_path}: {e}")
                results.append(
                    {
                        "original_path": str(document.file_path),
                        "new_path": None,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return results

    def undo_organization(self, organized_path: Path, original_path: Path) -> Path:
        """
        Undo file organization by moving file back to original location.

        Args:
            organized_path: Current path of the organized file
            original_path: Original path to restore to

        Returns:
            Path to the restored file
        """
        if not organized_path.exists():
            raise FileNotFoundError(f"Organized file not found: {organized_path}")

        # Ensure original directory exists
        original_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file back
        shutil.move(str(organized_path), str(original_path))

        # Clean up empty directories
        self._cleanup_empty_directories(organized_path.parent)

        logger.info(f"Restored file from {organized_path} to {original_path}")
        return original_path

    def _cleanup_empty_directories(self, directory: Path):
        """
        Remove empty directories up to the output directory.

        Args:
            directory: Directory to check and potentially remove
        """
        try:
            # Don't remove the output directory itself
            if directory == self.output_dir:
                return

            # Check if directory is empty
            if directory.exists() and not any(directory.iterdir()):
                directory.rmdir()
                logger.info(f"Removed empty directory: {directory}")

                # Recursively check parent
                if directory.parent != self.output_dir:
                    self._cleanup_empty_directories(directory.parent)
        except Exception as e:
            logger.warning(f"Could not remove directory {directory}: {e}")

    def get_organization_summary(self) -> Dict[str, Any]:
        """
        Get a summary of the organization history.

        Returns:
            Dictionary with organization statistics
        """
        total = len(self.organization_history)
        companies = set()
        doc_types = set()

        for entry in self.organization_history:
            if entry["doc_info"].company_name:
                companies.add(entry["doc_info"].company_name)
            if entry["doc_info"].document_type:
                doc_types.add(entry["doc_info"].document_type)

        summary = {
            "total_organized": total,
            "unique_companies": len(companies),
            "unique_document_types": len(doc_types),
            "companies": list(companies),
            "document_types": list(doc_types),
        }

        # Add normalization statistics if enabled
        if self.enable_company_normalization and self.company_normalizer:
            summary["normalization"] = self.company_normalizer.get_statistics()

        return summary

    def get_company_normalization_info(self) -> Optional[Dict[str, Any]]:
        """
        Get detailed company normalization information.

        Returns:
            Dictionary with normalization details or None if disabled
        """
        if not self.enable_company_normalization or not self.company_normalizer:
            return None

        return {
            "enabled": True,
            "statistics": self.company_normalizer.get_statistics(),
            "companies": self.company_normalizer.list_companies(),
        }
