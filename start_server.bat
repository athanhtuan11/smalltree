@echo off
echo ==========================================
echo    🚀 KHOI DONG SERVER MAM NON - AI FARM
echo ==========================================
echo.

echo 🔧 Activating conda environment: flaskenv...
call conda activate flaskenv

echo.
echo 🌐 Starting Flask server...
echo 📍 Server URL: http://localhost:5000
echo 🤖 AI Dashboard: http://localhost:5000/ai-dashboard
echo.
echo ⚠️  Press Ctrl+C to stop server
echo ==========================================

python run.py

echo.
echo 🛑 Server stopped.
pause
