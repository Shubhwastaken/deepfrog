@echo off
setlocal enabledelayedexpansion

echo [1/4] 🔍 Detecting Python...

:: Try py launcher first
py --version >nul 2>&1
if %errorlevel% == 0 (
    set PY_CMD=py -3.10
    echo Found Python Launcher (py)
) else (
    :: Try absolute paths found earlier
    if exist "C:\Users\Ankit\AppData\Local\Programs\Python\Python310\python.exe" (
        set PY_CMD="C:\Users\Ankit\AppData\Local\Programs\Python\Python310\python.exe"
        echo Found Python 3.10 at absolute path
    ) else if exist "C:\Users\Ankit\AppData\Local\Programs\Python\Python39\python.exe" (
        set PY_CMD="C:\Users\Ankit\AppData\Local\Programs\Python\Python39\python.exe"
        echo Found Python 3.9 at absolute path
    ) else (
        echo ❌ No usable Python found. Please install Python 3.10 from python.org
        exit /b 1
    )
)

echo [2/4] 🏗️ Creating Virtual Environments...

:: Backend venv
cd backend
%PY_CMD% -m venv .venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create backend venv. Python process may be blocked by system.
    exit /b 1
)
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
cd ..

:: Frontend venv
cd frontend
%PY_CMD% -m venv .venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create frontend venv.
    exit /b 1
)
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\pip.exe install -r requirements.txt
cd ..

echo [3/4] 🔑 Setting up Environment Variables...
if not exist .env (
    copy .env.example .env
    echo Created .env from template
)

echo [4/4] ✅ Setup Complete!
echo.
echo To run the project:
echo 1. Open Terminal A: cd backend; .\.venv\Scripts\activate; uvicorn app.main:app --reload
echo 2. Open Terminal B: cd frontend; .\.venv\Scripts\activate; python app.py
echo.
pause
