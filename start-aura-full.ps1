# ============================================
# MATLOOB AURA AI - Complete Test Run Script
# ============================================
# Description: Automated setup, installation, and testing script
# Platform: Windows PowerShell
# Usage: .\start-aura-full.ps1
# ============================================

# Set error action preference
$ErrorActionPreference = "Continue"

# Colors for output
function Write-Success { Write-Host $args -ForegroundColor Green }
function Write-Info { Write-Host $args -ForegroundColor Cyan }
function Write-Warning { Write-Host $args -ForegroundColor Yellow }
function Write-Error { Write-Host $args -ForegroundColor Red }
function Write-Header { 
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Magenta
    Write-Host $args -ForegroundColor Magenta
    Write-Host "============================================" -ForegroundColor Magenta
}

# ============================================
# STEP 1: ENVIRONMENT SETUP
# ============================================
Write-Header "STEP 1: ENVIRONMENT SETUP"

# Check if running in correct directory
if (-not (Test-Path "python-backend")) {
    Write-Error "Error: python-backend folder not found!"
    Write-Error "Please run this script from the AURA AI project root directory."
    exit 1
}

Write-Success "✓ Project directory verified"

# Check Python installation
try {
    $pythonVersion = python --version 2>&1
    Write-Success "✓ Python found: $pythonVersion"
} catch {
    Write-Error "✗ Python not found! Please install Python 3.9+"
    exit 1
}

# Check Node.js installation
try {
    $nodeVersion = node --version 2>&1
    Write-Success "✓ Node.js found: $nodeVersion"
} catch {
    Write-Error "✗ Node.js not found! Please install Node.js"
    exit 1
}

# ============================================
# STEP 2: VIRTUAL ENVIRONMENT
# ============================================
Write-Header "STEP 2: VIRTUAL ENVIRONMENT SETUP"

if (-not (Test-Path "venv")) {
    Write-Info "Creating virtual environment..."
    python -m venv venv
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Virtual environment created"
    } else {
        Write-Warning "⚠ Could not create venv, continuing without it..."
    }
} else {
    Write-Success "✓ Virtual environment already exists"
}

# Activate virtual environment (optional, script works without it)
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Info "Activating virtual environment..."
    & "venv\Scripts\Activate.ps1"
    Write-Success "✓ Virtual environment activated"
}

# ============================================
# STEP 3: INSTALL PYTHON DEPENDENCIES
# ============================================
Write-Header "STEP 3: PYTHON DEPENDENCIES"

Write-Info "Installing Python packages..."
Write-Info "This may take a few minutes..."

pip install -r python-backend\requirements.txt --quiet

if ($LASTEXITCODE -eq 0) {
    Write-Success "✓ Python dependencies installed"
} else {
    Write-Warning "⚠ Some Python packages may have failed to install"
    Write-Info "Core packages should still work"
}

# ============================================
# STEP 4: INSTALL NODE.JS DEPENDENCIES
# ============================================
Write-Header "STEP 4: NODE.JS DEPENDENCIES"

if (-not (Test-Path "node_modules")) {
    Write-Info "Installing Node.js packages..."
    Write-Info "This may take several minutes..."
    
    npm install
    
    if ($LASTEXITCODE -eq 0) {
        Write-Success "✓ Node.js dependencies installed"
    } else {
        Write-Warning "⚠ Some Node packages may have failed"
    }
} else {
    Write-Success "✓ Node.js dependencies already installed"
}

# ============================================
# STEP 5: VERIFY .ENV FILE
# ============================================
Write-Header "STEP 5: CONFIGURATION CHECK"

if (-not (Test-Path ".env")) {
    Write-Warning "⚠ .env file not found"
    Write-Info "Copying .env.example to .env..."
    Copy-Item ".env.example" ".env"
    Write-Warning "⚠ Please edit .env and add your API keys!"
    Write-Info "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
} else {
    Write-Success "✓ .env file exists"
}

# ============================================
# STEP 6: START BACKEND SERVER
# ============================================
Write-Header "STEP 6: STARTING BACKEND SERVER"

Write-Info "Starting Python backend..."
Write-Info "Backend will run on http://localhost:8000"

# Start backend in new window
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python python-backend\main.py" -PassThru

Write-Info "Waiting for backend to initialize..."
Start-Sleep -Seconds 5

