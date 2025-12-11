# 🚀 ShopifyScraper - Quick Setup Guide

## Prerequisites

Before starting, ensure you have installed:
- **Node.js 18+** (https://nodejs.org/)
- **Python 3.8+** (https://www.python.org/)
- **Git** (optional, for version control)

## 📦 Installation (One Command)

### Windows:
```bash
npm run setup
```

### Linux/Mac:
```bash
npm run setup
```

**That's it!** The setup script will automatically:
- ✅ Install root dependencies
- ✅ Install backend dependencies  
- ✅ Install frontend dependencies
- ✅ Install Python packages (playwright, beautifulsoup4, lxml, requests, python-dotenv)
- ✅ Download Playwright Chromium browser

---

## ⚙️ Configuration

After installation, configure your `.env` file in the root directory:

### Required API Keys:

1. **Shopify Store Credentials:**
```env
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_your_access_token
```

2. **OpenAI API (for Romanian translation):**
```env
OPENAI_API_KEY=sk-proj-your_api_key
TARGET_LANGUAGE=ro
```

3. **CapSolver API (for automatic CAPTCHA solving):**
```env
CAPSOLVER_API_KEY=CAP-your_api_key
```
Get your key from: https://dashboard.capsolver.com/

4. **Headless Browser (for production/server):**
```env
HEADLESS_BROWSER=true
```
Set to `false` for local development if you want to see the browser.

---

## 🎯 Running the Application

```bash
npm run dev
```

This will start:
- **Backend** on http://localhost:5000
- **Frontend** on http://localhost:3000

---

## 📋 Available Scripts

| Command | Description |
|---------|-------------|
| `npm run setup` | Install all dependencies (run this first) |
| `npm run dev` | Start backend + frontend in development mode |
| `npm run backend` | Start only backend server |
| `npm run frontend` | Start only frontend app |
| `npm run build` | Build frontend for production |
| `npm run start` | Start production servers |

---

## 🔧 Troubleshooting

### Python not found
- **Windows:** Add Python to PATH during installation or run `setup.bat` as Administrator
- **Linux/Mac:** Install Python3: `sudo apt install python3 python3-pip` (Ubuntu/Debian)

### ModuleNotFoundError (Python packages not found)
This happens when Node.js doesn't use the Python venv. The app now **automatically detects** the venv, but if issues persist:

**Option 1 (Recommended):** Ensure venv is created in `backend/venv`:
```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate
pip install -r requirements.txt
```

**Option 2:** Set explicit Python path in `.env`:
```env
# Windows:
PYTHON_PATH=D:\My Projects\Upwork\backend\venv\Scripts\python.exe

# Linux/Mac:
PYTHON_PATH=/path/to/project/backend/venv/bin/python
```

**Verify:** Check that `backend/venv` folder exists with `Scripts` (Windows) or `bin` (Linux/Mac) inside.

### Playwright browser issues
Manually install Chromium browser:
```bash
cd backend
python -m playwright install chromium
python -m playwright install-deps chromium
```

### Port already in use
Change ports in `.env`:
```env
PORT=5001  # Backend port
```
And in `frontend/.env`:
```env
VITE_API_URL=http://localhost:5001
```

### CAPTCHA solving not working
1. Verify your CapSolver API key has credits: https://dashboard.capsolver.com/
2. Check logs for error messages
3. Fallback automatic solver will be used if API fails

---

## 📚 How It Works

1. **Paste 1688.com product URL** in the frontend
2. **Backend scrapes** product details (title, description, images, variants, prices)
3. **AI translates** to Romanian using ChatGPT API
4. **CAPTCHA solving** via CapSolver API (automatic)
5. **Prices converted** CNY → RON with markup
6. **Product uploaded** to your Shopify store

---

## 🛡️ Security Notes

- Never commit `.env` file to version control
- Keep API keys secret
- Use environment variables for production deployment
- For DigitalOcean/server deployment, ensure `HEADLESS_BROWSER=true`

---

## 📞 Support

For issues or questions, contact the developer or check:
- CapSolver docs: https://docs.capsolver.com/
- Playwright docs: https://playwright.dev/python/
- Shopify API docs: https://shopify.dev/docs/api

---

## 🎉 You're All Set!

Run `npm run dev` and start importing products from 1688.com to your Shopify store!
