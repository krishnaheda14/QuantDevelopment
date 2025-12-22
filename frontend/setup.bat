@echo off
REM GEMSCAP Quant - Frontend Setup Script for Windows
REM This script will install and run the React frontend

echo ================================================
echo GEMSCAP Quant - Frontend Setup
echo ================================================
echo.

REM Check if Node.js is installed
where node >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Node.js is not installed!
    echo Please download and install Node.js 18+ from: https://nodejs.org/
    echo.
    pause
    exit /b 1
)

REM Display Node.js version
echo Node.js version:
node --version
echo.

REM Check if npm is installed
where npm >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: npm is not installed!
    echo Please ensure Node.js installation includes npm.
    echo.
    pause
    exit /b 1
)

REM Display npm version
echo npm version:
npm --version
echo.

REM Navigate to frontend directory
cd /d "%~dp0"
echo Current directory: %CD%
echo.

REM Check if package.json exists
if not exist "package.json" (
    echo ERROR: package.json not found!
    echo Please ensure you are in the frontend directory.
    echo.
    pause
    exit /b 1
)

REM Install dependencies
echo ================================================
echo Installing dependencies...
echo This may take a few minutes...
echo ================================================
echo.

npm install

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: npm install failed!
    echo Try running: npm cache clean --force
    echo Then run this script again.
    echo.
    pause
    exit /b 1
)

echo.
echo ================================================
echo Installation complete!
echo ================================================
echo.

REM Ask user if they want to start the dev server
echo Do you want to start the development server now? (Y/N)
set /p START_SERVER=

if /i "%START_SERVER%"=="Y" (
    echo.
    echo ================================================
    echo Starting development server...
    echo The app will open at http://localhost:3000
    echo.
    echo IMPORTANT:
    echo - Ensure Python backend is running on port 8000
    echo - Press Ctrl+C to stop the server
    echo ================================================
    echo.
    npm run dev
) else (
    echo.
    echo Setup complete! To start the server later, run:
    echo npm run dev
    echo.
)

pause
