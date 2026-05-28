"""RunTest application workflow."""

from __future__ import annotations

from typing import Any
from pathlib import Path
from src.wind_turbine_analytics.application.configuration.config_models import (
    RunTestPipelineConfig,
)
from src.wind_turbine_analytics.application.workflows.base_workflow import BaseWorkflow
from src.logger_config import get_logger
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders import (
    PowerCurveChartVisualizer,
    WindRoseChartVisualizer,
    WindHistogramChartVisualizer,
    HeatmapChartVisualizer,
    CutInCutoutTimelineVisualizer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics import (
    ConsecutiveHoursAnalyzer,
    TestCutInCutOutAnalyzer,
    NominalPowerAnalyzer,
    AutonomousOperationAnalyzer,
    TestAvailabilityAnalyzer,
)
from src.wind_turbine_analytics.cli import StepStatus

logger = get_logger(__name__)

# Imports des tablers pour génération de rapports Word
from src.wind_turbine_analytics.data_processing.tabler.tables.runtest import (
    ConsecutiveHoursTabler,
    CutInCutOutTabler,
    NominalPowerValuesTabler,
    NominalPowerDurationTabler,
    AutonomousOperationTabler,
    AvailabilityTabler,
    RunTestSummaryTabler,
    CsvFilesTabler,
)
from src.wind_turbine_analytics.presentation.word_generation import RunTestWordPresenter


class RunTestWorkflow(BaseWorkflow):
    """Coordinates data loading, criteria evaluation, charts, and report rendering."""

    def __init__(
        self,
        config: RunTestPipelineConfig,
        presenter,
        output_dir: Path = None
    ) -> None:
        super().__init__(config, presenter)
        # Stocker output_dir pour les visualiseurs
        self.output_dir = output_dir if output_dir else Path("output/charts")

    def run(self) -> None:
        # Define pipeline steps
        steps = [
            "Load Configuration",
            "Criterion 1: Consecutive Hours",
            "Criterion 2: Cut-In/Cut-Out",
            "Criterion 3: Nominal Power",
            "Criterion 4: Autonomous Operation",
            "Criterion 5: Availability",
            "Generate Report",
        ]

        # Start pipeline with CLI
        self._presenter.start_pipeline(
            "RunTest Analysis",
            steps,
            "Wind Turbine Analytics - RunTest Pipeline"
        )

        # Step 1: Load Configuration
        self._presenter.show_step_start("Load Configuration")
        try:
            self.validation_step()
            self._presenter.show_step_complete(StepStatus.SUCCESS)
        except Exception as e:
            self._presenter.show_step_complete(StepStatus.ERROR, str(e))
            raise

        # Steps 2-7: Process criteria
        self.process_step()

        # End pipeline
        self._presenter.end_pipeline()
        return

    def _execute_step(self, step_name, analyzer, visualizers, tablers):
        """
        Execute a criterion analysis with CLI progress tracking.

        Args:
            step_name: Name of the criterion step
            analyzer: Analyzer instance
            visualizers: List of visualizer instances or None
            tablers: List of tabler instances or single tabler or None

        Returns:
            AnalysisResult from the step
        """
        # Start step with substeps
        substeps = ["Analyzing"]
        if visualizers:
            substeps.append("Visualizing")
        if tablers:
            substeps.append("Generating Tables")

        self._presenter.show_step_start(step_name, substeps)

        try:
            # Phase 1: Analyzing
            self._presenter.show_substep_update("Analyzing")
            result = analyzer.analyze(self.turbine_sources, self.validation_criteria)

            # Phase 2: Visualizing
            if result.requires_visuals and visualizers:
                self._presenter.show_substep_update("Visualizing")
                for visualizer in visualizers:
                    visualizer.generate(result)

            # Phase 3: Generating Tables
            if tablers:
                self._presenter.show_substep_update("Generating Tables")
                tabler_list = tablers if isinstance(tablers, list) else [tablers]
                for tabler in tabler_list:
                    table_data = tabler.generate(result)
                    if result.metadata is None:
                        result.metadata = {}
                    if "table_data" not in result.metadata:
                        result.metadata["table_data"] = {}
                    result.metadata["table_data"].update(table_data)

            self._presenter.show_step_complete(StepStatus.SUCCESS)
            return result

        except Exception as e:
            self._presenter.show_step_complete(StepStatus.ERROR, str(e))
            raise

    def process_step(self) -> None:
        """Traite toutes les analyses et génère le rapport Word si activé."""
        # Créer un summary_tabler pour agréger tous les résultats
        summary_tabler = RunTestSummaryTabler()

        # Stocker tous les résultats pour génération du rapport
        all_results = {}

        # Criterion 1: Minimum of 120 consecutive hours
        consecutive_hours_results = self._execute_step(
            "Criterion 1: Consecutive Hours",
            ConsecutiveHoursAnalyzer(),
            None,
            ConsecutiveHoursTabler(),
        )
        all_results["consecutive_hours"] = consecutive_hours_results
        summary_tabler.add_analysis_result(
            "consecutive_hours", consecutive_hours_results
        )

        # Criterion 2: 72 hours within cut-in to cut-out wind speed range
        test_cut_in_cut_out_results = self._execute_step(
            "Criterion 2: Cut-In/Cut-Out",
            TestCutInCutOutAnalyzer(),
            [CutInCutoutTimelineVisualizer(output_dir=self.output_dir)],
            CutInCutOutTabler(),
        )
        all_results["cut_in_cut_out"] = test_cut_in_cut_out_results
        summary_tabler.add_analysis_result(
            "cut_in_cut_out", test_cut_in_cut_out_results
        )

        # Criterion 3: 3 hours at or above 98% of nominal power
        nominal_power_result = self._execute_step(
            "Criterion 3: Nominal Power",
            NominalPowerAnalyzer(),
            [
                PowerCurveChartVisualizer(output_dir=self.output_dir),
                WindRoseChartVisualizer(output_dir=self.output_dir),
                WindHistogramChartVisualizer(output_dir=self.output_dir),
            ],
            [NominalPowerValuesTabler(), NominalPowerDurationTabler()],
        )
        all_results["nominal_power"] = nominal_power_result
        summary_tabler.add_analysis_result("nominal_power", nominal_power_result)

        # Criterion 4: Local acknowledgements / restarts (<=3)
        autonomous_operation_result = self._execute_step(
            "Criterion 4: Autonomous Operation",
            AutonomousOperationAnalyzer(),
            None,
            AutonomousOperationTabler(),
        )
        all_results["autonomous_operation"] = autonomous_operation_result
        summary_tabler.add_analysis_result(
            "autonomous_operation", autonomous_operation_result
        )

        # Criterion 5: Availability (>=92%)
        availability_result = self._execute_step(
            "Criterion 5: Availability",
            TestAvailabilityAnalyzer(),
            [HeatmapChartVisualizer(output_dir=self.output_dir)],
            AvailabilityTabler(),
        )
        all_results["availability"] = availability_result
        summary_tabler.add_analysis_result("availability", availability_result)

        # Generate Report
        self._presenter.show_step_start("Generate Report")
        try:
            self._render_report(all_results, summary_tabler)
            self._presenter.show_step_complete(StepStatus.SUCCESS)
        except Exception as e:
            self._presenter.show_step_complete(StepStatus.ERROR, str(e))
            raise

    def _render_report(
        self, all_results: dict, summary_tabler: RunTestSummaryTabler
    ) -> None:
        """
        Génère le rapport Word si activé dans la config.

        Args:
            all_results: Dict des résultats d'analyse par critère
            summary_tabler: Tableau récapitulatif avec tous les résultats accumulés
        """
        if not self._config.render_template:
            logger.debug("Template rendering disabled in config (render_template=False)")
            return

        logger.debug("Rendering Word report...")

        try:
            # Agréger toutes les table_data des résultats
            context = {}
            for analysis_name, result in all_results.items():
                if result.metadata and "table_data" in result.metadata:
                    context.update(result.metadata["table_data"])

            # Générer le tableau récapitulatif et l'ajouter au contexte
            summary_data = summary_tabler.generate()
            context.update(summary_data)

            # Générer le tableau des fichiers CSV utilisés
            csv_files_tabler = CsvFilesTabler()
            csv_files_data = csv_files_tabler.generate_from_turbine_farm(
                self.turbine_sources
            )
            logger.debug(
                f"CSV files table generated with {len(csv_files_data.get('csv_files_table', []))} rows"
            )
            context.update(csv_files_data)

            # Collecter les chemins des images de visualisation
            chart_paths = {}
            for analysis_name, result in all_results.items():
                if result.metadata and "charts" in result.metadata:
                    for chart_name, chart_info in result.metadata["charts"].items():
                        # Vérifier que png_path existe ET n'est pas None
                        png_path = chart_info.get("png_path")
                        if png_path is not None:
                            chart_paths[chart_name] = png_path
                            logger.debug(f"  ✅ Chart collected: {chart_name} -> {png_path}")
                        else:
                            logger.warning(f"  ⚠️ Chart {chart_name} has no PNG (Kaleido failed)")

            # Log diagnostic PNG disponibilité
            png_available = sum(
                1 for path in chart_paths.values() if path is not None
            )
            total_charts = len(chart_paths)
            logger.info(
                f"📊 Charts collectés : {png_available}/{total_charts} "
                f"avec PNG disponible"
            )

            if png_available < total_charts:
                logger.warning(
                    f"⚠️ {total_charts - png_available} PNG manquants "
                    f"(Kaleido non disponible). "
                    f"Graphiques visibles sur interface web uniquement."
                )

            # Ajouter les chemins d'images au contexte
            context["chart_paths"] = chart_paths

            # Préparer les métadonnées à partir de turbine_sources
            turbine_list = list(self.turbine_sources.farm.keys())

            # Récupérer test_start et test_end de la première turbine
            first_turbine_config = None
            if turbine_list:
                first_turbine_config = self.turbine_sources.farm[turbine_list[0]]

            # Extraire les valeurs des critères depuis validation_criteria
            criteria = self.validation_criteria.validation_criterion

            # Créer la liste des fichiers CSV utilisés
            csv_files_list = self._get_csv_files_list()

            metadata = {
                "test_start": (
                    first_turbine_config.test_start if first_turbine_config else "N/A"
                ),
                "test_end": (
                    first_turbine_config.test_end if first_turbine_config else "N/A"
                ),
                "turbines": turbine_list,
                # Informations sur le parc (depuis general_information)
                "park_name": (
                    self.general_information.park_name
                    if self.general_information
                    else "N/A"
                ),
                "model_wtg": (
                    self.general_information.model_wtg
                    if self.general_information
                    else "N/A"
                ),
                "nominal_power": (
                    self.general_information.nominal_power
                    if self.general_information
                    else "N/A"
                ),
                # Liste des fichiers CSV
                "csv_files": csv_files_list,
                # Valeurs des critères de validation
                "consecutive_hours_h": (
                    criteria.get("consecutive_hours").value
                    if "consecutive_hours" in criteria
                    else 120
                ),
                "cut_in_to_cut_out_h": (
                    criteria.get("cut_in_to_cut_out").value
                    if "cut_in_to_cut_out" in criteria
                    else 72
                ),
                # Cut-in/cut-out vitesses min/max depuis specification
                "cut_in_v_min": (
                    criteria.get("cut_in_to_cut_out").specification[0]
                    if "cut_in_to_cut_out" in criteria
                    and criteria.get("cut_in_to_cut_out").specification
                    else 3
                ),
                "cut_in_v_max": (
                    criteria.get("cut_in_to_cut_out").specification[1]
                    if "cut_in_to_cut_out" in criteria
                    and criteria.get("cut_in_to_cut_out").specification
                    else 25
                ),
                "nominal_power_h": (
                    criteria.get("nominal_power_hours").value
                    if "nominal_power_hours" in criteria
                    else 3
                ),
                "nominal_power_pct": (
                    criteria.get("nominal_power_hours").specification
                    if "nominal_power_hours" in criteria
                    else 97
                ),
                "local_restarts_max": (
                    criteria.get("local_restarts").value
                    if "local_restarts" in criteria
                    else 3
                ),
                "availability_min_pct": (
                    criteria.get("availability").value
                    if "availability" in criteria
                    else 92
                ),
            }

            # Rendre le rapport Word avec RunTestWordPresenter
            presenter = RunTestWordPresenter(
                template_path=self._config.template_path,
                output_path=self._config.output_path,
            )
            presenter.render_report(context, metadata=metadata)

        except FileNotFoundError as e:
            logger.error(f"Template file not found: {e}")
            logger.debug(
                "Please create a Word template with docxtpl tags at: "
                f"{self._config.template_path}"
            )
        except Exception as e:
            logger.error(f"Failed to render Word report: {e}")

    def _get_csv_files_list(self) -> list:
        """
        Récupère la liste des fichiers CSV utilisés pour l'analyse.

        Returns:
            Liste de dictionnaires avec les informations des fichiers
            Format: [{'turbine': 'E1', 'type': 'Operation', 'filename': 'xxx.csv'}, ...]
        """
        from pathlib import Path

        files_list = []

        for turbine_id, turbine_config in self.turbine_sources.farm.items():
            # Fichier de données d'opération
            if (
                turbine_config.general_information
                and turbine_config.general_information.path_operation_data
            ):
                operation_path = Path(
                    turbine_config.general_information.path_operation_data
                )
                files_list.append(
                    {
                        "turbine": turbine_id,
                        "type": "Données SCADA",
                        "filename": operation_path.name,
                    }
                )

            # Fichier de logs
            if (
                turbine_config.general_information
                and turbine_config.general_information.path_log_data
            ):
                log_path = Path(turbine_config.general_information.path_log_data)
                files_list.append(
                    {
                        "turbine": turbine_id,
                        "type": "Logs alarmes",
                        "filename": log_path.name,
                    }
                )

        return files_list


def run_runtest_pipeline(config: RunTestPipelineConfig, presenter) -> Any:
    return RunTestWorkflow(config=config, presenter=presenter).run()
