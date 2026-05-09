"""
Reusable deck-rendering component (extracted from pages/1_good-decks.py).

Provides typed access to MarvelCDB deck payloads and a single ``render_deck``
entry point. Other pages (e.g., a future hero-pairings deck preview) can
import :func:`render_deck` instead of duplicating the layout logic.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from html import escape as html_escape
from typing import Any, Mapping, Sequence

import streamlit as st

from components.hero_card_viewer import get_obligation_nemesis, open_hero_cards_dialog
from data.constants import HERO_ALTER_EGOS


# ─── Aspect / type constants ────────────────────────────────────────────────

ASPECT_COLORS: dict[str, str] = {
    "aggression": "aggression",
    "justice": "justice",
    "leadership": "leadership",
    "protection": "protection",
    "basic": "basic",
    "hero": "hero",
    "encounter": "basic",
    "campaign": "basic",
    "pool": "pool",
}

ASPECT_DISPLAY: dict[str, str] = {
    "aggression": "Aggression",
    "justice": "Justice",
    "leadership": "Leadership",
    "protection": "Protection",
    "basic": "Basic",
    "pool": "'Pool",
}

TYPE_ORDER: list[str] = [
    "ally", "support", "upgrade", "event", "resource", "player_side_scheme",
]
TYPE_LABELS: dict[str, str] = {
    "ally": "Allies",
    "event": "Events",
    "support": "Supports",
    "upgrade": "Upgrades",
    "resource": "Resources",
    "player_side_scheme": "Side Schemes",
}

TIER_COLORS: dict[str, str] = {
    "S": "#e74c3c", "A": "#e67e22", "B": "#f1c40f",
    "C": "#2ecc71", "D": "#3498db", "F": "#95a5a6",
}


# ─── Typed deck shape ───────────────────────────────────────────────────────

@dataclass(frozen=True)
class DeckView:
    """A normalized read-only view over a MarvelCDB deck payload.

    This is intentionally narrow: we only surface the fields actually consumed
    by the renderer, which catches mistakes earlier than ``deck_data.get(...)``
    sprinkled all over the page.
    """

    name: str
    aspect: str
    description_md: str
    url: str
    slots: Mapping[str, int]
    hero_code: str
    deck_id: str
    api_type: str

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "DeckView":
        return cls(
            name=str(payload.get("name") or "Unnamed Deck"),
            aspect=_aspect_from_meta(payload.get("meta")),
            description_md=str(payload.get("description_md") or ""),
            url=str(payload.get("url") or ""),
            slots={str(k): int(v) for k, v in (payload.get("slots") or {}).items()},
            hero_code=str(payload.get("hero_code") or ""),
            deck_id=str(payload.get("id") or "unknown"),
            api_type=str(payload.get("api_type") or "deck"),
        )


def _aspect_from_meta(meta_str: Any) -> str:
    if not meta_str:
        return "basic"
    try:
        return str(json.loads(meta_str).get("aspect") or "basic")
    except (json.JSONDecodeError, TypeError):
        return "basic"


def _fix_description_links(md_text: str) -> str:
    if not md_text:
        return ""
    return re.sub(r"\]\(/card/", "](https://marvelcdb.com/card/", md_text)


def card_image_url(card: Mapping[str, Any]) -> str:
    src = card.get("imagesrc", "") or ""
    return f"https://marvelcdb.com{src}" if src else ""


# ─── HTML builders (no Streamlit calls) ─────────────────────────────────────

def build_card_row(card: Mapping[str, Any], qty: int, *, show_aspect_dot: bool = False) -> str:
    name = html_escape(card.get("name", "Unknown"))
    code = card.get("code", "")
    cost = card.get("cost")
    cost_str = f"({cost})" if cost is not None else ""
    card_url = f"https://marvelcdb.com/card/{code}"
    faction = card.get("faction_code", "basic")
    dot_class = ASPECT_COLORS.get(faction, "basic")
    img_url = card_image_url(card)

    dot_html = (
        f'<span class="aspect-dot dot-{dot_class}" '
        f'title="{ASPECT_DISPLAY.get(faction, faction.title())}"></span>'
    ) if show_aspect_dot else ""

    # Use a single shared tooltip preview (#10): we tag the link with the image
    # URL via data-card-img and let one delegated handler display it. This
    # avoids creating one <img> per card row, which is a major DOM weight win
    # for big decks.
    return (
        '<div class="card-row">'
        f'{dot_html}<span class="card-qty">{qty}\u00d7</span>'
        f'<span class="card-name"><a href="{card_url}" target="_blank" '
        f'data-card-img="{html_escape(img_url)}" data-card-name="{name}">{name}</a></span>'
        f'<span class="card-cost">{cost_str}</span>'
        '</div>'
    )


def _section_weight(cards_with_qty: Sequence[tuple[Mapping[str, Any], int]], include_header: bool = False) -> int:
    type_groups = {card.get("type_code", "unknown") for card, _ in cards_with_qty}
    return len(cards_with_qty) + len(type_groups) + (1 if include_header else 0)


def _render_section_grid_html(section_blocks: Sequence[tuple[str, int]]) -> str:
    if not section_blocks:
        return ""
    columns: list[list[str]] = [[], []]
    weights = [0, 0]
    for html_block, weight in section_blocks:
        idx = 0 if weights[0] <= weights[1] else 1
        columns[idx].append(html_block)
        weights[idx] += weight
    return (
        '<div class="deck-section-grid">'
        f'<div class="deck-section-column">{"".join(columns[0])}</div>'
        f'<div class="deck-section-column">{"".join(columns[1])}</div>'
        '</div>'
    )


def _render_card_section_html(
    cards_with_qty: Sequence[tuple[Mapping[str, Any], int]],
    section_class: str,
    *,
    show_aspect_dot: bool = False,
) -> str:
    by_type: dict[str, list[tuple[Mapping[str, Any], int]]] = {}
    for card, qty in cards_with_qty:
        by_type.setdefault(card.get("type_code", "unknown"), []).append((card, qty))

    parts: list[str] = []
    for type_code in TYPE_ORDER:
        group = by_type.pop(type_code, None)
        if not group:
            continue
        label = TYPE_LABELS.get(type_code, type_code.replace("_", " ").title())
        total = sum(q for _, q in group)
        parts.append(f'<div class="card-type-header type-{section_class}">{label} ({total})</div>')
        group.sort(key=lambda x: x[0].get("name", ""))
        parts.extend(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in group)

    for type_code, group in by_type.items():
        label = type_code.replace("_", " ").title()
        total = sum(q for _, q in group)
        parts.append(f'<div class="card-type-header type-{section_class}">{label} ({total})</div>')
        group.sort(key=lambda x: x[0].get("name", ""))
        parts.extend(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in group)
    return "".join(parts)


def _build_section_block(
    cards_with_qty: Sequence[tuple[Mapping[str, Any], int]],
    section_class: str,
    *,
    header_html: str = "",
    show_aspect_dot: bool = False,
) -> str:
    return (
        '<div class="faction-section">'
        f'{header_html}'
        f'{_render_card_section_html(cards_with_qty, section_class, show_aspect_dot=show_aspect_dot)}'
        '</div>'
    )


def _render_sorted_cards_html(
    cards_with_qty: Sequence[tuple[Mapping[str, Any], int]],
    sort_mode: str,
    *,
    show_aspect_dot: bool = False,
    prepend_blocks: Sequence[tuple[str, int]] | None = None,
) -> str:
    section_blocks: list[tuple[str, int]] = list(prepend_blocks) if prepend_blocks else []

    if sort_mode == "name":
        sorted_cards = sorted(cards_with_qty, key=lambda x: x[0].get("name", "").lower())
        midpoint = (len(sorted_cards) + 1) // 2
        for chunk in (sorted_cards[:midpoint], sorted_cards[midpoint:]):
            if not chunk:
                continue
            section_blocks.append((
                '<div class="faction-section">'
                f'{"".join(build_card_row(c, q, show_aspect_dot=show_aspect_dot) for c, q in chunk)}'
                '</div>',
                len(chunk),
            ))
    elif sort_mode == "cost":
        by_cost: dict[int, list[tuple[Mapping[str, Any], int]]] = {}
        for card, qty in cards_with_qty:
            cost = card.get("cost")
            by_cost.setdefault(cost if cost is not None else -1, []).append((card, qty))
        for cost_key in sorted(by_cost.keys()):
            group = by_cost[cost_key]
            group.sort(key=lambda x: x[0].get("name", "").lower())
            total = sum(q for _, q in group)
            label = f"Cost {cost_key}" if cost_key >= 0 else "No Cost"
            section_blocks.append((
                _build_section_block(
                    group, "basic",
                    header_html=f'<div class="faction-header type-basic">{label} ({total})</div>',
                    show_aspect_dot=show_aspect_dot,
                ),
                _section_weight(group, include_header=True),
            ))
    elif sort_mode == "aspect":
        by_faction: dict[str, list[tuple[Mapping[str, Any], int]]] = {}
        for card, qty in cards_with_qty:
            by_faction.setdefault(card.get("faction_code", "basic"), []).append((card, qty))
        for faction in sorted(by_faction.keys()):
            group = by_faction[faction]
            group.sort(key=lambda x: x[0].get("name", "").lower())
            total = sum(q for _, q in group)
            css_f = ASPECT_COLORS.get(faction, "basic")
            label_f = ASPECT_DISPLAY.get(faction, faction.title())
            section_blocks.append((
                _build_section_block(
                    group, css_f,
                    header_html=f'<div class="faction-header type-{css_f}">{label_f} ({total})</div>',
                    show_aspect_dot=show_aspect_dot,
                ),
                _section_weight(group, include_header=True),
            ))
    elif sort_mode == "set":
        by_set: dict[str, list[tuple[Mapping[str, Any], int]]] = {}
        for card, qty in cards_with_qty:
            by_set.setdefault(card.get("pack_name", "Unknown"), []).append((card, qty))
        for pack in sorted(by_set.keys()):
            group = by_set[pack]
            group.sort(key=lambda x: x[0].get("name", "").lower())
            total = sum(q for _, q in group)
            section_blocks.append((
                _build_section_block(
                    group, "basic",
                    header_html=f'<div class="faction-header type-basic">{html_escape(pack)} ({total})</div>',
                    show_aspect_dot=show_aspect_dot,
                ),
                _section_weight(group, include_header=True),
            ))

    return _render_section_grid_html(section_blocks)


# ─── Public renderer ────────────────────────────────────────────────────────

def deck_widget_namespace(deck: DeckView) -> str:
    """Build a widget-key namespace guaranteed unique across decks.

    Including hero_code + url-hash defends against the duplicate-element error
    that crashed mobile users when two decks shared an ``id`` (or both fell
    through to the ``"unknown"`` default).
    """
    fingerprint = abs(hash(deck.url or deck.name)) % (10 ** 8)
    return f"{deck.deck_id}_{deck.hero_code}_{fingerprint}"


def render_deck(
    deck_data: Mapping[str, Any],
    card_db: Mapping[str, Any],
    *,
    show_header: bool = True,
    community_tier_lookup=None,
) -> None:
    """Render a full deck display with flowing two-column layout.

    Parameters
    ----------
    deck_data : raw MarvelCDB payload (will be normalized via DeckView).
    card_db : full card database keyed by code.
    show_header : when ``False``, skip the title/badge/stat row (used when the
        caller renders its own header, e.g. inside a tab).
    community_tier_lookup : optional callable ``(hero_name) -> (tier, avg)`` so
        this module doesn't need to import the page's community tier helper.
    """
    deck = DeckView.from_payload(deck_data)
    deck_name = html_escape(deck.name)
    aspect_class = ASPECT_COLORS.get(deck.aspect, "basic")
    aspect_label = ASPECT_DISPLAY.get(deck.aspect, deck.aspect.title() if deck.aspect else "Basic")
    description = _fix_description_links(deck.description_md)

    hero_cards: list[tuple[Mapping[str, Any], int]] = []
    aspect_cards: list[tuple[Mapping[str, Any], int]] = []
    unknown_codes: list[str] = []

    for code, qty in deck.slots.items():
        card = card_db.get(code)
        if card is None:
            unknown_codes.append(code)
            continue
        if card.get("faction_code") == "hero":
            hero_cards.append((card, qty))
        else:
            aspect_cards.append((card, qty))

    def _merge_by_name(cards):
        merged: dict[str, tuple[Mapping[str, Any], int]] = {}
        order: list[str] = []
        for card, qty in cards:
            key = card.get("name", "")
            if key in merged:
                existing_card, existing_qty = merged[key]
                if not existing_card.get("imagesrc") and card.get("imagesrc"):
                    existing_card = card
                merged[key] = (existing_card, existing_qty + qty)
            else:
                merged[key] = (card, qty)
                order.append(key)
        return [merged[k] for k in order]

    hero_cards = _merge_by_name(hero_cards)
    aspect_cards = _merge_by_name(aspect_cards)

    total_cards = sum(deck.slots.values())
    hero_count = sum(q for _, q in hero_cards)
    aspect_count = sum(q for _, q in aspect_cards)

    # ── Header ──
    if show_header:
        link_html = (
            f' &nbsp; <a class="mcdb-link" href="{deck.url}" target="_blank" '
            f'rel="noopener noreferrer">MarvelCDB \u2197</a>'
        ) if deck.url else ""

        hero_card_h = card_db.get(deck.hero_code, {}) if deck.hero_code else {}
        hero_display_name = hero_card_h.get("name") or st.session_state.get("deck_hero", "")

        tier_badge_html = ""
        if community_tier_lookup is not None:
            try:
                comm_tier, comm_avg = community_tier_lookup(hero_display_name)
            except Exception:
                comm_tier, comm_avg = None, None
            if comm_tier:
                tier_color = TIER_COLORS.get(comm_tier, "#95a5a6")
                tier_badge_html = (
                    f'<span class="aspect-badge" style="background:{tier_color};" '
                    f'title="Community Hero Power avg {comm_avg:.2f}/6">'
                    f'Community Tier {comm_tier}</span>'
                )

        st.markdown(
            f'<div class="deck-title">{deck_name}'
            f'<span class="aspect-badge aspect-{aspect_class}">{aspect_label}</span>'
            f'{tier_badge_html}</div>'
            f'<div class="deck-stats">'
            f'<div class="deck-stat"><strong>{total_cards}</strong> cards</div>'
            f'<div class="deck-stat"><strong>{aspect_count}</strong> aspect/basic</div>'
            f'{link_html}</div>',
            unsafe_allow_html=True,
        )

    # ── Sort selector ──
    key_ns = deck_widget_namespace(deck)
    sort_col, combine_col, view_col = st.columns([3, 1, 1])
    with sort_col:
        sort_choice = st.radio(
            "Sort by",
            ["Type", "Name", "Cost", "Set"],
            index=0,
            horizontal=True,
            key=f"deck_sort_{key_ns}",
        )
    sort_mode = sort_choice.lower() if sort_choice != "Type" else "default"
    with combine_col:
        combine_aspects = st.checkbox("Combine aspects", value=False, key=f"deck_combine_{key_ns}")
    with view_col:
        st.write("")
        hero_card_btn = card_db.get(deck.hero_code, {}) if deck.hero_code else {}
        hero_name_btn = hero_card_btn.get("name") or st.session_state.get("deck_hero", "")
        if hero_name_btn and st.button("View Hero Cards", key=f"view_hero_cards_{key_ns}"):
            open_hero_cards_dialog(hero_name_btn, HERO_ALTER_EGOS.get(hero_name_btn, ""))

    # ── Hero block ──
    hero_prepend_blocks: list[tuple[str, int]] = []
    if hero_cards:
        hero_header_html = f'<div class="faction-header type-hero">Hero Cards ({hero_count})</div>'
        hero_prepend_blocks.append((
            _build_section_block(hero_cards, "hero", header_html=hero_header_html),
            _section_weight(hero_cards, include_header=True),
        ))

    # ── Card display ──
    if aspect_cards or hero_prepend_blocks:
        if sort_mode == "default" and not combine_aspects:
            cards_by_faction: dict[str, list[tuple[Mapping[str, Any], int]]] = {}
            for card, qty in aspect_cards:
                cards_by_faction.setdefault(card.get("faction_code", "basic"), []).append((card, qty))
            factions = sorted(cards_by_faction.keys())
            section_blocks = list(hero_prepend_blocks)
            for faction in factions:
                cards_f = cards_by_faction[faction]
                css_f = ASPECT_COLORS.get(faction, "basic")
                label_f = ASPECT_DISPLAY.get(faction, faction.title())
                include_header = len(factions) > 1
                header_html = (
                    f'<div class="faction-header type-{css_f}">{label_f} ({sum(q for _, q in cards_f)})</div>'
                ) if include_header else ""
                section_blocks.append((
                    _build_section_block(cards_f, css_f, header_html=header_html),
                    _section_weight(cards_f, include_header=include_header),
                ))
            st.markdown(_render_section_grid_html(section_blocks), unsafe_allow_html=True)
        elif sort_mode == "default" and combine_aspects:
            css_combined = ASPECT_COLORS.get(deck.aspect, "basic")
            combined_blocks = list(hero_prepend_blocks)
            if aspect_cards:
                combined_blocks.append((
                    _build_section_block(aspect_cards, css_combined, show_aspect_dot=True),
                    _section_weight(aspect_cards),
                ))
            st.markdown(_render_section_grid_html(combined_blocks), unsafe_allow_html=True)
        else:
            st.markdown(
                _render_sorted_cards_html(
                    aspect_cards, sort_mode,
                    show_aspect_dot=combine_aspects,
                    prepend_blocks=hero_prepend_blocks,
                ),
                unsafe_allow_html=True,
            )

    # ── Description ──
    if show_header and description.strip():
        with st.expander("Deck Description"):
            st.markdown(description)

    # ── Obligation & Nemesis ──
    if deck.hero_code:
        obligation_cards, nemesis_cards = get_obligation_nemesis(deck.hero_code, card_db)
        if obligation_cards or nemesis_cards:
            total_enc = (
                sum(c.get("quantity", 1) for c in obligation_cards)
                + sum(c.get("quantity", 1) for c in nemesis_cards)
            )
            html_parts = [f'<div class="faction-header type-hero">Obligation &amp; Nemesis ({total_enc})</div>']
            if obligation_cards:
                html_parts.append('<div class="card-type-header type-hero">Obligation</div>')
                html_parts.extend(build_card_row(c, c.get("quantity", 1)) for c in obligation_cards)
            if nemesis_cards:
                html_parts.append('<div class="card-type-header type-hero">Nemesis Set</div>')
                html_parts.extend(build_card_row(c, c.get("quantity", 1)) for c in nemesis_cards)
            st.markdown("".join(html_parts), unsafe_allow_html=True)

    if unknown_codes:
        with st.expander(f"{len(unknown_codes)} card(s) not found in database"):
            st.code(", ".join(unknown_codes))


def deck_aspect(deck_data: Mapping[str, Any]) -> str:
    """Return the aspect string for a raw deck payload (for filtering)."""
    return _aspect_from_meta(deck_data.get("meta"))
