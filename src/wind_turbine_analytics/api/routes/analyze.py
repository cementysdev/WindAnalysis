"""
Analysis endpoints for triggering RunTest and SCADA workflows.
"""
from pathlib import Path
from fastapi import APIRouter, HTTPException

from src.logger_config import get_logger
from src.wind_turbine_analytics.api.models.requests import AnalyzeRequest
from src.wind_turbine_analytics.api.models.responses import AnalyzeResponse
from src.wind_turbine_analytics.application.configuration.config_models import (
    RunTestPipelineConfig,
    ScadaRunnerConfig,
)
from src.wind_turbine_analytics.application.workflows.runtest_workflow import RunTestWorkflow
from src.wind_turbine_analytics.application.workflows.scada_workflow import ScadaWorkflow
from src.wind_turbine_analytics.api.services.workflow_adapter import WorkflowAdapter

logger = get_logger(__name__)
router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("/runtest", response_model=AnalyzeResponse)
async def run_runtest_analysis(request: AnalyzeRequest):
    """
    Trigger a RunTest analysis workflow.

    This endpoint executes the RunTest workflow (acceptance testing) and returns
    all generated charts and tables as JSON, along with metadata.

    Args:
        request: Analysis request with folder_path and configuration options

    Returns:
        AnalyzeResponse with charts, tables, and metadata

    Raises:
        HTTPException 400: If folder_path or config.yml is invalid
        HTTPException 500: If workflow execution fails
    """
    logger.debug(f"Received RunTest analysis request for: {request.folder_path}")

    # Validate folder and config.yml
    folder = Path(request.folder_path)
    if not folder.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Le dossier {request.folder_path} n'existe pas."
        )

    config_file = folder / "config.yml"
    if not config_file.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Le fichier config.yml est introuvable dans {request.folder_path}."
        )

    # Create workflow configuration
    config = RunTestPipelineConfig(
        root_path=str(folder),
        template_path=request.template_path or "./assets/templates/template_runtest.docx",
        output_path=request.output_path or f"./output/runtest_{folder.name}.docx",
        render_template=request.render_template,
    )

    logger.debug(f"RunTest config created: output_path={config.output_path}")

    # Execute workflow via adapter
    try:
        adapter = WorkflowAdapter()
        result = adapter.run_workflow(config, RunTestWorkflow)

        if result.status == "error":
            logger.error(f"RunTest workflow returned error: {result.message}")
            raise HTTPException(status_code=500, detail=result.message)

        logger.debug(f"RunTest analysis completed successfully: {len(result.charts)} charts, {len(result.tables)} tables")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during RunTest analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur inattendue lors de l'analyse : {str(e)}"
        )


@router.post("/scada", response_model=AnalyzeResponse)
async def run_scada_analysis(request: AnalyzeRequest):
    """
    Trigger a SCADA analysis workflow.

    This endpoint executes the SCADA workflow (performance monitoring) and returns
    all generated charts and tables as JSON, along with metadata.

    Args:
        request: Analysis request with folder_path and configuration options

    Returns:
        AnalyzeResponse with charts, tables, and metadata

    Raises:
        HTTPException 400: If folder_path or config.yml is invalid
        HTTPException 500: If workflow execution fails
    """
    logger.debug(f"Received SCADA analysis request for: {request.folder_path}")

    # Validate folder and config.yml
    folder = Path(request.folder_path)
    if not folder.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Le dossier {request.folder_path} n'existe pas."
        )

    config_file = folder / "config.yml"
    if not config_file.exists():
        raise HTTPException(
            status_code=400,
            detail=f"Le fichier config.yml est introuvable dans {request.folder_path}."
        )

    # Create workflow configuration
    config = ScadaRunnerConfig(
        root_path=str(folder),
        template_path=request.template_path or "./assets/templates/template_scada.docx",
        output_path=request.output_path or f"./output/scada_{folder.name}.docx",
        render_template=request.render_template,
    )

    logger.debug(f"SCADA config created: output_path={config.output_path}")

    # Execute workflow via adapter
    try:
        adapter = WorkflowAdapter()
        result = adapter.run_workflow(config, ScadaWorkflow)

        if result.status == "error":
            logger.error(f"SCADA workflow returned error: {result.message}")
            raise HTTPException(status_code=500, detail=result.message)

        logger.debug(f"SCADA analysis completed successfully: {len(result.charts)} charts, {len(result.tables)} tables")
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during SCADA analysis: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur inattendue lors de l'analyse : {str(e)}"
        )
