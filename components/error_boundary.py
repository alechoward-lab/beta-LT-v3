"""
Lightweight error boundary for Streamlit pages.

Wrap a page's main render block with :func:`page_boundary` so that any
unexpected exception is logged to the server console and displayed to the user
as a friendly retry banner instead of crashing the whole script.
"""

from __future__ import annotations

import contextlib
import logging
import traceback
from typing import Iterator

import streamlit as st

_log = logging.getLogger("beta-LT-v3.error_boundary")


@contextlib.contextmanager
def page_boundary(label: str = "page") -> Iterator[None]:
    """Context manager that catches exceptions and shows a friendly banner.

    Usage::

        with page_boundary("good-decks"):
            render_my_page()
    """
    try:
        yield
    except Exception:
        tb = traceback.format_exc()
        _log.exception("Unhandled error in %s", label)
        st.error(
            "Something went wrong while rendering this page. "
            "It's usually transient — try the retry button below."
        )
        cols = st.columns([1, 1, 4])
        with cols[0]:
            if st.button("🔄 Retry", key=f"_eb_retry_{label}"):
                st.rerun()
        with cols[1]:
            if st.button("🐞 Show details", key=f"_eb_show_{label}"):
                st.session_state[f"_eb_show_{label}_state"] = True
        if st.session_state.get(f"_eb_show_{label}_state"):
            st.code(tb, language="text")
