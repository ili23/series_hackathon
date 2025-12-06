# How to Run the Application

## ✅ Setup Complete!

The `pyvenv.cfg` file has been created and fixed. Your virtual environment is ready.

## Steps to Run

### 1. Activate Virtual Environment

**PowerShell:**
```powershell
.\vnv\Scripts\Activate.ps1
```

**Command Prompt:**
```cmd
vnv\Scripts\activate.bat
```

You should see `(vnv)` in your prompt.

### 2. Install Dependencies (if needed)

```powershell
# Check if whisper is installed
python -c "import whisper; print('OK')"

# If error, install it:
pip install openai-whisper

# Install all dependencies
pip install -r requirements.txt
```

### 3. Run the Application

```powershell
python backend/app.py
```

## What You'll See

When the app starts successfully:

```
INFO - Database initialized at ...
INFO - Kafka initialization complete
 * Running on http://0.0.0.0:5000
Press CTRL+C to quit
```

## Quick Test

Once running, you can test the health endpoint:
- Open browser: http://localhost:5000
- Or use: `curl http://localhost:5000`

## Troubleshooting

### "No module named 'whisper'"
```powershell
pip install openai-whisper
```

### "No module named 'flask'"
```powershell
pip install -r requirements.txt
```

### Virtual environment issues
If you still have issues, recreate the venv:
```powershell
Remove-Item -Recurse -Force vnv
python -m venv vnv
.\vnv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Current Status

✅ Virtual environment exists (`vnv/`)  
✅ `pyvenv.cfg` file created  
✅ Dependencies listed in `requirements.txt`  

## Next: Run It!

```powershell
# 1. Activate
.\vnv\Scripts\Activate.ps1

# 2. Run
python backend/app.py
```

