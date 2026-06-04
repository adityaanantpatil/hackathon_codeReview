🔍 CodeReview AI

📌 Problem Statement
Students learning programming often submit assignments without knowing if their code is clean, efficient, or following best practices. Waiting for teacher feedback is slow, and peer review is inconsistent. There is no instant, intelligent code review tool designed for learners.

💡 Solution
CodeReview AI is a web app where students paste or upload their code and receive instant AI-generated feedback — explained in beginner-friendly language — covering code quality, logic errors, style issues, and improvement suggestions.

✨ Features
🌐 Multi-language support — Python, Java, C++, JavaScript
🤖 AI-generated feedback via Google Gemini — logic, structure, style
📊 Scorecard — Readability, Efficiency, Correctness, Best Practices (scored 0–10)
🏅 Overall Grade — A+ to F, with color-coded badge
🐛 Issue cards — line-level comments with severity (Critical / Warning / Suggestion)
✨ Improved Code — AI-rewritten version of your code
📘 Learning Tips — personalized suggestions based on your code
💬 Ask CodeBuddy chatbot — appears after review and answers follow-up questions about the reviewed code using the same AI backend
📄 PDF Report — downloadable full review report via FPDF
🎨 Cyberpunk dark UI — interactive, terminal-inspired design

🛠️ Tech Stack
Frontend : Streamlit & CSS
Backend : Python 
AI Engine : Google Gemini API (gemini-2.5-flash)

📁 Project Structure
codereview-ai/
├── app.py               # Main Streamlit app — UI & routing
├── gemini_helper.py     # Gemini API calls & prompt engineering
├── pdf_report.py        # PDF report generation with FPDF
├── .env                 # API key -(MUST BE FILLED BY USER)
├── .gitignore           # Ignores .env and other sensitive files
├── requirements.txt     # All Python dependencies
└── assets/
    └── style.css        # Custom dark theme CSS

⚙️ Installation 
1. Clone the repository
git clone https://github.com/your-username/codereview-ai.git
cd codereview-ai
2. Install dependencies
pip install -r requirements.txt
3. Set up your API key
Create a .env file in the root directory:
GEMINI_API_KEY=your_api_key_here
4. Run the app
streamlit run app.py


🧠 How the AI Works
Your code is sent to Gemini 1.5 Flash with a structured prompt
Gemini returns a JSON response with scores, issues, improved code, and tips
The app parses and displays it across 4 interactive tabs
After the review appears, the **Ask CodeBuddy** chatbot window becomes available so students can ask follow-up questions like “Why is this bug happening?” or “Show me the corrected snippet.”
Optionally, you can download a PDF report of the full review

Review depth options:
Quick — brief overview of major issues
Standard — full review with explanations
Deep — includes time/space complexity + design pattern suggestions


📄 PDF Report Contents
When you click Download PDF Report, you get:

✅ Your submitted code
✅ Score table (all 4 metrics)
✅ Overall grade
✅ All issues with line numbers and explanations
✅ AI-improved version of the code
✅ Personalized learning tips
✅ Summary paragraph
✅ Timestamp + "Powered by Google Gemini" footer

---

## 🧩 Code Files Used in This Project and How They Help

The project has been cleaned so the UI logic is kept mainly in `app.py`. Earlier UI helper files like `components.py` and `state.py` were removed to keep the project simpler and easier to explain.

### 1. `app.py` — Main Website File
This is the main Streamlit application. It controls the complete website flow:

- loads the page layout and CSS
- shows the hero section, language selector, review depth selector, upload option, and code editor
- sends the submitted code to Gemini through `gemini_helper.py`
- displays scorecards, issues, improved code, learning tips, and summary
- shows the small **Ask CodeBuddy** chatbot window after the review is generated
- creates the PDF download button
- creates the Google Drive upload button
- manages Streamlit session state so the result stays visible after analysis

This file is important because it connects the frontend and backend together.

### 2. `assets/css/style.css` — Custom Website Styling
This file controls the visual design of the Streamlit website.

It helps by:

- giving the app a clean CodeBuddy-style frontend
- styling the background, cards, buttons, editor box, scorecards, issue cards, chatbot window, and Drive status boxes
- making the UI look more polished than default Streamlit
- keeping the frontend stack simple because no JavaScript is used

The upload button duplicate text issue was fixed here by removing the extra CSS-injected Upload text.

### 3. `src/services/gemini_helper.py` — AI Code Review Logic
This file handles all communication with the Google Gemini API.

It helps by:

- reading the `GEMINI_API_KEY` from `.env`
- creating the Gemini client
- sending the student's code, language, and review depth to Gemini
- requesting a structured JSON response
- returning scores, issues, improved code, learning tips, and summary back to `app.py`
- answering chatbot follow-up questions after a review using the same Gemini/Ollama backend logic

This keeps AI-related logic separate from the website UI.

### 4. `src/services/pdf_report.py` — PDF Report Generator
This file creates the downloadable PDF report.

It helps by:

- taking the original code and AI review result
- creating a formatted PDF using FPDF
- adding score tables, grade, issues, improved code, learning tips, and summary
- returning PDF bytes to Streamlit so the user can download the report

This is used when the user clicks **Download PDF Report**.

### 5. `src/services/drive_uploader.py` — Google Drive Upload Feature
This file handles saving reports to Google Drive.

It helps by:

- checking if Google Drive is configured using `credential.json`
- opening the OAuth login flow during first setup
- creating or reusing a Google Drive folder named `CodeReview AI Reports`
- uploading the PDF report
- uploading a JSON copy of the full review data
- returning Drive links to show inside the website

This is used when the user clicks **Save to Google Drive**.

### 6. `requirements.txt` — Python Dependencies
This file lists all packages needed to run the project.

