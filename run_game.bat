::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAnk
::fBw5plQjdG8=
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCyDJGyX8VAjFAJBWgWOAES0A5EO4f7+086CsUYJW/IDaprVmrOPLeVd713hFQ==
::YB416Ek+ZG8=
::
::
::978f952a14a936cc963da21a135fa983
@echo off
echo Game Docker Launcher
echo ===================
echo.

REM Check if Docker is installed and running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo Docker is not running or not installed!
    echo Please make sure Docker Desktop is installed and running.
    echo.
    pause
    exit /b
)

REM Check if image exists, build if not
docker image inspect game-client >nul 2>&1
if %errorlevel% neq 0 (
    echo Building Docker image...
    docker build -t game-client .
    if %errorlevel% neq 0 (
        echo Failed to build Docker image!
        pause
        exit /b
    )
    echo Docker image built successfully!
) else (
    echo Docker image already exists.
)

echo.
echo Starting game client...
echo.
echo Make sure you have an X server (like VcXsrv) running if you're on Windows!
echo.

REM Run the Docker container
docker run -it --rm ^
    -e DISPLAY=host.docker.internal:0 ^
    -v "%CD%\map:/app/map" ^
    --network host ^
    game-client

pause