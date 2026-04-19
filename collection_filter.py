"""
Collection Filter — Sidebar widget to filter heroes by owned collection.
Import and call render_collection_filter() from any page to add the filter.
It stores the selection in st.session_state["owned_heroes"] (None = all owned).
"""

import streamlit as st
from default_heroes import default_heroes
from hero_image_urls import hero_image_urls


def _toggle_hero(hero):
    """Toggle a single hero in/out of the owned set."""
    owned = st.session_state.get("owned_heroes")
    if owned is None:
        owned = set(default_heroes.keys())
    if hero in owned:
        owned.discard(hero)
    else:
        owned.add(hero)
    st.session_state["owned_heroes"] = owned


def render_collection_filter():
    """Render a collection filter in the sidebar. Returns the set of owned hero names, or None if all are owned."""
    all_heroes = sorted(default_heroes.keys())

    with st.sidebar:
        st.markdown("### 📦 My Collection")
        use_filter = st.checkbox(
            "Filter by owned heroes",
            value=st.session_state.get("use_collection_filter", False),
            key="use_collection_filter",
        )

        if not use_filter:
            st.session_state["owned_heroes"] = None
            return None

        # Initialize owned heroes if not set
        if "owned_heroes" not in st.session_state or st.session_state["owned_heroes"] is None:
            st.session_state["owned_heroes"] = set(all_heroes)

        owned = st.session_state["owned_heroes"]

        # Quick buttons — use a form so the rerun happens cleanly after state update
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Select All", key="coll_all", width="stretch"):
                st.session_state["owned_heroes"] = set(all_heroes)
                st.rerun()
        with col2:
            if st.button("❌ Clear All", key="coll_clear", width="stretch"):
                st.session_state["owned_heroes"] = set()
                st.rerun()

        # Re-read owned after potential rerun
        owned = st.session_state["owned_heroes"]

        st.caption(f"{len(owned)} / {len(all_heroes)} heroes selected")

        # Hero image grid — 3 per row in sidebar, toggle on click
        cols_per_row = 3
        for i in range(0, len(all_heroes), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                idx = i + j
                if idx >= len(all_heroes):
                    break
                hero = all_heroes[idx]
                is_owned = hero in owned
                with col:
                    img = hero_image_urls.get(hero, "")
                    if img:
                        # Dim unowned heroes with CSS opacity trick via caption
                        if is_owned:
                            st.image(img, width="stretch")
                        else:
                            st.image(img, width="stretch")
                    label = "✅" if is_owned else "➕"
                    if st.button(
                        f"{label} {hero}",
                        key=f"coll_{idx}",
                        width="stretch",
                    ):
                        _toggle_hero(hero)
                        st.rerun()

        return set(owned)
