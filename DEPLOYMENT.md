# 🚀 Deployment Guide - SMARTII Assistant

## 🌐 Deploy to Cloud (Recommended)

### **Option 1: Deploy to Render + Vercel (FREE)**

This is the **EASIEST** way to get a shareable link that works on mobile and desktop!

#### **Step 1: Deploy Backend to Render**

1. **Create Render Account**: Go to [render.com](https://render.com) and sign up (FREE)

2. **Create New Web Service**:
   - Click "New +" → "Web Service"
   - Connect your GitHub repo: `https://github.com/abneeshsingh21/smartii-assistant-`
   - Configure:
     ```
     Name: smartii-backend
     Runtime: Python 3
     Build Command: cd backend && pip install -r ../requirements.txt
     Start Command: cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT
     Plan: Free
     ```

3. **Add Environment Variables**:
   ```
   GROQ_API_KEY=your_groq_key_here
   OPENAI_API_KEY=your_openai_key_here (optional)
   PORT=10000
   ```

4. **Deploy** - Wait 5-10 minutes. You'll get URL like:
   ```
   https://smartii-backend.onrender.com
   ```

#### **Step 2: Deploy Frontend to Vercel**

1. **Create Vercel Account**: Go to [vercel.com](https://vercel.com) and sign up (FREE)

2. **Import Project**:
   - Click "New Project"
   - Import from GitHub: `smartii-assistant-`
   - Configure:
     ```
     Framework Preset: Other
     Root Directory: frontend-v2
     Build Command: (leave empty - it's static)
     Output Directory: public
     ```

3. **Set Environment Variable**:
   ```
   VITE_BACKEND_URL=https://smartii-backend.onrender.com
   ```

4. **Deploy** - You'll get URL like:
   ```
   https://smartii-assistant.vercel.app
   ```

5. **Update Backend URL in Frontend**:
   - Edit `frontend-v2/public/js/script.js`
   - Change line 7:
   ```javascript
   API_BASE_URL: 'https://smartii-backend.onrender.com',
   BACKEND_WS_URL: 'wss://smartii-backend.onrender.com/ws',
   ```

**✅ DONE! Share this link with anyone:**
```
https://smartii-assistant.vercel.app
```

---

### **Option 2: Deploy to Railway (All-in-One)**

1. **Go to [railway.app](https://railway.app)** and sign up (FREE $5 credit)

2. **Click "New Project"** → "Deploy from GitHub repo"

3. **Select your repo**: `smartii-assistant-`

4. **Add Two Services**:

   **Backend Service:**
   ```
   Root Directory: backend
   Start Command: uvicorn app:app --host 0.0.0.0 --port $PORT
   Environment Variables:
     - GROQ_API_KEY=your_key
     - PORT=8000
   ```

   **Frontend Service:**
   ```
   Root Directory: frontend-v2
   Start Command: node server.js
   Environment Variables:
     - BACKEND_URL=https://your-backend.railway.app
   ```

5. **You'll get URLs like:**
   ```
   Backend:  https://smartii-backend-production.up.railway.app
   Frontend: https://smartii-frontend-production.up.railway.app
   ```

---

### **Option 3: Deploy to Heroku**

1. **Install Heroku CLI**:
   ```bash
   npm install -g heroku
   heroku login
   ```

2. **Create Heroku Apps**:
   ```bash
   cd C:\Users\lenovo\Desktop\smartii
   
   # Backend
   heroku create smartii-backend
   
   # Frontend
   heroku create smartii-frontend
   ```

3. **Add Buildpacks**:
   ```bash
   # Backend (Python)
   heroku buildpacks:set heroku/python -a smartii-backend
   
   # Frontend (Node.js)
   heroku buildpacks:set heroku/nodejs -a smartii-frontend
   ```

4. **Create Procfile for Backend**:
   ```
   web: cd backend && uvicorn app:app --host 0.0.0.0 --port $PORT
   ```

5. **Create Procfile for Frontend**:
   ```
   web: cd frontend-v2 && node server.js
   ```

6. **Deploy**:
   ```bash
   git push heroku main
   ```

---

## 📱 Mobile + Desktop Support

Your SMARTII will work on:
- ✅ **Windows** - Full features (voice, file access, app opening)
- ✅ **macOS** - Voice, web features
- ✅ **Android/iOS** - Voice, chat, web search (limited file/app access)
- ✅ **Any browser** - Chrome, Firefox, Safari, Edge

### Mobile Optimizations Already Included:
- ✅ Responsive design (works on all screen sizes)
- ✅ Touch-friendly buttons
- ✅ Mobile voice recognition (WebSpeech API)
- ✅ Progressive Web App (PWA) ready

---

## 🔐 Add API Keys

After deploying, add your API keys in the platform's dashboard:

### **Render (Backend)**:
1. Go to Dashboard → Your Service → Environment
2. Add:
   ```
   GROQ_API_KEY=gsk_your_groq_key
   OPENAI_API_KEY=sk_your_openai_key (optional)
   ```

### **Vercel (Frontend)**:
1. Go to Project Settings → Environment Variables
2. Add:
   ```
   VITE_BACKEND_URL=https://your-backend-url.onrender.com
   ```

---

## 🎯 Recommended: Render + Vercel

**Why?**
- ✅ **100% FREE** forever
- ✅ **Easy setup** - Just connect GitHub
- ✅ **Auto-deploy** on git push
- ✅ **SSL included** (HTTPS)
- ✅ **Custom domain** support
- ✅ **No credit card** required

**Performance:**
- Backend (Render): Free tier sleeps after 15 min idle, wakes in ~30s
- Frontend (Vercel): Always fast, global CDN
- Perfect for sharing with friends!

---

## 📤 Share Your SMARTII

Once deployed, share these links:

**Your Link:**
```
https://smartii-assistant.vercel.app
```

**Friend's Usage:**
1. Open link in browser (mobile or desktop)
2. Allow microphone permission
3. Click microphone button or say "Hey SMARTII"
4. Start talking!

**Features Available to Friends:**
- ✅ Voice commands
- ✅ Chat interface
- ✅ Web search with RAG
- ✅ Code execution
- ✅ Translation
- ✅ Calculator
- ✅ Weather info
- ⚠️ Limited: File access, app opening (only on your device)

---

## 🔄 Auto-Deploy on Git Push

After initial setup, every time you push to GitHub:
```bash
git add .
git commit -m "Update features"
git push origin main
```

Both Render and Vercel will **automatically redeploy**! 🚀

---

## 🆓 Free Tier Limits

### **Render (Backend):**
- ✅ FREE forever
- ⚠️ Sleeps after 15 minutes of inactivity
- ⚠️ 750 hours/month (enough for personal use)
- ✅ Wakes up automatically when accessed (~30 seconds)

### **Vercel (Frontend):**
- ✅ FREE forever
- ✅ 100 GB bandwidth/month
- ✅ Unlimited requests
- ✅ Always fast (no sleep)

**Tip:** First load might be slow (backend waking up), then it's fast!

---

## 🎨 Custom Domain (Optional)

### **Free Custom Domain:**
1. Get free domain from [Freenom](https://www.freenom.com) or [dot.tk](http://dot.tk)
2. In Vercel: Project Settings → Domains → Add Domain
3. Update DNS records as shown

**Example:**
```
smartii.tk → Your SMARTII
myassistant.ml → Your SMARTII
```

---

## 📊 Monitor Your Deployment

### **Render Dashboard:**
- View logs in real-time
- Check uptime and requests
- Monitor resource usage

### **Vercel Dashboard:**
- See deployment status
- Check analytics
- View error logs

---

## 🐛 Troubleshooting

### **Backend not working:**
1. Check Render logs for errors
2. Verify API keys are set
3. Check `requirements.txt` installed correctly

### **Frontend not connecting:**
1. Update `API_BASE_URL` in script.js
2. Check CORS settings in backend
3. Verify backend is running (visit backend URL)

### **Voice not working on mobile:**
1. Must use HTTPS (not HTTP)
2. Allow microphone permission
3. Use Chrome/Safari (best support)

---

## 🎉 Quick Start Checklist

- [ ] 1. Create Render account
- [ ] 2. Deploy backend to Render
- [ ] 3. Add GROQ_API_KEY to Render
- [ ] 4. Get backend URL from Render
- [ ] 5. Create Vercel account
- [ ] 6. Deploy frontend to Vercel
- [ ] 7. Update API_BASE_URL in script.js
- [ ] 8. Push changes to GitHub
- [ ] 9. Share Vercel URL with friends
- [ ] 10. Enjoy your cloud AI assistant! 🚀

---

**Need Help?** Contact: **Abneesh Singh**

**Estimated Time:** 20-30 minutes for first deployment
**Cost:** $0.00 (FREE forever on free tiers)
