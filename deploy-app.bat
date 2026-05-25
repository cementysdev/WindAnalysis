@echo off
REM Script complet de deploiement Databricks Apps
REM Usage: deploy-app.bat

echo ========================================
echo  Deploiement Wind Turbine Analytics
echo ========================================
echo.

REM Configuration environnement
set DATABRICKS_CONFIG_PROFILE=dev
set MSYS_NO_PATHCONV=1

echo [1/4] Build du frontend React...
cd frontend
call npm run build
if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec du build frontend
    cd ..
    pause
    exit /b 1
)
cd ..

echo.
echo [2/4] Copie du frontend dans static_frontend...
rmdir /S /Q static_frontend 2>nul
mkdir static_frontend
xcopy /E /I /Y frontend\dist\* static_frontend\

echo.
echo [3/4] Synchronisation du code source...
C:\WINDOWS\databricks.exe sync . /Workspace/Users/gottfried.jacquet@socotec.com/wind-analytics-dev

if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec de la synchronisation
    pause
    exit /b 1
)

echo.
echo [4/4] Deploiement de l'application (2-3 minutes)...

REM Verifier si l'app existe, sinon la creer
C:\WINDOWS\databricks.exe apps get wind-analytics-dev >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo App inexistante, creation en cours...
    C:\WINDOWS\databricks.exe bundle deploy -t dev
    if %ERRORLEVEL% NEQ 0 (
        echo ERREUR: Echec de creation via bundle
        pause
        exit /b 1
    )
)

REM Deployer le code
C:\WINDOWS\databricks.exe apps deploy wind-analytics-dev --source-code-path /Workspace/Users/gottfried.jacquet@socotec.com/wind-analytics-dev

if %ERRORLEVEL% NEQ 0 (
    echo ERREUR: Echec du deploiement
    echo Consultez les logs sur: https://dbc-2bfbd02e-3e5e.cloud.databricks.com/apps/wind-analytics-dev
    pause
    exit /b 1
)

echo.
echo ========================================
echo  Deploiement termine avec succes !
echo ========================================
echo.
echo Accedez a votre app:
echo https://dbc-2bfbd02e-3e5e.cloud.databricks.com/apps/wind-analytics-dev
echo.
echo Note: L'app redemarre automatiquement apres le deploiement
echo Attendez 30 secondes avant d'acceder a l'interface
echo.
pause
