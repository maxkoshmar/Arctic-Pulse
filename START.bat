@echo off
setlocal

echo Arctic Pulse startup
echo.

docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running.
    echo Start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/3] Starting containers...
docker compose -p arctic up -d
if errorlevel 1 (
    echo [ERROR] Failed to start containers.
    pause
    exit /b 1
)

echo [2/3] Waiting for PostgreSQL...
:wait_pg
docker exec arctic-postgres pg_isready -U arctic_user -d arctic_pulse >nul 2>&1
if errorlevel 1 (
    timeout /t 3 /nobreak >nul
    goto wait_pg
)
echo PostgreSQL is ready.

echo [3/3] Configuring Directus...
python setup_directus.py

echo.
echo Startup complete.
echo n8n: http://localhost:5678
echo Directus: http://localhost:8055
echo n8n login: make your account and use workflow json
echo Directus login: admin@arctic.ru / admin123
echo.
echo Opening...
start "" "frontend\home.html"
pause
