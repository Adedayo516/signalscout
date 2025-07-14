# 🚀 **SignalScout Deployment Guide**

## **Step 1: Create GitHub Repository**

1. Go to [GitHub.com](https://github.com) and sign in
2. Click **"New"** (green button) to create repository
3. Repository settings:
   - **Name**: `signalscout`
   - **Description**: `AI Content Intelligence Platform`
   - **Visibility**: Public ✅
   - **DO NOT** check any initialize options
4. Click **"Create repository"**

## **Step 2: Upload Your Files**

### **Method A: Drag & Drop (Easiest)**
1. On your new GitHub repository page, click **"uploading an existing file"**
2. **Drag ALL files** from your `/Users/adedayoadeniyi/Documents/SignalScout/` folder into GitHub
3. Write commit message: `Initial SignalScout deployment`
4. Click **"Commit changes"**

### **Method B: Command Line**
```bash
cd /Users/adedayoadeniyi/Documents/SignalScout
git init
git add .
git commit -m "Initial SignalScout deployment"
git remote add origin https://github.com/YOUR_USERNAME/signalscout.git
git branch -M main
git push -u origin main
```

## **Step 3: Deploy Backend (Railway)**

1. Go to [Railway.app](https://railway.app)
2. Click **"Start a New Project"**
3. Click **"Deploy from GitHub repo"**
4. Select **"signalscout"** repository
5. Choose **"Deploy Backend"**
6. Set **Root Directory**: `/backend`

### **Add Environment Variables in Railway:**
1. Go to your project → **"Variables"** tab
2. Add these variables:
```
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_client_secret
REDDIT_USER_AGENT=SignalScout/1.0
YOUTUBE_API_KEY=your_youtube_api_key
OPENAI_API_KEY=your_openai_api_key
DATABASE_URL=sqlite:///./data/signalscout.db
```

3. **Copy your Railway URL** (looks like: `https://signalscout-production.railway.app`)

## **Step 4: Deploy Frontend (Vercel)**

1. Go to [Vercel.com](https://vercel.com)
2. Click **"New Project"**
3. **"Import Git Repository"** → Select **"signalscout"**
4. Configure:
   - **Framework Preset**: React
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

### **Add Environment Variable in Vercel:**
1. Go to **"Environment Variables"**
2. Add:
```
Name: REACT_APP_API_URL
Value: https://your-railway-backend-url.railway.app
```
3. Click **"Deploy"**

## **Step 5: Get Your API Keys**

### **Reddit API (Free)**
1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps)
2. Click **"Create App"**
3. Choose **"script"**
4. Copy `client_id` and `client_secret`

### **YouTube API (Free)**
1. Go to [console.developers.google.com](https://console.developers.google.com)
2. Create new project
3. Enable **"YouTube Data API v3"**
4. Create credentials → **"API Key"**

### **OpenAI API (Paid)**
1. Go to [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
2. Create new secret key
3. Add $5+ credit to your account

## **Step 6: Test Your Live App**

1. Open your Vercel URL (like: `https://signalscout.vercel.app`)
2. Check API status shows **"Connected"**
3. Try fetching Reddit trends
4. Generate some content!

## ✅ **Your SignalScout URLs**
- **Frontend**: `https://signalscout-username.vercel.app`
- **Backend API**: `https://signalscout-production.railway.app`

---

## 🆘 **Troubleshooting**

### **"API Not Connected" Error**
- Check Railway environment variables are set
- Verify Vercel has correct `REACT_APP_API_URL`

### **Build Failures**
- Check deployment logs in Railway/Vercel dashboard
- Ensure all files uploaded correctly

### **API Key Issues**
- Verify keys are active and have proper permissions
- Check quotas haven't been exceeded

---

**🎉 Once deployed, you'll have SignalScout live and ready to analyze trends worldwide!**