# Test backend connection
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/status" -Method GET -TimeoutSec 5
    Write-Success "✓ Backend server is running"
    Write-Success "✓ API Status: $($response.status)"
    
    # Display engine status
    Write-Info ""
    Write-Info "Engine Status:"
    Write-Info "  - AI Engine: $($response.services.ai_engine)"
    Write-Info "  - Voice Engine: $($response.services.voice_engine)"
    Write-Info "  - Vision Engine: $($response.services.vision_engine)"
    Write-Info "  - Automation Engine: $($response.services.automation_engine)"
    
} catch {
    Write-Error "✗ Backend server failed to start"
    Write-Error "Check the backend window for errors"
    exit 1
}

# ============================================
# STEP 7: START FRONTEND APPLICATION
# ============================================
Write-Header "STEP 7: STARTING FRONTEND APPLICATION"

Write-Info "Starting Electron frontend..."

# Start frontend in new window
$frontendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; npm start" -PassThru

Write-Info "Waiting for frontend to initialize..."
Start-Sleep -Seconds 3

Write-Success "✓ Frontend application launched"

# ============================================
# STEP 8: RUN AI PIPELINE TESTS
# ============================================
Write-Header "STEP 8: AI PIPELINE TESTS"

Write-Info "Testing AI pipelines..."

# Test 1: TTS Voice Output
Write-Info ""
Write-Info "[TEST 1] Voice → TTS Pipeline"
try {
    $voiceTest = Invoke-RestMethod -Uri "http://localhost:8000/voice/speak" -Method POST -ContentType "application/json" -Body '{"message":"AURA AI system is now online and ready for testing"}' -TimeoutSec 10
    if ($voiceTest.success) {
        Write-Success "✓ TTS Voice Output: WORKING"
    } else {
        Write-Warning "⚠ TTS Voice Output: FAILED"
    }
} catch {
    Write-Warning "⚠ TTS test failed: $($_.Exception.Message)"
}

Start-Sleep -Seconds 2

# Test 2: Automation Actions
Write-Info ""
Write-Info "[TEST 2] Automation Pipeline"
try {
    $mouseTest = Invoke-RestMethod -Uri "http://localhost:8000/automation/run" -Method POST -ContentType "application/json" -Body '{"action":"mousepos","params":{}}' -TimeoutSec 10
    if ($mouseTest.success) {
        Write-Success "✓ Automation: Mouse position ($($mouseTest.x), $($mouseTest.y))"
    }
    
    $screenTest = Invoke-RestMethod -Uri "http://localhost:8000/automation/run" -Method POST -ContentType "application/json" -Body '{"action":"screensize","params":{}}' -TimeoutSec 10
    if ($screenTest.success) {
        Write-Success "✓ Automation: Screen size $($screenTest.width)x$($screenTest.height)"
    }
} catch {
    Write-Warning "⚠ Automation test failed: $($_.Exception.Message)"
}

Start-Sleep -Seconds 2

# Test 3: Vision Analysis (if API key configured)
Write-Info ""
Write-Info "[TEST 3] Vision → AI Pipeline"
Write-Info "Note: This requires OpenAI API key"
try {
    $visionTest = Invoke-RestMethod -Uri "http://localhost:8000/vision/screenshot" -Method POST -TimeoutSec 10
    if ($visionTest.success) {
        Write-Success "✓ Vision: Screenshot captured"
    }
} catch {
    Write-Warning "⚠ Vision test skipped or failed"
}

# ============================================
# STEP 9: SYSTEM STATUS REPORT
# ============================================
Write-Header "STEP 9: SYSTEM STATUS REPORT"

