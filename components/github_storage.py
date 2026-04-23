"""
Persistent JSON storage backed by a file in the GitHub repo.

On Streamlit Cloud the local filesystem resets every deploy, so we read/write
the data file via the GitHub Contents API.  Locally it falls back to plain
file I/O so development works without a token.

Required Streamlit secrets (only for cloud deployment):
    [github]
    token = "ghp_..."
    repo  = "alechoward-lab/beta-LT-v3"       # owner/repo
    path  = "beta-LT-v3/community_tier_lists.json"   # path inside repo
    branch = "main"
"""

import json
import os
import base64
import streamlit as st

try:
    import requests as _requests
except ImportError:
    _requests = None


def _github_cfg():
    """Return (token, repo, path, branch) from Streamlit secrets, or None."""
    try:
        sec = st.secrets["github"]
        return sec["token"], sec["repo"], sec["path"], sec.get("branch", "main")
    except (KeyError, FileNotFoundError):
        return None


def _gh_read(token, repo, path, branch):
    """Fetch a file from GitHub and return (content_str, sha)."""
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    r = _requests.get(url, headers=headers, params={"ref": branch}, timeout=15)
    if r.status_code == 404:
        return None, None
    r.raise_for_status()
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    return content, data["sha"]


def _gh_write(token, repo, path, branch, content_str, sha=None):
    """Create or update a file on GitHub."""
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    body = {
        "message": "Update community tier list data",
        "content": base64.b64encode(content_str.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    if sha:
        body["sha"] = sha
    r = _requests.put(url, headers=headers, json=body, timeout=15)
    r.raise_for_status()


# ── Public API ──

def load_json(local_path, default=None):
    """Load JSON data — from GitHub if secrets are configured, else local file."""
    if default is None:
        default = {}

    cfg = _github_cfg()
    if cfg and _requests:
        token, repo, path, branch = cfg
        try:
            content, sha = _gh_read(token, repo, path, branch)
            if content is None:
                return default, None
            return json.loads(content), sha
        except Exception as e:
            st.warning(f"Could not load from GitHub: {e}")
            return default, None

    # Local fallback
    if os.path.exists(local_path):
        with open(local_path, "r") as f:
            return json.load(f), None
    return default, None


def save_json(data, local_path, sha=None):
    """Save JSON data and return (ok, error_message, retryable)."""
    MAX_SIZE = 5 * 1024 * 1024  # 5 MB guard
    content_str = json.dumps(data)
    if len(content_str) > MAX_SIZE:
        return False, "Data too large to save.", False

    cfg = _github_cfg()
    if cfg:
        if not _requests:
            return False, "Could not save to GitHub: requests is not installed.", False

        token, repo, path, branch = cfg
        try:
            _gh_write(token, repo, path, branch, content_str, sha=sha)
            return True, None, False
        except Exception as e:
            response = getattr(e, "response", None)
            retryable = response is not None and response.status_code in {409, 422}
            if response is not None:
                try:
                    message = response.json().get("message") or response.text
                except ValueError:
                    message = response.text
                error_message = f"Could not save to GitHub ({response.status_code}): {message}"
            else:
                error_message = f"Could not save to GitHub: {e}"
            return False, error_message, retryable

    # Local fallback
    try:
        with open(local_path, "w") as f:
            json.dump(data, f)
        return True, None, False
    except Exception as e:
        return False, f"Could not save locally: {e}", False
