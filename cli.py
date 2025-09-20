#!/usr/bin/env python3
"""Command-line interface for OCRganizer."""

import argparse
import contextlib
import io
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.status import Status
from rich.table import Table
from rich.text import Text
from rich.tree import Tree

from src.ai_analyzer import AIAnalyzer
from src.config import get_config
from src.file_organizer import FileOrganizer, OrganizationStrategy
from src.pdf_processor import PDFProcessor

# Set up console and logging
console = Console()
error_console = Console(stderr=True)


# Custom logging setup to capture errors separately
class ErrorCapture:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def add_error(self, message, file_name=None):
        self.errors.append(
            {"message": message, "file": file_name, "timestamp": datetime.now()}
        )

    def add_warning(self, message, file_name=None):
        self.warnings.append(
            {"message": message, "file": file_name, "timestamp": datetime.now()}
        )

    def get_error_summary(self):
        return {
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "errors": self.errors,
            "warnings": self.warnings,
        }


# Global error capture instance
error_capture = ErrorCapture()

# Set up logging to capture errors
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    handlers=[RichHandler(console=error_console, show_time=False, show_path=False)],
)
logger = logging.getLogger(__name__)


def print_header():
    """Print a beautiful header for the application."""
    header_text = """
 ██████╗  ██████╗██████╗  ██████╗  █████╗ ███╗   ██╗██╗███████╗███████╗██████╗ 
██╔═══██╗██╔════╝██╔══██╗██╔════╝ ██╔══██╗████╗  ██║██║╚══███╔╝██╔════╝██╔══██╗
██║   ██║██║     ██████╔╝██║  ███╗███████║██╔██╗ ██║██║  ███╔╝ █████╗  ██████╔╝
██║   ██║██║     ██╔══██╗██║   ██║██╔══██║██║╚██╗██║██║ ███╔╝  ██╔══╝  ██╔══██╗
╚██████╔╝╚██████╗██║  ██║╚██████╔╝██║  ██║██║ ╚████║██║███████╗███████╗██║  ██║
 ╚═════╝  ╚═════╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝╚══════╝╚══════╝╚═╝  ╚═╝
    """

    console.print(
        Panel(
            Align.center(Text(header_text, style="bold cyan")),
            title="[bold white]📄 AI-Powered Document Organization[/bold white]",
            subtitle="[dim]Intelligently categorize and organize your PDFs[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )
    console.print()


def create_stats_panel(stats: Dict[str, Any]) -> Panel:
    """Create a statistics panel."""
    table = Table(show_header=False, box=None, padding=(0, 1))
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold white")

    table.add_row("📊 Total Files", str(stats.get("total", 0)))
    table.add_row("✅ Processed", str(stats.get("processed", 0)))
    table.add_row("❌ Failed", str(stats.get("failed", 0)))
    table.add_row("🏢 Companies", str(stats.get("companies", 0)))
    table.add_row("📋 Doc Types", str(stats.get("doc_types", 0)))
    table.add_row("⚡ Success Rate", f"{stats.get('success_rate', 0):.1f}%")

    return Panel(
        table, title="[bold]📈 Live Stats[/bold]", border_style="green", width=30
    )


def create_file_status_text(
    current_file: str,
    file_index: int,
    total_files: int,
    file_time: float = 0,
    doc_info: Dict = None,
) -> Text:
    """Create a single line status for current file processing."""
    text = Text()

    if not current_file:
        text.append("Waiting to start...", style="dim")
        return text

    # Progress indicator
    text.append(f"[{file_index}/{total_files}] ", style="cyan")

    # File name
    text.append("📄 ", style="blue")
    text.append(f"{current_file}", style="bold white")

    # File processing time
    if file_time > 0:
        text.append(f" ({file_time:.1f}s)", style="dim")

    # Quick info if available
    if doc_info:
        text.append(" → ", style="dim")
        text.append(f"{doc_info.get('company', 'Unknown')}", style="cyan")
        text.append(" | ", style="dim")
        text.append(f"{doc_info.get('type', 'Unknown')}", style="blue")

        confidence = doc_info.get("confidence", 0)
        confidence_style = (
            "green" if confidence > 0.8 else "yellow" if confidence > 0.6 else "red"
        )
        text.append(f" ({confidence:.2f})", style=confidence_style)

    return text


def create_error_panel(error_summary: Dict) -> Panel:
    """Create a panel showing errors and warnings."""
    if error_summary["error_count"] == 0 and error_summary["warning_count"] == 0:
        return Panel(
            Text("No errors or warnings", style="green"),
            title="[bold green]✅ Status[/bold green]",
            border_style="green",
            height=8,
        )

    content = Text()

    if error_summary["error_count"] > 0:
        content.append(f"❌ {error_summary['error_count']} Errors\n", style="red")
        for error in error_summary["errors"][-3:]:  # Show last 3 errors
            file_info = f" ({error['file']})" if error["file"] else ""
            content.append(
                f"  • {error['message'][:60]}...{file_info}\n", style="dim red"
            )
        if error_summary["error_count"] > 3:
            content.append(
                f"  ... and {error_summary['error_count'] - 3} more\n", style="dim"
            )

    if error_summary["warning_count"] > 0:
        if error_summary["error_count"] > 0:
            content.append("\n")
        content.append(
            f"⚠️ {error_summary['warning_count']} Warnings\n", style="yellow"
        )
        for warning in error_summary["warnings"][-2:]:  # Show last 2 warnings
            file_info = f" ({warning['file']})" if warning["file"] else ""
            content.append(
                f"  • {warning['message'][:60]}...{file_info}\n", style="dim yellow"
            )
        if error_summary["warning_count"] > 2:
            content.append(
                f"  ... and {error_summary['warning_count'] - 2} more\n", style="dim"
            )

    border_style = "red" if error_summary["error_count"] > 0 else "yellow"
    title_style = "red" if error_summary["error_count"] > 0 else "yellow"

    return Panel(
        content,
        title=f"[bold {title_style}]⚠️ Issues[/bold {title_style}]",
        border_style=border_style,
        height=8,
    )


def main():
    """Main CLI function."""
    print_header()

    # Load configuration
    config = get_config()

    parser = argparse.ArgumentParser(
        description="OCRganizer - Organize PDFs using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all PDFs from input to output directory
  python cli.py

  # Process with custom settings
  python cli.py --input /path/to/pdfs --output /path/to/organized

  # Preview what would be organized (dry run)
  python cli.py --dry-run

  # Process with specific AI provider
  python cli.py --provider anthropic

  # Show detailed progress
  python cli.py --verbose
        """,
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default=config.files.input_dir,
        help=f"Input directory containing PDFs (default: {config.files.input_dir})",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=config.files.output_dir,
        help=f"Output directory for organized PDFs (default: {config.files.output_dir})",
    )

    parser.add_argument(
        "--provider",
        "-p",
        choices=["openai", "anthropic"],
        default=config.ai.preferred_provider,
        help=f"AI provider to use (default: {config.ai.preferred_provider})",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be organized without actually moving files",
    )

    parser.add_argument(
        "--copy",
        action="store_true",
        default=config.files.copy_mode,
        help=f"Copy files instead of moving them (default: {config.files.copy_mode})",
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Show detailed progress information",
    )

    parser.add_argument(
        "--structure",
        type=str,
        default=config.organization.structure_pattern,
        help=f"Folder structure pattern (default: {config.organization.structure_pattern})",
    )

    parser.add_argument(
        "--filename",
        type=str,
        default=config.organization.filename_pattern,
        help=f"Filename pattern (default: {config.organization.filename_pattern})",
    )

    parser.add_argument(
        "--confidence-threshold",
        type=float,
        default=config.processing.confidence_threshold,
        help=f"Minimum confidence threshold for auto-processing (default: {config.processing.confidence_threshold})",
    )

    parser.add_argument("--json-output", type=str, help="Save results to JSON file")

    parser.add_argument(
        "--disable-normalization",
        action="store_true",
        help="Disable company name normalization (may create duplicate folders)",
    )

    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=config.organization.company_similarity_threshold,
        help=f"Company name similarity threshold (0.0-1.0, default: {config.organization.company_similarity_threshold})",
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    else:
        # Suppress most logging for cleaner UI
        logging.getLogger().setLevel(logging.ERROR)

    # Validate paths
    input_dir = Path(args.input)
    output_dir = Path(args.output)

    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)

    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Find PDF files (recursively search all subdirectories)
    pdf_files = list(input_dir.rglob("*.pdf"))
    if not pdf_files:
        console.print("[red]❌ No PDF files found in the input directory[/red]")
        console.print(f"[dim]Searched in: {input_dir}[/dim]")
        return

    # Display initial information
    info_table = Table(show_header=False, box=box.ROUNDED)
    info_table.add_column("Setting", style="cyan")
    info_table.add_column("Value", style="white")

    info_table.add_row("📁 Input Directory", str(input_dir))
    info_table.add_row("📁 Output Directory", str(output_dir))
    info_table.add_row("📄 PDF Files Found", str(len(pdf_files)))
    info_table.add_row("🤖 AI Provider", args.provider.upper())
    info_table.add_row("🎯 Confidence Threshold", f"{args.confidence_threshold:.2f}")

    if args.dry_run:
        info_table.add_row("🔍 Mode", "[yellow]DRY RUN (Preview Only)[/yellow]")
    elif args.copy:
        info_table.add_row("📋 Mode", "[blue]COPY FILES[/blue]")
    else:
        info_table.add_row("📋 Mode", "[green]MOVE FILES[/green]")

    console.print(
        Panel(info_table, title="[bold]⚙️ Configuration[/bold]", border_style="blue")
    )
    console.print()

    # Initialize components
    try:
        with console.status("[cyan]Initializing AI analyzer...", spinner="dots"):
            ai_analyzer = AIAnalyzer(provider=args.provider)
        console.print(
            f"[green]✅ AI analyzer initialized ({args.provider.upper()})[/green]"
        )
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize AI analyzer: {e}[/red]")
        console.print("[yellow]💡 Please check your API keys in .env file[/yellow]")
        sys.exit(1)

    # Initialize other components
    pdf_processor = PDFProcessor()

    # Create organization strategy
    strategy = OrganizationStrategy(
        structure_pattern=args.structure, filename_pattern=args.filename
    )

    file_organizer = FileOrganizer(
        output_dir=output_dir,
        strategy=strategy,
        enable_company_normalization=not args.disable_normalization,
        similarity_threshold=args.similarity_threshold,
    )

    # Process files with beautiful progress display
    results = []
    successful = 0
    failed = 0
    companies_found = set()
    doc_types_found = set()
    start_time = time.time()

    # Create layout for live display
    layout = Layout()
    layout.split_column(
        Layout(name="progress", size=3),
        Layout(name="current_file", size=3),
        Layout(name="main"),
    )
    layout["main"].split_row(
        Layout(name="stats", ratio=1), Layout(name="errors", ratio=1)
    )

    # Capture stderr to catch PDF processing errors
    class ErrorCapturingHandler(logging.Handler):
        def emit(self, record):
            if record.levelno >= logging.ERROR:
                error_capture.add_error(
                    record.getMessage(), getattr(record, "filename", None)
                )
            elif record.levelno >= logging.WARNING:
                error_capture.add_warning(
                    record.getMessage(), getattr(record, "filename", None)
                )

    # Add our custom handler to capture errors
    error_handler = ErrorCapturingHandler()
    logging.getLogger().addHandler(error_handler)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        expand=True,
    ) as progress:
        task = progress.add_task("[cyan]Processing PDFs...", total=len(pdf_files))

        # Initialize stats
        stats = {
            "total": len(pdf_files),
            "processed": 0,
            "failed": 0,
            "companies": 0,
            "doc_types": 0,
            "success_rate": 0.0,
        }

        with Live(layout, console=console, refresh_per_second=2, screen=True) as live:
            for i, pdf_path in enumerate(pdf_files):
                current_file_name = pdf_path.name
                file_start_time = time.time()

                # Update progress description
                progress.update(
                    task,
                    description=f"[cyan]Processing PDFs... ({i+1}/{len(pdf_files)})",
                )

                # Update current file display
                layout["current_file"].update(
                    Panel(
                        create_file_status_text(
                            current_file_name, i + 1, len(pdf_files), 0
                        ),
                        title="[bold]🔄 Current File[/bold]",
                        border_style="blue",
                    )
                )

                # Update stats panel
                layout["stats"].update(create_stats_panel(stats))

                # Update errors panel
                layout["errors"].update(
                    create_error_panel(error_capture.get_error_summary())
                )

                try:
                    # Capture stderr during PDF processing
                    stderr_capture = io.StringIO()
                    with contextlib.redirect_stderr(stderr_capture):
                        # Extract text and metadata
                        pdf_doc = pdf_processor.process_pdf(pdf_path)

                    # Check for captured errors
                    stderr_content = stderr_capture.getvalue()
                    if stderr_content.strip():
                        for line in stderr_content.strip().split("\n"):
                            if "ERROR" in line:
                                error_capture.add_error(line.strip(), current_file_name)
                            elif "WARNING" in line:
                                error_capture.add_warning(
                                    line.strip(), current_file_name
                                )

                    # Analyze with AI
                    doc_info = ai_analyzer.analyze_document(pdf_doc)

                    # Calculate file processing time
                    file_time = time.time() - file_start_time

                    # Update current file display with results
                    doc_info_dict = {
                        "company": doc_info.company_name,
                        "type": doc_info.document_type,
                        "confidence": doc_info.confidence_score,
                    }

                    layout["current_file"].update(
                        Panel(
                            create_file_status_text(
                                current_file_name,
                                i + 1,
                                len(pdf_files),
                                file_time,
                                doc_info_dict,
                            ),
                            title="[bold]🔄 Current File[/bold]",
                            border_style="blue",
                        )
                    )

                    # Update tracking sets
                    companies_found.add(doc_info.company_name)
                    doc_types_found.add(doc_info.document_type)

                    # Check confidence threshold
                    low_confidence = (
                        doc_info.confidence_score < args.confidence_threshold
                    )

                    if args.dry_run:
                        # Preview organization
                        target_dir = file_organizer._create_directory_structure(
                            doc_info
                        )
                        filename = file_organizer._generate_filename(doc_info)
                        preview_path = target_dir / filename

                        result = {
                            "original_path": str(pdf_path),
                            "preview_path": str(preview_path),
                            "company": doc_info.company_name,
                            "type": doc_info.document_type,
                            "date": doc_info.date.isoformat()
                            if doc_info.date
                            else None,
                            "confidence": doc_info.confidence_score,
                            "suggested_name": doc_info.suggested_name,
                            "status": "preview",
                            "low_confidence": low_confidence,
                            "processing_time": file_time,
                        }
                        successful += 1  # Count previews as successful for stats
                    else:
                        # Actually organize the file
                        new_path = file_organizer.organize_file(
                            pdf_doc, doc_info, copy_file=args.copy
                        )

                        result = {
                            "original_path": str(pdf_path),
                            "new_path": str(new_path),
                            "company": doc_info.company_name,
                            "type": doc_info.document_type,
                            "date": doc_info.date.isoformat()
                            if doc_info.date
                            else None,
                            "confidence": doc_info.confidence_score,
                            "suggested_name": doc_info.suggested_name,
                            "status": "success",
                            "low_confidence": low_confidence,
                            "processing_time": file_time,
                        }
                        successful += 1

                    results.append(result)

                except Exception as e:
                    file_time = time.time() - file_start_time
                    error_capture.add_error(
                        f"Failed to process {pdf_path.name}: {str(e)}",
                        current_file_name,
                    )
                    results.append(
                        {
                            "original_path": str(pdf_path),
                            "status": "error",
                            "error": str(e),
                            "processing_time": file_time,
                        }
                    )
                    failed += 1

                # Update stats
                stats.update(
                    {
                        "processed": i + 1,
                        "failed": failed,
                        "companies": len(companies_found),
                        "doc_types": len(doc_types_found),
                        "success_rate": (successful / (i + 1)) * 100
                        if i + 1 > 0
                        else 0,
                    }
                )

                # Update all panels
                layout["stats"].update(create_stats_panel(stats))
                layout["errors"].update(
                    create_error_panel(error_capture.get_error_summary())
                )

                progress.advance(task)

                # Small delay to make the progress visible
                time.sleep(0.1)

    # Remove our custom handler
    logging.getLogger().removeHandler(error_handler)

    # Create beautiful summary
    console.print("\n")
    processing_time = time.time() - start_time

    # Summary statistics
    summary_table = Table(title="📊 Processing Summary", box=box.ROUNDED)
    summary_table.add_column("Metric", style="cyan", no_wrap=True)
    summary_table.add_column("Count", style="bold white", justify="right")
    summary_table.add_column("Details", style="dim")

    # Calculate average processing time per file
    avg_time_per_file = (
        sum(r.get("processing_time", 0) for r in results) / len(results)
        if results
        else 0
    )

    summary_table.add_row("📄 Total Files", str(len(pdf_files)), "")
    summary_table.add_row(
        "✅ Successful",
        str(successful),
        f"{(successful/len(pdf_files)*100):.1f}%" if pdf_files else "0%",
    )
    summary_table.add_row(
        "❌ Failed",
        str(failed),
        f"{(failed/len(pdf_files)*100):.1f}%" if pdf_files else "0%",
    )
    summary_table.add_row("🏢 Companies Found", str(len(companies_found)), "")
    summary_table.add_row("📋 Document Types", str(len(doc_types_found)), "")
    summary_table.add_row(
        "⏱️ Total Time",
        f"{processing_time:.1f}s",
        f"{len(pdf_files)/processing_time:.1f} files/sec"
        if processing_time > 0
        else "",
    )
    summary_table.add_row("🕰️ Avg Time/File", f"{avg_time_per_file:.1f}s", "")

    console.print(summary_table)

    # Show detailed error summary if there were errors
    error_summary = error_capture.get_error_summary()
    if error_summary["error_count"] > 0 or error_summary["warning_count"] > 0:
        console.print("\n")
        error_table = Table(title="⚠️ Issues Encountered", box=box.ROUNDED)
        error_table.add_column("Type", style="red")
        error_table.add_column("File", style="cyan")
        error_table.add_column("Message", style="white")

        # Show all errors
        for error in error_summary["errors"]:
            error_table.add_row(
                "❌ Error",
                error["file"] or "Unknown",
                error["message"][:80] + "..."
                if len(error["message"]) > 80
                else error["message"],
            )

        # Show warnings (limit to 5)
        for warning in error_summary["warnings"][:5]:
            error_table.add_row(
                "⚠️ Warning",
                warning["file"] or "Unknown",
                warning["message"][:80] + "..."
                if len(warning["message"]) > 80
                else warning["message"],
            )

        if error_summary["warning_count"] > 5:
            error_table.add_row(
                "⚠️ Warning",
                "...",
                f"and {error_summary['warning_count'] - 5} more warnings",
            )

        console.print(error_table)

    # Low confidence warnings
    low_confidence_files = [r for r in results if r.get("low_confidence", False)]
    if low_confidence_files:
        console.print("\n[yellow]⚠️ Low Confidence Files:[/yellow]")
        warning_table = Table(box=box.SIMPLE)
        warning_table.add_column("File", style="white")
        warning_table.add_column("Company", style="cyan")
        warning_table.add_column("Type", style="cyan")
        warning_table.add_column("Confidence", style="yellow")

        for result in low_confidence_files[:10]:  # Show max 10
            warning_table.add_row(
                Path(result["original_path"]).name,
                result.get("company", "Unknown"),
                result.get("type", "Unknown"),
                f"{result.get('confidence', 0):.2f}",
            )

        if len(low_confidence_files) > 10:
            warning_table.add_row(
                "...", f"and {len(low_confidence_files) - 10} more", "", ""
            )

        console.print(warning_table)

    # Companies and document types found
    if companies_found or doc_types_found:
        console.print("\n")

        columns = []

        if companies_found:
            companies_tree = Tree("🏢 Companies Found", style="cyan")
            for company in sorted(companies_found)[:15]:  # Show max 15
                companies_tree.add(company)
            if len(companies_found) > 15:
                companies_tree.add(f"... and {len(companies_found) - 15} more")
            columns.append(Panel(companies_tree, border_style="cyan"))

        if doc_types_found:
            types_tree = Tree("📋 Document Types", style="blue")
            for doc_type in sorted(doc_types_found):
                types_tree.add(doc_type)
            columns.append(Panel(types_tree, border_style="blue"))

        console.print(Columns(columns, equal=True))

    if not args.dry_run and successful > 0:
        # Get organization summary from file organizer
        try:
            org_summary = file_organizer.get_organization_summary()
            console.print(
                f"\n[green]✅ Successfully organized {org_summary.get('total_organized', successful)} files![/green]"
            )
        except:
            console.print(
                f"\n[green]✅ Successfully organized {successful} files![/green]"
            )

    # Save JSON output if requested
    if args.json_output:
        error_summary = error_capture.get_error_summary()
        avg_time_per_file = (
            sum(r.get("processing_time", 0) for r in results) / len(results)
            if results
            else 0
        )

        output_data = {
            "summary": {
                "total_processed": len(pdf_files),
                "successful": successful,
                "failed": failed,
                "companies_found": len(companies_found),
                "document_types_found": len(doc_types_found),
                "processing_time_seconds": processing_time,
                "average_time_per_file_seconds": avg_time_per_file,
                "success_rate": (successful / len(pdf_files)) * 100 if pdf_files else 0,
                "error_count": error_summary["error_count"],
                "warning_count": error_summary["warning_count"],
                "dry_run": args.dry_run,
                "timestamp": datetime.now().isoformat(),
            },
            "companies": sorted(list(companies_found)),
            "document_types": sorted(list(doc_types_found)),
            "errors": error_summary["errors"],
            "warnings": error_summary["warnings"],
            "results": results,
        }

        with open(args.json_output, "w") as f:
            json.dump(output_data, f, indent=2)

        console.print(f"\n[dim]📄 Results saved to {args.json_output}[/dim]")
        if error_summary["error_count"] > 0:
            console.print(
                f"[dim]   Including {error_summary['error_count']} errors and {error_summary['warning_count']} warnings[/dim]"
            )

    # Final message
    console.print("\n")
    if args.dry_run:
        console.print(
            Panel(
                "[yellow]🔍 This was a preview run - no files were moved.\n\n"
                "To actually organize the files, run the command again without --dry-run[/yellow]",
                title="[bold]Preview Complete[/bold]",
                border_style="yellow",
            )
        )
    else:
        if successful > 0:
            console.print(
                Panel(
                    f"[green]🎉 Successfully processed {successful} files!\n\n"
                    f"📁 Check your output directory: {output_dir}[/green]",
                    title="[bold]Processing Complete[/bold]",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    "[red]❌ No files were successfully processed.\n\n"
                    "Please check the error messages above and verify your configuration.[/red]",
                    title="[bold]Processing Failed[/bold]",
                    border_style="red",
                )
            )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️ Processing interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Unexpected error: {e}[/red]")
        if console.is_terminal:
            console.print("\n[dim]Run with --verbose for more details[/dim]")
        sys.exit(1)
