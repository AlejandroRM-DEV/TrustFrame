"""
TrustFrame - Video Analysis Tool

TrustFrame is a video analysis tool that compares two video files using both cryptographic and perceptual
hashing techniques. It provides detailed analysis of video integrity, frame-by-frame comparison, and sequence alignment
to detect modifications, insertions, deletions, and other changes between a reference video and evidence video.
"""

import sys
from pathlib import Path

import pyfiglet
import typer
from rich.console import Console
from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from typing_extensions import Annotated

from .comparator import VideoComparator
from .crypto import CryptoHasher
from .enums import CryptoAlgorithm, PerceptualAlgorithm
from .perceptual import PerceptualHasher

app = typer.Typer()


@app.command()
def analyze(
        # Required arguments: paths to reference and evidence videos
        reference: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, readable=True, resolve_path=True,
            help="Path to the reference video file"
        )],
        evidence: Annotated[Path, typer.Argument(
            exists=True, file_okay=True, readable=True, resolve_path=True,
            help="Path to the evidence video file to compare"
        )],

        # Optional parameters with defaults
        crypto_algorithm: Annotated[CryptoAlgorithm, typer.Option(
            help="Cryptographic hash algorithm to use for file integrity check"
        )] = CryptoAlgorithm.SHA256,
        perceptual_algorithm: Annotated[PerceptualAlgorithm, typer.Option(
            help="Perceptual hash algorithm to use for content comparison"
        )] = PerceptualAlgorithm.PHASH,
        max_frames: Annotated[int, typer.Option(
            help="Maximum number of frames to analyze from each video (None = all frames)"
        )] = None
):
    """
    Analyze two video files for differences using cryptographic and perceptual hashing.
    """
    console = Console()
    try:
        # Display application banner
        banner = pyfiglet.figlet_format("TrustFrame", font="slant")
        aligned = Align(banner, align="center")
        console.print(Panel(aligned, subtitle="Video Analysis Tool", expand=True))

        # === CRYPTOGRAPHIC HASH ANALYSIS ===
        # This section performs binary-level integrity checking
        console.print(f"\n[bold cyan]🔐 Cryptographic Hash Analysis ({crypto_algorithm.name})[/bold cyan]")
        hasher = CryptoHasher(crypto_algorithm)

        # Calculate hashes for both files
        original_hash = hasher.calculate_hash(reference)
        evidence_hash = hasher.calculate_hash(evidence)

        # Display cryptographic hash comparison results
        crypto_table = Table(title=f"{crypto_algorithm.name} Hash Summary", box=box.ROUNDED, expand=True)
        crypto_table.add_column("Reference", no_wrap=False, overflow="fold")
        crypto_table.add_column("Evidence", no_wrap=False, overflow="fold")

        # Color-code the match result
        value_style = "green" if original_hash == evidence_hash else "red"
        crypto_table.add_column("Match", style=value_style, no_wrap=False, overflow="fold")

        crypto_table.add_row(
            original_hash,
            evidence_hash,
            "Yes" if original_hash == evidence_hash else "No"
        )
        console.print(crypto_table)

        # === PERCEPTUAL HASH ANALYSIS ===
        # This section performs content-aware analysis of video frames
        console.print(f"\n[bold magenta]👁️  Perceptual Hash Analysis ({perceptual_algorithm.name})[/bold magenta]")
        perceptual_hasher = PerceptualHasher(perceptual_algorithm)

        # Get basic information about both videos
        console.print(f"\n[bold blue]Getting video information...[/bold blue]")
        ref_info = perceptual_hasher.get_video_info(reference)
        ev_info = perceptual_hasher.get_video_info(evidence)

        # Display video metadata comparison
        info_table = Table(title="Video Information", box=box.ROUNDED, expand=True)
        info_table.add_column("Video")
        info_table.add_column("Total Frames", justify="right")
        info_table.add_column("FPS", justify="right")
        info_table.add_column("Duration (s)", justify="right")

        info_table.add_row(
            f"Reference ({reference.name})",
            str(ref_info['total_frames']),
            f"{ref_info['fps']:.2f}",
            f"{ref_info['duration_seconds']:.2f}"
        )
        info_table.add_row(
            f"Evidence ({evidence.name})",
            str(ev_info['total_frames']),
            f"{ev_info['fps']:.2f}",
            f"{ev_info['duration_seconds']:.2f}"
        )
        console.print(info_table)

        # Determine frame sampling strategy
        if max_frames:
            target_frames = max_frames
            console.print(
                f"\n[bold yellow]Both videos will be analyzed using {target_frames} uniformly distributed frames[/bold yellow]"
            )
        else:
            target_frames = None
            console.print(f"\n[bold yellow]Analyzing all frames from both videos[/bold yellow]")

        # Analyze reference video
        console.print(f"\n[bold blue]Analyzing reference video: {reference.name}[/bold blue]")
        reference_analysis = perceptual_hasher.analyze_video(reference, target_frames)

        # Analyze evidence video
        console.print(f"\n[bold blue]Analyzing evidence video: {evidence.name}[/bold blue]")
        evidence_analysis = perceptual_hasher.analyze_video(evidence, target_frames)

        # === ADVANCED SEQUENCE ANALYSIS ===
        # This section performs sophisticated comparison of the two frame sequences
        console.print(f"\n[bold cyan]🔬 Advanced Sequence Analysis[/bold cyan]")

        comparator = VideoComparator()

        # Perform sequence alignment to identify all differences
        alignment, edit_distance = comparator.align_sequences(
            reference_analysis['frame_hashes'],
            evidence_analysis['frame_hashes']
        )

        # Analyze the types and counts of differences
        stats = comparator.analyze_differences(alignment)

        # Display sequence analysis summary
        stats_table = Table(title="Sequence Analysis Summary", box=box.ROUNDED, expand=True)
        stats_table.add_column("Operation Type")
        stats_table.add_column("Count", justify="right")
        stats_table.add_column("Description")

        stats_table.add_row("Matches", str(stats['matches']), "Identical frames in same position")
        stats_table.add_row("Substitutions", str(stats['substitutions']),
                            "Different frames in same position", style="yellow")
        stats_table.add_row("Insertions", str(stats['insertions']),
                            "Extra frames in evidence video", style="red")
        stats_table.add_row("Deletions", str(stats['deletions']),
                            "Missing frames from evidence video", style="red")
        stats_table.add_row("Edit Distance", str(edit_distance),
                            "Total operations needed to transform reference to evidence", style="red")

        console.print(stats_table)

        # === DETAILED ALIGNMENT DISPLAY ===
        # Show detailed frame-by-frame comparison (limited to first 1000 for performance)
        console.print(f"\n[bold magenta]📋 Detailed Alignment[/bold magenta]")

        alignment_table = Table(box=box.SIMPLE, expand=True)
        alignment_table.add_column("Operation", style="bold")
        alignment_table.add_column("Ref Frame", justify="center")
        alignment_table.add_column("Ev Frame", justify="center")
        alignment_table.add_column("Similarity", justify="center")
        alignment_table.add_column("Ref Hash", no_wrap=False, overflow="fold")
        alignment_table.add_column("Ev Hash", no_wrap=False, overflow="fold")

        # Process alignment results and calculate similarity scores
        for i, op in enumerate(alignment[:10]):  # Limit to 1000 for performance
            # Color-code operations by type
            operation_style = {
                'match': 'green',
                'substitution': 'yellow',
                'insertion': 'red',
                'deletion': 'red'
            }.get(op['type'], 'white')

            # Format frame numbers and hashes for display
            ref_frame = str(op['ref_frame']) if op['ref_frame'] else "---"
            ev_frame = str(op['ev_frame']) if op['ev_frame'] else "---"
            ref_hash = op['ref_hash'] if op['ref_hash'] else "---"
            ev_hash = op['ev_hash'] if op['ev_hash'] else "---"

            # Calculate similarity based on operation type
            if op['type'] == 'match':
                # Perfect matches have 100% similarity
                similarity_text = Text("100.0%", style="green")
            elif op['type'] in ['insertion', 'deletion']:
                # Insertions and deletions have 0% similarity
                similarity_text = Text("0.0%", style="red")
            elif op['type'] == 'substitution':
                # Calculate Hamming distance for substitutions
                hamming_result = comparator.calculate_hamming_distance(op['ref_hash'], op['ev_hash'])
                if hamming_result:
                    similarity_pct = hamming_result['similarity_percentage']
                    # Color-code similarity percentage
                    if similarity_pct >= 80:
                        style = "green"
                    elif similarity_pct >= 50:
                        style = "yellow"
                    else:
                        style = "red"
                    similarity_text = Text(f"{similarity_pct:.1f}%", style=style)
                else:
                    similarity_text = Text("N/A", style="dim")
            else:
                similarity_text = Text("N/A", style="dim")

            # Add row to alignment table
            alignment_table.add_row(
                Text(op['type'].upper(), style=operation_style),
                ref_frame,
                ev_frame,
                similarity_text,
                ref_hash,
                ev_hash
            )

        console.print(alignment_table)

        # Show truncation notice if needed
        if len(alignment) > 10:
            console.print(f"[dim]... and {len(alignment) - 10} more operations[/dim]")

        # === STATISTICAL ANALYSIS ===
        # Calculate comprehensive similarity statistics
        total_analyzed_frames = max(
            len(reference_analysis['frame_hashes']),
            len(evidence_analysis['frame_hashes'])
        )

        # Collect similarity scores for all operations
        similarity_scores = []
        substitution_similarities = []

        for op in alignment:
            if op['type'] == 'match':
                similarity_scores.append(100.0)
            elif op['type'] in ['insertion', 'deletion']:
                similarity_scores.append(0.0)
            elif op['type'] == 'substitution':
                hamming_result = comparator.calculate_hamming_distance(op['ref_hash'], op['ev_hash'])
                if hamming_result:
                    sim_pct = hamming_result['similarity_percentage']
                    similarity_scores.append(sim_pct)
                    substitution_similarities.append(sim_pct)
                else:
                    similarity_scores.append(0.0)

        # Calculate statistical metrics
        if similarity_scores:
            avg_similarity = sum(similarity_scores) / len(similarity_scores)
            min_similarity = min(similarity_scores)
            max_similarity = max(similarity_scores)
        else:
            avg_similarity = min_similarity = max_similarity = 0.0

        if substitution_similarities:
            avg_substitution_similarity = sum(substitution_similarities) / len(substitution_similarities)
        else:
            avg_substitution_similarity = 0.0

        # Categorize frames by similarity ranges
        high_similarity = sum(1 for s in similarity_scores if s >= 80)
        medium_similarity = sum(1 for s in similarity_scores if 50 <= s < 80)
        low_similarity = sum(1 for s in similarity_scores if s < 50)

        # === FINAL SUMMARY ===
        # Present comprehensive analysis results
        console.print(f"\n[bold green]📊 Final Summary[/bold green]")
        summary_table = Table(box=box.HEAVY, expand=True)
        summary_table.add_column("Metric", style="bold")
        summary_table.add_column("Value", justify="right")

        # Overall statistics
        summary_table.add_row("Frames Analyzed", str(total_analyzed_frames))
        summary_table.add_row("Overall Average Similarity", f"{avg_similarity:.2f}%")
        summary_table.add_row("Minimum Similarity", f"{min_similarity:.2f}%")
        summary_table.add_row("Maximum Similarity", f"{max_similarity:.2f}%")

        # Substitution-specific statistics
        if substitution_similarities:
            summary_table.add_row("Avg Substitution Similarity", f"{avg_substitution_similarity:.2f}%")

        summary_table.add_row("", "")  # Visual separator

        # Similarity distribution
        summary_table.add_row("High Similarity (≥80%)", f"{high_similarity} frames", style="green")
        summary_table.add_row("Medium Similarity (50-79%)", f"{medium_similarity} frames", style="yellow")
        summary_table.add_row("Low Similarity (<50%)", f"{low_similarity} frames", style="red")

        summary_table.add_row("", "")  # Visual separator

        # Modification summary
        summary_table.add_row("Identical Frames", f"{stats['matches']}/{total_analyzed_frames}")
        summary_table.add_row("Total Modifications",
                              str(stats['substitutions'] + stats['insertions'] + stats['deletions']))

        # Detailed modification breakdown
        if stats['insertions'] > 0:
            summary_table.add_row("Extra Frames Added", str(stats['insertions']), style="red")
        if stats['deletions'] > 0:
            summary_table.add_row("Frames Removed", str(stats['deletions']), style="red")
        if stats['substitutions'] > 0:
            summary_table.add_row("Frames Modified", str(stats['substitutions']), style="yellow")

        console.print(summary_table)

    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)


def main():
    typer.run(analyze)


if __name__ == '__main__':
    main()
