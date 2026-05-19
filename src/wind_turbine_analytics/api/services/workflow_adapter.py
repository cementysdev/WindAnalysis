"""
Workflow adapter to intercept results from existing workflows.

This adapter uses monkey-patching to capture Plotly figures and table data
from the workflow execution without modifying the core business logic.
"""
from typing import Any, Dict, List, Optional, Type, Union
from pathlib import Path
import traceback
import json
import numpy as np

from src.logger_config import get_logger
from src.wind_turbine_analytics.application.workflows.base_workflow import BaseWorkflow
from src.wind_turbine_analytics.application.configuration.config_models import (
    RunTestPipelineConfig,
    ScadaRunnerConfig,
)
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import BaseVisualizer
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.presentation.cli_presenter import CLIPipelinePresenter
from src.wind_turbine_analytics.api.models.responses import (
    AnalyzeResponse,
    ChartData,
    TableData,
)

logger = get_logger(__name__)


def convert_numpy_to_native(obj):
    """
    Recursively convert numpy types to native Python types for JSON serialization.

    Args:
        obj: Object to convert (can be dict, list, numpy array, etc.)

    Returns:
        Converted object with numpy types replaced by native Python types
    """
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.bool_):
        return bool(obj)
    elif isinstance(obj, dict):
        return {key: convert_numpy_to_native(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_to_native(item) for item in obj]
    elif isinstance(obj, tuple):
        return tuple(convert_numpy_to_native(item) for item in obj)
    else:
        return obj


class WorkflowAdapter:
    """
    Adapter to intercept and extract results from workflow executions.

    Uses monkey-patching to capture Plotly figures and table data during
    workflow execution without modifying the core business logic.
    """

    def __init__(self):
        self.captured_charts: List[Dict[str, Any]] = []
        self.captured_tables: List[Dict[str, Any]] = []
        self.metadata: Dict[str, Any] = {}
        self._original_visualizer_generate = None
        self._original_tabler_generate = None

    def run_workflow(
        self,
        config: Union[RunTestPipelineConfig, ScadaRunnerConfig],
        workflow_class: Type[BaseWorkflow],
        session_id: Optional[str] = None,
    ) -> AnalyzeResponse:
        """
        Execute a workflow and capture its results.

        Args:
            config: Workflow configuration (RunTestPipelineConfig or ScadaRunnerConfig)
            workflow_class: Workflow class to instantiate (RunTestWorkflow or ScadaWorkflow)
            session_id: Optional session ID for saving outputs to session directories

        Returns:
            AnalyzeResponse with charts, tables, and metadata

        Raises:
            Exception: If workflow execution fails
        """
        logger.debug(f"Starting workflow execution: {workflow_class.__name__}")
        if session_id:
            logger.debug(f"  Using session: {session_id}")

        # Reset captured data
        self.captured_charts = []
        self.captured_tables = []
        self.metadata = {}

        # Store original methods
        self._original_visualizer_generate = BaseVisualizer.generate
        self._original_tabler_generate = BaseTabler.generate

        # Apply monkey patches
        self._patch_visualizer()
        self._patch_tabler()

        try:
            # Instantiate workflow with CLI presenter
            presenter = CLIPipelinePresenter()
            workflow = workflow_class(config=config, presenter=presenter)

            logger.debug("Running workflow validation and processing...")
            workflow.run()  # Returns None but generates side effects

            # Extract metadata from workflow
            self._extract_metadata(workflow)

            # Save to session if session_id provided
            if session_id:
                self._save_to_session(session_id)

            logger.debug(
                f"Workflow completed: {len(self.captured_charts)} charts, "
                f"{len(self.captured_tables)} tables captured"
            )

            return AnalyzeResponse(
                status="success",
                message=(
                    f"Analyse complétée avec succès. "
                    f"{len(self.captured_charts)} graphiques et "
                    f"{len(self.captured_tables)} tableaux générés."
                ),
                charts=[ChartData(**chart) for chart in self.captured_charts],
                tables=[TableData(**table) for table in self.captured_tables],
                report_path=str(config.output_path) if config.render_template else None,
                metadata=self.metadata,
            )

        except Exception as e:
            logger.error(f"Workflow execution failed: {str(e)}")
            logger.error(traceback.format_exc())

            return AnalyzeResponse(
                status="error",
                message=f"Erreur lors de l'analyse : {str(e)}",
                charts=[],
                tables=[],
                report_path=None,
                metadata={"error_details": traceback.format_exc()},
            )

        finally:
            # Restore original methods
            self._restore_patches()

    def _patch_visualizer(self):
        """Monkey-patch BaseVisualizer.generate() to capture Plotly figures."""
        adapter = self  # Capture self in closure

        def patched_generate(visualizer_instance, result):
            """Patched generate method that captures Plotly figure."""
            try:
                # Create the Plotly figure
                fig = visualizer_instance._create_figure(result)

                # Convert figure to dict and replace numpy arrays with native Python types
                plotly_dict = fig.to_dict()
                plotly_dict_clean = convert_numpy_to_native(plotly_dict)

                # Capture the figure as JSON
                adapter.captured_charts.append({
                    "name": visualizer_instance.chart_name,
                    "plotly_json": plotly_dict_clean,
                })

                logger.debug(f"Captured chart: {visualizer_instance.chart_name}")

            except Exception as e:
                logger.warning(f"Failed to capture chart {visualizer_instance.chart_name}: {e}")

            # Continue with original behavior (save PNG/JSON to disk)
            return adapter._original_visualizer_generate(visualizer_instance, result)

        BaseVisualizer.generate = patched_generate

    def _patch_tabler(self):
        """Monkey-patch BaseTabler.generate() to capture table data."""
        adapter = self  # Capture self in closure

        def patched_generate(tabler_instance, result):
            """Patched generate method that captures table data."""
            # Call original method to get formatted table
            original_result = adapter._original_tabler_generate(tabler_instance, result)

            try:
                # Extract table data from the result
                table_name = tabler_instance.table_name
                if table_name in original_result:
                    rows = original_result[table_name]

                    if rows and len(rows) > 0:
                        # Extract columns from first row
                        columns = list(rows[0].keys())

                        # Convert any numpy types in rows to native Python types
                        rows_clean = convert_numpy_to_native(rows)

                        adapter.captured_tables.append({
                            "name": table_name,
                            "columns": columns,
                            "rows": rows_clean,
                        })

                        logger.debug(f"Captured table: {table_name} ({len(rows)} rows)")

            except Exception as e:
                logger.warning(f"Failed to capture table {tabler_instance.table_name}: {e}")

            return original_result

        BaseTabler.generate = patched_generate

    def _restore_patches(self):
        """Restore original methods after workflow execution."""
        if self._original_visualizer_generate:
            BaseVisualizer.generate = self._original_visualizer_generate
            logger.debug("Restored BaseVisualizer.generate()")

        if self._original_tabler_generate:
            BaseTabler.generate = self._original_tabler_generate
            logger.debug("Restored BaseTabler.generate()")

    def _extract_metadata(self, workflow: BaseWorkflow):
        """
        Extract metadata from workflow after execution.

        Args:
            workflow: Executed workflow instance with populated attributes
        """
        try:
            # Extract general information
            if hasattr(workflow, "general_information") and workflow.general_information:
                self.metadata["park_name"] = workflow.general_information.park_name
                self.metadata["client_name"] = workflow.general_information.client_name
                self.metadata["model_wtg"] = workflow.general_information.model_wtg
                self.metadata["nominal_power"] = workflow.general_information.nominal_power

            # Extract turbine list
            if hasattr(workflow, "turbine_sources") and workflow.turbine_sources and workflow.turbine_sources.farm:
                turbine_ids = list(workflow.turbine_sources.farm.keys())
                self.metadata["turbines"] = turbine_ids

                # Extract test dates from first turbine (assuming same period for all)
                if turbine_ids:
                    first_turbine = workflow.turbine_sources.farm[turbine_ids[0]]
                    if first_turbine.test_start:
                        self.metadata["test_start"] = str(first_turbine.test_start)
                    if first_turbine.test_end:
                        self.metadata["test_end"] = str(first_turbine.test_end)

            # Extract validation criteria
            if (hasattr(workflow, "validation_criteria") and
                workflow.validation_criteria and
                workflow.validation_criteria.validation_criterion):
                criteria = {}
                for key, criterion in workflow.validation_criteria.validation_criterion.items():
                    criteria[key] = {
                        "value": criterion.value,
                        "unit": criterion.unit,
                        "specification": criterion.specification,
                    }
                self.metadata["criteria"] = criteria

            logger.debug(f"Extracted metadata: {list(self.metadata.keys())}")

        except Exception as e:
            logger.warning(f"Failed to extract some metadata: {e}")

    def _save_to_session(self, session_id: str):
        """
        Save captured charts and tables to session directories.

        Args:
            session_id: Session identifier
        """
        from src.wind_turbine_analytics.api.services.session_manager import SessionManager

        logger.info(f"Starting to save session results for {session_id}")
        logger.debug(f"  Charts to save: {len(self.captured_charts)}")
        logger.debug(f"  Tables to save: {len(self.captured_tables)}")

        try:
            session_manager = SessionManager()

            # Save charts to session/charts/
            charts_path = session_manager.get_charts_path(session_id)
            charts_saved = 0
            for i, chart in enumerate(self.captured_charts):
                try:
                    chart_name = chart.get('name', f'chart_{i}')
                    chart_file = charts_path / f"{chart_name}.json"

                    with open(chart_file, 'w', encoding='utf-8') as f:
                        json.dump(chart['plotly_json'], f, indent=2, ensure_ascii=False)

                    charts_saved += 1
                    logger.debug(f"  Saved chart: {chart_name}")

                except Exception as e:
                    logger.warning(f"  Failed to save chart {chart.get('name', i)}: {e}")

            logger.info(f"Saved {charts_saved}/{len(self.captured_charts)} charts to {charts_path}")

            # Save tables to session/tables/
            tables_path = session_manager.get_tables_path(session_id)
            tables_saved = 0
            for i, table in enumerate(self.captured_tables):
                try:
                    table_name = table.get('name', f'table_{i}')
                    table_file = tables_path / f"{table_name}.json"

                    with open(table_file, 'w', encoding='utf-8') as f:
                        json.dump(table, f, indent=2, ensure_ascii=False)

                    tables_saved += 1
                    logger.debug(f"  Saved table: {table_name}")

                except Exception as e:
                    logger.warning(f"  Failed to save table {table.get('name', i)}: {e}")

            logger.info(f"Saved {tables_saved}/{len(self.captured_tables)} tables to {tables_path}")

            # Update session metadata
            session_metadata = {
                "status": "completed",
                "charts_count": len(self.captured_charts),
                "tables_count": len(self.captured_tables),
                **self.metadata
            }
            session_manager.save_session_metadata(session_id, session_metadata)

            logger.info(f"Session {session_id} metadata updated successfully")

        except Exception as e:
            logger.error(f"Failed to save session results: {e}")
            logger.error(traceback.format_exc())
