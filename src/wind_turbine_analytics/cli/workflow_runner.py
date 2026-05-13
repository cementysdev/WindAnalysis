"""CLI wrapper for running workflows with modern UI."""

from typing import Optional, Callable
from pathlib import Path
import traceback
from .console import console, create_header, create_footer
from .progress import PipelineProgress, StepStatus
from .logger import CLILogger, setup_cli_logging


class WorkflowRunner:
    """
    Wraps workflow execution with modern CLI interface.

    Provides:
    - Header/footer display
    - Progress tracking
    - Error handling
    - Logging integration
    """

    def __init__(
        self,
        workflow_name: str,
        steps: list[str],
        subtitle: Optional[str] = None
    ):
        """
        Initialize workflow runner.

        Args:
            workflow_name: Name of the workflow
            steps: List of step names
            subtitle: Optional subtitle for header
        """
        self.workflow_name = workflow_name
        self.steps = steps
        self.subtitle = subtitle or f"{workflow_name} Pipeline"

        self.cli_logger = CLILogger(console)
        setup_cli_logging(self.cli_logger)

        self.progress: Optional[PipelineProgress] = None

    def run(self, workflow_func: Callable, *args, **kwargs):
        """
        Run a workflow function with CLI interface.

        Args:
            workflow_func: Function to execute
            *args: Positional arguments for workflow
            **kwargs: Keyword arguments for workflow

        Returns:
            Result from workflow function
        """
        # Clear screen and show header
        console.clear()
        header = create_header(
            title="WTA",
            subtitle=self.subtitle
        )
        console.print(header)
        console.print()

        result = None
        error_occurred = False

        try:
            # Start progress tracking
            with PipelineProgress(self.steps, title=self.workflow_name) as progress:
                self.progress = progress

                # Execute workflow
                result = workflow_func(self, *args, **kwargs)

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠ Pipeline interrupted by user[/yellow]")
            error_occurred = True

        except Exception as e:
            console.print(f"\n[red]✗ Pipeline failed: {str(e)}[/red]")
            if console.is_terminal:
                console.print("\n[dim]Traceback:[/dim]")
                console.print_exception(show_locals=False)
            error_occurred = True

        finally:
            # Show footer
            if self.progress:
                stats = self.progress.stats
                elapsed = self.progress.total_elapsed_time

                console.print()
                footer = create_footer(
                    elapsed_time=elapsed,
                    total_steps=stats["total"],
                    completed=stats["completed"],
                    failed=stats["failed"] + (1 if error_occurred else 0),
                    warnings=stats["warnings"],
                )
                console.print(footer)

        return result

    def start_step(self, step_name: str, substeps: Optional[list[str]] = None):
        """Start a pipeline step."""
        if self.progress:
            self.progress.start_step(step_name, substeps)

    def update_substep(self, substep_name: str):
        """Update to next substep."""
        if self.progress:
            self.progress.update_substep(substep_name)

    def complete_step(
        self,
        status: StepStatus = StepStatus.SUCCESS,
        message: Optional[str] = None
    ):
        """Complete current step."""
        if self.progress:
            self.progress.complete_step(status, message)

    def skip_step(self, step_name: str):
        """Skip a step."""
        if self.progress:
            self.progress.skip_step(step_name)

    def log_info(self, message: str):
        """Log info message."""
        self.cli_logger.info(message)

    def log_success(self, message: str):
        """Log success message."""
        self.cli_logger.success(message)

    def log_warning(self, message: str):
        """Log warning message."""
        self.cli_logger.warning(message)

    def log_error(self, message: str, exc: Optional[Exception] = None):
        """Log error message."""
        self.cli_logger.error(message, exc)
