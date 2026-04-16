@echo off
setlocal

echo =====================================================
echo 🧠 DeepFrog Customs Brain - Local Mock Launch (v2)
echo =====================================================
echo.

echo [1/4] 🚀 Starting Redis Server...
:: Using cmd /c start cmd /k to ensure the window stays open even if it crashes
start "Redis Server" cmd /k "cd /D C:\Users\Ankit\OneDrive\Desktop\deepfrog\Redis && redis-server.exe"
timeout /t 5 /nobreak >nul

echo [2/4] 🚀 Starting FastAPI Backend...
cd backend
start "Backend API" .\.venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
cd ..

echo [3/4] 🚀 Starting Background Worker...
cd backend
start "AI Worker" .\.venv\Scripts\python.exe worker.py
cd ..

echo [4/4] 🚀 Starting Flask Frontend...
cd frontend
start "Frontend UI" .\.venv\Scripts\python.exe app.py
cd ..

echo.
echo =====================================================
echo ✅ ALL SERVICES STARTED!
echo =====================================================
echo.
echo 🌐 FRONTEND: http://localhost:3000
echo 🔌 BACKEND API: http://localhost:8000/docs
echo.
echo Please keep all 4 terminal windows open.
echo.
echo Check the Redis Server window:
echo It should say "Ready to accept connections"
echo =====================================================
echo.
pause
