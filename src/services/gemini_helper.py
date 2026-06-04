"""
AI review helper for CodeBuddy.

Primary provider:
    Google Gemini API

Fallback provider:
    Local Ollama through http://localhost:11434/api/chat

Why fallback exists:
    Gemini can sometimes return 503 UNAVAILABLE during high demand. When that
    happens, this module automatically tries the next Gemini model and then
    Ollama if enabled.
"""

from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field, ValidationError


# Load environment variables explicitly from the project root.
ROOT_DIR = Path(__file__).resolve().parents[2]
for env_name in (".env", "env"):
    env_path = ROOT_DIR / env_name
    if env_path.exists():
        load_dotenv(env_path, override=False)


_client = None


class IssueSchema(BaseModel):
    title: str = Field(..., description="Short issue title")
    lines: str = Field(..., description="Line number/range, e.g. '12' or '14-16'")
    severity: str = Field(..., description="'Critical', 'Warning', or 'Suggestion'")
    explanation: str = Field(..., description="Beginner-friendly explanation")
    fix: str = Field(..., description="Actionable fix suggestion")


class ScoresSchema(BaseModel):
    readability: int = Field(..., description="0 to 10")
    efficiency: int = Field(..., description="0 to 10")
    correctness: int = Field(..., description="0 to 10")
    best_practices: int = Field(..., description="0 to 10")


class CodeReviewResponse(BaseModel):
    scores: ScoresSchema
    overall_grade: str = Field(..., description="'A+', 'A', 'B', 'C', 'D', or 'F'")
    issues: List[IssueSchema]
    improved_code: str
    learning_tips: List[str]
    summary: str


def has_api_key() -> bool:
    """Return True when a non-placeholder Gemini API key is available."""
    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    return bool(api_key and api_key != "your_api_key_here")


def use_ollama_fallback() -> bool:
    """Return True when Ollama fallback is enabled."""
    return os.getenv("USE_OLLAMA_FALLBACK", "true").strip().lower() in {"1", "true", "yes", "on"}


def has_any_ai_backend() -> bool:
    """Gemini key OR local Ollama fallback is enough to attempt review."""
    return has_api_key() or use_ollama_fallback()


def get_gemini_models() -> list[str]:
    """
    Comma-separated fallback order.

    Default uses Flash-Lite first because it is usually lighter/faster, then
    Flash for stronger output if available.
    """
    raw = os.getenv("GEMINI_MODELS", "gemini-2.5-flash-lite,gemini-2.5-flash").strip()
    models = [m.strip() for m in raw.split(",") if m.strip()]
    return models or ["gemini-2.5-flash-lite", "gemini-2.5-flash"]


def get_ollama_model() -> str:
    return os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b").strip() or "qwen2.5-coder:7b"


def get_ollama_base_url() -> str:
    return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip().rstrip("/")


def get_client() -> genai.Client:
    """Lazy Gemini client."""
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key or api_key == "your_api_key_here":
            raise ValueError(
                "Gemini API key is not configured. Add GEMINI_API_KEY to the .env file."
            )
        _client = genai.Client(api_key=api_key)
    return _client


def _depth_instruction(depth: str) -> str:
    depth_instructions = {
        "Quick": "Perform a rapid review. Focus strictly on critical bugs and highly obvious style improvements.",
        "Standard": "Perform a standard review. Provide balanced feedback across readability, efficiency, correctness, and best practices.",
        "Deep": "Perform a deep architectural review. Analyze time/space complexity, modularity, error resilience, and optimization opportunities.",
    }
    return depth_instructions.get(depth, depth_instructions["Standard"])


def _build_prompt(code: str, language: str, depth: str) -> str:
    return f"""You are CodeReview AI, a supportive programming tutor reviewing a student's code.

Return JSON only. Do not use markdown. Do not add text outside JSON.

JSON schema:
{{
  "scores": {{
    "readability": <integer 0-10>,
    "efficiency": <integer 0-10>,
    "correctness": <integer 0-10>,
    "best_practices": <integer 0-10>
  }},
  "overall_grade": "<A+|A|B|C|D|F>",
  "issues": [
    {{
      "title": "<short issue title>",
      "lines": "<line number/range or N/A>",
      "severity": "<Critical|Warning|Suggestion>",
      "explanation": "<beginner-friendly explanation>",
      "fix": "<clear fix suggestion>"
    }}
  ],
  "improved_code": "<complete improved code>",
  "learning_tips": ["<tip 1>", "<tip 2>", "<tip 3>"],
  "summary": "<2-3 sentence encouraging summary>"
}}

Review instructions:
{_depth_instruction(depth)}

Programming language: {language}

Code to review:
```{language.lower()}
{code}
```"""


