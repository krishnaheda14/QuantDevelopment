# GEMSCAP Quantitative Trading System - Setup Script
# Automated setup for Windows with Redis installation options

Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "GEMSCAP Quantitative Trading System - Setup" -ForegroundColor Cyan
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "[1/6] Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "Python 3\.([0-9]+)") {
    $minorVersion = [int]$matches[1]
    if ($minorVersion -ge 9) {
        Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Python 3.9+ required (found $pythonVersion)" -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "  ✗ Python not found or version check failed" -ForegroundColor Red
    exit 1
}

# Install Python dependencies
Write-Host ""
Write-Host "[2/6] Installing Python dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ✗ Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "  ✓ Dependencies installed" -ForegroundColor Green

# Check for Redis
Write-Host ""
Write-Host "[3/6] Checking Redis installation..." -ForegroundColor Yellow
$redisPath = Get-Command redis-server -ErrorAction SilentlyContinue

if ($null -eq $redisPath) {
    Write-Host "  ⚠ Redis not found" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Redis Installation Options:" -ForegroundColor Cyan
    Write-Host "  1) Install via Chocolatey (recommended)" -ForegroundColor White
    Write-Host "  2) Download from GitHub (manual)" -ForegroundColor White
    Write-Host "  3) Use in-memory fallback (no Redis)" -ForegroundColor White
    Write-Host ""
    $choice = Read-Host "Select option (1-3)"
    
    switch ($choice) {
        "1" {
            Write-Host "  Installing Chocolatey..." -ForegroundColor Yellow
            if (!(Get-Command choco -ErrorAction SilentlyContinue)) {
                Set-ExecutionPolicy Bypass -Scope Process -Force
                [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
                Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
            }
            Write-Host "  Installing Redis via Chocolatey..." -ForegroundColor Yellow
            choco install redis-64 -y
            Write-Host "  ✓ Redis installed" -ForegroundColor Green
            Write-Host "  ℹ You may need to restart your terminal" -ForegroundColor Cyan
        }
        "2" {
            Write-Host ""
            Write-Host "  Manual Installation:" -ForegroundColor Cyan
            Write-Host "  1. Download: https://github.com/microsoftarchive/redis/releases" -ForegroundColor White
            Write-Host "  2. Extract to C:\Redis" -ForegroundColor White
            Write-Host "  3. Add C:\Redis to PATH" -ForegroundColor White
            Write-Host "  4. Run redis-server.exe" -ForegroundColor White
            Write-Host ""
            Pause
        }
        "3" {
            Write-Host "  ℹ Running in fallback mode (in-memory only)" -ForegroundColor Cyan
            Write-Host "  ℹ Data persistence will be limited" -ForegroundColor Yellow
        }
        default {
            Write-Host "  ✗ Invalid choice" -ForegroundColor Red
            exit 1
        }
    }
} else {
    Write-Host "  ✓ Redis found at: $($redisPath.Source)" -ForegroundColor Green
}

# Test Redis connection
Write-Host ""
Write-Host "[4/6] Testing Redis connection..." -ForegroundColor Yellow
$redisRunning = $false
try {
    $connection = New-Object System.Net.Sockets.TcpClient
    $connection.Connect("localhost", 6379)
    $connection.Close()
    $redisRunning = $true
    Write-Host "  ✓ Redis is running on localhost:6379" -ForegroundColor Green
} catch {
    Write-Host "  ⚠ Redis is not running" -ForegroundColor Yellow
    Write-Host "  ℹ Start Redis with: redis-server" -ForegroundColor Cyan
    Write-Host "  ℹ Or the app will run in fallback mode" -ForegroundColor Cyan
}

# Create directories
Write-Host ""
Write-Host "[5/6] Creating directories..." -ForegroundColor Yellow
$directories = @("data", "logs", "backend\services", "backend\api")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Created $dir" -ForegroundColor Green
    }
}

# Run setup verification
Write-Host ""
Write-Host "[6/6] Running setup verification..." -ForegroundColor Yellow
python check_setup.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ⚠ Setup verification found issues" -ForegroundColor Yellow
    Write-Host "  ℹ You can still proceed, but functionality may be limited" -ForegroundColor Cyan
}

# Summary
Write-Host ""
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=======================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host ""
if (!$redisRunning) {
    Write-Host "  1. Start Redis:" -ForegroundColor White
    Write-Host "     redis-server" -ForegroundColor Gray
    Write-Host ""
}
Write-Host "  2. Start the backend:" -ForegroundColor White
Write-Host "     python start_backend.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. In a new terminal, start the frontend:" -ForegroundColor White
Write-Host "     python start_frontend.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  4. Open browser:" -ForegroundColor White
Write-Host "     Backend:  http://localhost:8000" -ForegroundColor Gray
Write-Host "     Frontend: http://localhost:8501" -ForegroundColor Gray
Write-Host ""
Write-Host "Or use the all-in-one launcher:" -ForegroundColor Cyan
Write-Host "  python run_all.py" -ForegroundColor Gray
Write-Host ""
