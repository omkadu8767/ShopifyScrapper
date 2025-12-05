@echo off
echo ====================================
echo ShopifyScraper Setup Script
echo ====================================
echo.

echo [1/5] Installing root dependencies...
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install root dependencies
    pause
    exit /b 1
)
echo ✓ Root dependencies installed
echo.

echo [2/5] Installing backend dependencies...
cd backend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install backend dependencies
    cd ..
    pause
    exit /b 1
)
cd ..
echo ✓ Backend dependencies installed
echo.

echo [3/5] Installing frontend dependencies...
cd frontend
call npm install
if errorlevel 1 (
    echo ERROR: Failed to install frontend dependencies
    cd ..
    pause
    exit /b 1
)
cd ..
echo ✓ Frontend dependencies installed
echo.

echo [4/5] Installing Python dependencies...
python --version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Python not found in PATH
    echo Please install Python 3.8+ and add it to PATH
    echo Skipping Python dependencies...
) else (
    cd backend
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install Python dependencies
        cd ..
        pause
        exit /b 1
    )
    cd ..
    echo ✓ Python dependencies installed
)
echo.

echo [5/5] Installing Playwright browsers...
cd backend
python -m playwright install chromium
if errorlevel 1 (
    echo WARNING: Failed to install Playwright browsers
    echo You may need to run this manually later
) else (
    echo ✓ Playwright browsers installed
)
cd ..
echo.

echo ====================================
echo ✓ Setup Complete!
echo ====================================
echo.
echo Next steps:
echo 1. Configure your .env file with API keys
echo 2. Run: npm run dev
echo.
pause
