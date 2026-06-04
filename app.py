"""
CodeBuddy / CodeReview AI - Main Streamlit Application

Tech stack intentionally remains:
- Streamlit for frontend
- CSS for styling
- Python for backend logic
- Google Gemini for AI review
"""

from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path
from typing import Any

import streamlit as st

from src.services.gemini_helper import get_code_review, has_api_key, has_any_ai_backend
from src.services.pdf_report import generate_pdf_report
from src.services.drive_uploader import is_drive_configured, save_review_to_drive


# ─────────────────────────────────────────────────────────────────────────────
# App constants
# ─────────────────────────────────────────────────────────────────────────────

APP_NAME = "CodeBuddy"
PAGE_TITLE = "CodeBuddy — AI Code Review for Learners"
PAGE_ICON = "🟩"

ROOT_DIR = Path(__file__).resolve().parent
CSS_PATH = ROOT_DIR / "assets" / "css" / "style.css"

SUPPORTED_LANGUAGES = ["Python", "JavaScript", "Java", "C++"]
REVIEW_DEPTHS = ["Quick", "Standard", "Deep"]

LANGUAGE_ICONS = {
    "Python": "🐍",
    "JavaScript": "🌐",
    "Java": "☕",
    "C++": "⚙️",
}

FILE_TYPES = {
    "Python": ["py"],
    "JavaScript": ["js"],
    "Java": ["java"],
    "C++": ["cpp", "cc", "cxx", "hpp", "h"],
}

ALL_UPLOAD_TYPES = sorted({ext for extensions in FILE_TYPES.values() for ext in extensions})

DEFAULT_CODE = """def calculate_sum(a,b):
result=a+b
print("The sum is: " + str(result))
return result

x = calculate_sum(5,10)
print(x)"""

