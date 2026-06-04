"""
Google Drive uploader service for CodeBuddy.

Uploads the generated PDF report and a JSON copy of the structured review.
It can upload either:
1. to a default "CodeReview AI Reports" folder, or
2. to a user-provided Google Drive folder link/ID.

Important:
    A Drive folder link alone is not permission. The Google account that
    authorizes this app must have edit access to the pasted folder.
"""

from __future__ import annotations

import io
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    _GOOGLE_IMPORT_ERROR: Exception | None = None
except Exception as exc:  # Keeps the Streamlit app from crashing if deps are missing.
    Credentials = None
    Request = None
    InstalledAppFlow = None
    build = None
    MediaIoBaseUpload = None
    _GOOGLE_IMPORT_ERROR = exc


# Full Drive scope is used so the app can upload to a pasted folder link that
# the signed-in user owns or has edit access to. If token.json was created with
# an older scope, delete token.json and run setup again.
SCOPES = ["https://www.googleapis.com/auth/drive"]

ROOT_DIR = Path(__file__).resolve().parents[2]
TOKEN_PATH = ROOT_DIR / "token.json"
# Primary filename requested for this project.
CREDENTIALS_PATH = ROOT_DIR / "credential.json"
# Legacy fallback so old projects with credentials.json still work.
LEGACY_CREDENTIALS_PATH = ROOT_DIR / "credentials.json"
DRIVE_FOLDER_NAME = "CodeReview AI Reports"


def get_credentials_path() -> Path:
    """Return the configured Google OAuth credential file path."""
    if CREDENTIALS_PATH.exists():
        return CREDENTIALS_PATH
    if LEGACY_CREDENTIALS_PATH.exists():
        return LEGACY_CREDENTIALS_PATH
    return CREDENTIALS_PATH


def _require_google_packages() -> None:
    if _GOOGLE_IMPORT_ERROR is not None:
        raise ImportError(
            "Google Drive packages are not installed. Run: pip install -r requirements.txt"
        ) from _GOOGLE_IMPORT_ERROR


def is_drive_configured() -> bool:
    """Return True when credential.json exists in the project root."""
    return get_credentials_path().exists()


def extract_drive_folder_id(folder_link_or_id: str) -> Optional[str]:
    """
    Extract a Google Drive folder ID from either a full folder link or raw ID.

    Supported examples:
      - https://drive.google.com/drive/folders/FOLDER_ID
      - https://drive.google.com/open?id=FOLDER_ID
      - FOLDER_ID
    """
    value = (folder_link_or_id or "").strip()
    if not value:
        return None

    patterns = [
        r"/folders/([A-Za-z0-9_-]+)",
        r"[?&]id=([A-Za-z0-9_-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, value)
        if match:
            return match.group(1)

    if re.fullmatch(r"[A-Za-z0-9_-]{10,}", value):
        return value

    return None


def _credentials_have_required_scopes(creds) -> bool:
    token_scopes = set(getattr(creds, "scopes", None) or [])
    return all(scope in token_scopes for scope in SCOPES)


def _validate_json_file(path: Path, friendly_name: str) -> None:
    """Give a clear error if a required Google auth JSON file is blank or invalid."""
    if not path.exists():
        raise FileNotFoundError(f"{friendly_name} not found at: {path}")

    if path.stat().st_size == 0:
        raise ValueError(
            f"{friendly_name} is empty. Delete it and download/create a valid Google OAuth JSON file again."
        )

    try:
        json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{friendly_name} is not valid JSON. Open it and check that it starts with '{{'. "
            f"If it is blank or HTML/text, download the OAuth client JSON again."
        ) from exc


def _load_saved_token():
    """Load token.json safely. Bad tokens are deleted so setup can run again."""
    if not TOKEN_PATH.exists():
        return None

    try:
        _validate_json_file(TOKEN_PATH, "token.json")
        return Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)
    except Exception:
        # token.json can be safely recreated by OAuth setup, so remove bad copies.
        try:
            TOKEN_PATH.unlink()
        except OSError:
            pass
        return None


def _get_credentials():
    """
    Load/refresh OAuth credentials.

    First-time setup opens a browser and writes token.json in the project root.
    Later runs reuse token.json automatically.
    """
    _require_google_packages()

    creds = _load_saved_token()

    # Re-authorize if token was created using the older/default scope.
    if creds and not _credentials_have_required_scopes(creds):
        creds = None
        try:
            TOKEN_PATH.unlink()
        except OSError:
            pass

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            credentials_path = get_credentials_path()
            if not credentials_path.exists():
                raise FileNotFoundError(
                    "credential.json not found. Place it beside app.py in the project root, "
                    "then run: python src/services/drive_uploader.py --setup"
                )

            _validate_json_file(credentials_path, "credential.json")

            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)

        TOKEN_PATH.write_text(creds.to_json(), encoding="utf-8")

    return creds


def _get_drive_service():
    creds = _get_credentials()
    return build("drive", "v3", credentials=creds)


