"""
Point d'entrée pour Databricks Apps.
Lance FastAPI avec configuration Databricks-native.
"""
import os
import sys
import uvicorn
from pathlib import Path

# Ajouter src/ au PYTHONPATH si nécessaire
project_root = Path(__file__).parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

def main():
    """Lance l'application FastAPI."""
    # Port injecté par Databricks Apps
    port = int(os.getenv("DATABRICKS_APP_PORT", "8000"))

    # Configuration uvicorn
    uvicorn.run(
        "wind_turbine_analytics.api.main:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
        access_log=True,
    )

if __name__ == "__main__":
    main()
