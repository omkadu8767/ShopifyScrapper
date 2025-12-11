#!/bin/bash

echo "===================================="
echo "ShopifyScraper Setup Script"
echo "===================================="
echo ""

echo "[1/5] Installing root dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install root dependencies"
    exit 1
fi
echo "✓ Root dependencies installed"
echo ""

echo "[2/5] Installing backend dependencies..."
cd backend
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install backend dependencies"
    cd ..
    exit 1
fi
cd ..
echo "✓ Backend dependencies installed"
echo ""

echo "[3/5] Installing frontend dependencies..."
cd frontend
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install frontend dependencies"
    cd ..
    exit 1
fi
cd ..
echo "✓ Frontend dependencies installed"
echo ""

echo "[4/5] Setting up Python virtual environment..."
if ! command -v python3 &> /dev/null; then
    echo "WARNING: Python3 not found in PATH"
    echo "Please install Python 3.8+ and add it to PATH"
    echo "Skipping Python setup..."
else
    cd backend
    
    echo "Creating Python virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        cd ..
        exit 1
    fi
    
    echo "Activating virtual environment..."
    source venv/bin/activate
    
    echo "Installing Python dependencies..."
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install Python dependencies"
        cd ..
        exit 1
    fi
    cd ..
    echo "✓ Python virtual environment created and dependencies installed"
fi
echo ""

echo "[5/5] Installing Playwright browsers..."
cd backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    python -m playwright install chromium
    if [ $? -ne 0 ]; then
        echo "WARNING: Failed to install Playwright browsers"
        echo "You may need to run this manually later"
    else
        python -m playwright install-deps chromium 2>/dev/null || echo "Note: System dependencies may need manual installation"
        echo "✓ Playwright browsers installed"
    fi
else
    echo "WARNING: Virtual environment not found, skipping Playwright"
fi
cd ..
echo ""

echo "===================================="
echo "✓ Setup Complete!"
echo "===================================="
echo ""
echo "Next steps:"
echo "1. Configure your .env file with API keys"
echo "2. Run: npm run dev"
echo ""
