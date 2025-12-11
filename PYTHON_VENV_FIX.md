# 🔧 Python Virtual Environment Fix

## Problem

When running the project, you may encounter:
```
ModuleNotFoundError: No module named 'playwright'
ModuleNotFoundError: No module named 'bs4'
```

This happens because **Node.js was calling system Python instead of the venv Python**.

## Solution Applied

### ✅ 1. Automatic Python Path Detection

The backend now **automatically detects** the venv Python:

- **Windows**: Uses `backend/venv/Scripts/python.exe`
- **Linux/Mac**: Uses `backend/venv/bin/python`
- **Fallback**: Uses system Python if venv not found

See: `backend/routes/import.js` - `getPythonPath()` function

### ✅ 2. Updated Setup Scripts

Both `setup.bat` (Windows) and `setup.sh` (Linux/Mac) now:

1. **Create virtual environment** in `backend/venv`
2. **Activate** the venv
3. **Install** Python packages inside the venv
4. **Install** Playwright browsers in the venv

### ✅ 3. Updated Documentation

`SETUP_INSTRUCTIONS.md` now includes:
- How to verify venv is created
- How to manually set `PYTHON_PATH` if needed
- Troubleshooting for ModuleNotFoundError

## How to Fix on Your Friend's Laptop

### Option A: Re-run Setup (Recommended)

1. **Delete old installation** (if any):
```bash
# Windows:
rmdir /s /q backend\venv
rmdir /s /q node_modules
rmdir /s /q backend\node_modules
rmdir /s /q frontend\node_modules

# Linux/Mac:
rm -rf backend/venv node_modules backend/node_modules frontend/node_modules
```

2. **Run setup again**:
```bash
npm run setup
```

3. **Verify venv was created**:
```bash
# Windows:
dir backend\venv\Scripts\python.exe

# Linux/Mac:
ls backend/venv/bin/python
```

4. **Test Python detection**:
```bash
node backend/test_python.js
```

You should see:
```
✅ Using venv Python: D:\...\backend\venv\Scripts\python.exe
✅ Python version: Python 3.12.x
✅ playwright
✅ beautifulsoup4
✅ lxml
✅ requests
```

5. **Start the application**:
```bash
npm run dev
```

### Option B: Manual Fix (If Option A fails)

1. **Create venv manually**:
```bash
cd backend
python -m venv venv

# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
```

2. **Install packages**:
```bash
pip install -r requirements.txt
playwright install chromium
```

3. **Verify installation**:
```bash
pip list
```

Should show: playwright, beautifulsoup4, lxml, requests, python-dotenv

4. **Deactivate and test**:
```bash
deactivate
cd ..
node backend/test_python.js
```

### Option C: Set PYTHON_PATH Manually

If automatic detection still fails, set it explicitly in `.env`:

**Windows:**
```env
PYTHON_PATH=D:\My Projects\Upwork\backend\venv\Scripts\python.exe
```

**Linux/Mac:**
```env
PYTHON_PATH=/home/user/project/backend/venv/bin/python
```

**Find the path**:
```bash
# Windows (in activated venv):
where python

# Linux/Mac (in activated venv):
which python
```

## Verification Checklist

✅ `backend/venv` folder exists  
✅ `backend/venv/Scripts/python.exe` (Windows) or `backend/venv/bin/python` (Linux/Mac) exists  
✅ `node backend/test_python.js` shows all packages installed  
✅ `npm run dev` starts without errors  
✅ Importing a 1688 product works without ModuleNotFoundError  

## Why This Happened

Node.js `child_process.spawn('python', ...)` calls **system Python** by default, not the venv Python. System Python doesn't have the packages installed (playwright, bs4, etc.).

**Old behavior:**
```javascript
const pythonPath = process.env.PYTHON_PATH || 'python';  // Always system Python
```

**New behavior:**
```javascript
const pythonPath = getPythonPath();  // Automatically detects venv Python
```

## Files Changed

1. `backend/routes/import.js` - Added `getPythonPath()` function
2. `setup.bat` - Now creates venv and installs packages inside it
3. `setup.sh` - Now creates venv and installs packages inside it
4. `SETUP_INSTRUCTIONS.md` - Added troubleshooting section
5. `backend/test_python.js` - New test script to verify detection

## Test the Fix

Run this on your friend's laptop:

```bash
# 1. Test Python detection
node backend/test_python.js

# 2. Try importing a product
npm run dev
# Go to http://localhost:3000
# Paste a 1688.com URL
# Check console for errors
```

If you see errors, check:
1. Does `backend/venv` exist?
2. Run `node backend/test_python.js` - what does it show?
3. Check `.env` file - is `PYTHON_PATH` set correctly?

## Success Criteria

When everything works, you should see:

**Backend console:**
```
✅ Using venv Python: D:\...\backend\venv\Scripts\python.exe
Server running on port 5000
```

**When importing:**
```
🚀 Navigating to product: https://detail.1688.com/...
✅ Page loaded: 200
📊 Starting data extraction...
✅ CAPTCHA solved successfully!
```

**No errors like:**
```
❌ ModuleNotFoundError: No module named 'playwright'
❌ ModuleNotFoundError: No module named 'bs4'
```

## Next Steps

1. Send this document to your friend
2. Ask them to delete `backend/venv` folder
3. Ask them to run `npm run setup` again
4. Ask them to run `node backend/test_python.js`
5. If all packages show ✅, the fix is working!

---

**Need help?** Check `SETUP_INSTRUCTIONS.md` for detailed setup guide.
