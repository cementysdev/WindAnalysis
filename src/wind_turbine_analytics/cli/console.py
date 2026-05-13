"""Console configuration and header/footer utilities."""

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.table import Table
from datetime import datetime
from pyfiglet import Figlet
from typing import Optional

# Global console instance
console = Console()


def create_header(title: str = "Wind Turbine Analytics", subtitle: Optional[str] = None) -> Panel:
    """
    Create an ASCII art header with pyfiglet.

    Args:
        title: Main title text
        subtitle: Optional subtitle

    Returns:
        Rich Panel with header
    """
    # Generate ASCII art
    fig = Figlet(font="ansi_shadow")
    ascii_art = fig.renderText(title)

    # Create gradient effect (blue to cyan)
    text = Text()
    lines = ascii_art.split('\n')

    for i, line in enumerate(lines):
        if not line.strip():
            continue
        # Gradient from blue to cyan
        ratio = i / max(len(lines) - 1, 1)
        r = int(0 + (0 * ratio))
        g = int(100 + (155 * ratio))
        b = int(200 + (55 * ratio))
        color = f"#{r:02x}{g:02x}{b:02x}"
        text.append(line + "\n", style=color)

    # Add subtitle if provided
    if subtitle:
        text.append("\n")
        text.append(subtitle, style="bold cyan")

    # Add timestamp
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    text.append(f"\n\n{timestamp}", style="dim")

    return Panel(
        Align.center(text),
        border_style="blue",
        padding=(1, 2),
    )


def create_footer(
    elapsed_time: float,
    total_steps: int,
    completed: int,
    failed: int,
    warnings: int
) -> Panel:
    """
    Create a summary footer with statistics.

    Args:
        elapsed_time: Total elapsed time in seconds
        total_steps: Total number of steps
        completed: Number of completed steps
        failed: Number of failed steps
        warnings: Number of warnings

    Returns:
        Rich Panel with footer
    """
    # Create statistics table
    table = Table.grid(padding=(0, 2))
    table.add_column(style="cyan", justify="right")
    table.add_column(style="white")

    # Format elapsed time
    hours, remainder = divmod(int(elapsed_time), 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        time_str = f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        time_str = f"{minutes}m {seconds}s"
    else:
        time_str = f"{seconds}s"

    table.add_row("Duration:", time_str)
    table.add_row("Total Steps:", str(total_steps))
    table.add_row("Completed:", f"[green]{completed}[/green]")

    if failed > 0:
        table.add_row("Failed:", f"[red]{failed}[/red]")

    if warnings > 0:
        table.add_row("Warnings:", f"[yellow]{warnings}[/yellow]")

    # Completion rate
    completion_rate = (completed / total_steps * 100) if total_steps > 0 else 0
    table.add_row("Completion:", f"{completion_rate:.1f}%")

    # Status message
    if failed > 0:
        status = "[red]✗ Pipeline completed with errors[/red]"
    elif warnings > 0:
        status = "[yellow]⚠ Pipeline completed with warnings[/yellow]"
    else:
        status = "[green]✓ Pipeline completed successfully[/green]"

    # Combine table and status
    content = Table.grid()
    content.add_row(table)
    content.add_row("")
    content.add_row(Align.center(status))

    return Panel(
        Align.center(content),
        title="[bold]Summary[/bold]",
        border_style="green" if failed == 0 else ("red" if failed > 0 else "yellow"),
        padding=(1, 2),
    )
