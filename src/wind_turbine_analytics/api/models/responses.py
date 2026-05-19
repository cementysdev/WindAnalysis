"""
Pydantic response models for API endpoints.
"""
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel


class ChartData(BaseModel):
    """
    Representation of a Plotly chart.

    Attributes:
        name: Identifier of the chart (e.g., "power_curve_chart")
        plotly_json: Plotly JSON representation (dict with 'data' and 'layout' keys)
    """
    name: str
    plotly_json: Dict[str, Any]


class TableData(BaseModel):
    """
    Representation of a data table.

    Attributes:
        name: Identifier of the table (e.g., "summary_table")
        columns: List of column names
        rows: List of rows, each row is a dict mapping column name to value
    """
    name: str
    columns: List[str]
    rows: List[Dict[str, Any]]


class AnalyzeResponse(BaseModel):
    """
    Complete response for analysis endpoints.

    Attributes:
        status: Status of the analysis ("success" or "error")
        message: Human-readable description of the result
        charts: List of all generated charts
        tables: List of all generated tables
        report_path: Path to generated Word report (if render_template=True)
        metadata: Additional information (park name, turbines, dates, criteria)
    """
    status: Literal["success", "error"]
    message: str
    charts: List[ChartData]
    tables: List[TableData]
    report_path: Optional[str] = None
    metadata: Dict[str, Any]


class HealthResponse(BaseModel):
    """
    Health check response.

    Attributes:
        status: Status of the API ("healthy" or "unhealthy")
        version: API version
    """
    status: str
    version: str


class UploadResponse(BaseModel):
    """
    Response for ZIP upload endpoint.

    Attributes:
        session_id: Unique session identifier (UUID)
        original_filename: Name of the uploaded ZIP file
        workflow_type: Type of analysis workflow
        config_preview: Parsed config.yml content preview
        created_at: ISO 8601 timestamp of session creation
        message: Human-readable success message
    """
    session_id: str
    original_filename: str
    workflow_type: Literal["runtest", "scada"]
    config_preview: Dict[str, Any]
    created_at: str
    message: str


class SessionSummary(BaseModel):
    """
    Summary information for a session (used in listing).

    Attributes:
        session_id: Unique session identifier
        created_at: ISO 8601 timestamp
        workflow_type: Type of analysis workflow
        park_name: Name of the wind farm (if available)
        status: Session status (created, completed, error)
        charts_count: Number of charts generated
        tables_count: Number of tables generated
    """
    session_id: str
    created_at: str
    workflow_type: Literal["runtest", "scada"]
    park_name: Optional[str] = None
    status: str
    charts_count: int = 0
    tables_count: int = 0


class SessionDetail(BaseModel):
    """
    Detailed information for a specific session.

    Attributes:
        metadata: Complete session metadata
        charts: List of all charts generated in this session
        tables: List of all tables generated in this session
    """
    metadata: Dict[str, Any]
    charts: List[ChartData]
    tables: List[TableData]
