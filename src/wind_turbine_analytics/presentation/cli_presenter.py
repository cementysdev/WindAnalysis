"""CLI Presenter with modern Rich interface."""

from typing import Optional, List
from .console_presenter import ConsolePipelinePresenter
from ..cli import (
    console,
    create_header,
    create_footer,
    PipelineProgress,
    StepStatus,
)


class CLIPipelinePresenter(ConsolePipelinePresenter):
    """
    Presenter with modern CLI interface using Rich.

    Features:
    - ASCII art header with gradient
    - Live progress bars (global + per-step)
    - Substep tracking with icons
    - Colored status indicators
    - Summary footer with statistics

    Backward compatible with ConsolePipelinePresenter.
    Auto-detects terminal capability and falls back to simple mode.
    """

    def __init__(self):
        """Initialize CLI presenter."""
        super().__init__()
        self.progress: Optional[PipelineProgress] = None
        self.use_cli = console.is_terminal  # Auto-detect Rich support
        self.workflow_name = ""
        self.steps: List[str] = []

    def start_pipeline(
        self, workflow_name: str, steps: List[str], subtitle: str
    ):
        """
        Start pipeline with CLI interface.

        Args:
            workflow_name: Name of the workflow
            steps: List of step names
            subtitle: Subtitle for header
        """
        self.workflow_name = workflow_name
        self.steps = steps

        if self.use_cli:
            # Clear screen and show header
            console.clear()
            header = create_header(title="WTA", subtitle=subtitle)
            console.print(header)
            console.print()

            # Start progress tracking
            self.progress = PipelineProgress(steps, workflow_name)
            self.progress.__enter__()

    def show_step_start(
        self, step_name: str, substeps: Optional[List[str]] = None
    ):
        """
        Start a pipeline step.

        Args:
            step_name: Name of the step
            substeps: Optional list of substep names
        """
        if self.progress:
            self.progress.start_step(step_name, substeps)

    def show_substep_update(self, substep_name: str):
        """
        Update to next substep.

        Args:
            substep_name: Name of the substep
        """
        if self.progress:
            self.progress.update_substep(substep_name)

    def show_step_complete(
        self, status: StepStatus = StepStatus.SUCCESS, message: Optional[str] = None
    ):
        """
        Complete current step.

        Args:
            status: Final status of the step
            message: Optional error/warning message
        """
        if self.progress:
            self.progress.complete_step(status, message)

    def skip_step(self, step_name: str):
        """
        Skip a step.

        Args:
            step_name: Name of the step to skip
        """
        if self.progress:
            self.progress.skip_step(step_name)

    def end_pipeline(self):
        """End pipeline and show summary footer."""
        if self.progress:
            # Get statistics
            stats = self.progress.stats
            elapsed = self.progress.total_elapsed_time

            # Exit progress tracking
            self.progress.__exit__(None, None, None)

            # Show footer
            console.print()
            footer = create_footer(
                elapsed_time=elapsed,
                total_steps=stats["total"],
                completed=stats["completed"],
                failed=stats["failed"],
                warnings=stats["warnings"],
            )
            console.print(footer)

            # Reset
            self.progress = None
