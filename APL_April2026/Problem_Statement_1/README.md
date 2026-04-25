# 🏏 SmartVenue AI
### Google Cloud · Build with AI · Agentic Premier League

An autonomous AI agent that manages crowd flow, queue times, and real-time
coordination for 50,000+ attendees at large sporting venues.

---

## 📁 Project Structure

```
smartvenue_ai/
├── venue_simulator.py    # Fake IoT sensor data (no hardware needed)
├── agent_tools.py        # Tool functions the AI agent can call
├── smartvenue_agent.py   # Core Gemini AI agent with function-calling
├── dashboard.py          # Streamlit demo UI (what judges will see)
├── Dockerfile            # For Google Cloud Run deployment
├── requirements.txt      # Python dependencies
└── README.md             # This file
```

---

## 🚀 Setup (5 minutes)

### Step 1 — Install Python packages

Open terminal in this folder and run:

```bash
pip install -r requirements.txt
```

This installs:
- `google-generativeai` — Gemini AI with function calling
- `streamlit` — The live demo dashboard
- `faker` — For realistic mock data

### Step 2 — Get a FREE Gemini API Key

1. Go to: **https://aistudio.google.com/apikey**
2. Sign in with Google
3. Click "Create API Key"
4. Copy the key

### Step 3 — Set your API key

**Mac/Linux:**
```bash
export GEMINI_API_KEY="your-key-here"
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your-key-here
```

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your-key-here"
```

---

## ▶ Running the Project

### Option A — Dashboard (best for demo to judges)

```bash
streamlit run dashboard.py
```

Opens at: **http://localhost:8501**

What to show judges:
1. Drag the "Match Minute" slider to **185** (halftime) — lots of alerts appear
2. Click **Run Agent Cycle** — watch Gemini reason and take actions
3. Show the action log (push notifications sent, staff alerted, signage updated)
4. Drag to **385** (post-match exit) — shows exit congestion scenario
5. Type a custom query like "Check Food Court A and redirect fans"

### Option B — Terminal only (quick test)

```bash
# Test at halftime (minute 185)
python smartvenue_agent.py 185

# Test at crowd surge (minute 90)
python smartvenue_agent.py 90

# Test post-match (minute 385)
python smartvenue_agent.py 385
```

You'll see the agent's step-by-step reasoning and tool calls printed live.

---

## 🏗 How It Works

```
Match Minute Input
      │
      ▼
VenueSimulator ──────────────────────────────────┐
(venue_simulator.py)                             │
Generates realistic:                             │
• Zone crowd densities (0-100%)                  │
• Gate queue wait times                          │
• Concession stall queues                        │
• Incidents (medical, overcrowding)              │
      │                                          │
      ▼                                          │
Agent Tools ◄────────────────────────────────────┘
(agent_tools.py)
Python functions the AI can call:
• scan_all_zones()           → read sensor data
• get_gate_queue_time(g)     → read sensor data
• send_push_notification()   → ACTION
• alert_ground_staff()       → ACTION
• update_digital_signage()   → ACTION
• open_additional_gate()     → ACTION
      │
      ▼
Gemini 1.5 Flash (Function Calling)
(smartvenue_agent.py)
• Reads system prompt with behavior rules
• Decides which tools to call
• Loops until all issues resolved
• Writes incident summary report
      │
      ▼
Streamlit Dashboard
(dashboard.py)
• Live zone density map
• Gate queue status
• Agent reasoning + actions
• Alert feed
```

---

## ☁️ Deploy to Google Cloud (for production demo)

### Prerequisites
- Google Cloud account (free tier works)
- [gcloud CLI installed](https://cloud.google.com/sdk/docs/install)

### Step 1 — Login and set project

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
```

### Step 2 — Enable required APIs

```bash
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Step 3 — Deploy with one command

```bash
gcloud run deploy smartvenue-ai \
  --source . \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars GEMINI_API_KEY=your-key-here \
  --memory 1Gi \
  --port 8080
```

After ~3 minutes you get a live URL like:
`https://smartvenue-ai-xxxxx-em.a.run.app`

That URL works for anyone — share with judges!

---

## 🎯 Demo Script for Judges (2 minutes)

**Minute 0:** "This is SmartVenue AI — an autonomous agent managing 50,000 fans"

**Show dashboard** — point to zone map, gate status, alert feed

**Drag to minute 185 (Halftime):**
"Halftime just started. Watch what happens — food courts are packed,
gates are backed up. Our agent will handle this."

**Click Run Agent:**
"The agent scans all zones, identifies critical areas, and takes action..."

Point to action log:
- "📲 Push notification sent to 48,000 fans — directing them to shortest queues"
- "📻 Staff alerted at Food Court A with URGENT priority"
- "📺 Digital signage updated at all concourse boards"

**Ask for custom query:** "What if a judge wants to check something specific?"
Type: `"Medical emergency reported at North Stand — what should we do?"`
Watch agent reason through it.

**Close:** "Built on Gemini 1.5 Flash with function calling, deployed on Google Cloud Run.
Zero real hardware needed — plugs into existing stadium IoT infrastructure."

---

## 🔧 Troubleshooting

**"ModuleNotFoundError: No module named 'google.generativeai'"**
```bash
pip install google-generativeai
```

**"GEMINI_API_KEY not set"**
```bash
export GEMINI_API_KEY="your-key"  # Linux/Mac
# OR paste it into the sidebar text box in the dashboard
```

**"quota exceeded" error from Gemini**
- You're on the free tier — wait 1 minute and try again
- Or get a paid key at console.cloud.google.com

**Streamlit port already in use**
```bash
streamlit run dashboard.py --server.port 8502
```
