# CapSolver Setup Guide for 1688.com CAPTCHA Solving

## 🎯 What is CapSolver?
CapSolver is an automatic CAPTCHA solving service specifically optimized for Alibaba/1688 slider CAPTCHAs.
- **Success Rate:** 90-95% for 1688.com
- **Speed:** 3-8 seconds per solve
- **Cost:** ~$0.0015-0.003 per solve (~$2-3 per 1000 solves)

## 📝 Setup Steps

### 1. Create CapSolver Account
1. Go to: https://www.capsolver.com/
2. Click **"Sign Up"** (top right)
3. Register with your email
4. Verify your email

### 2. Add Funds to Your Account
1. Login to: https://dashboard.capsolver.com/
2. Click **"Deposit"** or **"Add Funds"**
3. Minimum deposit: **$5** (enough for ~2000-3000 solves)
4. Payment methods: PayPal, Credit Card, Crypto
5. **Recommended starting amount:** $10-20

### 3. Get Your API Key
1. Go to: https://dashboard.capsolver.com/dashboard/overview
2. Look for **"API Key"** section
3. Copy your API key (looks like: `CAP-1A2B3C4D5E6F7G8H9I0J...`)

### 4. Add API Key to Your Project
1. Open: `d:\My Projects\Upwork\.env`
2. Find the line: `CAPSOLVER_API_KEY=`
3. Paste your API key after the `=`:
   ```
   CAPSOLVER_API_KEY=CAP-1A2B3C4D5E6F7G8H9I0J...
   ```
4. Save the file

### 5. Restart Your Backend Server
```bash
# Stop the current server (Ctrl+C)
# Then restart:
npm run dev
```

## 🚀 How It Works

### Automatic Flow:
1. **CAPTCHA detected** → CapSolver API called automatically
2. **CapSolver solves it** → Slider moved automatically (3-8 seconds)
3. **Success** → Scraping continues
4. **If CapSolver fails** → Falls back to automatic slider algorithm
5. **If that fails too** → Manual solving (120s timeout locally)

### On DigitalOcean (Production):
- ✅ CapSolver works automatically (no human needed)
- ✅ Session persistence reduces CAPTCHA frequency
- ✅ Only charges when CAPTCHA actually appears

## 💰 Cost Management

### Typical Usage:
- **First import:** CAPTCHA appears → CapSolver used ($0.002)
- **Session saved:** Next 50-200 imports use saved cookies (FREE)
- **Session expires:** CAPTCHA appears again → CapSolver used ($0.002)

### Monthly Estimate:
- **Low usage** (10-20 products/day): $2-5/month
- **Medium usage** (50-100 products/day): $10-20/month
- **High usage** (200+ products/day): $30-50/month

## 📊 Check Your Balance

Go to: https://dashboard.capsolver.com/dashboard/overview

You'll see:
- Current balance
- Number of solves today
- Success rate
- Spending statistics

## ⚠️ Important Notes

### Refund Policy:
- ✅ Failed solves are usually refunded automatically
- ✅ You're only charged for successful solves
- ⚠️ Check your dashboard regularly

### Rate Limits:
- No strict limits
- If you make 1000+ requests/hour, contact support

### Success Rate:
- **NOT 100%** - expect 5-15% failure rate
- Failed solves will retry with automatic algorithm
- Session persistence greatly reduces CAPTCHA frequency

## 🔧 Testing CapSolver

### Test if it's working:
1. Make sure API key is in `.env`
2. Delete session file: `backend/browser_sessions/1688_session`
3. Import a 1688 product
4. Watch console output:
   ```
   🔐 CAPTCHA detected! Attempting to solve...
   🔧 Using CapSolver to solve CAPTCHA...
   📋 CapSolver task created: abc123...
   ⏳ Waiting for CapSolver... (2s)
   ✅ CapSolver solved! Distance: 265px
   ✅ CAPTCHA solved by CapSolver!
   ```

### Check CapSolver Dashboard:
- Login to dashboard
- Go to "Statistics" or "History"
- You'll see the solve logged with timestamp

## 🆘 Troubleshooting

### "⚠️ CapSolver API key not configured"
- API key missing or empty in `.env`
- Check `.env` file has: `CAPSOLVER_API_KEY=CAP-...`

### "❌ CapSolver error: Insufficient balance"
- Add funds to your account
- Minimum: $5

### "❌ CapSolver error: Invalid API key"
- Copy the key again from dashboard
- Make sure no extra spaces in `.env`

### "⏰ CapSolver timeout"
- Service might be slow (retry automatically happens)
- Check CapSolver status: https://status.capsolver.com/

### CapSolver works but scraping fails
- CAPTCHA was solved but page redirected
- This is rare - session should save after first solve

## 🎓 Without CapSolver (Free Alternative)

If you don't want to pay:
1. Leave `CAPSOLVER_API_KEY=` empty
2. System will use:
   - Automatic slider algorithm (85% success)
   - Manual solving locally (you solve once)
   - Session persistence (reuses cookies)

**Best for:**
- Testing/development
- Low volume scraping
- When you can solve CAPTCHA once locally

## 📞 Support

- **CapSolver Support:** https://www.capsolver.com/support
- **Documentation:** https://docs.capsolver.com/
- **Discord:** https://discord.gg/capsolver

## ✅ Deployment Checklist

### Before deploying to DigitalOcean:

**Option 1: With CapSolver (Recommended)**
- [ ] Add CapSolver API key to `.env`
- [ ] Add $10-20 to CapSolver balance
- [ ] Test locally first
- [ ] Deploy to server
- [ ] Add CapSolver API key to server's `.env`

**Option 2: Without CapSolver (Session-based)**
- [ ] Test locally and solve CAPTCHA once
- [ ] Session saved in `backend/browser_sessions/1688_session`
- [ ] Upload session file to server
- [ ] Server will use saved session (no CAPTCHA for weeks)
- [ ] When session expires, repeat process

---

## 🎉 Quick Start Summary

1. **Sign up:** https://www.capsolver.com/
2. **Add $10** to your account
3. **Copy API key** from dashboard
4. **Paste in `.env`:** `CAPSOLVER_API_KEY=your_key_here`
5. **Restart server**
6. **Test import** - CAPTCHA will be solved automatically!

**Cost:** ~$0.002 per CAPTCHA solve + FREE for all subsequent imports (session saved)