def _extract_json(text: str) -> dict[str, Any]:
    """Extract JSON from model output, even if it accidentally wraps it in text."""
    raw = (text or "").strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(raw[start : end + 1])

    raise ValueError("Model did not return valid JSON.")


def _normalize_review(data: dict[str, Any]) -> dict[str, Any]:
    """Validate and lightly repair review data so Streamlit can render safely."""
    try:
        validated = CodeReviewResponse.model_validate(data)
        return json.loads(validated.model_dump_json())
    except (ValidationError, AttributeError):
        # Pydantic v1 fallback
        try:
            validated = CodeReviewResponse.parse_obj(data)
            return json.loads(validated.json())
        except Exception:
            pass

    scores = data.get("scores") if isinstance(data.get("scores"), dict) else {}
    issues = data.get("issues") if isinstance(data.get("issues"), list) else []

    safe_issues = []
    for issue in issues:
        if not isinstance(issue, dict):
            continue
        safe_issues.append(
            {
                "title": str(issue.get("title", "Issue")),
                "lines": str(issue.get("lines", "N/A")),
                "severity": str(issue.get("severity", "Suggestion")),
                "explanation": str(issue.get("explanation", "No explanation returned.")),
                "fix": str(issue.get("fix", "Review this section and correct the issue.")),
            }
        )

    return {
        "scores": {
            "readability": int(scores.get("readability", 5) or 5),
            "efficiency": int(scores.get("efficiency", 5) or 5),
            "correctness": int(scores.get("correctness", 5) or 5),
            "best_practices": int(scores.get("best_practices", 5) or 5),
        },
        "overall_grade": str(data.get("overall_grade", "C")),
        "issues": safe_issues,
        "improved_code": str(data.get("improved_code", "")),
        "learning_tips": list(data.get("learning_tips", []))[:3] or [
            "Use clear indentation and spacing.",
            "Test edge cases before submitting.",
            "Use readable variable and function names.",
        ],
        "summary": str(data.get("summary", "Review completed.")),
    }


def _review_with_gemini(code: str, language: str, depth: str, model: str) -> dict[str, Any]:
    client = get_client()
    prompt = _build_prompt(code, language, depth)

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CodeReviewResponse,
            temperature=0.2,
        ),
    )

    data = _extract_json(response.text)
    data = _normalize_review(data)
    data["_provider"] = "Gemini"
    data["_model_used"] = model
    return data


def _review_with_ollama(code: str, language: str, depth: str) -> dict[str, Any]:
    model = get_ollama_model()
    base_url = get_ollama_base_url()
    prompt = _build_prompt(code, language, depth)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "You are a strict JSON-only code review assistant. Return one valid JSON object only.",
            },
            {"role": "user", "content": prompt},
        ],
        "format": "json",
        "stream": False,
        "options": {
            "temperature": 0.2,
        },
    }

    request = urllib.request.Request(
        f"{base_url}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.URLError as exc:
        raise RuntimeError(
            f"Ollama is not reachable at {base_url}. Start Ollama and pull the model: ollama pull {model}"
        ) from exc

    content = result.get("message", {}).get("content", "")
    data = _extract_json(content)
    data = _normalize_review(data)
    data["_provider"] = "Ollama"
    data["_model_used"] = model
    return data


def get_code_review(code: str, language: str, depth: str = "Standard") -> Dict[str, Any]:
    """
    Get AI-powered code review.

    Fallback order:
      1. Gemini models from GEMINI_MODELS
      2. Ollama local model if USE_OLLAMA_FALLBACK=true
    """
    errors: list[str] = []

    if has_api_key():
        for model in get_gemini_models():
            try:
                return _review_with_gemini(code, language, depth, model)
            except Exception as exc:
                errors.append(f"Gemini {model}: {str(exc)}")

    if use_ollama_fallback():
        try:
            return _review_with_ollama(code, language, depth)
        except Exception as exc:
            errors.append(f"Ollama {get_ollama_model()}: {str(exc)}")

    if not errors:
        errors.append(
            "No AI backend configured. Add GEMINI_API_KEY to .env or enable Ollama fallback."
        )

    return {
        "error": True,
        "message": "All AI review backends failed. " + " | ".join(errors[-3:]),
    }


def test_api_connection() -> bool:
    """Lightweight config check for UI status."""
    return has_any_ai_backend()
