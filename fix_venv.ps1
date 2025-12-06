# Fix virtual environment - create pyvenv.cfg if missing
# Run this from the project root directory

Write-Host "Checking virtual environment..." -ForegroundColor Green

if (-not (Test-Path "vnv")) {
    Write-Host "Virtual environment 'vnv' does not exist. Creating it..." -ForegroundColor Yellow
    python -m venv vnv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error creating virtual environment!" -ForegroundColor Red
        exit 1
    }
}

# Check if pyvenv.cfg exists
if (-not (Test-Path "vnv\pyvenv.cfg")) {
    Write-Host "pyvenv.cfg is missing. Creating it..." -ForegroundColor Yellow
    
    # Get Python version
    $pythonVersion = python --version
    $pythonPath = (Get-Command python).Source
    
    # Create pyvenv.cfg
    $cfgContent = @"
home = $pythonPath
include-system-site-packages = false
version = $pythonVersion
"@
    
    $cfgContent | Out-File -FilePath "vnv\pyvenv.cfg" -Encoding ASCII -NoNewline
    
    Write-Host "Created pyvenv.cfg" -ForegroundColor Green
} else {
    Write-Host "pyvenv.cfg already exists" -ForegroundColor Green
}

# Activate and install dependencies
Write-Host "`nActivating virtual environment..." -ForegroundColor Green
& "vnv\Scripts\Activate.ps1"

Write-Host "Installing/updating dependencies..." -ForegroundColor Green
python -m pip install --upgrade pip
pip install -r requirements.txt

Write-Host "`n✓ Virtual environment is ready!" -ForegroundColor Green
Write-Host "`nTo run the application:" -ForegroundColor Cyan
Write-Host "  1. Activate: .\vnv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Run: python backend/app.py" -ForegroundColor White