It helps by letting anyone install all required libraries using:

```bash
pip install -r requirements.txt
```

Main dependencies include:

- `streamlit` for the web app
- `google-genai` for Gemini AI
- `fpdf2` for PDF generation
- `python-dotenv` for loading `.env`
- Google auth libraries for Drive upload

### 7. `.env` — API Key File
This file stores the Gemini API key locally.

Example:

```env
GEMINI_API_KEY=your_api_key_here
```

It is not uploaded to GitHub because it contains a private key.

### 8. `.env.example` — Sample Environment File
This file shows the correct format for `.env`.

It helps other users understand what key is required without exposing the real API key.

### 9. `.gitignore` — Files Not to Upload
This file prevents private or unnecessary files from being committed.

It ignores:

- `.env`
- `credential.json`
- `token.json`
- virtual environments
- Python cache folders
- generated PDF files

This keeps the repository clean and protects private credentials.

### 10. `.streamlit/config.toml` — Streamlit Settings
This file stores Streamlit configuration.

It helps by:

- setting app theme options
- keeping Streamlit behavior consistent across systems

### 11. `test_samples/` — Example Code Files
This folder contains sample programs for Python, JavaScript, Java, and C++.

It helps by:

- giving demo inputs for testing the website
- making it easier to show how the app reviews different languages
- helping during presentations when no external code file is available

---

## 📁 Current Clean Project Structure

```text
codereview-ai-clean/
├── app.py                         # Main Streamlit website and UI logic
├── README.md                      # Project explanation and setup guide
├── requirements.txt               # Python dependencies
├── .env.example                   # Example API key format
├── .gitignore                     # Ignores private/cache files
├── .streamlit/
│   └── config.toml                # Streamlit app configuration
├── assets/
│   └── css/
│       └── style.css              # All custom CSS styling
├── src/
│   ├── __init__.py
│   └── services/
│       ├── __init__.py
│       ├── gemini_helper.py       # Gemini API review logic
│       ├── pdf_report.py          # PDF report generation
│       └── drive_uploader.py      # Google Drive upload logic
└── test_samples/
    ├── sample_python.py
    ├── sample_javascript.js
    ├── sample_java.java
    └── sample_cpp.cpp
```

---

## 🧹 Cleanup Note

If Python cache folders appear after running the app, they can be safely deleted. They are automatically created by Python and are not part of the source code.

PowerShell command:

```powershell
Get-ChildItem -Recurse -Directory -Filter __pycache__ | Remove-Item -Recurse -Force
```

Also delete any `.pyc` files if needed:

```powershell
Get-ChildItem -Recurse -Filter *.pyc | Remove-Item -Force
```

---

## ☁️ Google Drive Setup

To use the **Save to Google Drive** button:

1. Enable **Google Drive API** in Google Cloud Console.
2. Create OAuth Client credentials for a Desktop app.
3. Download the file as `credential.json`.
4. Place `credential.json` in the project root beside `app.py`.
5. Run:

```bash
python src/services/drive_uploader.py --setup
```

6. Restart the app:

```bash
streamlit run app.py
```

After this, the website can upload both the PDF report and JSON review data to Google Drive.



---

## ☁️ Saving to a User's Google Drive Folder

The website now includes a **User Google Drive folder link** field in the results section.

How it works:

1. The user creates a folder in Google Drive.
2. The user copies the folder link.
3. The user pastes that folder link into the website.
4. The app uploads the PDF report and JSON review file into that folder.

Important permission note:

A Drive folder link by itself does not give upload permission. The Google account that authorized the app must have edit access to the folder.

For local/demo use:

- Put `credential.json` beside `app.py`.
- Run:

```bash
python src/services/drive_uploader.py --setup
```

- Sign in with the Google account that should upload the files.
- If you want to upload to another user's folder, that user must share the folder with edit access to the signed-in Google account.
- Paste their folder link in the website and click **Save to Google Drive**.

If you changed from the old Drive setup, delete `token.json` and run setup again because the app now uses a Drive scope that supports user-provided folder links.

```bash
del token.json
python src/services/drive_uploader.py --setup
```

For a public multi-user website, every user should authenticate with their own Google account using OAuth. A simple pasted folder link is not enough for a production public app because Google Drive requires account permission before files can be written.


---

## 🔁 Gemini Fallback + Ollama Backup

Sometimes Gemini may return:

```text
503 UNAVAILABLE: This model is currently experiencing high demand
```

This usually means the selected Gemini model is temporarily overloaded. The app now handles this by trying multiple models automatically, then falling back to local Ollama.

### Recommended Gemini Models

In `.env`, use:

```env
GEMINI_MODELS=gemini-2.5-flash-lite,gemini-2.5-flash
```

`gemini-2.5-flash-lite` is used first because it is lighter and usually better for quick/high-volume tasks. If it fails, the app tries `gemini-2.5-flash`.

### Ollama Backup

Install/start Ollama, then pull a code-friendly model:

```bash
ollama pull qwen2.5-coder:7b
```

Then add this to `.env`:

```env
USE_OLLAMA_FALLBACK=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
```

If Gemini fails because of high demand, the app will automatically send the review request to Ollama.

Other useful Ollama options:

```bash
ollama pull llama3.2:3b
ollama pull codellama:7b
```

Then change:

```env
OLLAMA_MODEL=llama3.2:3b
```

or:

```env
OLLAMA_MODEL=codellama:7b
```

### Notes

- Ollama runs locally, so it is slower or faster depending on your laptop/PC.
- Ollama quality depends on the model you pull.
- Gemini output is usually more consistent for structured JSON.
- Ollama is useful as a backup when Gemini has quota or high-demand errors.
