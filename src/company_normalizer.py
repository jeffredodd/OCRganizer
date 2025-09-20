"""Company name normalization module for reducing duplicate organization folders.

This module provides functionality to normalize company names and detect similar
organizations to prevent duplicate folder creation.
"""

import logging
import re
import shutil
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, List, Optional, Set

logger = logging.getLogger(__name__)


@dataclass
class CompanyMapping:
    """Represents a mapping between variations of company names."""

    canonical_name: str
    variations: Set[str] = field(default_factory=set)
    folder_name: str = ""

    def __post_init__(self):
        """Set folder name if not provided."""
        if not self.folder_name:
            self.folder_name = self._sanitize_name(self.canonical_name)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for folder usage."""
        if not name:
            return "Unknown"

        # Replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        name = re.sub(invalid_chars, "_", name)

        # Replace multiple spaces with single underscore
        name = re.sub(r"\s+", "_", name)

        # Remove leading/trailing spaces and underscores
        name = name.strip("_").strip()

        return name or "Unknown"


class CompanyNormalizer:
    """Handles company name normalization and duplicate detection."""

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        similarity_threshold: float = 0.8,
        auto_merge_duplicates: bool = True,
    ):
        """Initialize the company normalizer.

        Args:
            output_dir: Output directory to scan for existing companies
            similarity_threshold: Threshold for fuzzy matching (0.0-1.0)
            auto_merge_duplicates: Automatically merge duplicate company folders
        """
        self.similarity_threshold = similarity_threshold
        self.auto_merge_duplicates = auto_merge_duplicates
        self.output_dir = output_dir
        self.company_mappings: Dict[str, CompanyMapping] = {}
        self.normalized_to_canonical: Dict[str, str] = {}

        # Common company suffixes and prefixes to normalize
        self.common_suffixes = {
            "inc",
            "inc.",
            "incorporated",
            "corp",
            "corp.",
            "corporation",
            "llc",
            "l.l.c.",
            "ltd",
            "ltd.",
            "limited",
            "co",
            "co.",
            "company",
            "bank",
            "credit union",
            "federal credit union",
        }

        self.common_prefixes = {"the", "a", "an"}

        # Load existing companies if output directory provided
        if output_dir:
            self.scan_existing_companies(output_dir)

            # Auto-merge duplicates if enabled
            if auto_merge_duplicates:
                self._auto_merge_duplicates()

    def scan_existing_companies(self, output_dir: Path) -> None:
        """Scan existing output directory for company folders.

        Args:
            output_dir: Directory to scan for existing company folders
        """
        if not output_dir.exists():
            logger.info("Output directory doesn't exist yet, starting fresh")
            return

        logger.info(f"Scanning existing companies in {output_dir}")

        for item in output_dir.iterdir():
            if item.is_dir() and item.name != "Unknown":
                # Convert folder name back to a readable company name
                company_name = self._folder_name_to_company_name(item.name)

                # Create mapping for existing company
                mapping = CompanyMapping(
                    canonical_name=company_name, folder_name=item.name
                )
                mapping.variations.add(company_name)
                mapping.variations.add(item.name)

                self.company_mappings[company_name.lower()] = mapping
                self.normalized_to_canonical[
                    self._normalize_name(company_name)
                ] = company_name

                logger.debug(f"Found existing company: {company_name} -> {item.name}")

        logger.info(f"Found {len(self.company_mappings)} existing companies")

    def normalize_company_name(self, company_name: str) -> str:
        """Normalize a company name to match existing companies or create new canonical name.

        Args:
            company_name: Raw company name from AI analysis

        Returns:
            Normalized canonical company name
        """
        if not company_name or company_name.lower() in ["unknown", "null", "none"]:
            return "Unknown"

        # First, try exact match (case insensitive)
        exact_match = self._find_exact_match(company_name)
        if exact_match:
            logger.debug(f"Exact match found: {company_name} -> {exact_match}")
            return exact_match

        # Try fuzzy matching against existing companies
        fuzzy_match = self._find_fuzzy_match(company_name)
        if fuzzy_match:
            logger.info(f"Fuzzy match found: {company_name} -> {fuzzy_match}")
            # Add this variation to the existing mapping
            canonical = fuzzy_match
            self.company_mappings[canonical.lower()].variations.add(company_name)
            return canonical

        # No match found, create new canonical name
        canonical_name = self._create_canonical_name(company_name)
        self._add_new_company(canonical_name, company_name)

        logger.info(f"New company created: {company_name} -> {canonical_name}")
        return canonical_name

    def get_folder_name(self, canonical_name: str) -> str:
        """Get the folder name for a canonical company name.

        Args:
            canonical_name: Canonical company name

        Returns:
            Sanitized folder name
        """
        mapping = self.company_mappings.get(canonical_name.lower())
        if mapping:
            return mapping.folder_name

        # Fallback: create sanitized name
        return self._sanitize_name(canonical_name)

    def _find_exact_match(self, company_name: str) -> Optional[str]:
        """Find exact match for company name."""
        # Check direct mapping
        if company_name.lower() in self.company_mappings:
            return self.company_mappings[company_name.lower()].canonical_name

        # Check variations
        for mapping in self.company_mappings.values():
            if company_name.lower() in [v.lower() for v in mapping.variations]:
                return mapping.canonical_name

        return None

    def _find_fuzzy_match(self, company_name: str) -> Optional[str]:
        """Find fuzzy match for company name using similarity scoring."""
        normalized_input = self._normalize_name(company_name)
        best_match = None
        best_score = 0.0

        for canonical, mapping in self.company_mappings.items():
            # Check against canonical name
            canonical_normalized = self._normalize_name(mapping.canonical_name)
            score = self._calculate_similarity(normalized_input, canonical_normalized)

            if score > best_score and score >= self.similarity_threshold:
                best_score = score
                best_match = mapping.canonical_name

            # Check against variations
            for variation in mapping.variations:
                variation_normalized = self._normalize_name(variation)
                score = self._calculate_similarity(
                    normalized_input, variation_normalized
                )

                if score > best_score and score >= self.similarity_threshold:
                    best_score = score
                    best_match = mapping.canonical_name

        if best_match:
            logger.debug(
                f"Fuzzy match: {company_name} -> {best_match} (score: {best_score:.3f})"
            )

        return best_match

    def _normalize_name(self, name: str) -> str:
        """Normalize name for comparison by removing common variations."""
        if not name:
            return ""

        # Convert to lowercase
        normalized = name.lower().strip()

        # Remove punctuation and extra spaces
        normalized = re.sub(r"[^\w\s]", " ", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()

        # Split into words
        words = normalized.split()

        # Remove common prefixes
        while words and words[0] in self.common_prefixes:
            words.pop(0)

        # Remove common suffixes
        while words and words[-1] in self.common_suffixes:
            words.pop()

        # Join back
        return " ".join(words)

    def _calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two normalized names."""
        if not name1 or not name2:
            return 0.0

        # Use SequenceMatcher for basic similarity
        basic_similarity = SequenceMatcher(None, name1, name2).ratio()

        # Boost score for exact word matches
        words1 = set(name1.split())
        words2 = set(name2.split())

        if words1 and words2:
            word_overlap = len(words1.intersection(words2)) / len(words1.union(words2))

            # Special case: if one is a subset of the other with high word overlap
            if word_overlap > 0.8:
                subset_bonus = 0.2
            else:
                subset_bonus = 0.0

            # Weighted combination with subset bonus
            return min(1.0, 0.6 * basic_similarity + 0.3 * word_overlap + subset_bonus)

        return basic_similarity

    def _create_canonical_name(self, company_name: str) -> str:
        """Create a canonical name from the input company name."""
        # Clean up the name
        canonical = company_name.strip()

        # Capitalize properly
        canonical = self._proper_case(canonical)

        return canonical

    def _proper_case(self, name: str) -> str:
        """Apply proper case formatting to company name."""
        if not name:
            return name

        # Split on common delimiters
        parts = re.split(r"(\s+|[-_&/])", name)

        result_parts = []
        for part in parts:
            if part.strip():
                # Handle special cases
                if part.lower() in ["of", "and", "the", "for", "in", "on", "at", "by"]:
                    result_parts.append(part.lower())
                elif part.upper() in ["LLC", "INC", "CORP", "LTD", "USA", "US", "UK"]:
                    result_parts.append(part.upper())
                else:
                    result_parts.append(part.capitalize())
            else:
                result_parts.append(part)

        return "".join(result_parts)

    def _add_new_company(self, canonical_name: str, original_name: str) -> None:
        """Add a new company mapping."""
        mapping = CompanyMapping(canonical_name=canonical_name)
        mapping.variations.add(original_name)
        mapping.variations.add(canonical_name)

        self.company_mappings[canonical_name.lower()] = mapping
        self.normalized_to_canonical[
            self._normalize_name(canonical_name)
        ] = canonical_name

    def _folder_name_to_company_name(self, folder_name: str) -> str:
        """Convert a folder name back to a readable company name."""
        # Replace underscores with spaces
        name = folder_name.replace("_", " ")

        # Apply proper case
        name = self._proper_case(name)

        return name

    def _sanitize_name(self, name: str) -> str:
        """Sanitize name for folder usage."""
        if not name:
            return "Unknown"

        # Replace invalid characters
        invalid_chars = r'[<>:"/\\|?*]'
        name = re.sub(invalid_chars, "_", name)

        # Replace multiple spaces with single underscore
        name = re.sub(r"\s+", "_", name)

        # Remove leading/trailing spaces and underscores
        name = name.strip("_").strip()

        return name or "Unknown"

    def get_statistics(self) -> Dict[str, any]:
        """Get statistics about the normalization mappings."""
        total_variations = sum(
            len(mapping.variations) for mapping in self.company_mappings.values()
        )

        return {
            "total_companies": len(self.company_mappings),
            "total_variations": total_variations,
            "average_variations_per_company": total_variations
            / len(self.company_mappings)
            if self.company_mappings
            else 0,
            "similarity_threshold": self.similarity_threshold,
        }

    def list_companies(self) -> List[Dict[str, any]]:
        """List all companies and their variations."""
        companies = []
        for mapping in self.company_mappings.values():
            companies.append(
                {
                    "canonical_name": mapping.canonical_name,
                    "folder_name": mapping.folder_name,
                    "variations": list(mapping.variations),
                }
            )

        return sorted(companies, key=lambda x: x["canonical_name"])

    def _auto_merge_duplicates(self) -> None:
        """Automatically merge duplicate company folders."""
        if not self.output_dir or not self.output_dir.exists():
            return

        logger.info("Scanning for duplicate company folders to merge...")

        # Find potential duplicates
        companies = list(self.company_mappings.values())
        duplicates = []

        for i, company1 in enumerate(companies):
            for company2 in companies[i + 1 :]:
                name1 = self._normalize_name(company1.canonical_name)
                name2 = self._normalize_name(company2.canonical_name)
                similarity = self._calculate_similarity(name1, name2)

                # Use higher threshold for auto-merging (more conservative)
                if similarity > 0.85:
                    duplicates.append(
                        {
                            "company1": company1,
                            "company2": company2,
                            "similarity": similarity,
                        }
                    )

        if not duplicates:
            logger.debug("No duplicate company folders found")
            return

        logger.info(f"Found {len(duplicates)} duplicate pairs to merge")

        # Perform merges
        merged_count = 0
        for dup in duplicates:
            if self._merge_company_folders(dup["company1"], dup["company2"]):
                merged_count += 1

        if merged_count > 0:
            logger.info(f"Successfully merged {merged_count} duplicate company folders")
            # Rescan companies after merging
            self.company_mappings.clear()
            self.normalized_to_canonical.clear()
            self.scan_existing_companies(self.output_dir)

    def _merge_company_folders(
        self, company1: CompanyMapping, company2: CompanyMapping
    ) -> bool:
        """Merge two company folders.

        Args:
            company1: First company mapping
            company2: Second company mapping

        Returns:
            True if merge was successful, False otherwise
        """
        folder1 = self.output_dir / company1.folder_name
        folder2 = self.output_dir / company2.folder_name

        if not folder1.exists() or not folder2.exists():
            logger.warning(
                f"Cannot merge {company1.canonical_name} <-> {company2.canonical_name}: folder missing"
            )
            return False

        # Count files to decide which folder to keep
        count1 = sum(1 for _ in folder1.rglob("*.pdf"))
        count2 = sum(1 for _ in folder2.rglob("*.pdf"))

        # Keep the folder with more files, or the one with shorter name as tiebreaker
        if count1 > count2 or (
            count1 == count2
            and len(company1.canonical_name) <= len(company2.canonical_name)
        ):
            keep_folder, merge_folder = folder1, folder2
            keep_name, merge_name = company1.canonical_name, company2.canonical_name
        else:
            keep_folder, merge_folder = folder2, folder1
            keep_name, merge_name = company2.canonical_name, company1.canonical_name

        logger.info(
            f"Merging '{merge_name}' into '{keep_name}' ({count1 + count2} files total)"
        )

        try:
            # Move all files from merge_folder to keep_folder
            files_moved = 0
            for item in merge_folder.rglob("*"):
                if item.is_file():
                    # Calculate relative path
                    rel_path = item.relative_to(merge_folder)
                    target_path = keep_folder / rel_path

                    # Ensure target directory exists
                    target_path.parent.mkdir(parents=True, exist_ok=True)

                    # Handle filename conflicts
                    if target_path.exists():
                        stem = target_path.stem
                        suffix = target_path.suffix
                        counter = 1
                        while target_path.exists():
                            target_path = (
                                target_path.parent / f"{stem}_{counter}{suffix}"
                            )
                            counter += 1

                    # Move the file
                    shutil.move(str(item), str(target_path))
                    files_moved += 1

            # Remove empty merge folder
            shutil.rmtree(merge_folder)
            logger.info(
                f"Successfully merged {files_moved} files and removed {merge_folder.name}"
            )
            return True

        except Exception as e:
            logger.error(f"Error merging {merge_name} into {keep_name}: {e}")
            return False