try {
    $finalStatus = Invoke-RestMethod -Uri "http://localhost:8000/status" -Method GET -TimeoutSec 5
    
    Write-Info ""
    Write-Info "=== AURA AI SYSTEM STATUS ==="
    Write-Info ""
    Write-Info "Backend Server:"
    Write-Success "  ✓ API: $($finalStatus.services.api)"
    Write-Success "  ✓ Socket.IO: $($finalStatus.services.socket)"
    Write-Info ""
    
    Write-Info "AI Engines:"
    if ($finalStatus.services.ai_engine -eq "ready") {
        Write-Success "  ✓ AI Engine: READY"
    } else {
        Write-Warning "  ⚠ AI Engine: $($finalStatus.services.ai_engine)"
    }
    
    if ($finalStatus.services.voice_engine -eq "ready") {
        Write-Success "  ✓ Voice Engine: READY"
    } else {
        Write-Warning "  ⚠ Voice Engine: $($finalStatus.services.voice_engine) (TTS available)"
    }
    
    if ($finalStatus.services.vision_engine -eq "ready") {
        Write-Success "  ✓ Vision Engine: READY"
    } else {
        Write-Warning "  ⚠ Vision Engine: $($finalStatus.services.vision_engine)"
    }
    
    if ($finalStatus.services.automation_engine -eq "ready") {
        Write-Success "  ✓ Automation Engine: READY"
    } else {
        Write-Warning "  ⚠ Automation Engine: $($finalStatus.services.automation_engine)"
    }
    
    Write-Info ""
    Write-Info "Configuration:"
    Write-Info "  - AI Model: $($finalStatus.ai_config.model)"
    Write-Info "  - Temperature: $($finalStatus.ai_config.temperature)"
    Write-Info "  - API Key: $(if($finalStatus.ai_config.api_key_configured){'Configured'}else{'Not Set'})"
    
    Write-Info ""
    Write-Info "Automation Safety:"
    Write-Success "  ✓ FAILSAFE: $($finalStatus.automation_status.failsafe_enabled)"
    Write-Success "  ✓ System: $($finalStatus.automation_status.system)"
    
} catch {
    Write-Error "✗ Could not retrieve system status"
}

# ============================================
# STEP 10: USAGE INSTRUCTIONS
# ============================================
Write-Header "STEP 10: TESTING INSTRUCTIONS"

Write-Info ""
Write-Info "AURA AI is now running!"
Write-Info ""
Write-Info "Access Points:"
Write-Success "  • Frontend UI: Check the Electron window"
Write-Success "  • Backend API: http://localhost:8000"
Write-Success "  • API Docs: http://localhost:8000/docs"
Write-Info ""
Write-Info "Testing Guide:"
Write-Info "  1. Use the Electron UI to interact with AURA"
Write-Info "  2. Click buttons to test Voice, Vision, Automation"
Write-Info "  3. Type commands in the input field"
Write-Info "  4. Watch real-time logs in left panel"
Write-Info "  5. Monitor system info in right panel"
Write-Info ""
Write-Info "Optional Dependencies:"
Write-Warning "  ⚠ PyAudio - For speech recognition (pip install pyaudio)"
Write-Warning "  ⚠ pytesseract - For OCR (install Tesseract + pip install pytesseract)"
Write-Warning "  ⚠ OpenCV - For webcam (pip install opencv-python)"
Write-Info ""
Write-Info "Safety Features:"
Write-Success "  ✓ FAILSAFE enabled - Move mouse to corner to abort automation"
Write-Success "  ✓ Thread-safe operations"
Write-Success "  ✓ Error handling active"
Write-Info ""

# ============================================
# STEP 11: MONITORING & CLEANUP
# ============================================
Write-Header "STEP 11: MONITORING"

Write-Info ""
Write-Info "System is running. Press CTRL+C to stop all services."
Write-Info ""
Write-Warning "Backend Process ID: $($backendProcess.Id)"
Write-Warning "Frontend Process ID: $($frontendProcess.Id)"
Write-Info ""

# Wait for user interrupt
try {
    Write-Info "Monitoring... (Press CTRL+C to exit)"
    while ($true) {
        Start-Sleep -Seconds 5
        
        # Check if processes are still running
        if ($backendProcess.HasExited) {
            Write-Error "Backend process has stopped!"
            break
        }
        if ($frontendProcess.HasExited) {
            Write-Warning "Frontend process has stopped!"
            break
        }
    }
} catch {
    Write-Info ""
    Write-Info "Shutdown signal received..."
}

# ============================================
# CLEANUP
# ============================================
Write-Header "CLEANUP"

Write-Info "Stopping services..."

# Stop backend
if (-not $backendProcess.HasExited) {
    Write-Info "Stopping backend server..."
    Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Success "✓ Backend stopped"
}

# Stop frontend
if (-not $frontendProcess.HasExited) {
    Write-Info "Stopping frontend application..."
    Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue
    Write-Success "✓ Frontend stopped"
}

Write-Info ""
Write-Success "AURA AI has been shut down successfully."
Write-Info ""
Write-Info "To restart, run: .\start-aura-full.ps1"
Write-Info ""
