"""
Configuration endpoint for reading config.yml without running full analysis.
"""
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import yaml
from typing import Dict, Any, Optional

from src.logger_config import get_logger
from src.wind_turbine_analytics.api.services.session_manager import SessionManager

logger = get_logger(__name__)

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get("", response_model=Dict[str, Any])
async def read_config(
    folder_path: Optional[str] = Query(None, description="Path to folder containing config.yml (legacy)"),
    session_id: Optional[str] = Query(None, description="Session ID from ZIP upload")
):
    """
    Read and parse config.yml file without running analysis.

    Args:
        folder_path: (Legacy) Path to folder containing config.yml
        session_id: (New) Session ID from ZIP upload

    Returns:
        Parsed YAML configuration as dictionary

    Raises:
        HTTPException 400: If neither folder_path nor session_id provided, or if they don't exist
        HTTPException 404: If config.yml not found
        HTTPException 500: If YAML parsing fails
    """
    try:
        # Validate that at least one parameter is provided
        if not folder_path and not session_id:
            raise HTTPException(
                status_code=400,
                detail="You must provide either 'folder_path' or 'session_id'"
            )

        # Determine folder based on source
        if session_id:
            logger.debug(f"Reading config for session: {session_id}")
            session_manager = SessionManager()

            if not session_manager.session_exists(session_id):
                raise HTTPException(
                    status_code=400,
                    detail=f"Session {session_id} not found"
                )

            folder = session_manager.get_uploaded_path(session_id)
        else:
            logger.debug(f"Reading config from folder: {folder_path}")
            folder = Path(folder_path)

            # Validate folder exists
            if not folder.exists():
                raise HTTPException(
                    status_code=400,
                    detail=f"Folder not found: {folder_path}"
                )

        # Find config.yml (search recursively for session uploads)
        config_file = folder / "config.yml"
        if not config_file.exists():
            # Try searching recursively
            config_files = list(folder.rglob("config.yml"))
            if not config_files:
                raise HTTPException(
                    status_code=404,
                    detail=f"config.yml not found in {folder}"
                )
            config_file = config_files[0]

        # Read and parse YAML
        logger.debug(f"Reading config from: {config_file}")
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)

        logger.debug(f"Successfully parsed config.yml with {len(config_data.get('turbines', {}))} turbines")

        return config_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading config.yml: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to parse config.yml: {str(e)}"
        )
