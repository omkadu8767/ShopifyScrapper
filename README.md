 # 1688 → Shopify Product Importer

**Complete automated system for importing products from 1688.com to Shopify**

Developed for: **SHOPGURU INTERNATIONAL SRL**

---

## 🚀 Quick Start

```bash
# 1. Install dependencies (one command)
npm run setup

# 2. Configure API keys in .env file

# 3. Start application
npm run dev
```

**Need help?** See [SETUP_INSTRUCTIONS.md](./SETUP_INSTRUCTIONS.md) for detailed setup guide.

---

## 📋 Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
  - [Local Development Setup](#local-development-setup)
  - [Production Deployment (DigitalOcean)](#production-deployment-digitalocean)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)
- [License](#license)

---

## ✨ Features

### Core Functionality
- **Automated Scraping**: Extracts complete product data from any 1688.com product page using Playwright
- **CAPTCHA Solving**: Automatic CAPTCHA bypass using CapSolver API with fallback to automatic slider solving
- **AI Translation**: Professional Chinese to Romanian translation using ChatGPT API (GPT-4o-mini)
- **Description Rewriting**: Converts product descriptions into professional, SEO-optimized Shopify format
- **Variant Extraction**: Intelligent extraction of colors, sizes, and capacities from multiple HTML structures
- **Image Processing**: Downloads, optimizes, and compresses images to WebP format (filters out videos)
- **Automatic Upload**: Creates complete Shopify products with variants, pricing, and SEO fields
- **Web Interface**: User-friendly UI for importing products
- **RESTful API**: Public API endpoint for programmatic imports
- **Import Tracking**: SQLite database tracks all imports with status and history

### Advanced Features
- **Intelligent Pricing**: 6x markup with CNY to RON conversion (0.68 rate) and .99 rounding
- **Default Inventory**: All variants automatically set to 100 units in stock
- **Variant Generation**: Automatically creates all variant combinations from .feature-item and .expand-view-list
- **Session Persistence**: Browser session saved to reduce CAPTCHA frequency
- **Headless Mode**: Supports headless browser operation for production deployment
- **SEO Optimization**: Auto-generates SEO titles, meta descriptions, and image alt-text
- **Error Handling**: Robust error handling with detailed logging and debugging console output
- **Rate Limiting**: Built-in protection against API abuse
- **Real-time Status**: Live import status tracking with polling

---

## 🛠 Technology Stack

### Backend
- **Node.js** + Express.js (REST API server)
- **Python 3.8+** (Scraping with automatic venv detection)
- **Playwright Sync API** (Browser automation with Chrome/Chromium)
- **CapSolver API** (Automatic CAPTCHA solving for 1688.com)
- **ChatGPT API** (GPT-4o-mini for Romanian translation)
- **BeautifulSoup4 & lxml** (HTML parsing)
- **SQLite** (Import tracking database)
- **Shopify Admin API 2024-10** (Product creation)

### Frontend
- **React 18** (UI framework)
- **Vite** (Build tool - fast development)
- **Tailwind CSS 3.4** (Utility-first styling)
- **Axios** (HTTP client)

### Deployment
- **PM2** (Process management)
- **Nginx** (Reverse proxy + load balancing)
- **Let's Encrypt** (SSL/TLS certificates)
- **UFW** (Firewall)

---

## 📦 Prerequisites

### For Local Development
- **Node.js** 18+ (LTS version recommended)
- **Python** 3.8+
- **npm** 9+
- **Git**

### For Production Deployment
- **Ubuntu/Debian** server (DigitalOcean droplet recommended)
- **Domain name** with DNS pointing to server
- **Minimum 2GB RAM**, 2 vCPU
- **Root or sudo access**

### API Keys Required
- **Shopify Admin API Token** (with product write permissions)
- **ChatGPT API Key** (OpenAI API for Romanian translation)
- **CapSolver API Key** (Optional - for automatic CAPTCHA solving, falls back to automatic slider)

---

## 🚀 Installation

### Local Development Setup

#### 1. Clone the Repository
```bash
git clone <repository-url>
cd 1688-shopify-importer
```

#### 2. Automated Installation (Recommended)
```bash
# One command to install everything
npm run setup
```

This will automatically:
- ✅ Install root, backend, and frontend npm packages
- ✅ Create Python virtual environment in `backend/venv`
- ✅ Install Python packages (playwright, beautifulsoup4, lxml, requests, python-dotenv)
- ✅ Download Playwright Chromium browser

**Verify installation:**
```bash
node backend/test_python.js
```

#### Alternative: Manual Installation
```bash
# Install Node.js dependencies
npm install
cd backend && npm install && cd ..
cd frontend && npm install && cd ..

# Create Python virtual environment
cd backend
python -m venv venv

# Activate venv (Windows)
venv\Scripts\activate
# Activate venv (Linux/Mac)
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
playwright install chromium
deactivate
cd ..
```

#### 5. Configure Environment Variables
```bash
# Copy the example file
copy .env.example .env

# Edit .env with your actual credentials
notepad .env
```

**Required configurations in `.env`:**
```env
# Shopify Configuration
SHOPIFY_STORE_URL=your-store.myshopify.com
SHOPIFY_ACCESS_TOKEN=shpat_xxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SHOPIFY_API_VERSION=2024-10

# AI Translation (ChatGPT)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TARGET_LANGUAGE=ro

# CapSolver API (for automatic CAPTCHA solving)
CAPSOLVER_API_KEY=CAP-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Pricing Rules (6x markup)
PRICE_MARKUP_PERCENTAGE=6.0
PRICE_MARKUP_FIXED=0
CNY_TO_RON_RATE=0.68
ENABLE_99_ROUNDING=true

# Scraper Configuration
SCRAPER_TIMEOUT=60000
HEADLESS_BROWSER=true

# Image Processing
IMAGE_FORMAT=webp
IMAGE_QUALITY=85
MAX_IMAGE_WIDTH=2048
```

#### 6. Start Development Servers
```bash
# Start both frontend and backend concurrently
npm run dev
```

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/api/health

---

### Production Deployment (DigitalOcean)

#### 1. Create DigitalOcean Droplet
- **OS**: Ubuntu 22.04 LTS
- **Plan**: Basic ($12/month minimum - 2GB RAM, 2 vCPUs)
- **Datacenter**: Choose closest to your customers
- **Authentication**: SSH keys recommended

#### 2. Connect to Server
```bash
ssh root@your_server_ip
```

#### 3. Clone Repository
```bash
cd /var/www
git clone <repository-url> 1688-shopify-importer
cd 1688-shopify-importer
```

#### 4. Run Deployment Script
```bash
chmod +x deployment/deploy.sh
./deployment/deploy.sh
```

The script will:
- Install Node.js, Python, and system dependencies
- Install all project dependencies
- Install Playwright browsers
- Build the frontend
- Configure Nginx
- Setup firewall rules
- Create PM2 process configuration

#### 5. Configure Environment
```bash
# Copy and edit environment file
cp .env.example .env
nano .env
```

#### 6. Update Nginx Configuration
```bash
# Edit the domain name
sudo nano /etc/nginx/sites-available/1688-shopify-importer

# Change 'your-domain.com' to your actual domain
# Example: shopify-importer.yourdomain.com

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

#### 7. Setup SSL Certificate
```bash
# Install SSL certificate for your domain
sudo certbot --nginx -d your-domain.com

# Follow the prompts
# Choose option 2: Redirect HTTP to HTTPS
```

#### 8. Start Application
```bash
# Start with PM2
pm2 start ecosystem.config.js

# Save PM2 process list
pm2 save

# Setup PM2 to start on system boot
pm2 startup
# Run the command that PM2 outputs
```

#### 9. Verify Deployment
```bash
# Check PM2 status
pm2 status

# View logs
pm2 logs

# Check if services are running
curl http://localhost:5000/api/health
curl http://localhost:3000
```

Your application should now be accessible at `https://your-domain.com`

---

##⚙️ Configuration

### Environment Variables

| Variable | Description | Example | Required |
|----------|-------------|---------|----------|
| `SHOPIFY_STORE_URL` | Your Shopify store domain | `mystore.myshopify.com` | Yes |
| `SHOPIFY_ACCESS_TOKEN` | Shopify Admin API token | `shpat_xxxxx` | Yes |
| `SHOPIFY_API_VERSION` | Shopify API version | `2024-10` | No (default: `2024-10`) |
| `OPENAI_API_KEY` | ChatGPT API key for translation | `sk-proj-xxxxx` | Yes |
| `CAPSOLVER_API_KEY` | CapSolver API for CAPTCHA | `CAP-xxxxx` | No (falls back to auto) |
| `TARGET_LANGUAGE` | Translation target language | `ro`, `en` | No (default: `ro`) |
| `PRICE_MARKUP_PERCENTAGE` | Price multiplier | `6.0` = 6x markup | No (default: `6.0`) |
| `PRICE_MARKUP_FIXED` | Fixed amount to add | `0` RON | No (default: `0`) |
| `CNY_TO_RON_RATE` | Currency conversion rate | `0.68` | No (default: `0.68`) |
| `ENABLE_99_ROUNDING` | Round prices to .99 | `true` or `false` | No (default: `true`) |
| `HEADLESS_BROWSER` | Run browser in headless mode | `true` or `false` | No (default: `true`) |
| `SCRAPER_TIMEOUT` | Scraper timeout in ms | `60000` | No (default: `60000`) |
| `IMAGE_FORMAT` | Image output format | `webp`, `jpg`, `png` | No (default: `webp`) |
| `IMAGE_QUALITY` | Image quality (1-100) | `85` | No (default: `85`) |
| `MAX_IMAGE_WIDTH` | Maximum image width | `2048` | No (default: `2048`) |
| `PORT` | Backend server port | `5000` | No (default: `5000`) |

### Getting API Keys

#### Shopify Admin API Token
1. Login to your Shopify admin panel
2. Go to **Settings** → **Apps and sales channels**
3. Click **Develop apps**
4. Create a new app or select existing
5. Configure **Admin API scopes**: `write_products`, `read_products`
6. Install app and copy the **Admin API access token**

#### ChatGPT API Key (OpenAI)
1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in with OpenAI account
3. Click **Create new secret key**
4. Name it "1688-Shopify-Translator"
5. Copy the API key (starts with `sk-proj-`)
6. Add billing method if not already done

#### CapSolver API Key (Optional)
1. Go to [CapSolver Dashboard](https://dashboard.capsolver.com/)
2. Sign up or log in
3. Navigate to **API Key** section
4. Copy your API key (starts with `CAP-`)
5. Add balance for CAPTCHA solving credits
6. **Note**: If not configured, automatic slider solving will be used as fallback

---

## 📖 Usage

### Web Interface

1. Open your browser and navigate to:
   - **Local**: http://localhost:3000
   - **Production**: https://your-domain.com

2. **Import a Product**:
   - Paste a 1688 product URL in the input field
   - Example: `https://detail.1688.com/offer/673821945613.html`
   - Click **"Import Product"** button
   - Watch the real-time logs for progress
   - Check the import history table for status

3. **View Import History**:
   - Scroll down to see recent imports
   - Status indicators: Pending → Processing → Completed/Failed
   - Click **Refresh** to update the list

### API Usage

#### Import Product Endpoint
```bash
POST /api/import
Content-Type: application/json

{
  "url": "https://detail.1688.com/offer/673821945613.html"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Import started",
  "importId": 42
}
```

#### Get Import Status
```bash
GET /api/import/:id
```

**Response:**
```json
{
  "success": true,
  "import": {
    "id": 42,
    "url": "https://detail.1688.com/...",
    "title": "产品名称",
    "status": "completed",
    "shopify_product_id": "8234567890",
    "created_at": "2025-11-21T10:30:00.000Z",
    "completed_at": "2025-11-21T10:32:15.000Z"
  }
}
```

#### Get Import History
```bash
GET /api/import/history?limit=20
```

#### Health Check
```bash
GET /api/health
```

---

## 📁 Project Structure

```
1688-shopify-importer/
│
├── backend/                    # Backend Node.js + Python services
│   ├── server.js              # Express.js main server
│   ├── package.json           # Backend dependencies
│   ├── requirements.txt       # Python dependencies
│   │
│   ├── routes/
│   │   └── import.js          # Import API routes
│   │
│   ├── services/
│   │   ├── shopify_service.js # Shopify API integration
│   │   ├── ai_translator.py   # AI translation service
│   │   └── image_processor.py # Image download & optimization
│   │
│   ├── scrapers/
│   │   └── scraper_1688.py    # 1688.com product scraper
│   │
│   └── database/
│       └── db.js              # SQLite database wrapper
│
├── frontend/                   # React + Vite frontend
│   ├── index.html             # HTML entry point
│   ├── package.json           # Frontend dependencies
│   ├── vite.config.js         # Vite configuration
│   ├── tailwind.config.js     # Tailwind CSS config
│   ├── postcss.config.js      # PostCSS config
│   │
│   ├── src/
│   │   ├── main.jsx           # React entry point
│   │   ├── App.jsx            # Main application component
│   │   └── index.css          # Tailwind CSS + custom styles
│   │
│   └── public/                # Static assets
│
├── deployment/                 # Deployment configurations
│   ├── deploy.sh              # Automated deployment script
│   └── nginx.conf             # Nginx reverse proxy config
│
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── package.json               # Root package.json (concurrently)
├── ecosystem.config.js        # PM2 process configuration
└── README.md                  # This file
```

---

## 🔧 Troubleshooting

### Common Issues

#### 1. **ModuleNotFoundError: No module named 'playwright'**

**Cause**: Node.js not using Python virtual environment

**Solutions**:
```bash
# Test Python detection
node backend/test_python.js

# If venv not found, recreate it
cd backend
rmdir /s /q venv  # Windows
rm -rf venv       # Linux/Mac
cd ..
npm run setup

# Verify installation
node backend/test_python.js
```

**Manual fix**:
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
playwright install chromium
```

See [PYTHON_VENV_FIX.md](./PYTHON_VENV_FIX.md) for detailed troubleshooting.

#### 2. **Import fails with "Scraping failed"**

**Cause**: 1688 website structure changed or blocking requests

**Solutions**:
- Check if the URL is valid and accessible
- Verify CapSolver API key has credits: https://dashboard.capsolver.com/
- Set `HEADLESS_BROWSER=false` to see browser for debugging
- Update scraper selectors in `backend/scrapers/scraper_1688.py`
- Try with a different product URL
- Check browser session: `backend/browser_sessions/1688_session`

#### 3. **"Translation failed" error**

**Cause**: Invalid ChatGPT API key or quota exceeded

**Solutions**:
- Verify `OPENAI_API_KEY` in `.env` is correct (starts with `sk-proj-`)
- Check API usage and billing at [OpenAI Platform](https://platform.openai.com/usage)
- Ensure you have available credits
- Check network connectivity to OpenAI APIs
- Verify model `gpt-4o-mini` is accessible

#### 4. **"Shopify upload failed"**

**Cause**: Invalid Shopify credentials or insufficient permissions

**Solutions**:
- Verify `SHOPIFY_STORE_URL` format: `store.myshopify.com` (no https://)
- Check `SHOPIFY_ACCESS_TOKEN` is valid and active
- Ensure Shopify app has `write_products` and `read_products` scopes
- Verify API version `2024-10` is supported by your store
- Check Shopify API rate limits (avoid too many rapid imports)
- Review variant data format (ensure all required fields present)

#### 5. **CAPTCHA not solving / "Please wait continuously"**

**Cause**: CAPTCHA solver not working or headless mode issue

**Solutions**:
```bash
# Check CapSolver credits
# Visit: https://dashboard.capsolver.com/

# Test in visible mode (disable headless)
# In .env file:
HEADLESS_BROWSER=false

# Check CapSolver API key
# Should start with: CAP-

# View detailed logs
pm2 logs 1688-shopify-backend
```

**If CapSolver fails**: Automatic slider solving will be attempted as fallback

**Session persistence**: After first successful CAPTCHA, browser session is saved to `backend/browser_sessions/1688_session` to reduce future CAPTCHAs

#### 6. **Images not uploading**

**Cause**: Image URLs blocked or download failed

**Solutions**:
- Check image URLs are accessible from CDN
- Verify images are from `img.alicdn.com` domain
- Check disk space for temporary downloads
- Ensure images aren't videos (scraper filters them)
- Review image processor logs for errors

#### 5. **Frontend not connecting to backend**

**Cause**: CORS issues or wrong API URL

**Solutions**:
- Check backend is running: `curl http://localhost:5000/api/health`
- Verify proxy settings in `vite.config.js`
- Check CORS settings in `backend/server.js`
- Clear browser cache

#### 6. **PM2 process keeps crashing**

**Cause**: Application errors or resource limits

**Solutions**:
```bash
# View detailed logs
pm2 logs 1688-shopify-backend --lines 100

# Check error logs
pm2 logs 1688-shopify-backend --err

# Restart with fresh state
pm2 delete all
pm2 start ecosystem.config.js

# Check system resources
free -h
df -h
```

#### 7. **Nginx 502 Bad Gateway**

**Cause**: Backend not running or port mismatch

**Solutions**:
```bash
# Check if backend is running
pm2 status

# Test backend directly
curl http://localhost:5000/api/health

# Check Nginx logs
sudo tail -f /var/log/nginx/error.log

# Verify Nginx configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

### Debugging Tips

#### Enable Verbose Logging
```bash
# Backend logs
pm2 logs 1688-shopify-backend --lines 200

# Follow logs in real-time
pm2 logs --lines 0
```

#### Test Individual Components

**Test Scraper**:
```bash
cd backend
python scrapers/scraper_1688.py "https://detail.1688.com/offer/xxxxx.html"
```

**Test AI Translation**:
```bash
cd backend
python services/ai_translator.py "中文产品描述" "Product Title"
```

**Test Shopify Connection**:
```bash
curl -X GET \
  https://your-store.myshopify.com/admin/api/2024-10/shop.json \
  -H 'X-Shopify-Access-Token: your_token'
```

---

## 🔄 Maintenance

### Regular Updates

#### Update Dependencies
```bash
# Update Node.js packages
cd backend && npm update && cd..
cd frontend && npm update && cd ..

# Update Python packages
cd backend
pip install --upgrade -r requirements.txt
```

#### Update on Production Server
```bash
# Pull latest changes
cd /var/www/1688-shopify-importer
git pull origin main

# Rebuild frontend
cd frontend
npm install
npm run build
cd ..

# Restart services
pm2 restart all
```

### Database Maintenance

#### Backup Database
```bash
# Backup SQLite database
cd backend
cp database.sqlite database.sqlite.backup_$(date +%Y%m%d)
```

#### Clean Old Imports
```bash
# Connect to database
sqlite3 backend/database.sqlite

# Delete imports older than 30 days
DELETE FROM imports WHERE created_at < datetime('now', '-30 days');

# Vacuum to reclaim space
VACUUM;

# Exit
.quit
```

### Monitor Performance

```bash
# View PM2 monitoring dashboard
pm2 monit

# Check resource usage
pm2 status

# View memory usage
free -h

# Check disk space
df -h

# View Nginx access logs
sudo tail -f /var/log/nginx/1688-shopify-access.log
```

### Backup Strategy

```bash
#!/bin/bash
# Save as: backup.sh

BACKUP_DIR="/var/backups/1688-shopify"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp /var/www/1688-shopify-importer/backend/database.sqlite \
   $BACKUP_DIR/database_$DATE.sqlite

# Backup .env file
cp /var/www/1688-shopify-importer/.env \
   $BACKUP_DIR/env_$DATE.txt

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.sqlite" -mtime +7 -delete

echo "Backup completed: $DATE"
```

Add to cron for daily backups:
```bash
crontab -e

# Add this line for daily backup at 2 AM
0 2 * * * /var/www/1688-shopify-importer/backup.sh
```

---

## 📞 Support & Warranty

### 30-Day Warranty Includes:
- ✅ Bug fixes for scraping issues
- ✅ Fixes for Shopify upload problems
- ✅ Support for deployment issues
- ✅ Configuration assistance

### Out of Scope:
- ❌ Changes to 1688 website structure (requires scraper updates)
- ❌ Shopify API changes (may require updates)
- ❌ Custom feature requests
- ❌ Server infrastructure issues

---

## 📄 License

**Private License - All Rights Reserved**

© 2025 SHOPGURU INTERNATIONAL SRL

This software and all associated documentation are the exclusive property of SHOPGURU INTERNATIONAL SRL.

**Restrictions:**
- ❌ No redistribution
- ❌ No reselling
- ❌ No public sharing
- ❌ No reuse in other projects

**Confidentiality:**
All API credentials and business logic remain confidential.

---

## 👨‍💻 Development Information

**Developed for:** SHOPGURU INTERNATIONAL SRL  
**Project Timeline:** 7-10 days  
**Contract Value:** $200 USD  
**Completion Date:** November 2025

**Milestones:**
- ✅ Milestone 1: 1688 Scraper ($60)
- ✅ Milestone 2: Shopify Auto-Upload ($90)
- ✅ Milestone 3: Deployment + UI + Documentation ($50)

---

## 🎯 Project Success Criteria

The project is considered complete when:
- ✅ At least 3 different 1688 links successfully import
- ✅ All images upload correctly to Shopify
- ✅ Variants generate properly
- ✅ UI and API endpoint work without errors
- ✅ System runs reliably on DigitalOcean 24/7
- ✅ Complete documentation delivered

---

**For technical support during warranty period, contact the development team.**

Last Updated: December 04, 2025\
"# ShopifyScrapper" 
"# ShopifyScrapper" 
"# ShopifyScrapper" 
"# ShopifyScrapper" 
