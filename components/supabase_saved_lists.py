"""
Supabase-backed storage for shareable Community Tier Lists.

Phase 1 scope:
- Public read by slug
- Anonymous create with hashed edit token
- Update / delete via slug + edit token (multi-use, manual rotation)
- Last-write-wins on concurrent updates
- Existing community aggregate submissions remain in GitHub JSON (untouched)

Required Streamlit secrets:
    [supabase]
    url = "https://<project-ref>.supabase.co"
    service_role_key = "..."
    feature_enabled = true
"""

from __future__ import annotations

import hashlib
import secrets as _secrets
import re
import time
from typing import Any

import streamlit as st

try:
    import requests as _requests
except ImportError:  # pragma: no cover - requests is in requirements.txt
    _requests = None


TABLE = "community_saved_lists"
PAYLOAD_VERSION = 1
CATALOG_VERSION = "v1"
PAYLOAD_BYTE_CAP = 65535
SLUG_RE = re.compile(r"^[A-Za-z0-9_-]{6,16}$")
SLUG_LEN = 8
SLUG_RETRIES = 5
HTTP_TIMEOUT = 15


# ─── Config / client ─────────────────────────────────────────────────────────

def _cfg() -> dict | None:
    try:
        sec = st.secrets["supabase"]
    except (KeyError, FileNotFoundError):
        return None
    url = sec.get("url")
    key = sec.get("service_role_key")
    if not url or not key:
        return None
    if not bool(sec.get("feature_enabled", True)):
        return None
    return {
        "url": url.rstrip("/"),
        "key": key,
        "headers": {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    }


def is_enabled() -> bool:
    """Return True if Supabase saved-list feature is configured and available."""
    return _cfg() is not None and _requests is not None


def _endpoint(cfg: dict) -> str:
    return f"{cfg['url']}/rest/v1/{TABLE}"


# ─── Token + slug utilities ──────────────────────────────────────────────────

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _generate_slug() -> str:
    return _secrets.token_urlsafe(SLUG_LEN)[:SLUG_LEN].replace("=", "").replace("/", "_").replace("+", "-")


def _generate_token() -> str:
    return _secrets.token_urlsafe(24)


def is_valid_slug(slug: str) -> bool:
    return bool(slug) and bool(SLUG_RE.match(slug))


# ─── Payload normalization ───────────────────────────────────────────────────

TIERS = ["S", "A", "B", "C", "D", "F"]


def normalize_payload(
    raw: dict,
    valid_subjects: set[str] | list[str],
) -> dict:
    """Return a sanitized payload dict.

    - Keeps only known tier keys.
    - Filters out unknown subjects (e.g. retired entities).
    - Preserves order within tiers.
    """
    valid = set(valid_subjects)
    tiers_in = (raw or {}).get("tiers") or {}
    out_tiers = {t: [] for t in TIERS}
    for t in TIERS:
        for subj in (tiers_in.get(t) or []):
            if subj in valid and subj not in (s for lst in out_tiers.values() for s in lst):
                out_tiers[t].append(subj)
    return {
        "tiers": out_tiers,
        "tier_list_type": (raw or {}).get("tier_list_type"),
        "player_count": (raw or {}).get("player_count", "Any"),
        "payload_version": (raw or {}).get("payload_version", PAYLOAD_VERSION),
        "catalog_version": (raw or {}).get("catalog_version", CATALOG_VERSION),
    }


def build_payload(
    tiers: dict[str, list[str]],
    tier_list_type: str,
    player_count: str,
) -> dict:
    return {
        "tiers": {t: list(tiers.get(t, [])) for t in TIERS},
        "tier_list_type": tier_list_type,
        "player_count": player_count,
        "payload_version": PAYLOAD_VERSION,
        "catalog_version": CATALOG_VERSION,
    }


def _payload_size_ok(payload: dict) -> bool:
    import json as _json
    return len(_json.dumps(payload).encode("utf-8")) <= PAYLOAD_BYTE_CAP


# ─── HTTP helpers ────────────────────────────────────────────────────────────

def _http(method: str, url: str, cfg: dict, **kwargs):
    headers = dict(cfg["headers"])
    headers.update(kwargs.pop("headers", {}))
    return _requests.request(method, url, headers=headers, timeout=HTTP_TIMEOUT, **kwargs)


# ─── Public API ──────────────────────────────────────────────────────────────

def create_saved_list(
    *,
    tiers: dict[str, list[str]],
    tier_list_type: str,
    player_count: str = "Any",
    title: str | None = None,
) -> tuple[bool, dict | None, str | None]:
    """Create a new saved list. Returns (ok, {slug, edit_token}, error)."""
    cfg = _cfg()
    if not cfg or not _requests:
        return False, None, "Saved-list feature is not configured."

    payload = build_payload(tiers, tier_list_type, player_count)
    if not _payload_size_ok(payload):
        return False, None, "Tier list payload is too large to save."

    edit_token = _generate_token()
    edit_token_hash = _hash_token(edit_token)
    base_row = {
        "title": (title or None),
        "tier_list_type": tier_list_type,
        "player_count": player_count or "Any",
        "payload_json": payload,
        "payload_version": PAYLOAD_VERSION,
        "catalog_version": CATALOG_VERSION,
        "edit_token_hash": edit_token_hash,
        "is_public": True,
    }

    last_err = "Unknown error creating saved list."
    for _ in range(SLUG_RETRIES):
        slug = _generate_slug()
        row = dict(base_row, slug=slug)
        try:
            r = _http(
                "POST",
                _endpoint(cfg),
                cfg,
                json=row,
                headers={"Prefer": "return=representation"},
            )
        except Exception as e:  # network error
            return False, None, f"Network error contacting database: {e}"

        if r.status_code in (200, 201):
            return True, {"slug": slug, "edit_token": edit_token}, None

        # 409/23505 = unique violation on slug → retry with new slug
        body_text = r.text or ""
        if r.status_code == 409 or "23505" in body_text or "duplicate key" in body_text.lower():
            last_err = "Slug collision; retrying."
            continue

        last_err = f"Database error ({r.status_code}): {body_text[:300]}"
        break

    return False, None, last_err


def get_saved_list_by_slug(slug: str) -> tuple[bool, dict | None, str | None]:
    """Fetch a saved list. Returns (ok, row_dict | None, error)."""
    cfg = _cfg()
    if not cfg or not _requests:
        return False, None, "Saved-list feature is not configured."
    if not is_valid_slug(slug):
        return False, None, "Invalid share link."

    try:
        r = _http(
            "GET",
            _endpoint(cfg),
            cfg,
            params={"slug": f"eq.{slug}", "select": "*", "limit": 1},
        )
    except Exception as e:
        return False, None, f"Network error contacting database: {e}"

    if r.status_code != 200:
        return False, None, f"Database error ({r.status_code})."
    rows = r.json() or []
    if not rows:
        return True, None, None
    return True, rows[0], None


def update_saved_list_with_token(
    *,
    slug: str,
    edit_token: str,
    tiers: dict[str, list[str]],
    tier_list_type: str,
    player_count: str = "Any",
    title: str | None = None,
) -> tuple[bool, str | None]:
    """Update a saved list. Returns (ok, error)."""
    cfg = _cfg()
    if not cfg or not _requests:
        return False, "Saved-list feature is not configured."
    if not is_valid_slug(slug):
        return False, "Invalid share link."
    if not edit_token:
        return False, "Edit code is required."

    payload = build_payload(tiers, tier_list_type, player_count)
    if not _payload_size_ok(payload):
        return False, "Tier list payload is too large to save."

    update_row: dict[str, Any] = {
        "payload_json": payload,
        "tier_list_type": tier_list_type,
        "player_count": player_count or "Any",
        "payload_version": PAYLOAD_VERSION,
        "catalog_version": CATALOG_VERSION,
    }
    if title is not None:
        update_row["title"] = title or None

    try:
        r = _http(
            "PATCH",
            _endpoint(cfg),
            cfg,
            params={
                "slug": f"eq.{slug}",
                "edit_token_hash": f"eq.{_hash_token(edit_token)}",
            },
            json=update_row,
            headers={"Prefer": "return=representation"},
        )
    except Exception as e:
        return False, f"Network error contacting database: {e}"

    if r.status_code not in (200, 204):
        return False, f"Database error ({r.status_code})."
    rows = []
    try:
        rows = r.json() or []
    except Exception:
        rows = []
    if not rows:
        return False, "Edit code did not match this saved list."
    return True, None


def delete_saved_list_with_token(
    *, slug: str, edit_token: str
) -> tuple[bool, str | None]:
    """Delete a saved list. Returns (ok, error)."""
    cfg = _cfg()
    if not cfg or not _requests:
        return False, "Saved-list feature is not configured."
    if not is_valid_slug(slug):
        return False, "Invalid share link."
    if not edit_token:
        return False, "Edit code is required."

    try:
        r = _http(
            "DELETE",
            _endpoint(cfg),
            cfg,
            params={
                "slug": f"eq.{slug}",
                "edit_token_hash": f"eq.{_hash_token(edit_token)}",
            },
            headers={"Prefer": "return=representation"},
        )
    except Exception as e:
        return False, f"Network error contacting database: {e}"

    if r.status_code not in (200, 204):
        return False, f"Database error ({r.status_code})."
    rows = []
    try:
        rows = r.json() or []
    except Exception:
        rows = []
    if not rows:
        return False, "Edit code did not match this saved list."
    return True, None


def increment_view_count(slug: str) -> None:
    """Best-effort: bump view_count and last_viewed_at. Silently ignores errors."""
    cfg = _cfg()
    if not cfg or not _requests or not is_valid_slug(slug):
        return
    try:
        r = _http(
            "GET",
            _endpoint(cfg),
            cfg,
            params={"slug": f"eq.{slug}", "select": "view_count", "limit": 1},
        )
        if r.status_code != 200:
            return
        rows = r.json() or []
        if not rows:
            return
        cur = int(rows[0].get("view_count") or 0)
        _http(
            "PATCH",
            _endpoint(cfg),
            cfg,
            params={"slug": f"eq.{slug}"},
            json={
                "view_count": cur + 1,
                "last_viewed_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            },
        )
    except Exception:
        return
