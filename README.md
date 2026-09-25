# CodeReview AI
### *Instant, Pedagogical Code Feedback for the Next Generation of Developers*

[![Winner - IntelliAI Arena 2026](https://img.shields.io/badge/IntelliAI%20Arena%202026-Champs%20Winner-gold?style=for-the-badge&logo=trophy)](#)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](#)
[![Streamlit](https://img.shields.io/badge/Frontend-Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](#)
[![Google Gemini](https://img.shields.io/badge/AI%20Engine-Gemini%202.5-4285F4?style=for-the-badge&logo=google&logoColor=white)](#)
[![Ollama](https://img.shields.io/badge/Local%20Fallback-Ollama-black?style=for-the-badge&logo=ollama&logoColor=white)](#)

---

## The Problem
Students learning to program face an uphill battle:
- **Delayed Feedback:** Manual code reviews from instructors take days or weeks.
- **Inconsistent Peer Reviews:** Peer feedback often misses subtle logic bugs, antipatterns, and security risks.
- **Overwhelming Tooling:** Professional linters and static analyzers output cryptic warning codes rather than beginner-accessible explanations.

## The Solution
**CodeReview AI** bridges the gap between raw linters and human mentors. Students submit code in Python, Java, C++, or JavaScript and receive instantaneous, structured, and empathetic reviews:
- Explanations written in **accessible, beginner-friendly language**.
- Quantitative scorecards across readability, efficiency, correctness, and best practices.
- Interactive follow-up discussions with an embedded conversational tutor (**Ask CodeBuddy**).
- Zero-downtime resilience via seamless **Gemini Cloud -> Ollama Local** model fallbacks.

---

## Core Features

| Feature | Description |
| :--- | :--- |
| **Polyglot Parsing** | Native support for **Python, Java, C++, and JavaScript**. |
| **Granular Scorecard** | 0-10 numeric ratings covering Readability, Efficiency, Correctness, and Best Practices. |
| **Grading Engine** | Dynamic badge grading from **A+ to F** calibrated against beginner competencies. |
| **Line-Level Issue Cards** | Pinpointed issues flagged by severity: `Critical`, `Warning`, or `Suggestion`. |
| **Refactored Code Diff** | Side-by-side rewritten code demonstrating idiomatic patterns. |
| **Personalized Learning Tips** | Context-aware pedagogical notes reinforcing foundational computer science concepts. |
| **Ask CodeBuddy Chatbot** | Interactive in-app assistant to answer immediate questions about the reviewed snippet. |
| **Automated PDF Reports** | Professional, downloadable executive reviews built on `FPDF2`. |
| **Google Drive Export** | One-click direct backup of PDF summaries and raw JSON metadata to user Drive folders. |
| **Zero-Downtime Fallback** | Automated circuit-breaking: Falls back from `gemini-2.5-flash` to local offline `Ollama` models. |

---

## Architecture & Workflow

```text
[ Student Code Input ] 
       |
       v
[ Streamlit UI: app.py ] ---> [ gemini_helper.py ]
                                     |
                 -----------------------------------------
                 v                                       v
       [ Google Gemini API ]                   [ Local Ollama Engine ]
       (Primary: 2.5 Flash Lite/Flash)         (Fallback: Qwen 2.5 / Llama 3.2)
                 |                                       |
                 -----------------------------------------
                                     v
                          [ Structured JSON Review ]
                                     |
       -----------------------------------------------------------
       v                             v                             v
[ UI Scorecards & Diffs ]   [ Ask CodeBuddy Chat ]        [ Export Pipeline ]
                                                     -------------|-------------
                                                     v                           v
                                            [ pdf_report.py ]          [ drive_uploader.py ]
                                            (Local PDF Download)       (Google Drive Sync)
Tech Stack
Frontend & App Framework: Streamlit with customized Cyberpunk-styled CSS.

AI Core: Google GenAI SDK (gemini-2.5-flash-lite, gemini-2.5-flash).

Offline / Edge Fallback: Ollama running qwen2.5-coder:7b or llama3.2:3b.

Document Engine: fpdf2 for dynamic vectorized PDF generation.

Cloud Storage: Google Drive API v3 (OAuth 2.0).

Environment Management: python-dotenv.

Repository Structure
Plaintext
codereview-ai/
|-- app.py                       # Core Streamlit application & state orchestrator
|-- requirements.txt             # Project dependencies
|-- .env.example                 # Environment template
|-- .gitignore                   # Excludes tokens, credentials, caches
|
|-- .streamlit/
|   |-- config.toml              # Streamlit theme & execution configs
|
|-- assets/
|   |-- css/
|       |-- style.css            # Dark/Cyberpunk responsive stylesheet
|
|-- src/
|   |-- __init__.py
|   |-- services/
|       |-- __init__.py
|       |-- gemini_helper.py     # Gemini & Ollama prompt engineering logic
|       |-- pdf_report.py        # PDF builder and report compiler
|       |-- drive_uploader.py    # Google Drive OAuth & file sync engine
|
|-- test_samples/                # Ready-to-test multi-language programs
    |-- sample_python.py
    |-- sample_javascript.js
    |-- sample_java.java
    |-- sample_cpp.cpp
Quickstart Guide
1. Clone the Repository
Bash
git clone [https://github.com/your-username/codereview-ai.git](https://github.com/your-username/codereview-ai.git)
cd codereview-ai
2. Configure Environment
Create and activate an isolated virtual environment:

Bash
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
Install requirements:

Bash
pip install -r requirements.txt
3. Set Up API Credentials
Duplicate the sample environment file:

Bash
cp .env.example .env
Edit .env and supply your Gemini API key:

Code snippet
GEMINI_API_KEY=AIzaSy...your_actual_key_here
GEMINI_MODELS=gemini-2.5-flash-lite,gemini-2.5-flash

# Optional: Local Fallback Setup
USE_OLLAMA_FALLBACK=true
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5-coder:7b
4. Launch the Application
Bash
streamlit run app.py
Integrations & Reliability
Gemini-to-Ollama Fallback
If the cloud model encounters rate limits or upstream 503 High Demand errors, the pipeline dynamically reroutes the prompt to your local Ollama daemon without breaking the user session.

Bash
# Pull the recommended coding model
ollama pull qwen2.5-coder:7b

# Alternative lightweight models
ollama pull llama3.2:3b
ollama pull codellama:7b
Google Drive Setup
To enable remote report archiving:

Enable the Google Drive API in Google Cloud Console.

Generate an OAuth 2.0 Client ID (Desktop Application) and download it as credential.json in the root folder.

Authenticate once via CLI:

Bash
python src/services/drive_uploader.py --setup
Enter target folder links directly inside the app UI to upload PDF summaries and raw JSON audits automatically.

Exported PDF Reports
Generated PDF reports package the entire audit for offline review or grading hand-ins:

Original source code snippet with syntax framing.

Tabular breakdown across all 4 evaluation metrics.

Color-coded grade badge with overall summary narrative.

Line-by-line issue breakdowns with priority indicators.

Refactored solution snippet and custom recommendations.

IntelliAI Arena 2026
Built and submitted as the award-winning entry for IntelliAI Arena 2026, CodeReview AI demonstrates how intelligent multi-tier LLM architectures can democratize one-on-one computer science education.
