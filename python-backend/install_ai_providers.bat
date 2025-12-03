@echo off
REM AURA AI - Install Multi-Provider Dependencies

echo ====================================================================
echo   AURA AI - Installing Multi-Provider Dependencies
echo ====================================================================
echo.

REM Check if virtual environment exists
if exist "..\venv\Scripts\activate.bat" (
    echo [1/4] Activating virtual environment...
    call ..\venv\Scripts\activate.bat
) else (
    echo [!] Virtual environment not found. Creating one...
    python -m venv ..\venv
    call ..\venv\Scripts\activate.bat
)

echo [2/4] Upgrading pip...
python -m pip install --upgrade pip

echo [3/4] Installing AI provider dependencies...
pip install cohere>=5.11.0
pip install google-generativeai>=0.8.0
pip install requests>=2.31.0

echo [4/4] Verifying installation...
python -c "import cohere; print('✓ Cohere installed')"
python -c "import google.generativeai; print('✓ Google Generative AI installed')"
python -c "import requests; print('✓ Requests installed')"

echo.
echo ====================================================================
echo   Installation Complete!
echo ====================================================================
echo.
echo Next steps:
echo 1. Add API keys to .env file (see .env.example)
echo 2. Run tests: python test_ai_fallback.py
echo 3. Start AURA: ..\start-aura-production.ps1
echo.
pause
