# News API - Quick Configuration Guide

## Current Status: Mock Mode ✅

The service is currently using **mock data** for prototype testing. This is perfect for development!

## To Enable Real News API (Optional)

### 1️⃣ Get API Key (2 minutes)
- Visit: https://newsapi.org/register
- Sign up (free)
- Copy your API key

### 2️⃣ Update `.env` File
```bash
# Add these lines to backend/.env
NEWS_API_KEY="paste_your_key_here"
NEWS_API_ENABLED=True
```

### 3️⃣ Restart Backend
```bash
# Stop and restart your backend server
```

### 4️⃣ Test It
```bash
cd backend
python test_news_integration.py
```

## That's It! 🎉

### What You Get:
- ✅ **Mock Mode** (default): Sample news in English, Telugu, Hindi
- ✅ **Live Mode** (with API key): Real agricultural news
- ✅ **Automatic Fallback**: If API fails, uses mock data
- ✅ **Caching**: Reduces API calls (1-hour cache)
- ✅ **Free Tier**: 100 requests/day (plenty for testing)

### Files Modified:
- ✅ `backend/app/core/config.py` - Added NEWS_API_* settings
- ✅ `backend/.env.example` - Added example config
- ✅ `backend/app/services/news_service.py` - Uses config settings

### Documentation:
- 📖 Full guide: `backend/NEWS_API_SETUP.md`
- 📖 Service docs: `backend/app/services/NEWS_SERVICE_README.md`

## No Action Needed for MVP

The mock data works great for testing! Only configure the real API when you need actual news content.
