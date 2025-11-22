@echo off
echo Setting up Python 3.12 for this project...
echo.
echo Step 1: Download Python 3.12.7
echo Please download from: https://www.python.org/ftp/python/3.12.7/python-3.12.7-amd64.exe
echo.
echo Step 2: Run the installer
echo - IMPORTANT: Uncheck "Add to PATH"
echo - Choose "Install Now" or customize install location
echo.
echo Step 3: After installation, run this script again and press any key...
pause

echo.
echo Creating virtual environment with Python 3.12...
"C:\Users\%USERNAME%\AppData\Local\Programs\Python\Python312\python.exe" -m venv backend\venv

echo.
echo Activating virtual environment...
call backend\venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r backend\requirements.txt
python -m playwright install chromium

echo.
echo Setup complete! 
echo.
echo To use this environment:
echo 1. Run: backend\venv\Scripts\activate.bat
echo 2. Update .env file with: PYTHON_PATH=backend\venv\Scripts\python.exe
echo.
pause
