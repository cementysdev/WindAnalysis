@echo off
REM Nettoyer le dossier experiments sur Databricks workspace

echo Suppression du dossier experiments sur Databricks...
C:\WINDOWS\databricks.exe workspace delete --recursive /Workspace/Users/gottfried.jacquet@socotec.com/wind-analytics-dev/experiments --profile dev

echo Done!
pause
