@echo off
REM Configuration d'environnement pour Databricks CLI
REM Usage: databricks-env.bat

set DATABRICKS_TF_EXEC_PATH=C:\Users\gjacquet\.databricks\bin\terraform.exe
set DATABRICKS_TF_VERSION=1.5.7
set DATABRICKS_CONFIG_PROFILE=dev
set PATH=C:\Users\gjacquet\.databricks\bin;%PATH%

echo Configuration Databricks CLI chargee
echo.
echo Commandes disponibles:
echo   databricks bundle validate --target dev
echo   databricks bundle deploy --target dev
echo   databricks apps list
