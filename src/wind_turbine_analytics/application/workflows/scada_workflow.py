"""SCADA application workflow."""

from __future__ import annotations


import pandas as pd
from typing import Dict, Any
from pathlib import Path
from src.wind_turbine_analytics.application.configuration.config_models import (
    ScadaRunnerConfig,
)
from src.wind_turbine_analytics.application.workflows.base_workflow import BaseWorkflow
from src.wind_turbine_analytics.data_processing.analyzer.logics.tba_cut_in_cut_out_analyzer import (
    TbACutInCutOutAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.tba_manifacturer_analyzer import (
    TbaManufacturerAnalyzer,
)
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
    StatusSummaryTabler,
    GpsCoordinatesTabler,
)
from src.wind_turbine_analytics.data_processing.tabler.tables.scada.table_tba_cut_in_cut_out import (
    TbaCutInCutOutTabler,
)
from src.wind_turbine_analytics.data_processing.tabler.tables.scada.table_tba_manufacturer import (
    TbaManufacturerTabler,
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
    TbaCutInCutOutVisualizer,
    TbaManufacturerVisualizer,
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

    def __init__(
        self,
        config: ScadaRunnerConfig,
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
            "EBA Cut-In/Cut-Out",
            "EBA Manufacturer",
            "TBA Cut-In/Cut-Out",
            "TBA Manufacturer",
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
            "SCADA Analysis", steps, "Wind Turbine Analytics - SCADA Pipeline"
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

        # Créer un status_summary_tabler pour vue d'ensemble des statuts
        status_summary_tabler = StatusSummaryTabler()

        # Stocker tous les résultats pour génération du rapport
        all_results = {}

        # EBA Cut-In/Cut-Out Analysis
        eba_cutin_result = self._execute_step(
            "EBA Cut-In/Cut-Out",
            EbACutInCutOutAnalyzer(),
            [EbaCutInCutOutVisualizer(output_dir=self.output_dir)],
            [EbaCutInCutOutTabler()],
        )
        all_results["eba_cut_in_cut_out"] = eba_cutin_result
        summary_tabler.add_analysis_result("eba_cut_in_cut_out", eba_cutin_result)
        status_summary_tabler.add_analysis_result(
            "eba_cut_in_cut_out", eba_cutin_result
        )

        # EBA Manufacturer Analysis
        eba_mfr_result = self._execute_step(
            "EBA Manufacturer",
            EbaManufacturerAnalyzer(),
            [EbaManufacturerVisualizer(output_dir=self.output_dir), EbaLossVisualizer(output_dir=self.output_dir)],
            [EbaManufacturerTabler(), EbaLossTabler()],
        )
        all_results["eba_manufacturer"] = eba_mfr_result
        summary_tabler.add_analysis_result("eba_manufacturer", eba_mfr_result)
        status_summary_tabler.add_analysis_result("eba_manufacturer", eba_mfr_result)

        # TBA Cut-In/Cut-Out Analysis
        tba_cutin_result = self._execute_step(
            "TBA Cut-In/Cut-Out",
            TbACutInCutOutAnalyzer(),
            [TbaCutInCutOutVisualizer(output_dir=self.output_dir)],
            [TbaCutInCutOutTabler()],
        )
        all_results["tba_cut_in_cut_out"] = tba_cutin_result
        summary_tabler.add_analysis_result("tba_cut_in_cut_out", tba_cutin_result)
        status_summary_tabler.add_analysis_result(
            "tba_cut_in_cut_out", tba_cutin_result
        )

        # TBA Manufacturer Analysis
        tba_mfr_result = self._execute_step(
            "TBA Manufacturer",
            TbaManufacturerAnalyzer(),
            [TbaManufacturerVisualizer(output_dir=self.output_dir)],
            [TbaManufacturerTabler()],
        )
        all_results["tba_manufacturer"] = tba_mfr_result
        summary_tabler.add_analysis_result("tba_manufacturer", tba_mfr_result)
        status_summary_tabler.add_analysis_result("tba_manufacturer", tba_mfr_result)

        # Code Error Analysis
        error_codes_result = self._execute_step(
            "Code Error Analysis",
            CodeErrorAnalyzer(),
            [TopErrorCodeFrequencyVisualizer(output_dir=self.output_dir), TreemapErrorCodeVisualizer(output_dir=self.output_dir)],
            [ErrorCodeParetoFrequencyTabler(), ErrorCodeParetoDurationTabler()],
        )
        all_results["error_codes"] = error_codes_result

        # Data Availability Analysis
        availability_result = self._execute_step(
            "Data Availability",
            DataAvailabilityAnalyzer(),
            [DataAvailabilityVisualizer(output_dir=self.output_dir)],
            [DataAvailabilityTabler()],
        )
        all_results["data_availability"] = availability_result
        summary_tabler.add_analysis_result("data_availability", availability_result)
        status_summary_tabler.add_analysis_result(
            "data_availability", availability_result
        )

        # Wind Direction Calibration
        calibration_result = self._execute_step(
            "Wind Calibration",
            WindDirectionCalibrationAnalyzer(),
            [
                WindDirectionCalibrationVisualizer(output_dir=self.output_dir),
                PowerRoseChartVisualizer(output_dir=self.output_dir),
                WindRoseChartVisualizer(output_dir=self.output_dir),
            ],
            [WindDirectionCalibrationTabler()],
        )
        all_results["wind_calibration"] = calibration_result
        summary_tabler.add_analysis_result("wind_calibration", calibration_result)
        status_summary_tabler.add_analysis_result(
            "wind_calibration", calibration_result
        )

        # Tip Speed Ratio
        tsr_result = self._execute_step(
            "Tip Speed Ratio",
            TipSpeedRatioAnalyzer(),
            [RPMVisualizer(output_dir=self.output_dir)],
            [TipSpeedRatioTabler()],
        )
        all_results["tip_speed_ratio"] = tsr_result
        summary_tabler.add_analysis_result("tip_speed_ratio", tsr_result)
        status_summary_tabler.add_analysis_result("tip_speed_ratio", tsr_result)

        # Normative Yield (Power Curve)
        normative_result = self._execute_step(
            "Normative Yield",
            NormativeYieldAnalyzer(),
            [PowerCurveChartVisualizer(output_dir=self.output_dir)],
            [NormativeYieldTabler()],
        )
        all_results["normative_yield"] = normative_result
        status_summary_tabler.add_analysis_result("normative_yield", normative_result)

        # Pitch Analysis
        pitch_analyzer_result = self._execute_step(
            "Pitch Analysis",
            PitchAnalyzer(),
            [PitchVisualizer(output_dir=self.output_dir)],
            [PitchTabler()],
        )
        all_results["pitch_angle"] = pitch_analyzer_result
        summary_tabler.add_analysis_result("pitch_angle", pitch_analyzer_result)
        status_summary_tabler.add_analysis_result("pitch_angle", pitch_analyzer_result)

        # Performance Level Analysis
        performance_level_result = self._execute_step(
            "Performance Level",
            PerformanceLevelAnalyzer(),
            [PerformanceLevelVisualizer(output_dir=self.output_dir)],
            [PerformanceLevelTabler()],
        )
        all_results["performance_level"] = performance_level_result
        status_summary_tabler.add_analysis_result(
            "performance_level", performance_level_result
        )

        # Generate Report
        self._presenter.show_step_start("Generate Report")
        try:
            self._render_report(all_results, summary_tabler, status_summary_tabler)
            self._presenter.show_step_complete(StepStatus.SUCCESS)
        except Exception as e:
            self._presenter.show_step_complete(StepStatus.ERROR, str(e))
            raise

    def _extract_metadata_fields(
        self, fields: list, source=None, default="N/A"
    ) -> dict:
        """
        Extract multiple fields from a source object with fallback to default.

        Args:
            fields: List of field names to extract
            source: Source object to extract from (defaults to self.general_information)
            default: Default value if field or source is None

        Returns:
            Dict mapping field names to their values
        """
        if source is None:
            source = self.general_information

        if source is None:
            return {field: default for field in fields}

        return {field: getattr(source, field, default) for field in fields}

    def _render_report(
        self,
        all_results: dict,
        summary_tabler: ScadaSummaryTabler,
        status_summary_tabler: StatusSummaryTabler,
    ) -> None:
        """
        Génère le rapport Word SCADA si activé dans la config.

        Args:
            all_results: Dict des résultats d'analyse par type
            summary_tabler: Tableau récapitulatif avec tous les résultats
            status_summary_tabler: Tableau de synthèse des statuts
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

            # Générer le tableau de synthèse des statuts et l'ajouter au contexte
            status_summary_data = status_summary_tabler.generate()
            context.update(status_summary_data)
            logger.debug(
                f"Status summary table: {len(status_summary_data.get('status_summary_table', []))} rows"
            )

            # Générer le tableau des fichiers CSV utilisés
            csv_files_tabler = CsvFilesTabler()
            csv_files_data = csv_files_tabler.generate_from_turbine_farm(
                self.turbine_sources
            )
            logger.debug(
                f"CSV files table: {len(csv_files_data.get('csv_files_table', []))} rows"
            )
            context.update(csv_files_data)

            # Générer le tableau des coordonnées GPS
            gps_coordinates_tabler = GpsCoordinatesTabler()
            gps_coordinates_data = gps_coordinates_tabler.generate_from_turbine_farm(
                self.turbine_sources
            )
            logger.debug(
                f"GPS coordinates table: {len(gps_coordinates_data.get('gps_coordinates_table', []))} rows"
            )
            context.update(gps_coordinates_data)

            # Collecter les chemins des images de visualisation
            chart_paths = {}
            for analysis_name, result in all_results.items():
                if result.metadata and "charts" in result.metadata:
                    for chart_name, chart_info in result.metadata["charts"].items():
                        # Vérifier que png_path existe ET n'est pas None
                        png_path = chart_info.get("png_path")
                        if png_path is not None:
                            chart_paths[chart_name] = png_path
                            logger.debug(f"  ✅ Chart collected: {chart_name}")
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

            # Préparer les métadonnées
            turbine_list = list(self.turbine_sources.farm.keys())

            # Récupérer analysis_start et analysis_end de la première turbine
            first_turbine_config = (
                self.turbine_sources.farm[turbine_list[0]] if turbine_list else None
            )

            # Extract general information fields using helper method
            general_info_fields = [
                "park_name",
                "commune",
                "region",
                "country",
                "constructor",
                "model_wtg",
                "nominal_power",
                "client_name",
                "client_location",
                "client_contact",
                "author_name",
                "author_email",
                "author_phone",
                "verificator_name",
                "verificator_email",
                "verificator_phone",
                "approver_name",
                "approver_email",
                "approver_phone",
            ]

            # Build metadata dict
            metadata = {
                "analysis_start": (
                    first_turbine_config.test_start if first_turbine_config else "N/A"
                ),
                "analysis_end": (
                    first_turbine_config.test_end if first_turbine_config else "N/A"
                ),
                "turbines": turbine_list,
            }

            # Add all general information fields
            metadata.update(self._extract_metadata_fields(general_info_fields))

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
