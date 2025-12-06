@echo off
REM Batch script to set up virtual environment and install dependencies
REM Run this from the project root directory

echo Setting up virtual environment...

REM Check if virtual environment exists
if exist "vnv" (
    echo Virtual environment 'vnv' already exists
    set /p recreate="Do you want to recreate it? (y/n): "
    if /i "%recreate%"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q vnv
    ) else (
        echo Using existing virtual environment
    )
)

REM Create virtual environment if it doesn't exist
if not exist "vnv" (
    echo Creating virtual environment...
    python -m venv vnv
    
    if errorlevel 1 (
        echo Error creating virtual environment!
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call vnv\Scripts\activate.bat

if errorlevel 1 (
    echo Error activating virtual environment!
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies from requirements.txt...
pip install -r requirements.txt

if errorlevel 1 (
    echo Error installing dependencies!
    exit /b 1
)

REM Verify key packages
echo.
echo Verifying installations...
python -c "import flask; print('✓ Flask installed')"
python -c "import kafka; print('✓ Kafka installed')"
python -c "import whisper; print('✓ Whisper installed')"
python -c "import sqlalchemy; print('✓ SQLAlchemy installed')"
python -c "import requests; print('✓ Requests installed')"

echo.
echo ✓ Setup complete!
echo.
echo To run the application:
echo   1. Activate virtual environment: vnv\Scripts\activate.bat
echo   2. Run: python backend/app.py

pause

