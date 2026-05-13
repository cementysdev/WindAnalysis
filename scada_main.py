import sys

from src.wind_turbine_analytics.presentation.cli_presenter import CLIPipelinePresenter
from src.wind_turbine_analytics.application import ScadaRunnerConfig, run_scada_pipeline


# scada_main.py (ajuster les defaults)
DEFAULT_RUNTEST_ROOT = "./experiments/scada_analyse"
DEFAULT_TEMPLATE_PATH = "./assets/templates/template_scada.docx"
DEFAULT_OUTPUT_PATH = "./output/scada/scada_output.docx"


if __name__ == "__main__":
    root_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_RUNTEST_ROOT
    template_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TEMPLATE_PATH
    output_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUTPUT_PATH
    config = ScadaRunnerConfig(
        root_path=root_path,
        template_path=template_path,
        output_path=output_path,
        render_template=True,
    )

    presenter = CLIPipelinePresenter()
    run_scada_pipeline(config=config, presenter=presenter)
