@echo off
echo Starting VoiceLibra setup...

REM Create venv if it doesn't exist
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    call venv\Scripts\activate.bat
)

REM Clear log file
echo. > debug.log
echo Log file cleared.

REM Check for required directories
if not exist data (
    mkdir data
    echo Created data directory.
)

REM Run the main application
echo Starting VoiceLibra application...
python main.py

REM Display log output
echo Execution completed. Log file contents:
echo -----------------------------------
powershell -command "Get-Content debug.log -Tail 20"
echo -----------------------------------

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

echo VoiceLibra execution finished.
pause