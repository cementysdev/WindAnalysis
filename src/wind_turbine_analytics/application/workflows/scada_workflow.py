"""SCADA application workflow."""

from __future__ import annotations


import pandas as pd
from typing import Dict, Any
from src.wind_turbine_analytics.application.configuration.config_models import (
    ScadaRunnerConfig,
)
from src.wind_turbine_analytics.application.workflows.base_workflow import BaseWorkflow
from src.wind_turbine_analytics.data_processing.data_processing import (
    DataProcessingStep,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics import (
    EbACutInCutOutAnalyzer,
    EbaManufacturerAnalyzer,
    DataAvailabilityAnalyzer,
    CodeErrorAnalyzer,
    NormativeYieldAnalyzer,
    PerformanceLevelAnalyzer,
    PitchAnalyzer,
    TipSpeedRatioAnalyzer,
    WindDirectionCalibrationAnalyzer,
)
from src.wind_turbine_analytics.data_processing.tabler.tables.scada import (
    EbaCutInCutOutTabler,
    EbaManufacturerTabler,
    EbaLossTabler,
    ScadaSummaryTabler,
    ErrorCodeParetoFrequencyTabler,
    ErrorCodeParetoDurationTabler,
    WindDirectionCalibrationTabler,
    NormativeYieldTabler,
    TipSpeedRatioTabler,
    PitchTabler,
    DataAvailabilityTabler,
    PerformanceLevelTabler,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders import (
    DataAvailabilityVisualizer,
    EbaCutInCutOutVisualizer,
    EbaManufacturerVisualizer,
    EbaLossVisualizer,
    PerformanceLevelVisualizer,
    PowerCurveChartVisualizer,
    PowerRoseChartVisualizer,
    RPMVisualizer,
    TopErrorCodeFrequencyVisualizer,
    TreemapErrorCodeVisualizer,
    WindDirectionCalibrationVisualizer,
    WindRoseChartVisualizer,
    PitchVisualizer,
)
from src.wind_turbine_analytics.data_processing.tabler.tables.runtest import (
    CsvFilesTabler,
)
from src.wind_turbine_analytics.presentation.word_generation import ScadaWordPresenter
from src.wind_turbine_analytics.cli import StepStatus
from src.logger_config import get_logger

logger = get_logger(__name__)


class ScadaWorkflow(BaseWorkflow):
    """Coordinates SCADA data ingestion, criteria evaluation, and chart exports."""

    def __init__(self, config: ScadaRunnerConfig, presenter) -> None:
        super().__init__(config, presenter)

    def run(self) -> None:
        # Define pipeline steps
        steps = [
            "Load Configuration",
            "EBA Cut-In/Cut-Out",
            "EBA Manufacturer",
            "Code Error Analysis",
            "Data Availability",
            "Wind Calibration",
            "Tip Speed Ratio",
            "Normative Yield",
            "Pitch Analysis",
            "Performance Level",
            "Generate Report",
        ]

        # Start pipeline with CLI
        self._presenter.start_pipeline(
            "SCADA Analysis",
            steps,
            "Wind Turbine Analytics - SCADA Pipeline"
        )

        # Step 1: Load Configuration
        self._presenter.show_step_start("Load Configuration")
        try:
            self.validation_step()
            self._presenter.show_step_complete(StepStatus.SUCCESS)
        except Exception as e:
            self._presenter.show_step_complete(StepStatus.ERROR, str(e))
            raise

        # Steps 2-11: Process analyses
        self.process_step()

        # End pipeline
        self._presenter.end_pipeline()
        return

    def _execute_step(self, step_name, analyzer, visualizers, tablers):
        """
        Execute a DataProcessingStep with CLI progress tracking.

        Args:
            step_name: Name of the step
            analyzer: Analyzer instance
            visualizers: List of visualizer instances
            tablers: List of tabler instances or None
            add_to_summary: Whether to add result to summary tabler

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
        """Traite toutes les analyses SCADA et génère le rapport Word si activé."""
        # Créer un summary_tabler pour agréger tous les résultats
        summary_tabler = ScadaSummaryTabler()

        # Stocker tous les résultats pour génération du rapport
        all_results = {}

        # EBA Cut-In/Cut-Out Analysis
        eba_cutin_result = self._execute_step(
            "EBA Cut-In/Cut-Out",
            EbACutInCutOutAnalyzer(),
            [EbaCutInCutOutVisualizer()],
            [EbaCutInCutOutTabler()],
        )
        all_results["eba_cut_in_cut_out"] = eba_cutin_result
        summary_tabler.add_analysis_result("eba_cut_in_cut_out", eba_cutin_result)

        # EBA Manufacturer Analysis
        eba_mfr_result = self._execute_step(
            "EBA Manufacturer",
            EbaManufacturerAnalyzer(),
            [EbaManufacturerVisualizer(), EbaLossVisualizer()],
            [EbaManufacturerTabler(), EbaLossTabler()],
        )
        all_results["eba_manufacturer"] = eba_mfr_result
        summary_tabler.add_analysis_result("eba_manufacturer", eba_mfr_result)

        # Code Error Analysis
        error_codes_result = self._execute_step(
            "Code Error Analysis",
            CodeErrorAnalyzer(),
            [TopErrorCodeFrequencyVisualizer(), TreemapErrorCodeVisualizer()],
            [ErrorCodeParetoFrequencyTabler(), ErrorCodeParetoDurationTabler()],
        )
        all_results["error_codes"] = error_codes_result

        # Data Availability Analysis
        availability_result = self._execute_step(
            "Data Availability",
            DataAvailabilityAnalyzer(),
            [DataAvailabilityVisualizer()],
            [DataAvailabilityTabler()],
        )
        all_results["data_availability"] = availability_result
        summary_tabler.add_analysis_result("data_availability", availability_result)

        # Wind Direction Calibration
        calibration_result = self._execute_step(
            "Wind Calibration",
            WindDirectionCalibrationAnalyzer(),
            [
                WindDirectionCalibrationVisualizer(),
                PowerRoseChartVisualizer(),
                WindRoseChartVisualizer(),
            ],
            [WindDirectionCalibrationTabler()],
        )
        all_results["wind_calibration"] = calibration_result
        summary_tabler.add_analysis_result("wind_calibration", calibration_result)

        # Tip Speed Ratio
        tsr_result = self._execute_step(
            "Tip Speed Ratio",
            TipSpeedRatioAnalyzer(),
            [RPMVisualizer()],
            [TipSpeedRatioTabler()],
        )
        all_results["tip_speed_ratio"] = tsr_result
        summary_tabler.add_analysis_result("tip_speed_ratio", tsr_result)

        # Normative Yield (Power Curve)
        normative_result = self._execute_step(
            "Normative Yield",
            NormativeYieldAnalyzer(),
            [PowerCurveChartVisualizer()],
            [NormativeYieldTabler()],
        )
        all_results["normative_yield"] = normative_result

        # Pitch Analysis
        pitch_analyzer_result = self._execute_step(
            "Pitch Analysis",
            PitchAnalyzer(),
            [PitchVisualizer()],
            [PitchTabler()],
        )
        all_results["pitch_angle"] = pitch_analyzer_result
        summary_tabler.add_analysis_result("pitch_angle", pitch_analyzer_result)

        # Performance Level Analysis
        performance_level_result = self._execute_step(
            "Performance Level",
            PerformanceLevelAnalyzer(),
            [PerformanceLevelVisualizer()],
            [PerformanceLevelTabler()],
        )
        all_results["performance_level"] = performance_level_result

        # Generate Report
        self._presenter.show_step_start("Generate Report")
        try:
            self._render_report(all_results, summary_tabler)
            self._presenter.show_step_complete(StepStatus.SUCCESS)
        except Exception as e:
            self._presenter.show_step_complete(StepStatus.ERROR, str(e))
            raise

    def _render_report(
        self, all_results: dict, summary_tabler: ScadaSummaryTabler
    ) -> None:
        """
        Génère le rapport Word SCADA si activé dans la config.

        Args:
            all_results: Dict des résultats d'analyse par type
            summary_tabler: Tableau récapitulatif avec tous les résultats
        """
        if not self._config.render_template:
            logger.debug("Template rendering disabled (render_template=False)")
            return

        logger.debug("Rendering SCADA Word report...")

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
                f"CSV files table: {len(csv_files_data.get('csv_files_table', []))} rows"
            )
            context.update(csv_files_data)

            # Collecter les chemins des images de visualisation
            chart_paths = {}
            for analysis_name, result in all_results.items():
                if result.metadata and "charts" in result.metadata:
                    for chart_name, chart_info in result.metadata["charts"].items():
                        if "png_path" in chart_info:
                            chart_paths[chart_name] = chart_info["png_path"]
                            logger.debug(f"Chart collected: {chart_name}")

            # Ajouter les chemins d'images au contexte
            context["chart_paths"] = chart_paths

            # Préparer les métadonnées
            turbine_list = list(self.turbine_sources.farm.keys())

            # Récupérer analysis_start et analysis_end de la première turbine
            first_turbine_config = None
            if turbine_list:
                first_turbine_config = self.turbine_sources.farm[turbine_list[0]]

            metadata = {
                "analysis_start": (
                    first_turbine_config.test_start if first_turbine_config else "N/A"
                ),
                "analysis_end": (
                    first_turbine_config.test_end if first_turbine_config else "N/A"
                ),
                "turbines": turbine_list,
                # Informations sur le parc
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
            }

            # Rendre le rapport Word avec ScadaWordPresenter
            presenter = ScadaWordPresenter(
                template_path=self._config.template_path,
                output_path=self._config.output_path,
            )
            presenter.render_report(context, metadata=metadata)

            logger.debug(f"✅ SCADA report saved to: {self._config.output_path}")

        except FileNotFoundError as e:
            logger.error(f"Template file not found: {e}")
            logger.debug(f"Please create template at: {self._config.template_path}")
        except Exception as e:
            logger.error(f"Failed to render SCADA Word report: {e}")
            import traceback

            logger.error(traceback.format_exc())


def run_scada_pipeline(config: ScadaRunnerConfig, presenter) -> Any:
    return ScadaWorkflow(config=config, presenter=presenter).run()
