# Quick Start Guide

## Setup and Run Instructions

### Step 1: Activate Virtual Environment

**PowerShell:**
```powershell
.\vnv\Scripts\Activate.ps1
```

**Command Prompt (CMD):**
```cmd
vnv\Scripts\activate.bat
```

**Note:** If you get an execution policy error in PowerShell:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Step 2: Install Missing Dependencies

Check if `openai-whisper` is installed:
```powershell
python -c "import whisper; print('OK')"
```

If you get an error, install it:
```powershell
pip install openai-whisper
```

Install all dependencies:
```powershell
pip install -r requirements.txt
```

### Step 3: Run the Application

```powershell
python backend/app.py
```

## If Virtual Environment is Missing pyvenv.cfg

The `pyvenv.cfg` file is created automatically when you create a virtual environment. If it's missing, you can:

### Option A: Recreate Virtual Environment

```powershell
# Remove old virtual environment
Remove-Item -Recurse -Force vnv

# Create new one
python -m venv vnv

# Activate it
.\vnv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Option B: Use Setup Script

**PowerShell:**
```powershell
.\setup_venv.ps1
```

**Command Prompt:**
```cmd
setup_venv.bat
```

## Verify Installation

Run these commands to verify everything is installed:

```powershell
python -c "import flask; print('✓ Flask')"
python -c "import whisper; print('✓ Whisper')"
python -c "import sqlalchemy; print('✓ SQLAlchemy')"
python -c "import kafka; print('✓ Kafka')"
python -c "import requests; print('✓ Requests')"
```

## Expected Output When Running

When you run `python backend/app.py`, you should see:

```
INFO - Database initialized at ...
INFO - Kafka initialization complete
 * Running on http://0.0.0.0:5000
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'whisper'"
```powershell
pip install openai-whisper
```

### "ModuleNotFoundError: No module named 'flask'"
```powershell
pip install -r requirements.txt
```

### Virtual environment not activating
- Make sure you're in the project root directory
- Check that `vnv\Scripts\Activate.ps1` exists
- Try recreating the virtual environment

### Database errors
- The database will be created automatically at `parsing.db` in the project root
- Make sure you have write permissions

## Full Setup (First Time)

If starting fresh:

1. **Create virtual environment:**
   ```powershell
   python -m venv vnv
   ```

2. **Activate it:**
   ```powershell
   .\vnv\Scripts\Activate.ps1
   ```

3. **Install dependencies:**
   ```powershell
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Run the app:**
   ```powershell
   python backend/app.py
   ```

## Current Requirements

- Python 3.8+
- Flask 3.0.0
- kafka-python 2.3.0
- openai-whisper (local model)
- SQLAlchemy 2.0.25
- requests 2.31.0
- python-dotenv 1.0.0

