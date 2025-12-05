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

echo "[4/5] Installing Python dependencies..."
if ! command -v python3 &> /dev/null; then
    echo "WARNING: Python3 not found in PATH"
    echo "Please install Python 3.8+ and add it to PATH"
    echo "Skipping Python dependencies..."
else
    cd backend
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install Python dependencies"
        cd ..
        exit 1
    fi
    cd ..
    echo "✓ Python dependencies installed"
fi
echo ""

echo "[5/5] Installing Playwright browsers..."
cd backend
python3 -m playwright install chromium
if [ $? -ne 0 ]; then
    echo "WARNING: Failed to install Playwright browsers"
    echo "You may need to run this manually later"
else
    python3 -m playwright install-deps chromium 2>/dev/null || echo "Note: System dependencies may need manual installation"
    echo "✓ Playwright browsers installed"
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
