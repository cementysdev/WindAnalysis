"""
Session management endpoints for listing, viewing, and deleting sessions.
"""
import json
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from src.logger_config import get_logger
from src.wind_turbine_analytics.api.services.session_manager import SessionManager
from src.wind_turbine_analytics.api.models.responses import (
    SessionSummary,
    SessionDetail,
    ChartData,
    TableData,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/sessions", tags=["Sessions"])


class BulkDeleteRequest(BaseModel):
    """Request model for bulk delete endpoint."""
    session_ids: List[str]


class BulkDeleteResponse(BaseModel):
    """Response model for bulk delete endpoint."""
    results: dict[str, str]
    deleted_count: int
    failed_count: int


@router.get("", response_model=List[SessionSummary])
async def list_sessions():
    """
    List all sessions with their metadata.

    Returns:
        List of SessionSummary objects sorted by creation date (newest first)

    Example response:
        [
            {
                "session_id": "a3f2e4d5-...",
                "created_at": "2026-05-19T15:30:00Z",
                "workflow_type": "scada",
                "park_name": "Parc Éolien Test",
                "status": "completed",
                "charts_count": 15,
                "tables_count": 6
            },
            ...
        ]
    """
    try:
        session_manager = SessionManager()
        sessions = session_manager.list_sessions()

        logger.info(f"Listed {len(sessions)} sessions")

        # Convert to SessionSummary models
        summaries = []
        for session_metadata in sessions:
            summary = SessionSummary(
                session_id=session_metadata.get("session_id", "unknown"),
                created_at=session_metadata.get("created_at", ""),
                workflow_type=session_metadata.get("workflow_type", "scada"),
                park_name=session_metadata.get("park_name"),
                status=session_metadata.get("status", "unknown"),
                charts_count=session_metadata.get("charts_count", 0),
                tables_count=session_metadata.get("tables_count", 0),
            )
            summaries.append(summary)

        return summaries

    except Exception as e:
        logger.error(f"Error listing sessions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list sessions: {str(e)}"
        )


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    """
    Get detailed information for a specific session.

    Args:
        session_id: Session identifier (UUID or CLI timestamp_uuid)

    Returns:
        SessionDetail with metadata, charts, and tables

    Raises:
        HTTPException 404: If session not found
        HTTPException 500: If error loading session data

    Example response:
        {
            "metadata": {
                "session_id": "a3f2e4d5-...",
                "created_at": "2026-05-19T15:30:00Z",
                "workflow_type": "scada",
                "park_name": "Parc Éolien Test",
                "status": "completed",
                "turbines": ["E1", "E6", "E8"],
                "charts_count": 15,
                "tables_count": 6
            },
            "charts": [
                {
                    "name": "eba_loss_chart",
                    "plotly_json": { ... }
                },
                ...
            ],
            "tables": [
                {
                    "name": "summary_table",
                    "columns": ["turbine", "availability"],
                    "rows": [{"turbine": "E1", "availability": 98.5}, ...]
                },
                ...
            ]
        }
    """
    try:
        session_manager = SessionManager()

        # Check if session exists
        if not session_manager.session_exists(session_id):
            logger.warning(f"Session not found: {session_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        # Load metadata
        metadata = session_manager.get_session_metadata(session_id)
        logger.debug(f"Loaded metadata for session {session_id}")

        # Load charts from charts/ directory
        charts_path = session_manager.get_charts_path(session_id)
        charts = []

        if charts_path.exists():
            for chart_file in sorted(charts_path.glob("*.json")):
                try:
                    with open(chart_file, "r", encoding="utf-8") as f:
                        plotly_json = json.load(f)

                    chart = ChartData(
                        name=chart_file.stem,
                        plotly_json=plotly_json
                    )
                    charts.append(chart)
                    logger.debug(f"  Loaded chart: {chart_file.stem}")

                except Exception as e:
                    logger.warning(f"  Failed to load chart {chart_file.name}: {e}")

        logger.info(f"Loaded {len(charts)} charts for session {session_id}")

        # Load tables from tables/ directory
        tables_path = session_manager.get_tables_path(session_id)
        tables = []

        if tables_path.exists():
            for table_file in sorted(tables_path.glob("*.json")):
                try:
                    with open(table_file, "r", encoding="utf-8") as f:
                        table_data = json.load(f)

                    # table_data should already have name, columns, rows
                    table = TableData(
                        name=table_data.get("name", table_file.stem),
                        columns=table_data.get("columns", []),
                        rows=table_data.get("rows", [])
                    )
                    tables.append(table)
                    logger.debug(f"  Loaded table: {table_file.stem}")

                except Exception as e:
                    logger.warning(f"  Failed to load table {table_file.name}: {e}")

        logger.info(f"Loaded {len(tables)} tables for session {session_id}")

        # Return SessionDetail
        return SessionDetail(
            metadata=metadata,
            charts=charts,
            tables=tables
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error loading session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to load session: {str(e)}"
        )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """
    Delete a single session completely (directory and all contents).

    Args:
        session_id: Session identifier to delete

    Returns:
        Success message with deleted session_id

    Raises:
        HTTPException 404: If session not found
        HTTPException 500: If deletion fails

    Example response:
        {
            "message": "Session a3f2e4d5-... deleted successfully",
            "session_id": "a3f2e4d5-..."
        }
    """
    try:
        session_manager = SessionManager()

        # Check if session exists
        if not session_manager.session_exists(session_id):
            logger.warning(f"Session not found for deletion: {session_id}")
            raise HTTPException(
                status_code=404,
                detail=f"Session {session_id} not found"
            )

        # Delete session
        session_manager.delete_session(session_id)
        logger.info(f"Session {session_id} deleted via API")

        return {
            "message": f"Session {session_id} deleted successfully",
            "session_id": session_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete session: {str(e)}"
        )


@router.delete("", response_model=BulkDeleteResponse)
async def delete_multiple_sessions(request: BulkDeleteRequest):
    """
    Delete multiple sessions in a single batch operation.

    Args:
        request: BulkDeleteRequest containing list of session_ids

    Returns:
        BulkDeleteResponse with results per session and summary counts

    Example request:
        {
            "session_ids": ["a3f2e4d5-...", "b7c1f9e2-...", "d4a8e3f1-..."]
        }

    Example response:
        {
            "results": {
                "a3f2e4d5-...": "deleted",
                "b7c1f9e2-...": "deleted",
                "d4a8e3f1-...": "error: Session not found"
            },
            "deleted_count": 2,
            "failed_count": 1
        }
    """
    try:
        session_manager = SessionManager()

        logger.info(f"Bulk delete request for {len(request.session_ids)} sessions")

        # Delete sessions
        results = session_manager.delete_multiple_sessions(request.session_ids)

        # Count successes and failures
        deleted_count = sum(1 for status in results.values() if status == "deleted")
        failed_count = len(results) - deleted_count

        logger.info(f"Bulk delete completed: {deleted_count} deleted, {failed_count} failed")

        return BulkDeleteResponse(
            results=results,
            deleted_count=deleted_count,
            failed_count=failed_count
        )

    except Exception as e:
        logger.error(f"Error in bulk delete: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete sessions: {str(e)}"
        )
