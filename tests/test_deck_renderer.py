"""
Tests for deck rendering invariants.

Run: ``pytest tests/`` (requires pytest, listed in requirements-dev.txt).
"""

from __future__ import annotations

import pytest

from components.deck_renderer import DeckView, deck_widget_namespace


def _make_payload(**overrides):
    base = {
        "id": "unknown",
        "name": "Test Deck",
        "url": "https://marvelcdb.com/decklist/view/1/x",
        "hero_code": "01001a",
        "slots": {},
        "meta": '{"aspect": "leadership"}',
    }
    base.update(overrides)
    return base


def test_two_decks_with_same_id_get_unique_namespaces():
    """Regression: shared `id` must NOT collide once we factor in url/name.

    This is the bug that crashed mobile users — two decks falling back to
    ``deck_id == "unknown"`` would produce identical widget keys and trigger
    StreamlitDuplicateElementId."""
    a = DeckView.from_payload(_make_payload(name="Deck A", url="https://x/1"))
    b = DeckView.from_payload(_make_payload(name="Deck B", url="https://x/2"))
    assert deck_widget_namespace(a) != deck_widget_namespace(b)


def test_two_decks_with_same_id_and_no_url_still_unique_via_name():
    a = DeckView.from_payload(_make_payload(name="Deck A", url=""))
    b = DeckView.from_payload(_make_payload(name="Deck B", url=""))
    assert deck_widget_namespace(a) != deck_widget_namespace(b)


def test_namespace_is_stable_across_calls():
    """Same payload should always produce the same key — otherwise widget
    state (sort order, checkbox) would reset on every rerun."""
    p = _make_payload(id="42", name="N", url="u")
    assert deck_widget_namespace(DeckView.from_payload(p)) == deck_widget_namespace(DeckView.from_payload(p))


@pytest.mark.parametrize("aspect", ["aggression", "justice", "leadership", "protection", "basic"])
def test_aspect_round_trips_through_meta(aspect):
    deck = DeckView.from_payload(_make_payload(meta=f'{{"aspect": "{aspect}"}}'))
    assert deck.aspect == aspect


def test_aspect_defaults_to_basic_when_meta_missing():
    deck = DeckView.from_payload(_make_payload(meta=None))
    assert deck.aspect == "basic"


def test_aspect_defaults_to_basic_on_invalid_meta_json():
    deck = DeckView.from_payload(_make_payload(meta="not-json"))
    assert deck.aspect == "basic"


def test_slots_are_normalized_to_int():
    deck = DeckView.from_payload(_make_payload(slots={"01001": "3", "01002": 2}))
    assert deck.slots == {"01001": 3, "01002": 2}
