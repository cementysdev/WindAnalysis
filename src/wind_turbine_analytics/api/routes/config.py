"""
Configuration endpoint for reading config.yml without running full analysis.
"""
from fastapi import APIRouter, HTTPException, Query
from pathlib import Path
import yaml
from typing import Dict, Any

from src.logger_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/config", tags=["Configuration"])


@router.get("", response_model=Dict[str, Any])
async def read_config(folder_path: str = Query(..., description="Path to folder containing config.yml")):
    """
    Read and parse config.yml file without running analysis.

    Args:
        folder_path: Path to folder containing config.yml

    Returns:
        Parsed YAML configuration as dictionary

    Raises:
        HTTPException 400: If folder doesn't exist
        HTTPException 404: If config.yml not found
        HTTPException 500: If YAML parsing fails
    """
    try:
        folder = Path(folder_path)

        # Validate folder exists
        if not folder.exists():
            raise HTTPException(
                status_code=400,
                detail=f"Folder not found: {folder_path}"
            )

        # Validate config.yml exists
        config_file = folder / "config.yml"
        if not config_file.exists():
            raise HTTPException(
                status_code=404,
                detail=f"config.yml not found in {folder_path}"
            )

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
