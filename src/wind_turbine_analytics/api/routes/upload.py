"""
Upload endpoint for ZIP file handling.
"""
import yaml
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from src.logger_config import get_logger
from src.wind_turbine_analytics.api.models.responses import UploadResponse
from src.wind_turbine_analytics.api.services.session_manager import SessionManager

logger = get_logger(__name__)

router = APIRouter()


@router.post("/upload", response_model=UploadResponse)
async def upload_zip(
    file: UploadFile = File(...),
    workflow_type: Literal["runtest", "scada"] = Form(...),
) -> UploadResponse:
    """
    Upload a ZIP file and create a session.

    Steps:
    1. Validate that the file is a ZIP
    2. Create session via SessionManager (extracts ZIP)
    3. Validate config.yml exists
    4. Load config.yml for preview
    5. Save initial metadata
    6. Return session_id + config preview

    Args:
        file: Uploaded ZIP file
        workflow_type: Type of analysis workflow

    Returns:
        UploadResponse with session_id and config preview

    Raises:
        HTTPException 400: If file is not a ZIP or config.yml is missing
        HTTPException 500: If extraction or processing fails
    """
    logger.info(f"Received ZIP upload: {file.filename} (workflow: {workflow_type})")

    # Validate file extension
    if not file.filename.endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Le fichier doit être un ZIP. Extension détectée: "
            f"{Path(file.filename).suffix}",
        )

    # Validate file size (optional, FastAPI handles this with max_upload_size)
    # For now, we rely on FastAPI's default limits

    try:
        # Create session
        session_manager = SessionManager()
        session_id = session_manager.create_session(file)

        logger.info(f"Session {session_id} created successfully")

        # Load config.yml for preview
        uploaded_path = session_manager.get_uploaded_path(session_id)
        config_files = list(uploaded_path.rglob("config.yml"))

        if not config_files:
            # Should not happen (SessionManager validates this), but safety check
            raise HTTPException(
                status_code=400, detail="config.yml introuvable dans le ZIP"
            )

        config_path = config_files[0]
        logger.debug(f"Loading config from: {config_path}")

        # Parse config.yml
        with open(config_path, "r", encoding="utf-8") as f:
            config_preview = yaml.safe_load(f)

        # Update metadata with workflow type
        metadata = session_manager.get_session_metadata(session_id)
        metadata["workflow_type"] = workflow_type
        session_manager.save_session_metadata(session_id, metadata)

        logger.info(f"Session {session_id} ready for analysis")

        return UploadResponse(
            session_id=session_id,
            original_filename=file.filename,
            workflow_type=workflow_type,
            config_preview=config_preview,
            created_at=metadata["created_at"],
            message=f"Fichier {file.filename} uploadé avec succès. Session créée: {session_id}",
        )

    except ValueError as e:
        # SessionManager raises ValueError for invalid ZIP or missing config.yml
        logger.error(f"Validation error during upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error during upload: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erreur lors du traitement du fichier: {str(e)}"
        )
