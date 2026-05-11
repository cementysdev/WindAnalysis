from src.wind_turbine_analytics.application.workflows.base_workflow import BaseWorkflow
from src.wind_turbine_analytics.data_processing.data_result_models import AnalysisResult
from src.wind_turbine_analytics.data_processing.analyzer.base_analyzer import (
    BaseAnalyzer,
)
from src.wind_turbine_analytics.data_processing.visualizer.base_visualizer import (
    BaseVisualizer,
)
from src.wind_turbine_analytics.data_processing.tabler.base_tabler import BaseTabler
from src.wind_turbine_analytics.application.configuration.config_models import (
    TurbineFarm,
    ValidationCriteria,
)
from typing import Any, Optional, Union, List


class DataProcessingStep:
    def __init__(
        self,
        analyzer: BaseAnalyzer,
        visualizers: Optional[List[BaseVisualizer]] = None,
        tabler: Optional[Union[BaseTabler, List[BaseTabler]]] = None,
    ) -> None:
        self.analyzer: BaseAnalyzer = analyzer
        self.visualizers: Optional[List[BaseVisualizer]] = visualizers
        self.tabler: Optional[Union[BaseTabler, List[BaseTabler]]] = tabler

    def execute(self, context: TurbineFarm, criteria: ValidationCriteria) -> Any:
        from src.logger_config import get_logger

        logger = get_logger(__name__)

        result = self.analyzer.analyze(context, criteria)

        logger.info(
            f"requires_visuals={result.requires_visuals}, visualizers={self.visualizers}"
        )

        if result.requires_visuals:
            if self.visualizers is not None:
                logger.info(
                    f"Génération de {len(self.visualizers)} visualisation(s)..."
                )
                for visualizer in self.visualizers:
                    visualizer.generate(result)

        # Génération de tableaux
        if self.tabler is not None:
            # Gérer le cas d'un seul tabler ou d'une liste
            tablers = self.tabler if isinstance(self.tabler, list) else [self.tabler]

            # Générer les données de tableau pour chaque tabler
            for tabler_instance in tablers:
                table_data = tabler_instance.generate(result)

                # Stocker les données de tableau dans le résultat
                if result.metadata is None:
                    result.metadata = {}
                if "table_data" not in result.metadata:
                    result.metadata["table_data"] = {}

                # Fusionner les données de ce tableau dans le contexte global
                result.metadata["table_data"].update(table_data)

        return result
