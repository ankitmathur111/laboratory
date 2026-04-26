# PROJECT : SmartVenue AI — Crowd Management Agent
# FILE    : key_manager.py
# DEPLOY  : gcloud run deploy smartvenue-ai
"""
key_manager.py
--------------
Handles Gemini API key loading with this priority order:
  1. Google Secret Manager (Cloud Run production — most secure)
  2. Environment variable GEMINI_API_KEY (local laptop export)
  3. User input via UI (fallback — shown masked)

Drop this file into both smartvenue_ai/ and learnmate_ai/ folders.
"""

import os
import hashlib


def load_api_key() -> str:
    """
    Try to load the Gemini API key automatically.
    Returns the key string, or "" if not found anywhere automatic.
    """
    # ── 1. Try Google Secret Manager (works on Cloud Run) ─────────────────────
    try:
        from google.cloud import secretmanager
        project_id = _get_project_id()
        if project_id:
            client = secretmanager.SecretManagerServiceClient()
            name = f"projects/{project_id}/secrets/GEMINI_API_KEY/versions/latest"
            response = client.access_secret_version(request={"name": name})
            key = response.payload.data.decode("utf-8").strip()
            if key:
                return key
    except Exception:
        pass  # Not on Cloud Run, or secret doesn't exist yet

    # ── 2. Try environment variable (local laptop) ────────────────────────────
    key = os.environ.get("GEMINI_API_KEY", "").strip()
    if key:
        return key

    # ── 3. Not found — UI will ask user ──────────────────────────────────────
    return ""


def _get_project_id() -> str:
    """Detect GCP project ID from metadata server (only works on Cloud Run/GCE)."""
    try:
        import urllib.request
        req = urllib.request.Request(
            "http://metadata.google.internal/computeMetadata/v1/project/project-id",
            headers={"Metadata-Flavor": "Google"},
        )
        with urllib.request.urlopen(req, timeout=1) as resp:
            return resp.read().decode("utf-8")
    except Exception:
        return os.environ.get("GOOGLE_CLOUD_PROJECT", "")


def mask_key(key: str) -> str:
    """
    Returns a safe display string for the key.
    Shows first 4 chars + SHA256 fingerprint — enough to verify it's the right key
    without exposing the actual value.
    Example: "AIza••••••••••••••••  [fingerprint: a3f2c1]"
    """
    if not key:
        return ""
    fingerprint = hashlib.sha256(key.encode()).hexdigest()[:6]
    visible = key[:4]
    return f"{visible}{'•' * 20}  [fingerprint: {fingerprint}]"


def is_running_on_cloud() -> bool:
    """Returns True if running on Google Cloud Run."""
    return bool(os.environ.get("K_SERVICE") or os.environ.get("GOOGLE_CLOUD_PROJECT"))
