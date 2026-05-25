"""
Session Manager for Wind Turbine Analytics.

Manages temporary sessions for ZIP uploads, extracts files, and organizes outputs.
"""
import json
import os
import shutil
import uuid
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import UploadFile

from src.logger_config import get_logger

logger = get_logger(__name__)

# Volume path configuration (can be local or remote like Databricks Volumes)
VOLUME_BASE_PATH = os.getenv(
    "VOLUME_PATH",
    "tmp"  # Default to local tmp/ for backward compatibility
)


class SessionManager:
    """Manages session lifecycle for uploaded ZIP files and analysis results."""

    SESSIONS_ROOT = Path(VOLUME_BASE_PATH) / "sessions"
    CLI_SESSIONS_ROOT = Path(VOLUME_BASE_PATH) / "cli_sessions"

    def __init__(self):
        """Initialize SessionManager and ensure root directories exist."""
        self.SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)
        self.CLI_SESSIONS_ROOT.mkdir(parents=True, exist_ok=True)
        logger.debug(f"SessionManager initialized. Sessions root: {self.SESSIONS_ROOT}")

    def create_session(self, uploaded_file: UploadFile) -> str:
        """
        Create a new session from an uploaded ZIP file.

        Args:
            uploaded_file: FastAPI UploadFile containing the ZIP

        Returns:
            session_id (UUID string)

        Raises:
            ValueError: If ZIP is invalid or config.yml is missing
            Exception: If extraction fails
        """
        session_id = str(uuid.uuid4())
        session_path = self.get_session_path(session_id)
        uploaded_path = self.get_uploaded_path(session_id)

        logger.info(f"Creating session {session_id} from file: {uploaded_file.filename}")

        try:
            # Create session directory structure
            self._create_session_structure(session_id)

            # Save uploaded ZIP temporarily
            zip_temp_path = session_path / "temp.zip"
            with open(zip_temp_path, "wb") as f:
                f.write(uploaded_file.file.read())

            logger.debug(f"ZIP file saved to {zip_temp_path}")

            # Extract ZIP to uploaded/
            self._extract_zip(zip_temp_path, uploaded_path)

            # Validate config.yml exists
            self._validate_config_yml(uploaded_path)

            # Normalize paths in config.yml (experiments/ -> relative paths)
            self._normalize_config_paths(uploaded_path)

            # Remove temporary ZIP
            zip_temp_path.unlink()

            # Save initial metadata
            metadata = {
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "original_filename": uploaded_file.filename,
                "status": "created",
            }
            self.save_session_metadata(session_id, metadata)

            logger.info(f"Session {session_id} created successfully")
            return session_id

        except Exception as e:
            # Cleanup on failure
            if session_path.exists():
                shutil.rmtree(session_path, ignore_errors=True)
            logger.error(f"Failed to create session {session_id}: {e}")
            raise

    def create_cli_session(self, zip_path: Path) -> str:
        """
        Create a session for CLI usage from a ZIP file path.

        Args:
            zip_path: Path to the ZIP file

        Returns:
            session_id (timestamp_uuid format for traceability)

        Raises:
            ValueError: If ZIP is invalid or config.yml is missing
            FileNotFoundError: If zip_path doesn't exist
        """
        if not zip_path.exists():
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")

        # Generate CLI session ID with timestamp for easier debugging
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        session_id = f"{timestamp}_{unique_id}"

        # Use CLI sessions root
        session_path = self.CLI_SESSIONS_ROOT / session_id
        uploaded_path = session_path / "uploaded"

        logger.info(f"Creating CLI session {session_id} from: {zip_path}")

        try:
            # Create session directory structure
            session_path.mkdir(parents=True, exist_ok=True)
            (session_path / "charts").mkdir(exist_ok=True)
            (session_path / "tables").mkdir(exist_ok=True)
            (session_path / "reports").mkdir(exist_ok=True)
            uploaded_path.mkdir(exist_ok=True)

            # Extract ZIP
            self._extract_zip(zip_path, uploaded_path)

            # Validate config.yml
            self._validate_config_yml(uploaded_path)

            # Normalize paths in config.yml
            self._normalize_config_paths(uploaded_path)

            # Save metadata
            metadata = {
                "session_id": session_id,
                "created_at": datetime.utcnow().isoformat() + "Z",
                "original_filename": zip_path.name,
                "status": "created",
                "source": "cli",
            }

            metadata_file = session_path / "session_metadata.json"
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"CLI session {session_id} created successfully")
            return session_id

        except Exception as e:
            if session_path.exists():
                shutil.rmtree(session_path, ignore_errors=True)
            logger.error(f"Failed to create CLI session {session_id}: {e}")
            raise

    def get_session_path(self, session_id: str) -> Path:
        """Get the root path of a session."""
        # Check if it's a CLI session (contains underscore and timestamp pattern)
        if "_" in session_id and len(session_id.split("_")[0]) == 8:
            return self.CLI_SESSIONS_ROOT / session_id
        return self.SESSIONS_ROOT / session_id

    def get_uploaded_path(self, session_id: str) -> Path:
        """Get the path to uploaded files (extracted ZIP content)."""
        return self.get_session_path(session_id) / "uploaded"

    def get_charts_path(self, session_id: str) -> Path:
        """Get the path to charts directory."""
        return self.get_session_path(session_id) / "charts"

    def get_tables_path(self, session_id: str) -> Path:
        """Get the path to tables directory."""
        return self.get_session_path(session_id) / "tables"

    def get_reports_path(self, session_id: str) -> Path:
        """Get the path to reports directory."""
        return self.get_session_path(session_id) / "reports"

    def save_session_metadata(self, session_id: str, metadata: Dict) -> None:
        """
        Save session metadata to session_metadata.json.

        Args:
            session_id: Session identifier
            metadata: Dictionary of metadata to save
        """
        session_path = self.get_session_path(session_id)
        metadata_file = session_path / "session_metadata.json"

        # Load existing metadata if present
        existing_metadata = {}
        if metadata_file.exists():
            with open(metadata_file, "r", encoding="utf-8") as f:
                existing_metadata = json.load(f)

        # Merge with new metadata
        existing_metadata.update(metadata)

        # Save
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(existing_metadata, f, indent=2, ensure_ascii=False)

        logger.debug(f"Metadata saved for session {session_id}")

    def get_session_metadata(self, session_id: str) -> Dict:
        """
        Load session metadata from session_metadata.json.

        Args:
            session_id: Session identifier

        Returns:
            Dictionary of session metadata

        Raises:
            FileNotFoundError: If metadata file doesn't exist
        """
        session_path = self.get_session_path(session_id)
        metadata_file = session_path / "session_metadata.json"

        if not metadata_file.exists():
            raise FileNotFoundError(f"Metadata not found for session {session_id}")

        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        return metadata

    def list_sessions(self) -> List[Dict]:
        """
        List all sessions with their metadata.

        Returns:
            List of session metadata dictionaries
        """
        sessions = []

        # List API sessions
        if self.SESSIONS_ROOT.exists():
            for session_dir in self.SESSIONS_ROOT.iterdir():
                if session_dir.is_dir():
                    try:
                        metadata = self.get_session_metadata(session_dir.name)
                        sessions.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to load metadata for session {session_dir.name}: {e}")

        # List CLI sessions
        if self.CLI_SESSIONS_ROOT.exists():
            for session_dir in self.CLI_SESSIONS_ROOT.iterdir():
                if session_dir.is_dir():
                    try:
                        metadata = self.get_session_metadata(session_dir.name)
                        sessions.append(metadata)
                    except Exception as e:
                        logger.warning(f"Failed to load metadata for CLI session {session_dir.name}: {e}")

        # Sort by creation date (newest first)
        sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)

        logger.debug(f"Listed {len(sessions)} sessions")
        return sessions

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: Session identifier

        Returns:
            True if session directory exists, False otherwise
        """
        return self.get_session_path(session_id).exists()

    def delete_session(self, session_id: str) -> None:
        """
        Delete a session completely (directory and all contents).

        Args:
            session_id: Session identifier

        Raises:
            FileNotFoundError: If session doesn't exist
        """
        session_path = self.get_session_path(session_id)

        if not session_path.exists():
            raise FileNotFoundError(f"Session {session_id} not found")

        logger.info(f"Deleting session {session_id}")
        shutil.rmtree(session_path, ignore_errors=True)
        logger.info(f"Session {session_id} deleted successfully")

    def delete_multiple_sessions(self, session_ids: List[str]) -> Dict[str, str]:
        """
        Delete multiple sessions in batch.

        Args:
            session_ids: List of session identifiers

        Returns:
            Dictionary mapping session_id -> status ("deleted" or "error: <message>")
        """
        results = {}

        for session_id in session_ids:
            try:
                self.delete_session(session_id)
                results[session_id] = "deleted"
            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")
                results[session_id] = f"error: {str(e)}"

        success_count = sum(1 for v in results.values() if v == "deleted")
        logger.info(f"Bulk delete: {success_count}/{len(session_ids)} sessions deleted")

        return results

    # Private helper methods

    def _create_session_structure(self, session_id: str) -> None:
        """Create the directory structure for a new session."""
        session_path = self.get_session_path(session_id)

        session_path.mkdir(parents=True, exist_ok=True)
        (session_path / "uploaded").mkdir(exist_ok=True)
        (session_path / "charts").mkdir(exist_ok=True)
        (session_path / "tables").mkdir(exist_ok=True)
        (session_path / "reports").mkdir(exist_ok=True)

        logger.debug(f"Session structure created for {session_id}")

    def _extract_zip(self, zip_path: Path, destination: Path) -> None:
        """
        Extract a ZIP file to a destination directory.

        Args:
            zip_path: Path to the ZIP file
            destination: Destination directory

        Raises:
            ValueError: If file is not a valid ZIP
        """
        try:
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                # Log ZIP contents before extraction
                file_list = zip_ref.namelist()
                logger.info(f"ZIP contains {len(file_list)} files/folders")
                logger.debug(f"ZIP structure: {file_list[:10]}")  # Log first 10 entries

                zip_ref.extractall(destination)

            # Count extracted files
            extracted_files = list(destination.rglob("*"))
            file_count = sum(1 for f in extracted_files if f.is_file())
            logger.info(f"✅ Extracted {file_count} files from ZIP to {destination}")

            # Log directory structure for debugging
            if file_count == 0:
                logger.error(f"❌ No files extracted! ZIP was empty or structure invalid")
            else:
                csv_files = list(destination.rglob("*.csv"))
                logger.info(f"Found {len(csv_files)} CSV files after extraction")

        except zipfile.BadZipFile as e:
            raise ValueError(f"Invalid ZIP file: {e}")

    def _validate_config_yml(self, uploaded_path: Path) -> None:
        """
        Validate that config.yml exists in the uploaded files.

        Args:
            uploaded_path: Path to uploaded files directory

        Raises:
            ValueError: If config.yml is not found
        """
        # Search for config.yml in the uploaded directory (can be at root or in subdirectory)
        config_files = list(uploaded_path.rglob("config.yml"))

        if not config_files:
            raise ValueError(
                "config.yml not found in ZIP. "
                "Please ensure your ZIP contains a config.yml file."
            )

        logger.debug(f"config.yml found at: {config_files[0].relative_to(uploaded_path)}")

    def _normalize_config_paths(self, uploaded_path: Path) -> None:
        """
        Normalize file paths in config.yml to be relative to uploaded/ directory.

        Replaces patterns like:
        - .\\experiments\\scada_analyse\\DATA\\LU09\\file.csv
        - experiments/scada_analyse/DATA/LU09/file.csv
        - ./experiments/scada_analyse/DATA/LU09/file.csv

        With relative paths:
        - DATA/LU09/file.csv

        Args:
            uploaded_path: Path to uploaded files directory containing config.yml
        """
        import re
        import yaml

        # Find config.yml
        config_files = list(uploaded_path.rglob("config.yml"))
        if not config_files:
            logger.warning("No config.yml found for path normalization")
            return

        config_path = config_files[0]
        logger.info(f"Normalizing paths in {config_path}")

        try:
            # Read config.yml content as text
            with open(config_path, "r", encoding="utf-8") as f:
                content = f.read()

            original_content = content

            # Pattern 1: .\experiments\scada_analyse\ (Windows backslash)
            content = re.sub(
                r'[.]\\+experiments\\+[^\\]+\\+',
                '',
                content
            )

            # Pattern 2: ./experiments/scada_analyse/ (Unix forward slash)
            content = re.sub(
                r'\./experiments/[^/]+/',
                '',
                content
            )

            # Pattern 3: experiments/scada_analyse/ (no leading dot)
            content = re.sub(
                r'experiments/[^/]+/',
                '',
                content
            )

            # Pattern 4: experiments\scada_analyse\ (Windows, no leading dot)
            content = re.sub(
                r'experiments\\+[^\\]+\\+',
                '',
                content
            )

            # If changes were made, save the normalized config
            if content != original_content:
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(content)

                logger.info(f"✅ Config paths normalized in {config_path.name}")
                logger.debug(f"Removed 'experiments/...' prefixes from paths")
            else:
                logger.debug("No path normalization needed")

        except Exception as e:
            logger.error(f"Failed to normalize config paths: {e}")
            # Non-fatal: continue without normalization