def _get_or_create_folder(service, folder_name: str) -> str:
    query = (
        f"name='{folder_name}' "
        f"and mimeType='application/vnd.google-apps.folder' "
        f"and trashed=false"
    )
    results = service.files().list(q=query, fields="files(id, name)").execute()
    files = results.get("files", [])
    if files:
        return files[0]["id"]

    folder_metadata = {
        "name": folder_name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    folder = service.files().create(body=folder_metadata, fields="id").execute()
    return folder["id"]


def _validate_folder(service, folder_id: str) -> None:
    """Fail early if the folder link is invalid or the signed-in user cannot access it."""
    folder = service.files().get(
        fileId=folder_id,
        fields="id, name, mimeType",
        supportsAllDrives=True,
    ).execute()

    if folder.get("mimeType") != "application/vnd.google-apps.folder":
        raise ValueError("The provided Google Drive link is not a folder link.")


def _upload_pdf(service, folder_id: str, pdf_bytes: bytes, filename: str) -> dict[str, str]:
    file_metadata = {"name": filename, "parents": [folder_id]}
    media = MediaIoBaseUpload(
        io.BytesIO(pdf_bytes),
        mimetype="application/pdf",
        resumable=True,
    )
    return service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink, createdTime",
        supportsAllDrives=True,
    ).execute()


def _upload_json(service, folder_id: str, review_data: dict[str, Any], filename: str) -> dict[str, str]:
    json_str = json.dumps(review_data, indent=2, ensure_ascii=False)
    file_metadata = {
        "name": filename,
        "parents": [folder_id],
        "mimeType": "application/json",
    }
    media = MediaIoBaseUpload(
        io.BytesIO(json_str.encode("utf-8")),
        mimetype="application/json",
        resumable=False,
    )
    return service.files().create(
        body=file_metadata,
        media_body=media,
        fields="id, name, webViewLink, createdTime",
        supportsAllDrives=True,
    ).execute()


def save_review_to_drive(
    review_data: dict[str, Any],
    pdf_bytes: Optional[bytes],
    language: str,
    code_snippet: str,
    target_folder_link: Optional[str] = None,
) -> dict[str, Any]:
    """
    Upload review PDF and JSON to Google Drive.

    If target_folder_link is provided, files are uploaded to that folder.
    Otherwise, a default "CodeReview AI Reports" folder is created/reused.

    The authenticated Google account must have edit access to the target folder.

    Returns:
        {
          success: bool,
          pdf_link: str | None,
          json_link: str | None,
          folder_link: str | None,
          error: str | None
        }
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    grade = str(review_data.get("overall_grade", "N-A")).replace("/", "-")
    language_safe = language.replace("+", "plus").replace(" ", "_")
    base_name = f"codereview_{language_safe}_{grade}_{timestamp}"

    result = {
        "success": False,
        "pdf_link": None,
        "json_link": None,
        "folder_link": None,
        "error": None,
    }

    try:
        service = _get_drive_service()

        folder_id = extract_drive_folder_id(target_folder_link or "")
        if folder_id:
            _validate_folder(service, folder_id)
        else:
            folder_id = _get_or_create_folder(service, DRIVE_FOLDER_NAME)

        result["folder_link"] = f"https://drive.google.com/drive/folders/{folder_id}"

        if pdf_bytes:
            pdf_meta = _upload_pdf(service, folder_id, pdf_bytes, f"{base_name}.pdf")
            result["pdf_link"] = pdf_meta.get("webViewLink")

        enriched_data = {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "language": language,
                "grade": grade,
                "code_snippet": code_snippet,
                "target_folder": result["folder_link"],
            },
            "review": review_data,
        }
        json_meta = _upload_json(service, folder_id, enriched_data, f"{base_name}.json")
        result["json_link"] = json_meta.get("webViewLink")
        result["success"] = True

    except Exception as exc:
        result["error"] = (
            f"{str(exc)} Make sure credential.json is a valid Google OAuth client JSON file, "
            "the folder link is valid, and the Google account authorized during setup has edit access."
        )

    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CodeBuddy Google Drive setup")
    parser.add_argument("--setup", action="store_true", help="Authorize Google Drive access")
    parser.add_argument("--test", action="store_true", help="Upload a test JSON file")
    parser.add_argument("--folder", type=str, default="", help="Optional Drive folder link/ID for test upload")
    args = parser.parse_args()

    if args.setup:
        _get_credentials()
        print(f"Authorization successful. Token saved to: {TOKEN_PATH}")

    if args.test:
        upload_result = save_review_to_drive(
            review_data={"overall_grade": "A", "summary": "Test upload from CodeBuddy"},
            pdf_bytes=None,
            language="Python",
            code_snippet="print('hello')",
            target_folder_link=args.folder,
        )
        if upload_result["success"]:
            print("Test upload successful.")
            print("JSON:", upload_result["json_link"])
            print("Folder:", upload_result["folder_link"])
        else:
            print("Upload failed:", upload_result["error"])
