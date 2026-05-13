"""Pipeline progress tracking with rich progress bars."""

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
    TimeElapsedColumn,
)
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.console import Group
from .console import console


class StepStatus(Enum):
    """Status of a pipeline step."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SKIPPED = "skipped"


@dataclass
class PipelineStep:
    """Represents a single step in the pipeline."""
    name: str
    status: StepStatus = StepStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: Optional[str] = None
    substeps: List["PipelineStep"] = field(default_factory=list)
    current_substep: int = 0

    @property
    def icon(self) -> str:
        """Get icon for current status."""
        return {
            StepStatus.PENDING: "○",
            StepStatus.RUNNING: "⟳",
            StepStatus.SUCCESS: "✓",
            StepStatus.WARNING: "⚠",
            StepStatus.ERROR: "✗",
            StepStatus.SKIPPED: "→",
        }[self.status]

    @property
    def color(self) -> str:
        """Get color for current status."""
        return {
            StepStatus.PENDING: "dim",
            StepStatus.RUNNING: "cyan",
            StepStatus.SUCCESS: "green",
            StepStatus.WARNING: "yellow",
            StepStatus.ERROR: "red",
            StepStatus.SKIPPED: "dim",
        }[self.status]

    @property
    def elapsed_time(self) -> Optional[float]:
        """Get elapsed time in seconds."""
        if self.start_time is None:
            return None
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()


class PipelineProgress:
    """
    Manages pipeline progress with live display.

    Features:
    - Global progress bar
    - Per-step status tracking
    - Substep support
    - Live updates
    - Sidebar with step history
    """

    def __init__(self, steps: List[str], title: str = "Pipeline Progress"):
        """
        Initialize pipeline progress tracker.

        Args:
            steps: List of step names
            title: Pipeline title
        """
        self.title = title
        self.steps = [PipelineStep(name=name) for name in steps]
        self.current_step_idx = 0
        self.start_time = datetime.now()

        # Rich progress bars
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            expand=True,
        )

        self.global_task = self.progress.add_task(
            f"[cyan]{title}", total=len(steps)
        )
        self.current_task = None

        # Layout
        self.layout = Layout()
        self.layout.split_column(
            Layout(name="progress", size=3),
            Layout(name="steps", ratio=1),
        )

        self.live = None

    def __enter__(self):
        """Start live display."""
        self.live = Live(
            self._generate_display(),
            console=console,
            refresh_per_second=4,
            transient=False,
        )
        self.live.__enter__()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop live display."""
        if self.live:
            self.live.__exit__(exc_type, exc_val, exc_tb)

    def _generate_display(self) -> Group:
        """Generate the current display."""
        # Progress bars
        progress_panel = Panel(
            self.progress,
            title=f"[bold]{self.title}[/bold]",
            border_style="blue",
            padding=(0, 1),
        )

        # Steps table
        steps_table = Table.grid(padding=(0, 2))
        steps_table.add_column(style="white", width=3)
        steps_table.add_column(style="white")
        steps_table.add_column(style="dim", justify="right")

        for i, step in enumerate(self.steps):
            # Icon and status
            icon = step.icon
            name = step.name

            # Elapsed time
            time_str = ""
            if step.elapsed_time is not None:
                elapsed = step.elapsed_time
                if elapsed < 60:
                    time_str = f"{elapsed:.1f}s"
                else:
                    minutes = int(elapsed // 60)
                    seconds = int(elapsed % 60)
                    time_str = f"{minutes}m {seconds}s"

            # Highlight current step
            if i == self.current_step_idx and step.status == StepStatus.RUNNING:
                name = f"[bold {step.color}]{name}[/bold {step.color}]"
                icon = f"[bold {step.color}]{icon}[/bold {step.color}]"
            else:
                name = f"[{step.color}]{name}[/{step.color}]"
                icon = f"[{step.color}]{icon}[/{step.color}]"

            steps_table.add_row(icon, name, time_str)

            # Show substeps if running
            if i == self.current_step_idx and step.substeps:
                for j, substep in enumerate(step.substeps):
                    if j > step.current_substep:
                        break
                    sub_icon = substep.icon
                    sub_name = substep.name
                    steps_table.add_row(
                        "",
                        f"  [{substep.color}]{sub_icon} {sub_name}[/{substep.color}]",
                        "",
                    )

        steps_panel = Panel(
            steps_table,
            title="[bold]Pipeline Steps[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )

        return Group(progress_panel, steps_panel)

    def _update_display(self):
        """Update the live display."""
        if self.live:
            self.live.update(self._generate_display())

    def start_step(self, step_name: str, substeps: Optional[List[str]] = None):
        """
        Start a pipeline step.

        Args:
            step_name: Name of the step
            substeps: Optional list of substep names
        """
        # Find step
        step = next((s for s in self.steps if s.name == step_name), None)
        if not step:
            return

        self.current_step_idx = self.steps.index(step)

        # Update step
        step.status = StepStatus.RUNNING
        step.start_time = datetime.now()

        # Add substeps
        if substeps:
            step.substeps = [PipelineStep(name=name) for name in substeps]

        # Create task for this step
        if self.current_task is not None:
            self.progress.remove_task(self.current_task)

        self.current_task = self.progress.add_task(
            f"[cyan]{step_name}", total=len(substeps) if substeps else 1
        )

        self._update_display()

    def update_substep(self, substep_name: str):
        """
        Update to next substep.

        Args:
            substep_name: Name of the substep to activate
        """
        step = self.steps[self.current_step_idx]

        # Find substep
        substep = next((s for s in step.substeps if s.name == substep_name), None)
        if not substep:
            return

        # Mark previous substeps as success
        for i in range(step.current_substep, step.substeps.index(substep)):
            if step.substeps[i].status == StepStatus.RUNNING:
                step.substeps[i].status = StepStatus.SUCCESS
                step.substeps[i].end_time = datetime.now()

        # Start new substep
        step.current_substep = step.substeps.index(substep)
        substep.status = StepStatus.RUNNING
        substep.start_time = datetime.now()

        # Update progress
        self.progress.update(self.current_task, advance=1)
        self._update_display()

    def complete_step(self, status: StepStatus = StepStatus.SUCCESS, message: Optional[str] = None):
        """
        Complete current step.

        Args:
            status: Final status of the step
            message: Optional error message
        """
        step = self.steps[self.current_step_idx]
        step.status = status
        step.end_time = datetime.now()
        step.error_message = message

        # Mark all substeps as complete
        for substep in step.substeps:
            if substep.status == StepStatus.RUNNING:
                substep.status = status
                substep.end_time = datetime.now()

        # Update global progress
        self.progress.update(self.global_task, advance=1)

        # Complete current task
        if self.current_task is not None:
            try:
                task = next(
                    (t for t in self.progress.tasks if t.id == self.current_task),
                    None
                )
                if task:
                    self.progress.update(
                        self.current_task,
                        completed=task.total,
                    )
            except Exception:
                pass  # Ignore errors during task completion

        self._update_display()

    def skip_step(self, step_name: str):
        """
        Skip a step.

        Args:
            step_name: Name of the step to skip
        """
        step = next((s for s in self.steps if s.name == step_name), None)
        if not step:
            return

        step.status = StepStatus.SKIPPED
        self.progress.update(self.global_task, advance=1)
        self._update_display()

    @property
    def total_elapsed_time(self) -> float:
        """Get total elapsed time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def stats(self) -> Dict[str, int]:
        """Get pipeline statistics."""
        return {
            "total": len(self.steps),
            "completed": len([s for s in self.steps if s.status == StepStatus.SUCCESS]),
            "failed": len([s for s in self.steps if s.status == StepStatus.ERROR]),
            "warnings": len([s for s in self.steps if s.status == StepStatus.WARNING]),
            "skipped": len([s for s in self.steps if s.status == StepStatus.SKIPPED]),
        }
