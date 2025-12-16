# GEMSCAP Quant Project - Startup Script
# Run this to start all components

Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  GEMSCAP QUANT PROJECT - STARTUP SCRIPT" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Redis is running
Write-Host "🔍 Checking Redis..." -ForegroundColor Yellow
$redisRunning = Get-Process redis-server -ErrorAction SilentlyContinue

if (-not $redisRunning) {
    Write-Host "❌ Redis is not running!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please start Redis in a separate terminal:" -ForegroundColor Yellow
    Write-Host "  redis-server" -ForegroundColor White
    Write-Host ""
    Write-Host "Or install Redis:" -ForegroundColor Yellow
    Write-Host "  choco install redis (Windows with Chocolatey)" -ForegroundColor White
    Write-Host "  Or download from: https://redis.io/download" -ForegroundColor White
    Write-Host ""
    $continue = Read-Host "Continue anyway? (y/n)"
    if ($continue -ne "y") {
        exit
    }
}
else {
    Write-Host "✅ Redis is running" -ForegroundColor Green
}

# Check virtual environment
Write-Host ""
Write-Host "🔍 Checking virtual environment..." -ForegroundColor Yellow

if (-not (Test-Path ".venv")) {
    Write-Host "❌ Virtual environment not found!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    .\.venv\Scripts\activate
    pip install -r requirements.txt
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "✅ Virtual environment exists" -ForegroundColor Green
}

# Activate virtual environment
Write-Host ""
Write-Host "🔌 Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\activate

# Start backend
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  STARTING BACKEND (FastAPI)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "API will be available at: http://localhost:8000" -ForegroundColor Green
Write-Host "API Docs: http://localhost:8000/docs" -ForegroundColor Green
Write-Host ""
Write-Host "Starting in 3 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start backend in new terminal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\activate; python app.py"

Write-Host ""
Write-Host "✅ Backend started in new terminal" -ForegroundColor Green

# Wait for backend to initialize
Write-Host ""
Write-Host "⏳ Waiting for backend to initialize (10 seconds)..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Start dashboard
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  STARTING DASHBOARD (Streamlit)" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Dashboard will be available at: http://localhost:8501" -ForegroundColor Green
Write-Host ""
Write-Host "Starting in 3 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start dashboard in new terminal
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; .\.venv\Scripts\activate; streamlit run streamlit_app.py"

Write-Host ""
Write-Host "✅ Dashboard started in new terminal" -ForegroundColor Green

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  🎉 ALL SYSTEMS STARTED!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📡 API: http://localhost:8000" -ForegroundColor White
Write-Host "📊 Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "📚 API Docs: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "⏰ Wait 30-60 seconds for data collection" -ForegroundColor Yellow
Write-Host ""
Write-Host "To stop: Close the terminal windows or press Ctrl+C" -ForegroundColor White
Write-Host ""
Write-Host "Press any key to exit this startup script..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
