"""Command Line Interface (CLI) for candidate resume screening and ranking."""

import argparse
import sys
from pathlib import Path

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from src.config import settings
from src.models import FilterPreferences
from src.pipeline import ScreeningPipeline

console = Console(force_terminal=True, legacy_windows=False)


def run_cli() -> None:
    """Entry point for CLI execution."""
    parser = argparse.ArgumentParser(
        description="Candidate Resume Screening & Ranking System for SDE AI Internship"
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        default="./resumes",
        help="Path to directory containing candidate resumes (PDF, DOCX, TXT)",
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="./output/results.json",
        help="Path to write the output results JSON",
    )
    parser.add_argument(
        "--format", "-f",
        type=str,
        default="json,csv",
        help="Output export formats (comma-separated: json, csv)",
    )
    parser.add_argument(
        "--min-cgpa",
        type=float,
        default=None,
        help="Optional minimum CGPA filter (e.g. 7.5 on 10.0 scale)",
    )
    parser.add_argument(
        "--require-experience",
        action="store_true",
        help="Strictly filter for candidates with related industry/internship experience",
    )
    parser.add_argument(
        "--require-github",
        action="store_true",
        help="Strictly filter for candidates with a public GitHub profile link",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent worker threads",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="Launch the interactive Web Dashboard & FastAPI server",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for the FastAPI web server",
    )

    args = parser.parse_args()

    if args.serve:
        import uvicorn
        console.print(Panel.fit(
            f"[bold green]Starting Web Dashboard at http://localhost:{args.port}[/bold green]\n"
            f"[cyan]Access interactive folder upload, CGPA dial, and candidate cards.[/cyan]",
            title="FastAPI Web Interface"
        ))
        uvicorn.run("src.api:app", host="0.0.0.0", port=args.port, reload=False)
        return

    # CLI Batch Run
    console.print(Panel.fit(
        "[bold cyan]Candidate Resume Screening & Ranking Pipeline[/bold cyan]\n"
        f"Input Folder: [yellow]{args.input}[/yellow] | Output: [yellow]{args.output}[/yellow]",
        title="Kasparro SDE AI Screener"
    ))

    preferences = FilterPreferences(
        min_cgpa=args.min_cgpa,
        require_experience=args.require_experience,
        require_github_link=args.require_github,
    )

    pipeline = ScreeningPipeline()
    console.print("[dim]Scanning and evaluating candidate resumes...[/dim]")

    try:
        report = pipeline.process_directory(
            input_dir=args.input,
            preferences=preferences,
            max_workers=args.concurrency,
        )
    except Exception as e:
        console.print(f"[bold red]Failed to process directory:[/bold red] {e}")
        sys.exit(1)

    # Export formats
    formats = [f.strip().lower() for f in args.format.split(",")]
    if "json" in formats:
        pipeline.export_json(report, args.output)
        console.print(f"[green][OK] Exported JSON results to:[/green] {args.output}")

    if "csv" in formats:
        csv_path = Path(args.output).with_suffix(".csv")
        pipeline.export_csv(report, csv_path)
        console.print(f"[green][OK] Exported CSV results to:[/green] {csv_path}")

    if "xlsx" in formats or "excel" in formats or "all" in formats:
        xlsx_path = Path(args.output).with_suffix(".xlsx")
        pipeline.export_excel(report, xlsx_path)
        console.print(f"[green][OK] Exported Excel spreadsheet to:[/green] {xlsx_path}")

    if "docx" in formats or "doc" in formats or "all" in formats:
        docx_path = Path(args.output).with_suffix(".docx")
        pipeline.export_docx(report, docx_path)
        console.print(f"[green][OK] Exported Word Document to:[/green] {docx_path}")

    # Display Batch Summary
    summary = report.batch_summary
    summary_table = Table(title="Batch Processing Summary", show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="dim")
    summary_table.add_column("Count / Value", justify="right")

    summary_table.add_row("Total Resumes Ingested", str(summary.total_resumes))
    summary_table.add_row("Successfully Parsed", str(summary.successfully_parsed))
    summary_table.add_row("Eligible Candidates", f"[bold green]{summary.eligible}[/bold green]")
    summary_table.add_row("Rejected Candidates", f"[bold red]{summary.rejected}[/bold red]")
    summary_table.add_row("Failed / Unreadable", str(summary.failed_unreadable))
    summary_table.add_row("Average Score (Eligible)", f"{summary.average_score_eligible} / 100")
    console.print(summary_table)

    # Display GitHub Cohort Distribution
    if summary.github_cohorts:
        gh_table = Table(title="GitHub Developer Cohorts", show_header=True, header_style="bold blue")
        gh_table.add_column("Cohort", style="cyan")
        gh_table.add_column("Candidates", justify="right")
        for cohort, count in summary.github_cohorts.items():
            gh_table.add_row(cohort, str(count))
        console.print(gh_table)

    # Display Top Ranked Candidates Table
    if report.ranked_candidates:
        ranked_table = Table(
            title=f"Top Ranked Eligible Candidates ({len(report.ranked_candidates)} Total)",
            show_header=True,
            header_style="bold green"
        )
        ranked_table.add_column("Rank", justify="center", style="bold")
        ranked_table.add_column("Candidate Name", style="cyan")
        ranked_table.add_column("Total Score", justify="right", style="bold yellow")
        ranked_table.add_column("AI Depth (40)", justify="right")
        ranked_table.add_column("Python (30)", justify="right")
        ranked_table.add_column("Cloud (15)", justify="right")
        ranked_table.add_column("GitHub (10)", justify="right")
        ranked_table.add_column("Eng (5)", justify="right")
        ranked_table.add_column("GitHub Cohort", style="magenta")

        for c in report.ranked_candidates[:15]:  # Show top 15 in console
            ranked_table.add_row(
                f"#{c.rank}",
                c.candidate_name,
                f"{c.total_score:.1f}",
                f"{c.score_breakdown.ai_project_depth:.1f}",
                f"{c.score_breakdown.python_backend:.1f}",
                f"{c.score_breakdown.cloud_fullstack:.1f}",
                f"{c.score_breakdown.github:.1f}",
                f"{c.score_breakdown.engineering_depth:.1f}",
                c.github_metrics.cohort if c.github_metrics else "N/A",
            )
        console.print(ranked_table)

    # Display Sample Rejections
    if report.rejected_candidates:
        rejected_table = Table(
            title=f"Sample Disqualified Candidates ({len(report.rejected_candidates)} Total)",
            show_header=True,
            header_style="bold red"
        )
        rejected_table.add_column("Candidate Name", style="cyan")
        rejected_table.add_column("File Name", style="dim")
        rejected_table.add_column("Rejection Reasons", style="red")

        for c in report.rejected_candidates[:8]:  # Show sample 8
            rejected_table.add_row(
                c.candidate_name,
                c.file_name,
                "; ".join(c.rejection_reasons),
            )
        console.print(rejected_table)


if __name__ == "__main__":
    run_cli()
