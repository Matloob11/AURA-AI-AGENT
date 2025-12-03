# AURA AI - Install Multi-Provider Dependencies
# This script installs the new AI provider dependencies

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 68) -ForegroundColor Cyan
Write-Host "  AURA AI - Installing Multi-Provider Dependencies" -ForegroundColor Yellow
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 68) -ForegroundColor Cyan
Write-Host ""

# Check if virtual environment exists
if (Test-Path "..\venv\Scripts\Activate.ps1") {
    Write-Host "[1/4] Activating virtual environment..." -ForegroundColor Green
    & "..\venv\Scripts\Activate.ps1"
} else {
    Write-Host "[!] Virtual environment not found. Creating one..." -ForegroundColor Yellow
    python -m venv ..\venv
    & "..\venv\Scripts\Activate.ps1"
}

Write-Host "[2/4] Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

Write-Host "[3/4] Installing AI provider dependencies..." -ForegroundColor Green
pip install cohere>=5.11.0
pip install google-generativeai>=0.8.0
pip install requests>=2.31.0

Write-Host "[4/4] Verifying installation..." -ForegroundColor Green
python -c "import cohere; print('✓ Cohere installed')"
python -c "import google.generativeai; print('✓ Google Generative AI installed')"
python -c "import requests; print('✓ Requests installed')"

Write-Host ""
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 68) -ForegroundColor Cyan
Write-Host "  Installation Complete!" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 68) -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Add API keys to .env file (see .env.example)" -ForegroundColor White
Write-Host "2. Run tests: python test_ai_fallback.py" -ForegroundColor White
Write-Host "3. Start AURA: ..\start-aura-production.ps1" -ForegroundColor White
Write-Host ""
