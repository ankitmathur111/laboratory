# 🤖 Gemini AI - Python Learning Lab

A beginner-friendly Python project to explore and interact with **Google Gemini AI** using the official `google-genai` SDK. This project was built while learning Python and the Gemini API from scratch.

---

## 📌 What This Project Does

- Connects to Google Gemini AI using an API key stored securely in environment variables
- Sends prompts to the Gemini model and receives text responses
- Uses a **system instruction** to give the AI a custom persona (currently: William Shakespeare 🎭)
- Demonstrates how to configure model behavior using `temperature` and other settings

---

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or above
- A free Google AI Studio account → [aistudio.google.com](https://aistudio.google.com)
- VS Code (recommended editor)

---

### 1. Clone the Repository

```bash
git clone https://github.com/ankitmathur111/laboratory.git
cd laboratory
```

### 2. Install Dependencies

```bash
pip install google-genai
```

> ⚠️ Note: The older `google-generativeai` package is now deprecated (end-of-life: August 2025). This project uses the newer `google-genai` SDK introduced in October/November 2024.

### 3. Set Up Your API Key

Get your free API key from [Google AI Studio](https://aistudio.google.com) and store it as an environment variable on your machine.

**Windows:**
1. Search for **"Environment Variables"** in the Start menu
2. Under User Variables, click **New**
3. Set variable name as `GEMINI_API_KEY` and paste your key as the value
4. Restart VS Code completely after saving

**Linux / Mac:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

> 💡 If you use a custom environment variable name (e.g. `aistudio_key_laboratory`), pass it explicitly to the client as shown in the code.

### 4. Run the Script

```bash
python main.py
```

---

## 🧠 How It Works

```
Your Python Script  →  Gemini API (via google-genai SDK)  →  AI Response  →  Printed to Console
```

The script:
1. Reads the API key securely from environment variables using `os.getenv()`
2. Creates a Gemini client and selects the model
3. Sends a prompt along with a system instruction that shapes the AI's personality
4. Prints only the text response to the console

---

## 📁 Project Structure

```
laboratory/
│
├── main.py          # Main script to interact with Gemini AI
└── README.md        # You are here!
```

---

## ⚙️ Configuration

You can tweak the following in `main.py` to experiment:

| Setting | Current Value | What It Does |
|---|---|---|
| `model` | `gemini-2.5-flash` | The Gemini model being used |
| `system_instruction` | Shakespeare persona | Sets the AI's personality/role |
| `temperature` | `1.0` | Controls creativity (0.0 = factual, 2.0 = very creative) |
| `contents` | Your question/prompt | What you ask the AI |

---

## 🔐 Security Note

- **Never hardcode your API key** directly in the code
- The `.env` file (if used) should always be added to `.gitignore`
- This project uses `os.getenv()` to keep keys out of the codebase

---

## 📦 Dependencies

| Package | Purpose |
|---|---|
| `google-genai` | Official Google Gemini AI SDK (new unified SDK) |

---

## 📚 Resources

- [Google AI Studio](https://aistudio.google.com) — Get your free API key
- [google-genai on PyPI](https://pypi.org/project/google-genai/) — Package details
- [Gemini API Docs](https://ai.google.dev/gemini-api/docs) — Official documentation

---

## 🙋 About

This project was built by **[@ankitmathur111](https://github.com/ankitmathur111)** as part of a **personal Python learning journey** — exploring how to connect Python scripts to AI models and eventually build shareable web apps using tools like Streamlit.

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
