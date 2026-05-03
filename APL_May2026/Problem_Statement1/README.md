# 🏏 CricketLens AI – Problem Statement 1
### Build With AI :: Agentic Premier League 2026

> AI-powered cricket shot analysis using Gemini Vision API — upload an image or video frame and get detailed shot statistics, ball delivery insights, and match commentary.

---

## 🚀 Quick Start (Windows Laptop)

### Prerequisites
- Python 3.10+
- pip

### 1. Install dependencies
```bash
cd Problem_Statement1
pip install -r requirements.txt
```

### 2. Run the app
```bash
streamlit run app.py
```

The app opens at `http://localhost:8501`

### 3. Enter your Gemini API Key
Enter your Gemini API key in the **sidebar** (it is masked for security).
Get one free at: https://aistudio.google.com

---

## 📂 Project Structure

```
Problem_Statement1/
├── app.py                    # Main Streamlit app
├── requirements.txt          # Python dependencies
├── Dockerfile                # For Google Cloud Run
├── deploy.sh                 # Cloud Run deployment script
├── .streamlit/
│   └── config.toml           # Streamlit server config
├── assets/
│   └── style.css             # Custom dark-theme CSS
└── utils/
    ├── __init__.py
    ├── analyzer.py           # Gemini Vision analyzer
    ├── stats.py              # Statistics & DataFrame manager
    └── session.py            # Streamlit session state helpers
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔑 Masked API Key | Secure password-type input for Gemini key |
| 📸 Image Analysis | Upload JPG/PNG cricket images |
| 🎬 Video Frame | Upload MP4/MOV – first meaningful frame extracted |
| 🧠 Shot Detection | Identifies shot type, ball type, pitch length |
| 📊 Statistics | Interactive Plotly charts (pie, bar, wagon wheel) |
| 📋 History | All analyses logged in-session with timestamps |
| ⬇️ CSV Export | Download all stats as CSV |
| 🌙 Dark Theme | IPL-inspired dark green theme |

---

## ☁️ Google Cloud Run Deployment

```bash
# Authenticate with Google Cloud
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Deploy (single command)
bash deploy.sh
```

This will:
1. Build the Docker image using Cloud Build
2. Push to Google Container Registry
3. Deploy to Cloud Run (auto-scales, HTTPS endpoint)

---

## 🏏 Problem Statement Solved

**Problem:** It's impossible to keep track of a cricket match in terms of which shot was played, when it was played, and what kind of ball was delivered to get data analysis.

**Solution:** CricketLens AI uses **Gemini 2.5 Flash's vision capability** to analyze any cricket image or video frame and extract:
- Shot type played
- Ball delivery type & pitch length  
- Estimated runs scored & shot direction
- Ball-by-ball commentary
- Player technique & tactical insights
- Interactive statistics dashboard with wagon wheel

---

*Built at Build With AI :: APL, 3rd May 2026 | GDG Cloud New Delhi*
