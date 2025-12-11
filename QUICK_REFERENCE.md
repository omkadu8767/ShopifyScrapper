# 🚀 Quick Reference - ShopifyScraper

## First Time Setup

```bash
# 1. Extract the ZIP
# 2. Open terminal in the project folder
# 3. Run:
npm run setup

# Wait for completion (3-5 minutes)
```

## Start Application

```bash
npm run dev
```

Opens:
- Backend: http://localhost:5000
- Frontend: http://localhost:3000

## Verify Python Setup

```bash
node backend/test_python.js
```

Should show:
```
✅ Using venv Python: .../backend/venv/Scripts/python.exe
✅ Python version: Python 3.12.x
✅ playwright
✅ beautifulsoup4
✅ lxml
✅ requests
```

## Fix Python Issues

If you see `ModuleNotFoundError`:

```bash
# Delete venv and reinstall
cd backend
rmdir /s /q venv  # Windows
rm -rf venv       # Linux/Mac

# Go back and run setup
cd ..
npm run setup
```

## Configuration

Edit `.env` file in root folder:

```env
# Required:
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxx
OPENAI_API_KEY=sk-proj-xxxxx
CAPSOLVER_API_KEY=CAP-xxxxx

# Optional (already set):
PRICE_MARKUP_PERCENTAGE=6.0
HEADLESS_BROWSER=true
TARGET_LANGUAGE=ro
```

## Common Issues

### ❌ "Python not found"
- Windows: Install Python from python.org and check "Add to PATH"
- Linux: `sudo apt install python3 python3-pip`

### ❌ "Port already in use"
Close other apps using port 3000 or 5000:
```bash
# Windows:
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :3000
kill -9 <PID>
```

### ❌ "ModuleNotFoundError: No module named 'playwright'"
Run: `node backend/test_python.js` to diagnose

### ❌ "CAPTCHA not solving"
1. Check CapSolver credits: https://dashboard.capsolver.com/
2. Set `HEADLESS_BROWSER=false` in `.env` for testing

## Folder Structure

```
project/
├── backend/
│   ├── venv/              ← Python virtual environment (auto-created)
│   ├── scrapers/
│   │   └── scraper_1688.py
│   ├── routes/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   └── package.json
├── .env                   ← Configuration (edit this)
├── setup.bat              ← Windows setup
├── setup.sh               ← Linux/Mac setup
└── package.json
```

## Important Files

- `.env` - All configuration (API keys, settings)
- `SETUP_INSTRUCTIONS.md` - Detailed setup guide
- `PYTHON_VENV_FIX.md` - Fix Python/venv issues
- `backend/test_python.js` - Test Python detection

## Workflow

1. **Start app**: `npm run dev`
2. **Open browser**: http://localhost:3000
3. **Paste 1688 URL**: e.g., https://detail.1688.com/offer/123456.html
4. **Click Import**: Wait 30-60 seconds
5. **Check Shopify**: Product should appear

## Logs

Backend logs show:
```
🚀 Navigating to product: ...
✅ Page loaded: 200
🔐 CAPTCHA detected! Attempting to solve...
✅ CAPTCHA solved by CapSolver!
📊 Starting data extraction...
Found 15 unique images
✅ Extracted 2 variant type(s)
✅ Product uploaded to Shopify!
```

## Stop Application

Press `Ctrl+C` in terminal (twice)

## Update Application

If you receive updates:

```bash
# Backup .env file first!
# Then extract new ZIP and restore .env

# If Python files changed:
cd backend
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
```

## Support

- Setup issues: See `SETUP_INSTRUCTIONS.md`
- Python issues: See `PYTHON_VENV_FIX.md`
- CapSolver: https://docs.capsolver.com/
- Shopify API: https://shopify.dev/docs/api

---

**Remember**: Keep `.env` file secret - it contains your API keys!
