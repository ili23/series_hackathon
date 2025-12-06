# 🚀 Start Here - Run the Application

## ✅ Virtual Environment Fixed!

The `pyvenv.cfg` file has been created. Your virtual environment is now properly configured.

## Quick Start

### 1. Activate Virtual Environment

**PowerShell:**
```powershell
.\vnv\Scripts\Activate.ps1
```

**Command Prompt (CMD):**
```cmd
vnv\Scripts\activate.bat
```

You should see `(vnv)` in your prompt, indicating the virtual environment is active.

### 2. Verify Dependencies

Check if all required packages are installed:

```powershell
python -c "import flask; print('✓ Flask')"
python -c "import whisper; print('✓ Whisper')"
python -c "import sqlalchemy; print('✓ SQLAlchemy')"
python -c "import kafka; print('✓ Kafka')"
python -c "import requests; print('✓ Requests')"
```

### 3. Install Missing Packages (if needed)

If any package is missing:

```powershell
pip install openai-whisper  # If whisper is missing
pip install -r requirements.txt  # Install all dependencies
```

### 4. Run the Application

```powershell
python backend/app.py
```

## Expected Output

When the application starts successfully, you should see:

```
INFO - Database initialized at ...
INFO - Kafka initialization complete
 * Running on http://0.0.0.0:5000
```

## Troubleshooting

### "No module named 'whisper'"
```powershell
pip install openai-whisper
```

### "No module named 'flask'"
```powershell
pip install -r requirements.txt
```

### Virtual environment not activating
- Make sure you're in the project root: `C:\Users\YongY\OneDrive\Desktop\series_hackathon`
- Try: `.\vnv\Scripts\Activate.ps1`

### Execution Policy Error (PowerShell)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

## What the Application Does

1. **Listens to Kafka** for incoming iMessage events
2. **Processes voice messages** using local Whisper model
3. **Detects languages** from voice messages
4. **Saves to database** (User, Language, VoiceMessage tables)
5. **Matches users** who speak the same languages
6. **Creates group chats** via iMessage API

## Project Structure

```
series_hackathon/
├── backend/
│   ├── app.py              # ← Run this file
│   ├── voice_processor.py  # Whisper transcription
│   ├── event_handlers.py   # Kafka event processing
│   └── db/                 # Database models
├── vnv/                    # Virtual environment (activated)
├── parsing.db              # Database (created automatically)
└── requirements.txt        # Dependencies
```

## Next Steps

1. ✅ Virtual environment is fixed (`pyvenv.cfg` created)
2. Activate virtual environment
3. Install any missing dependencies
4. Run `python backend/app.py`
5. Send a voice message via iMessage to test!

## Need Help?

- Check `QUICK_START.md` for detailed setup instructions
- Check `RUN.md` for troubleshooting guide
- Run `.\setup_venv.ps1` to recreate virtual environment if needed

