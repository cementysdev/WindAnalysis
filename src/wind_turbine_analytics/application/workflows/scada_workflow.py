"""SCADA application workflow."""

from __future__ import annotations


import pandas as pd
from typing import Dict, Any
from src.wind_turbine_analytics.application.configuration.config_models import (
    ScadaRunnerConfig,
)
from src.wind_turbine_analytics.application.workflows.base_workflow import BaseWorkflow
from src.wind_turbine_analytics.data_processing.analyzer.logics.tip_speed_ratio import (
    TipSpeedRatioAnalyzer,
)
from src.wind_turbine_analytics.data_processing.analyzer.logics.wind_direction_calibration_analyzer import (
    WindDirectionCalibrationAnalyzer,
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
)
from src.wind_turbine_analytics.data_processing.tabler.tables.scada.table_yield_normative import (
    NormativeYieldTabler,
)
from src.wind_turbine_analytics.data_processing.tabler.tables.scada.tip_speed_ratio import TipSpeedRatioTabler
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.data_availability_visualizer import (
    DataAvailabilityVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.eba_cut_in_cut_out_visualizer import (
    EbaCutInCutOutVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.eba_manifacturer_visualizer import (
    EbaManufacturerVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.eba_loss_visualizer import (
    EbaLossVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.power_curve_chart_visualizer import (
    PowerCurveChartVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.power_rose_chart_visualizer import (
    PowerRoseChartVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.rpm_visualizer import (
    RPMVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.top_error_code_frequency_visualizer import (
    TopErrorCodeFrequencyVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.treemap_error_code_visualizer import (
    TreemapErrorCodeVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.wind_direction_calibration_visualizer import (
    WindDirectionCalibrationVisualizer,
)
from src.wind_turbine_analytics.data_processing.visualizer.chart_builders.wind_rose_chart_visualizer import (
    WindRoseChartVisualizer,
)
from src.wind_turbine_analytics.data_processing.tabler.tables.scada import (
    EbaCutInCutOutTabler,
    EbaManufacturerTabler,
    EbaLossTabler,
    ScadaSummaryTabler,
    ErrorCodeParetoFrequencyTabler,
    ErrorCodeParetoDurationTabler,
)
from src.wind_turbine_analytics.data_processing.tabler.tables.runtest import (
    CsvFilesTabler,
)
from src.wind_turbine_analytics.presentation.word_generation import ScadaWordPresenter
from src.logger_config import get_logger

logger = get_logger(__name__)


class ScadaWorkflow(BaseWorkflow):
    """Coordinates SCADA data ingestion, criteria evaluation, and chart exports."""

    def __init__(self, config: ScadaRunnerConfig, presenter) -> None:
        super().__init__(config, presenter)

    def run(self) -> None:
        self.validation_step()
        self.process_step()
        return

    def process_step(self) -> None:
        """Traite toutes les analyses SCADA et génère le rapport Word si activé."""
        # Créer un summary_tabler pour agréger tous les résultats
        summary_tabler = ScadaSummaryTabler()

        # Stocker tous les résultats pour génération du rapport
        all_results = {}

        # EBA Cut-In/Cut-Out Analysis
        eba_cutin_result = DataProcessingStep(
            analyzer=EbACutInCutOutAnalyzer(),
            visualizers=[EbaCutInCutOutVisualizer()],
            tabler=[EbaCutInCutOutTabler()],
        ).execute(self.turbine_sources, self.validation_criteria)
        all_results["eba_cut_in_cut_out"] = eba_cutin_result
        summary_tabler.add_analysis_result("eba_cut_in_cut_out", eba_cutin_result)

        # EBA Manufacturer Analysis
        eba_mfr_result = DataProcessingStep(
            analyzer=EbaManufacturerAnalyzer(),
            visualizers=[
                EbaManufacturerVisualizer(),
                EbaLossVisualizer(),
            ],
            tabler=[EbaManufacturerTabler(), EbaLossTabler()],
        ).execute(self.turbine_sources, self.validation_criteria)
        all_results["eba_manufacturer"] = eba_mfr_result
        summary_tabler.add_analysis_result("eba_manufacturer", eba_mfr_result)

        # Code Error Analysis
        error_codes_result = DataProcessingStep(
            analyzer=CodeErrorAnalyzer(),
            visualizers=[
                TopErrorCodeFrequencyVisualizer(),
                TreemapErrorCodeVisualizer(),
            ],
            tabler=[
                ErrorCodeParetoFrequencyTabler(),
                ErrorCodeParetoDurationTabler(),
            ],
        ).execute(self.turbine_sources, self.validation_criteria)
        all_results["error_codes"] = error_codes_result

        # Data Availability Analysis
        availability_result = DataProcessingStep(
            analyzer=DataAvailabilityAnalyzer(),
            visualizers=[DataAvailabilityVisualizer()],
            tabler=None,  # TODO: DataAvailabilityTabler si nécessaire
        ).execute(self.turbine_sources, self.validation_criteria)
        all_results["data_availability"] = availability_result
        summary_tabler.add_analysis_result("data_availability", availability_result)

        # Wind Direction Calibration
        calibration_result = DataProcessingStep(
            analyzer=WindDirectionCalibrationAnalyzer(),
            visualizers=[
                WindDirectionCalibrationVisualizer(),
                PowerRoseChartVisualizer(),
                WindRoseChartVisualizer(),
            ],
            tabler=None,  # TODO: WindCalibrationTabler si nécessaire
        ).execute(self.turbine_sources, self.validation_criteria)
        all_results["wind_calibration"] = calibration_result
        summary_tabler.add_analysis_result("wind_calibration", calibration_result)

        # Tip Speed Ratio
        tsr_result = DataProcessingStep(
            analyzer=TipSpeedRatioAnalyzer(),
            visualizers=[RPMVisualizer()],
            tabler=[TipSpeedRatioTabler()],  # TODO: TipSpeedRatioTabler si nécessaire
        ).execute(self.turbine_sources, self.validation_criteria)
        all_results["tip_speed_ratio"] = tsr_result
        summary_tabler.add_analysis_result("tip_speed_ratio", tsr_result)

        # Normative Yield (Power Curve)
        normative_result = DataProcessingStep(
            analyzer=NormativeYieldAnalyzer(),
            visualizers=[
                PowerCurveChartVisualizer()
            ],  # TODO: PowerCurveChartVisualizer si nécessaire
            tabler=[NormativeYieldTabler()],  # TODO: NormativeYieldTabler si nécessaire
        ).execute(self.turbine_sources, self.validation_criteria)
        all_results["normative_yield"] = normative_result

        # Générer le rapport Word si activé dans la config
        self._render_report(all_results, summary_tabler)

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
            logger.info("Template rendering disabled (render_template=False)")
            return

        logger.info("Rendering SCADA Word report...")

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
            logger.info(
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
                            logger.info(f"Chart collected: {chart_name}")

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

            logger.info(f"✅ SCADA report saved to: {self._config.output_path}")

        except FileNotFoundError as e:
            logger.error(f"Template file not found: {e}")
            logger.info(f"Please create template at: {self._config.template_path}")
        except Exception as e:
            logger.error(f"Failed to render SCADA Word report: {e}")
            import traceback

            logger.error(traceback.format_exc())


def run_scada_pipeline(config: ScadaRunnerConfig, presenter) -> Any:
    return ScadaWorkflow(config=config, presenter=presenter).run()
