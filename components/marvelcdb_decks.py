"""Helpers for MarvelCDB deck metadata and display."""

from datetime import datetime, timezone

import requests
import streamlit as st


def _parse_iso_datetime(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None


def _pluralize(value, unit):
    return f"{value} {unit}" if value == 1 else f"{value} {unit}s"


def format_relative_edit_time(timestamp):
    """Convert a timestamp into a compact human-readable age string."""
    updated_at = _parse_iso_datetime(timestamp)
    if not updated_at:
        return None

    now = datetime.now(timezone.utc)
    delta_seconds = max(0, int((now - updated_at).total_seconds()))

    if delta_seconds < 60:
        return "just now"

    minutes = delta_seconds // 60
    if minutes < 60:
        return _pluralize(minutes, "minute") + " ago"

    hours = minutes // 60
    if hours < 24:
        return _pluralize(hours, "hour") + " ago"

    days = hours // 24
    if days < 7:
        return _pluralize(days, "day") + " ago"

    weeks = days // 7
    if weeks < 5:
        return _pluralize(weeks, "week") + " ago"

    months = days // 30
    if months < 12:
        return _pluralize(months, "month") + " ago"

    years = days // 365
    return _pluralize(years, "year") + " ago"


@st.cache_data(ttl=3600, show_spinner="Loading MarvelCDB deck info...")
def fetch_deck_info(deck_id, api_type):
    """Fetch a public MarvelCDB deck or decklist payload."""
    if api_type == "decklist":
        url = f"https://marvelcdb.com/api/public/decklist/{deck_id}"
    else:
        url = f"https://marvelcdb.com/api/public/deck/{deck_id}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=3600)
def get_deck_age_label(deck_id, api_type):
    """Return a compact age label like '3 days ago'."""
    try:
        deck_info = fetch_deck_info(deck_id, api_type)
    except Exception:
        return ""

    age = format_relative_edit_time(deck_info.get("date_update") or deck_info.get("date_creation"))
    if not age:
        return ""
    return age


def format_deck_link(entry):
    """Format a MarvelCDB deck entry for markdown display."""
    age_label = get_deck_age_label(entry.get("deck_id"), entry.get("api_type", "deck"))
    suffix = f" · {age_label}" if age_label else ""
    return f"📋 [{entry['name']}]({entry['url']}){suffix}"
