"""
Script to create pyvenv.cfg file for virtual environment
"""
import sys
import os

# Get Python executable path
python_exe = sys.executable
python_base = getattr(sys, '_base_executable', python_exe)

# Get Python version
python_version = sys.version.split()[0]

# Get the directory where Python is installed
if os.path.exists(python_base):
    python_home = os.path.dirname(os.path.dirname(python_base))
else:
    # Fallback: try to find Python installation
    python_home = os.path.dirname(os.path.dirname(python_exe))

# Create pyvenv.cfg content
cfg_content = f"""home = {python_home}
include-system-site-packages = false
version = {python_version}
"""

# Write to vnv/pyvenv.cfg
venv_cfg_path = os.path.join('vnv', 'pyvenv.cfg')
with open(venv_cfg_path, 'w') as f:
    f.write(cfg_content)

print(f"Created {venv_cfg_path}")
print(f"Python home: {python_home}")
print(f"Python version: {python_version}")

