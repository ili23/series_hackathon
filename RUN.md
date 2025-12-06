# How to Run the Application

## Quick Start

### Option 1: Use Setup Script (Recommended)

**PowerShell:**
```powershell
.\setup_venv.ps1
```

**Command Prompt (CMD):**
```cmd
setup_venv.bat
```

### Option 2: Manual Setup

#### Step 1: Create/Activate Virtual Environment

**PowerShell:**
```powershell
# Create virtual environment (if it doesn't exist)
python -m venv vnv

# Activate it
.\vnv\Scripts\Activate.ps1
```

**Command Prompt (CMD):**
```cmd
# Create virtual environment (if it doesn't exist)
python -m venv vnv

# Activate it
vnv\Scripts\activate.bat
```

**Note:** If you get an execution policy error in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

#### Step 2: Install Dependencies

```powershell
# Make sure virtual environment is activated
# You should see (vnv) in your prompt

# Upgrade pip
python -m pip install --upgrade pip

# Install all dependencies
pip install -r requirements.txt
```

#### Step 3: Verify Installation

```powershell
python -c "import flask; print('Flask OK')"
python -c "import whisper; print('Whisper OK')"
python -c "import sqlalchemy; print('SQLAlchemy OK')"
python -c "import kafka; print('Kafka OK')"
```

#### Step 4: Run the Application

```powershell
# Make sure you're in the project root directory
# and virtual environment is activated

python backend/app.py
```

## Troubleshooting

### Issue: "No module named 'whisper'"

**Solution:** Install openai-whisper:
```powershell
pip install openai-whisper
```

### Issue: "No module named 'flask'"

**Solution:** Install dependencies:
```powershell
pip install -r requirements.txt
```

### Issue: Virtual environment not activating

**Solution:** 
- Make sure you're in the project root directory
- Try recreating the virtual environment:
  ```powershell
  Remove-Item -Recurse -Force vnv
  python -m venv vnv
  .\vnv\Scripts\Activate.ps1
  ```

### Issue: "pyvenv.cfg not found"

**Solution:** This file is created automatically when you create a venv. If it's missing, recreate the virtual environment:
```powershell
Remove-Item -Recurse -Force vnv
python -m venv vnv
```

### Issue: Permission errors

**Solution:** Run PowerShell/CMD as Administrator, or check file permissions.

## Running the Application

Once everything is set up:

1. **Activate virtual environment:**
   ```powershell
   .\vnv\Scripts\Activate.ps1
   ```

2. **Run the application:**
   ```powershell
   python backend/app.py
   ```

3. **You should see:**
   ```
   Database initialized at ...
   Kafka initialization complete
   * Running on http://0.0.0.0:5000
   ```

## Project Structure

```
series_hackathon/
├── backend/
│   ├── app.py              # Main application entry point
│   ├── config.py           # Configuration
│   ├── voice_processor.py  # Whisper transcription
│   ├── event_handlers.py   # Kafka event processing
│   └── db/                 # Database models and accessors
├── vnv/                    # Virtual environment
├── requirements.txt        # Python dependencies
└── setup_venv.ps1         # Setup script (PowerShell)
```

## Dependencies

- Flask 3.0.0
- kafka-python 2.3.0
- openai-whisper (local Whisper model)
- SQLAlchemy
- requests 2.31.0
- python-dotenv 1.0.0

## Notes

- The virtual environment is stored in the `vnv/` directory
- The database file (`parsing.db`) will be created automatically in the project root
- Whisper model will download automatically on first use (base model ~150MB)
- Make sure to activate the virtual environment before running the app