EXAMPLES = {
    "Python": {
        "title": "Bubble Sort",
        "description": "Classic sorting with a few beginner mistakes.",
        "code": """def bubble_sort(items):
    for i in range(len(items)):
        for j in range(len(items)):
            if items[j] > items[j + 1]:
                temp = items[j]
                items[j] = items[j + 1]
                items[j + 1] = temp
    return items

numbers = [5, 3, 8, 1]
print(bubble_sort(numbers))""",
    },
    "JavaScript": {
        "title": "Fetch & Display",
        "description": "API call with missing error handling.",
        "code": """async function loadUsers() {
  let response = await fetch('/api/users')
  let data = await response.json()
  document.getElementById('users').innerHTML = data
}

loadUsers()""",
    },
    "Java": {
        "title": "Calculator Class",
        "description": "Small OOP example with style issues.",
        "code": """public class Calculator {
    public static void main(String[] args) {
        int a=5;
        int b=10;
        int result=a+b;
        System.out.println("Sum is: " + result);
    }
}""",
    },
    "C++": {
        "title": "Simple Sum",
        "description": "Basic function with common C++ best-practice gaps.",
        "code": """#include <iostream>
using namespace std;

int calculateSum(int a,int b) {
    int result=a+b;
    cout << "Sum is: " << result << endl;
    return result;
}

int main() {
    int x = calculateSum(5,10);
    cout << x << endl;
    return 0;
}""",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# UI helpers kept inside app.py to reduce extra UI files
# ─────────────────────────────────────────────────────────────────────────────

def load_css() -> None:
    """Load external CSS file."""
    if CSS_PATH.exists():
        st.markdown(f"<style>{CSS_PATH.read_text(encoding='utf-8')}</style>", unsafe_allow_html=True)


def init_state() -> None:
    """Initialize all Streamlit session values."""
    defaults = {
        "review_data": None,
        "editor_code": DEFAULT_CODE,
        "analyzed": False,
        "selected_language": "Python",
        "selected_depth": "Standard",
        "pdf_bytes_cache": None,
        "pdf_cache_signature": None,
        "drive_upload_result": None,
        "drive_folder_link": "",
    }
    for key, value in defaults.items():
        st.session_state.setdefault(key, value)


def reset_review(keep_code: bool = True) -> None:
    """Clear old review output and cached files."""
    st.session_state.review_data = None
    st.session_state.analyzed = False
    st.session_state.pdf_bytes_cache = None
    st.session_state.pdf_cache_signature = None
    st.session_state.drive_upload_result = None
    if not keep_code:
        st.session_state.editor_code = ""


def load_example(language: str, code: str) -> None:
    """Load one of the example snippets into the editor."""
    st.session_state.selected_language = language
    st.session_state.editor_code = code
    reset_review(keep_code=True)


def language_label(language: str) -> str:
    return f"{LANGUAGE_ICONS.get(language, '💻')} {language}"


def language_from_label(label: str) -> str:
    for language in SUPPORTED_LANGUAGES:
        if label.endswith(language):
            return language
    return "Python"


def render_background() -> None:
    st.markdown(
        """
        <div class="blob blob-1"></div>
        <div class="blob blob-2"></div>
        <div class="blob blob-3"></div>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        f"""
        <header class="app-header">
            <div class="brand-lockup">
                <div class="brand-icon">⌁</div>
                <div>
                    <div class="brand-name">{APP_NAME}</div>
                    <div class="brand-caption">AI code review for learners</div>
                </div>
            </div>
            <div class="nav-pills">
                <span class="nav-pill active">Review</span>
            </div>
        </header>
        """,
        unsafe_allow_html=True,
    )


def render_hero() -> None:
    st.markdown(
        """
        <section class="hero-panel">
            <div class="hero-tag">✨ Instant feedback for student coders</div>
            <h1 class="hero-title">Get your code reviewed<br><span>in seconds, not days</span></h1>
            <p class="hero-subtitle">
                Paste your code, pick a language, and let CodeBuddy explain what is working,
                what is not, and how to improve it — in simple English.
            </p>
            <div class="features-strip">
                <span class="feature-chip">🔍 Logic Errors</span>
                <span class="feature-chip">🎨 Style Issues</span>
                <span class="feature-chip">⚡ Efficiency Tips</span>
                <span class="feature-chip">📝 Line Comments</span>
                <span class="feature-chip">📊 Score Card</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def open_editor_card(title: str = "Code review workspace") -> None:
    st.markdown(
        f"""
        <section class="editor-card">
            <div class="editor-header">
                <div class="editor-dots">
                    <span class="dot dot-red"></span>
                    <span class="dot dot-yellow"></span>
                    <span class="dot dot-green"></span>
                </div>
                <span class="editor-title">{escape(title)}</span>
            </div>
        """,
        unsafe_allow_html=True,
    )


def close_editor_card() -> None:
    st.markdown("</section>", unsafe_allow_html=True)


def render_counts(code: str) -> None:
    line_count = len(code.splitlines()) if code else 0
    char_count = len(code)
    st.markdown(
        f"""
        <div class="editor-meta">
            <span>{line_count} lines</span>
            <span>·</span>
            <span>{char_count} chars</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def score_color(score: int) -> str:
    if score >= 8:
        return "#4f8a5b"
    if score >= 5:
        return "#b48a3d"
    return "#d9786f"


def render_metric_card(name: str, score: int, icon: str) -> str:
    score = max(0, min(int(score or 0), 10))
    width = score * 10
    return f"""
    <div class="metric-card">
        <div class="metric-topline">
            <span>{escape(name)}</span>
            <span>{escape(icon)}</span>
        </div>
        <div class="metric-score">{score}<span>/10</span></div>
        <div class="progress-track">
            <div class="progress-fill" style="width:{width}%; background:{score_color(score)};"></div>
        </div>
    </div>
    """


def render_grade_badge(grade: str) -> None:
    grade_safe = escape(grade or "N/A")
    grade_class = (
        "grade-green" if grade in {"A+", "A"}
        else "grade-blue" if grade == "B"
        else "grade-amber" if grade == "C"
        else "grade-red"
    )
    st.markdown(
        f"""
        <div class="grade-card">
            <div class="grade-label">Overall Performance</div>
            <div class="grade-value {grade_class}">{grade_safe}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_issue_card(issue: dict[str, Any]) -> None:
    severity = escape(str(issue.get("severity", "Suggestion")))
    title = escape(str(issue.get("title", "Issue")))
    lines = escape(str(issue.get("lines", "N/A")))
    explanation = escape(str(issue.get("explanation", "No explanation provided.")))
    fix = escape(str(issue.get("fix", "")))

    lowered = severity.lower()
    if "critical" in lowered:
        card_class = "issue-critical"
        icon = "🔴"
    elif "warning" in lowered:
        card_class = "issue-warning"
        icon = "🟡"
    else:
        card_class = "issue-suggestion"
        icon = "🔵"

    fix_html = f'<div class="issue-fix"><strong>💡 Fix:</strong> {fix}</div>' if fix else ""
    st.markdown(
        f"""
        <article class="issue-card {card_class}">
            <div class="issue-head">
                <h4>{icon} {title}</h4>
                <span class="issue-badge">{severity}</span>
            </div>
            <div class="issue-line">Line(s): {lines}</div>
            <p>{explanation}</p>
            {fix_html}
        </article>
        """,
        unsafe_allow_html=True,
    )


def render_tip(tip: str, index: int) -> None:
    st.markdown(
        f"""
        <div class="tip-card">
            <span class="tip-index">{index}</span>
            <p>{escape(tip)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_summary(summary: str) -> None:
    st.markdown(
        f"""
        <div class="summary-card">
            {escape(summary or 'No summary available.')}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_example_card(language: str, title: str, description: str) -> None:
    icon = LANGUAGE_ICONS.get(language, "💻")
    st.markdown(
        f"""
        <div class="example-card-static">
            <div class="example-lang">{icon} {escape(language)}</div>
            <div class="example-name">{escape(title)}</div>
            <div class="example-desc">{escape(description)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_cached_pdf_report(code: str, language: str, review_data: dict) -> bytes:
    """Generate the PDF once and keep it in session state."""
    signature = f"{language}|{len(code)}|{review_data.get('overall_grade', '')}|{review_data.get('summary', '')}"
    if (
        st.session_state.pdf_bytes_cache is not None
        and st.session_state.pdf_cache_signature == signature
    ):
        return st.session_state.pdf_bytes_cache

    pdf_bytes = generate_pdf_report(code, language, review_data)
    st.session_state.pdf_bytes_cache = pdf_bytes
    st.session_state.pdf_cache_signature = signature
    return pdf_bytes


# ─────────────────────────────────────────────────────────────────────────────
# Streamlit page setup
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title=PAGE_TITLE,
    page_icon=PAGE_ICON,
    layout="wide",
    initial_sidebar_state="collapsed",
)

load_css()
init_state()
render_background()
render_header()
render_hero()


# ─────────────────────────────────────────────────────────────────────────────
# Editor panel
# ─────────────────────────────────────────────────────────────────────────────

open_editor_card("Code review workspace")

control_col_1, control_col_2, control_col_3 = st.columns([1.1, 1.1, 1.4])

with control_col_1:
    selected_label = st.selectbox(
        "Language",
        [language_label(language) for language in SUPPORTED_LANGUAGES],
        index=SUPPORTED_LANGUAGES.index(st.session_state.selected_language),
        key="language_picker",
    )
    st.session_state.selected_language = language_from_label(selected_label)

with control_col_2:
    st.session_state.selected_depth = st.selectbox(
        "Review depth",
        REVIEW_DEPTHS,
        index=REVIEW_DEPTHS.index(st.session_state.selected_depth),
        key="depth_picker",
    )

with control_col_3:
    uploaded_file = st.file_uploader(
        "Upload a file",
        type=ALL_UPLOAD_TYPES,
        help="Supported: .py, .js, .java, .cpp, .cc, .cxx, .hpp, .h",
        label_visibility="visible",
    )

if uploaded_file is not None:
    try:
        st.session_state.editor_code = uploaded_file.read().decode("utf-8")
        suffix = uploaded_file.name.rsplit(".", 1)[-1].lower()
        for language, extensions in FILE_TYPES.items():
            if suffix in extensions:
                st.session_state.selected_language = language
                break
    except UnicodeDecodeError:
        st.error("This file could not be decoded as UTF-8 text. Please upload a plain source-code file.")

st.markdown("<div class='editor-help'>Paste your code in the editor below, or upload a source file above.</div>", unsafe_allow_html=True)
code_input = st.text_area(
    "Paste your code below",
    key="editor_code",
    height=500,
    placeholder="# Paste your code here...\ndef hello():\n    print('Hello, World!')",
)
render_counts(code_input)

button_col_1, button_col_2, button_col_3 = st.columns([1.2, 1.0, 2.4])
with button_col_1:
    analyze_button = st.button("Review My Code", type="primary", use_container_width=True)
with button_col_2:
    clear_button = st.button("Clear", use_container_width=True)
with button_col_3:
    st.empty()

close_editor_card()

if clear_button:
    st.session_state.editor_code = ""
    reset_review(keep_code=True)
    st.rerun()

if analyze_button:
    if not code_input.strip():
        st.error("Please paste or upload some code first.")
    elif not has_any_ai_backend():
        st.error(
            "No AI backend is configured. Add GEMINI_API_KEY to .env or enable Ollama fallback."
        )
    else:
        with st.spinner("CodeBuddy is reviewing your code…"):
            review_data = get_code_review(
                code=code_input,
                language=st.session_state.selected_language,
                depth=st.session_state.selected_depth,
            )

        if review_data.get("error"):
            st.error(review_data.get("message", "Something went wrong while reviewing the code."))
            reset_review(keep_code=True)
        else:
            st.session_state.review_data = review_data
            st.session_state.analyzed = True
            st.session_state.pdf_bytes_cache = None
            st.session_state.pdf_cache_signature = None
            st.session_state.drive_upload_result = None
            if review_data.get("overall_grade") in {"A+", "A"}:
                st.balloons()
            st.rerun()


# ─────────────────────────────────────────────────────────────────────────────
# Results panel
# ─────────────────────────────────────────────────────────────────────────────

if st.session_state.analyzed and st.session_state.review_data:
    review_data = st.session_state.review_data
    scores = review_data.get("scores", {})

    st.markdown("<section class='result-shell'>", unsafe_allow_html=True)
    model_used = review_data.get("_model_used", "AI model")
    provider_used = review_data.get("_provider", "AI")
    st.markdown(
        f"""
        <div class="section-heading">
            <h2>📊 Review Results</h2>
            <span class="feature-chip">Model: {escape(provider_used)} · {escape(model_used)}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    score_cols = st.columns(4)
    metric_specs = [
        ("Readability", "readability", "📖"),
        ("Efficiency", "efficiency", "⚡"),
        ("Correctness", "correctness", "✅"),
        ("Best Practices", "best_practices", "🌱"),
    ]
    for col, (name, key, icon) in zip(score_cols, metric_specs):
        with col:
            st.markdown(render_metric_card(name, int(scores.get(key, 0) or 0), icon), unsafe_allow_html=True)

    render_grade_badge(review_data.get("overall_grade", "N/A"))

    issues_tab, improved_tab, tips_tab, summary_tab = st.tabs(
        ["🐛 Issues Found", "✨ Improved Code", "📘 Learning Tips", "📊 Summary"]
    )

    with issues_tab:
        issues = review_data.get("issues", [])
        if issues:
            for issue in issues:
                render_issue_card(issue)
        else:
            st.success("No issues found. Your code looks strong!")

    with improved_tab:
        improved_code = review_data.get("improved_code", "")
        if improved_code:
            st.code(improved_code, language=st.session_state.selected_language.lower())
        else:
            st.info("No rewritten version was suggested.")

    with tips_tab:
        learning_tips = review_data.get("learning_tips", [])
        if learning_tips:
            for index, tip in enumerate(learning_tips, 1):
                render_tip(tip, index)
        else:
            st.info("No extra learning tips were returned.")

    with summary_tab:
        render_summary(review_data.get("summary", ""))
        st.markdown("#### Submitted Code")
        st.code(st.session_state.editor_code, language=st.session_state.selected_language.lower())

    st.markdown("#### Export & Cloud Save")

    pdf_bytes = None
    try:
        pdf_bytes = get_cached_pdf_report(
            st.session_state.editor_code,
            st.session_state.selected_language,
            review_data,
        )
    except Exception as exc:
        st.error(f"PDF report could not be generated: {exc}")

    drive_result = st.session_state.get("drive_upload_result")
    if drive_result:
        if drive_result.get("success"):
            links = []
            if drive_result.get("pdf_link"):
                links.append(f"<a href='{drive_result['pdf_link']}' target='_blank'>PDF</a>")
            if drive_result.get("json_link"):
                links.append(f"<a href='{drive_result['json_link']}' target='_blank'>JSON</a>")
            if drive_result.get("folder_link"):
                links.append(f"<a href='{drive_result['folder_link']}' target='_blank'>Open Drive Folder</a>")
            st.markdown(
                f"<div class='drive-status drive-success'>✅ Saved to Google Drive: {' · '.join(links)}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div class='drive-status drive-error'>⚠️ Drive upload failed: {escape(drive_result.get('error', 'Unknown error'))}</div>",
                unsafe_allow_html=True,
            )

    st.session_state.drive_folder_link = st.text_input(
        "User Google Drive folder link",
        value=st.session_state.get("drive_folder_link", ""),
        placeholder="Paste user's Google Drive folder link here",
        help=(
            "The signed-in Google account must own this folder or have edit access. "
            "If left blank, the app saves to the default CodeReview AI Reports folder."
        ),
    )

    if not is_drive_configured():
        st.markdown(
            "<div class='drive-status drive-warning'>☁️ Google Drive API is not configured yet. A folder link alone is not enough. Add <strong>credential.json</strong> beside <strong>app.py</strong>, then run <code>python src/services/drive_uploader.py --setup</code>.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<div class='drive-status drive-info'>ℹ️ To save into another user's folder, ask them to share that folder with edit access to the Google account used during Drive setup, then paste the folder link above.</div>",
            unsafe_allow_html=True,
        )

    action_col_1, action_col_2, action_col_3, action_col_4 = st.columns(4)

    with action_col_1:
        if pdf_bytes:
            st.download_button(
                "Download PDF Report",
                data=pdf_bytes,
                file_name=f"code_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_pdf_report",
            )
        else:
            st.button("Download PDF Report", disabled=True, use_container_width=True)

    with action_col_2:
        if st.button(
            "Save to Google Drive",
            use_container_width=True,
            disabled=not bool(pdf_bytes) or not is_drive_configured(),
        ):
            with st.spinner("Saving PDF and JSON to Google Drive..."):
                st.session_state.drive_upload_result = save_review_to_drive(
                    review_data=review_data,
                    pdf_bytes=pdf_bytes,
                    language=st.session_state.selected_language,
                    code_snippet=st.session_state.editor_code,
                    target_folder_link=st.session_state.get("drive_folder_link", "").strip(),
                )
            st.rerun()

    with action_col_3:
        if st.button("Review Another", use_container_width=True):
            reset_review(keep_code=True)
            st.rerun()

    with action_col_4:
        if st.button("Reset to Sample", use_container_width=True):
            st.session_state.editor_code = DEFAULT_CODE
            reset_review(keep_code=True)
            st.rerun()

    st.markdown("</section>", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Examples
# ─────────────────────────────────────────────────────────────────────────────

st.markdown(
    """
    <div class="section-heading" style="margin-top: 2rem;">
        <h2>Try an example</h2>
    </div>
    """,
    unsafe_allow_html=True,
)

example_cols = st.columns(4)
for col, (language, example) in zip(example_cols, EXAMPLES.items()):
    with col:
        render_example_card(language, example["title"], example["description"])
        st.button(
            f"Try {language}",
            key=f"example_{language}",
            use_container_width=True,
            on_click=load_example,
            args=(language, example["code"]),
        )

st.markdown(
    "<div class='footer-note'>Built with Streamlit + CSS · Powered by Gemini · CodeBuddy © 2026</div>",
    unsafe_allow_html=True,
)
