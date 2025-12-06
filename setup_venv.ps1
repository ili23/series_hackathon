# PowerShell script to set up virtual environment and install dependencies
# Run this from the project root directory

Write-Host "Setting up virtual environment..." -ForegroundColor Green

# Check if virtual environment exists
if (Test-Path "vnv") {
    Write-Host "Virtual environment 'vnv' already exists" -ForegroundColor Yellow
    $recreate = Read-Host "Do you want to recreate it? (y/n)"
    if ($recreate -eq "y" -or $recreate -eq "Y") {
        Write-Host "Removing existing virtual environment..." -ForegroundColor Yellow
        Remove-Item -Recurse -Force vnv
    } else {
        Write-Host "Using existing virtual environment" -ForegroundColor Green
    }
}

# Create virtual environment if it doesn't exist
if (-not (Test-Path "vnv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Green
    python -m venv vnv
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error creating virtual environment!" -ForegroundColor Red
        exit 1
    }
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Green
& "vnv\Scripts\Activate.ps1"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error activating virtual environment!" -ForegroundColor Red
    Write-Host "You may need to run: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser" -ForegroundColor Yellow
    exit 1
}

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Green
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Green
pip install -r requirements.txt

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error installing dependencies!" -ForegroundColor Red
    exit 1
}

# Verify key packages
Write-Host "`nVerifying installations..." -ForegroundColor Green
python -c "import flask; print('✓ Flask installed')"
python -c "import kafka; print('✓ Kafka installed')"
python -c "import whisper; print('✓ Whisper installed')"
python -c "import sqlalchemy; print('✓ SQLAlchemy installed')"
python -c "import requests; print('✓ Requests installed')"

Write-Host "`n✓ Setup complete!" -ForegroundColor Green
Write-Host "`nTo run the application:" -ForegroundColor Cyan
Write-Host "  1. Activate virtual environment: .\vnv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  2. Run: python backend/app.py" -ForegroundColor White

