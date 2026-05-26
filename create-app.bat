@echo off
REM Creer l'application Databricks Apps manuellement

echo Creation de l'application wind-analytics-dev...

C:\WINDOWS\databricks.exe apps create wind-analytics-dev ^
    --description "Système d'analyse SCADA pour parcs éoliens - dev" ^
    --source-code-path /Workspace/Users/gottfried.jacquet@socotec.com/wind-analytics-dev

if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec de creation
    pause
    exit /b 1
)

echo.
echo ========================================
echo Application creee avec succes!
echo ========================================
echo.
echo Maintenant lancez: deploy-app.bat
echo.
pause
