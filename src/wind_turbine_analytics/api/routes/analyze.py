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
from src.wind_turbine_analytics.api.services.session_manager import SessionManager

logger = get_logger(__name__)
router = APIRouter(prefix="/analyze", tags=["Analysis"])


@router.post("/runtest", response_model=AnalyzeResponse)
async def run_runtest_analysis(request: AnalyzeRequest):
    """
    Trigger a RunTest analysis workflow.

    This endpoint executes the RunTest workflow (acceptance testing) and returns
    all generated charts and tables as JSON, along with metadata.

    Args:
        request: Analysis request with folder_path OR session_id

    Returns:
        AnalyzeResponse with charts, tables, and metadata

    Raises:
        HTTPException 400: If folder_path/session_id or config.yml is invalid
        HTTPException 500: If workflow execution fails
    """
    # Determine source: session_id or folder_path
    session_id = None
    if request.session_id:
        logger.debug(f"Received RunTest analysis request for session: {request.session_id}")
        session_manager = SessionManager()

        if not session_manager.session_exists(request.session_id):
            raise HTTPException(
                status_code=400,
                detail=f"Session {request.session_id} introuvable."
            )

        folder = session_manager.get_uploaded_path(request.session_id)
        session_id = request.session_id
    else:
        logger.debug(f"Received RunTest analysis request for folder: {request.folder_path}")
        folder = Path(request.folder_path)

        if not folder.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Le dossier {request.folder_path} n'existe pas."
            )

    # Validate config.yml
    config_file = folder / "config.yml"
    if not config_file.exists():
        # Try searching recursively (for ZIP extracts)
        config_files = list(folder.rglob("config.yml"))
        if not config_files:
            raise HTTPException(
                status_code=400,
                detail=f"Le fichier config.yml est introuvable dans {folder}."
            )
        config_file = config_files[0]
        folder = config_file.parent  # Use the directory containing config.yml

    # Create workflow configuration
    if session_id:
        session_manager = SessionManager()
        output_path = session_manager.get_reports_path(session_id) / "runtest_report.docx"
    else:
        output_path = request.output_path or f"./output/runtest_{folder.name}.docx"

    config = RunTestPipelineConfig(
        root_path=str(folder),
        template_path=request.template_path or "./assets/templates/template_runtest.docx",
        output_path=str(output_path),
        render_template=request.render_template,
    )

    logger.debug(f"RunTest config created: output_path={config.output_path}")

    # Execute workflow via adapter
    try:
        adapter = WorkflowAdapter()
        result = adapter.run_workflow(config, RunTestWorkflow, session_id=session_id)

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
        request: Analysis request with folder_path OR session_id

    Returns:
        AnalyzeResponse with charts, tables, and metadata

    Raises:
        HTTPException 400: If folder_path/session_id or config.yml is invalid
        HTTPException 500: If workflow execution fails
    """
    # Determine source: session_id or folder_path
    session_id = None
    if request.session_id:
        logger.debug(f"Received SCADA analysis request for session: {request.session_id}")
        session_manager = SessionManager()

        if not session_manager.session_exists(request.session_id):
            raise HTTPException(
                status_code=400,
                detail=f"Session {request.session_id} introuvable."
            )

        folder = session_manager.get_uploaded_path(request.session_id)
        session_id = request.session_id
    else:
        logger.debug(f"Received SCADA analysis request for folder: {request.folder_path}")
        folder = Path(request.folder_path)

        if not folder.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Le dossier {request.folder_path} n'existe pas."
            )

    # Validate config.yml
    config_file = folder / "config.yml"
    if not config_file.exists():
        # Try searching recursively (for ZIP extracts)
        config_files = list(folder.rglob("config.yml"))
        if not config_files:
            raise HTTPException(
                status_code=400,
                detail=f"Le fichier config.yml est introuvable dans {folder}."
            )
        config_file = config_files[0]
        folder = config_file.parent  # Use the directory containing config.yml

    # Create workflow configuration
    if session_id:
        session_manager = SessionManager()
        output_path = session_manager.get_reports_path(session_id) / "scada_report.docx"
    else:
        output_path = request.output_path or f"./output/scada_{folder.name}.docx"

    config = ScadaRunnerConfig(
        root_path=str(folder),
        template_path=request.template_path or "./assets/templates/template_scada.docx",
        output_path=str(output_path),
        render_template=request.render_template,
    )

    logger.debug(f"SCADA config created: output_path={config.output_path}")

    # Execute workflow via adapter
    try:
        adapter = WorkflowAdapter()
        result = adapter.run_workflow(config, ScadaWorkflow, session_id=session_id)

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
