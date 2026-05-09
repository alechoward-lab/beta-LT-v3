"""
Centralized MarvelCDB API client.

Provides:
* A single ``requests.Session`` with retry/backoff.
* A two-tier cache: an in-memory ``@st.cache_data`` layer and a disk snapshot.
* Graceful fallback to the on-disk snapshot when MarvelCDB is unreachable.

This is the only module in the project that should call MarvelCDB directly.
Pages should import :func:`fetch_all_cards`, :func:`fetch_deck`, etc.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any, Mapping

import requests
import streamlit as st

API_ROOT = "https://marvelcdb.com/api/public"
HTTP_TIMEOUT = 20
MAX_RETRIES = 3
BACKOFF = 0.6  # seconds; multiplied by 2**attempt

# Snapshot directory (project-relative). Survives across server restarts; used
# both as a warm cache for Streamlit's @st.cache_data and as a fallback when
# MarvelCDB is unreachable.
_SNAPSHOT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "_mcdb_cache",
)


def _ensure_snapshot_dir() -> None:
    try:
        os.makedirs(_SNAPSHOT_DIR, exist_ok=True)
    except OSError:
        pass


def _snapshot_path(name: str) -> str:
    safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", "."))
    return os.path.join(_SNAPSHOT_DIR, f"{safe}.json")


def _read_snapshot(name: str) -> tuple[Any, float] | None:
    path = _snapshot_path(name)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        return payload.get("data"), float(payload.get("ts", 0))
    except (OSError, ValueError):
        return None


def _write_snapshot(name: str, data: Any) -> None:
    _ensure_snapshot_dir()
    path = _snapshot_path(name)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "data": data}, f)
    except OSError:
        pass  # Snapshot is opportunistic; never block on cache failures.


@st.cache_resource(show_spinner=False)
def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "beta-LT-v3 / streamlit"})
    return s


class MarvelCDBUnavailable(RuntimeError):
    """Raised when the API is unreachable AND no snapshot is available."""


def _request(path: str, *, snapshot_key: str | None = None) -> Any:
    """GET ``API_ROOT + path`` with retries + on-disk snapshot fallback."""
    url = f"{API_ROOT}{path}"
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = _session().get(url, timeout=HTTP_TIMEOUT)
            resp.raise_for_status()
            data = resp.json()
            if snapshot_key:
                _write_snapshot(snapshot_key, data)
            return data
        except (requests.RequestException, ValueError) as e:
            last_exc = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF * (2 ** attempt))

    if snapshot_key:
        snap = _read_snapshot(snapshot_key)
        if snap is not None:
            return snap[0]

    raise MarvelCDBUnavailable(f"GET {url} failed: {last_exc}") from last_exc


@st.cache_data(ttl=3600, show_spinner="Loading card database...")
def fetch_all_cards() -> dict[str, Mapping[str, Any]]:
    """Full card database indexed by code. Falls back to disk snapshot."""
    cards = _request("/cards/", snapshot_key="all_cards")
    return {card["code"]: card for card in cards}


@st.cache_data(ttl=300, show_spinner="Loading deck...")
def fetch_deck(deck_id: str, api_type: str) -> Mapping[str, Any]:
    """Single deck or decklist. Falls back to disk snapshot."""
    if api_type == "decklist":
        path = f"/decklist/{deck_id}"
        key = f"decklist_{deck_id}"
    else:
        path = f"/deck/{deck_id}"
        key = f"deck_{deck_id}"
    return _request(path, snapshot_key=key)


def clear_caches() -> None:
    """Clear all in-memory caches (snapshot files are kept)."""
    fetch_all_cards.clear()
    fetch_deck.clear()
