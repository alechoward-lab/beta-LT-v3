"""
Navigation Banner & Page Header — Shared UI components for all pages.
Import and call render_nav_banner("page-id") and render_page_header("Title") from any page.
"""

import streamlit as st
import streamlit.components.v1 as components
from html import escape as html_escape

LOGO_URL = "https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/Daring_Lime_Logo.png?raw=true"


NAV_PAGES = [
    ("Community Tier Lists", "/", "home"),
    ("Out of the Box", "/hero-tier-list", "hero-tier-list"),
    ("Decks For Every Hero", "/good-decks", "good-decks"),
    ("Hero Pairings", "/hero-pairings", "hero-pairings"),
    ("Team Builder", "/team-builder", "team-builder"),
    ("Team Generator", "/team-generator", "team-generator"),
    ("Recommender", "/hero-recommender", "hero-recommender"),
    ("Hero Comparison", "/hero-comparison", "hero-comparison"),
    ("YouTube", "/youtube-channel", "youtube-channel"),
    ("Villain Tier List", "/villain-tier-list", "villain-tier-list"),
]


def render_nav_banner(current_page=""):
    """Render a coloured navigation banner with page links at the top of the page."""
    links_html = ""
    for label, href, page_id in NAV_PAGES:
        active = "nav-active" if page_id == current_page else ""
        links_html += f'<a href="{href}" class="nav-link {active}" target="_self">{label}</a> '

    # Global background image
    _bg_url = (
        "https://github.com/alechoward-lab/"
        "Marvel-Champions-Hero-Tier-List/blob/main/"
        "images/background/marvel_champions_background_image_v4.jpg?raw=true"
    )

    st.markdown(
        f"""<style>
.stApp {{
    background: url({_bg_url}) no-repeat center center fixed;
    background-size: cover;
}}
[data-testid="stMainBlockContainer"] {{
    background: rgba(10, 10, 28, 0.82);
}}
.nav-banner {{
    display: flex;
    align-items: center;
    gap: 4px;
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
    padding: 8px 12px;
    border-radius: 10px;
    margin-bottom: 18px;
    flex-wrap: wrap;
    justify-content: center;
    border: 1px solid rgba(255,255,255,0.1);
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}}
.nav-link {{
    color: #a0a8b8;
    text-decoration: none;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    transition: all 0.2s ease;
    white-space: nowrap;
}}
.nav-link:hover {{
    background: rgba(255,255,255,0.1);
    color: #ffffff;
    text-decoration: none;
}}
.nav-active {{
    background: rgba(52, 152, 219, 0.3) !important;
    color: #ffffff !important;
    border: 1px solid rgba(52, 152, 219, 0.5);
}}
.stMainBlockContainer {{
    animation: fadeIn 0.4s ease-in;
}}
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
::-webkit-scrollbar {{
    width: 8px;
}}
::-webkit-scrollbar-track {{
    background: rgba(0,0,0,0.1);
}}
::-webkit-scrollbar-thumb {{
    background: rgba(255,255,255,0.15);
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: rgba(255,255,255,0.25);
}}
[data-testid="stImage"] img {{
    border-radius: 10px;
    border: 2px solid rgba(255,255,255,0.5);
    box-shadow: 0 4px 15px rgba(0,0,0,0.5), 0 0 6px rgba(255,255,255,0.1);
    transition: border-color 0.3s ease, box-shadow 0.3s ease, transform 0.3s ease;
}}
[data-testid="stImage"] img:hover {{
    border-color: rgba(255,255,255,0.9);
    box-shadow: 0 0 15px rgba(255,255,255,0.5), 0 0 30px rgba(255,255,255,0.15), 0 8px 25px rgba(0,0,0,0.6);
    transform: scale(1.05);
}}
/* ── Mobile-friendly adjustments ── */
@media (max-width: 768px) {{
    .nav-banner {{
        gap: 2px;
        padding: 6px 8px;
    }}
    .nav-link {{
        padding: 4px 8px;
        font-size: 11px;
    }}
    .page-title {{
        font-size: 18px !important;
    }}
    .page-subtitle {{
        font-size: 11px !important;
    }}
    .page-header .logo {{
        height: 32px !important;
        margin-right: 8px !important;
    }}
    .social-icons img {{
        height: 22px !important;
    }}
    /* Make Streamlit column grids wrap on mobile */
    [data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
        gap: 8px !important;
    }}
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
        flex: 0 0 calc(33.33% - 8px) !important;
        min-width: calc(33.33% - 8px) !important;
        max-width: calc(33.33% - 8px) !important;
    }}
    [data-testid="stImage"] img {{
        border-width: 1px;
    }}
    [data-testid="stImage"] img:hover {{
        transform: none;
    }}
    /* Hide decorative elements on mobile — keep it functional */
    #onboarding-overlay {{
        padding: 14px 12px !important;
    }}
    #onboarding-overlay > div:first-child {{
        font-size: 16px !important;
    }}
    .hero-hover-panel {{ display: none !important; }}
    /* Tighten spacing on mobile */
    [data-testid="stExpander"] {{
        margin-bottom: 8px !important;
    }}
    h2 {{
        font-size: 18px !important;
        margin-top: 8px !important;
        margin-bottom: 4px !important;
    }}
}}
@media (max-width: 480px) {{
    [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {{
        flex: 0 0 calc(50% - 6px) !important;
        min-width: calc(50% - 6px) !important;
        max-width: calc(50% - 6px) !important;
    }}
    .nav-link {{
        padding: 3px 6px;
        font-size: 10px;
    }}
    .page-title {{
        font-size: 16px !important;
    }}
}}
</style>
<div class="nav-banner">
{links_html}
</div>""",
        unsafe_allow_html=True,
    )

    # Build keyboard help overlay
    _shortcut_list = "".join(
        f'<div style="display:flex;gap:10px;margin:3px 0;">'
        f'<kbd style="background:#2c3e50;padding:2px 8px;border-radius:4px;min-width:24px;text-align:center;font-size:13px;">{i+1}</kbd>'
        f'<span style="color:#c8cdd5;font-size:13px;">{label}</span></div>'
        for i, (label, _, _) in enumerate(NAV_PAGES[:9])
    )

    st.markdown(
        f"""<div id="keyboard-help" style="display:none;position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);
background:rgba(20,20,40,0.97);border:1px solid rgba(255,255,255,0.2);border-radius:12px;padding:20px 28px;
z-index:99999;box-shadow:0 8px 40px rgba(0,0,0,0.7);max-width:320px;">
<div style="font-size:16px;font-weight:bold;color:white;margin-bottom:10px;">⌨️ Keyboard Shortcuts</div>
{_shortcut_list}
<div style="display:flex;gap:10px;margin:8px 0 0 0;padding-top:8px;border-top:1px solid rgba(255,255,255,0.1);">
<kbd style="background:#2c3e50;padding:2px 8px;border-radius:4px;font-size:13px;">?</kbd>
<span style="color:#c8cdd5;font-size:13px;">Toggle this help</span></div>
</div>""",
        unsafe_allow_html=True,
    )

    # Keyboard shortcuts: press ? to show help, 1-9 to jump to pages
    _nav_urls = [href for _, href, _ in NAV_PAGES]
    _shortcut_js = "".join(
        f'case "{i+1}": window.parent.location.href="{url}"; break;'
        for i, url in enumerate(_nav_urls[:9])
    )
    components.html(
        f"""<script>
window.parent.document.addEventListener('keydown', function(e) {{
    if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
    if (e.key === '?') {{
        var el = window.parent.document.getElementById('keyboard-help');
        if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
        e.preventDefault();
    }}
    switch(e.key) {{ {_shortcut_js} }}
}});
</script>""",
        height=0,
    )


def render_page_header(title, subtitle=""):
    """Render a styled page header bar with logo and optional subtitle."""
    sub_html = f'<div class="page-subtitle">{html_escape(subtitle)}</div>' if subtitle else ""

    # Dark/light mode toggle
    light_mode = st.session_state.get("_light_mode", False)
    mode_icon = "☀️" if not light_mode else "🌙"

    st.markdown(
        f"""<style>
.page-header {{
    display: flex;
    justify-content: center;
    align-items: center;
    background: linear-gradient(135deg, rgba(26,26,46,0.8) 0%, rgba(22,33,62,0.8) 50%, rgba(15,52,96,0.6) 100%);
    padding: 12px 20px;
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    margin-bottom: 16px;
    text-align: center;
}}
.page-header .logo {{
    height: 45px;
    margin-right: 14px;
    filter: drop-shadow(0 2px 4px rgba(0,0,0,0.4));
}}
.page-title {{
    font-family: Arial, sans-serif;
    font-size: 26px;
    font-weight: bold;
    color: white;
    text-shadow: 1px 1px 4px rgba(0,0,0,0.5);
    letter-spacing: 0.02em;
}}
.page-subtitle {{
    font-size: 13px;
    color: #a0a8b8;
    margin-top: 2px;
    letter-spacing: 0.01em;
}}
.social-icons {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-left: auto;
    padding-left: 16px;
}}
.social-icons a {{
    transition: opacity 0.2s ease;
    display: flex;
    align-items: center;
}}
.social-icons a:hover {{
    opacity: 0.7;
}}
.theme-toggle {{
    cursor: pointer;
    font-size: 20px;
    margin-left: 12px;
    user-select: none;
    filter: drop-shadow(0 1px 2px rgba(0,0,0,0.4));
    transition: transform 0.2s ease;
}}
.theme-toggle:hover {{
    transform: scale(1.2);
}}
</style>
{"" if not light_mode else '''<style>
/* ── Light-mode overrides ── */

/* Main background & text */
.stApp, .stApp > header, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stBottomBlockContainer"] {
    background-color: #f7f8fc !important;
    color: #1e293b !important;
}
[data-testid="stMainBlockContainer"] {
    background-color: #f7f8fc !important;
}

/* Sidebar */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {
    background-color: #eef1f6 !important;
    color: #1e293b !important;
    border-right: 1px solid #d1d5db !important;
}

/* Body text everywhere */
.stApp p, .stApp li, .stApp label, .stApp span, .stApp div,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div,
[data-testid="stText"] {
    color: #1e293b !important;
}

/* Headings */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {
    color: #0f3460 !important;
}

/* Links */
.stApp a, [data-testid="stMarkdownContainer"] a {
    color: #2563eb !important;
}
.stApp a:hover, [data-testid="stMarkdownContainer"] a:hover {
    color: #1d4ed8 !important;
}

/* Nav banner */
.nav-banner {
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 50%, #94a3b8 100%) !important;
    border-color: rgba(0,0,0,0.08) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}
.nav-link {
    color: #334155 !important;
}
.nav-link:hover {
    background: rgba(0,0,0,0.06) !important;
    color: #0f172a !important;
}
.nav-active {
    background: rgba(37,99,235,0.15) !important;
    color: #1e40af !important;
    border-color: rgba(37,99,235,0.3) !important;
}

/* Page header */
.page-header {
    background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 50%, #94a3b8 100%) !important;
    border-color: rgba(0,0,0,0.08) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08) !important;
}
.page-title {
    color: #0f172a !important;
    text-shadow: none !important;
}
.page-subtitle {
    color: #475569 !important;
}

/* Expanders */
[data-testid="stExpander"] {
    border-color: #d1d5db !important;
    background: #ffffff !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span {
    color: #1e293b !important;
}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {
    background: #ffffff !important;
}

/* Buttons */
.stButton > button, [data-testid="stBaseButton-secondary"] {
    background: #e2e8f0 !important;
    color: #1e293b !important;
    border: 1px solid #cbd5e1 !important;
}
.stButton > button:hover, [data-testid="stBaseButton-secondary"]:hover {
    background: #cbd5e1 !important;
    border-color: #94a3b8 !important;
}
[data-testid="stBaseButton-primary"] {
    background: #2563eb !important;
    color: white !important;
    border-color: #1d4ed8 !important;
}

/* Selectboxes / dropdowns */
[data-testid="stSelectbox"] > div > div,
[data-baseweb="select"] > div {
    background: #ffffff !important;
    border-color: #d1d5db !important;
    color: #1e293b !important;
}
[data-baseweb="select"] span {
    color: #1e293b !important;
}

/* Text inputs */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: #ffffff !important;
    color: #1e293b !important;
    border-color: #d1d5db !important;
}

/* Sliders */
[data-testid="stSlider"] label,
[data-testid="stSlider"] div[data-testid="stTickBarMin"],
[data-testid="stSlider"] div[data-testid="stTickBarMax"] {
    color: #1e293b !important;
}
[data-testid="stSlider"] [data-testid="stThumbValue"] {
    color: #1e293b !important;
}

/* Tabs */
[data-testid="stTabs"] button {
    color: #475569 !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    color: #2563eb !important;
    border-bottom-color: #2563eb !important;
}

/* Checkboxes & toggles */
[data-testid="stCheckbox"] label span {
    color: #1e293b !important;
}

/* Radio buttons */
[data-testid="stRadio"] label {
    color: #1e293b !important;
}

/* Card images — softer look */
[data-testid="stImage"] img {
    border-color: rgba(0,0,0,0.15) !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1), 0 0 2px rgba(0,0,0,0.05) !important;
}
[data-testid="stImage"] img:hover {
    border-color: rgba(0,0,0,0.3) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.15), 0 0 4px rgba(0,0,0,0.08) !important;
}

/* Metrics */
[data-testid="stMetric"] {
    background: #ffffff !important;
    border-radius: 8px !important;
    border: 1px solid #e2e8f0 !important;
}
[data-testid="stMetricValue"] {
    color: #0f172a !important;
}
[data-testid="stMetricLabel"] {
    color: #475569 !important;
}

/* Horizontal dividers */
hr {
    border-color: #d1d5db !important;
}

/* Toast / alerts */
[data-testid="stAlert"] {
    background: #ffffff !important;
    color: #1e293b !important;
    border-color: #d1d5db !important;
}

/* Inline code & code blocks */
code {
    background: #e2e8f0 !important;
    color: #0f172a !important;
}

/* Scrollbar in light mode */
::-webkit-scrollbar-track {
    background: #f1f5f9 !important;
}
::-webkit-scrollbar-thumb {
    background: #94a3b8 !important;
}
::-webkit-scrollbar-thumb:hover {
    background: #64748b !important;
}

/* Deck list page — card rows and headers */
.card-row:hover {
    background: rgba(0,0,0,0.04) !important;
}
.card-qty {
    color: #1e293b !important;
}
.card-name, .card-name a {
    color: #1e293b !important;
}
.card-name a:hover {
    color: #2563eb !important;
}
.card-cost {
    color: #64748b !important;
}
.deck-title {
    color: #0f172a !important;
}
.deck-stat {
    background: rgba(0,0,0,0.04) !important;
    color: #475569 !important;
}
.deck-stat strong {
    color: #0f172a !important;
}
.deck-summary-note {
    color: #475569 !important;
}

/* Floating hero cards — softer border in light mode */
.card-float img {
    border-color: rgba(0,0,0,0.15) !important;
    box-shadow: 0 4px 16px rgba(0,0,0,0.12) !important;
}
.card-float:hover img {
    border-color: rgba(0,0,0,0.3) !important;
    box-shadow: 0 6px 24px rgba(0,0,0,0.2) !important;
}

/* Keyboard help overlay — works in light mode too */
#keyboard-help {
    background: rgba(255,255,255,0.97) !important;
    border-color: #d1d5db !important;
    color: #1e293b !important;
    box-shadow: 0 8px 40px rgba(0,0,0,0.15) !important;
}
</style>'''}
<div class="page-header">
<img class="logo" src="{LOGO_URL}" alt="Daring Lime Logo">
<div>
<div class="page-title">{html_escape(title)}</div>
{sub_html}
</div>
<div class="social-icons">
<a href="https://www.youtube.com/channel/UCpV2UWmBTAeIKUso1LkeU2A" target="_blank"><img src="https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/youtube_logo.png?raw=true" alt="YouTube" style="height:28px;"></a>
<a href="https://discord.gg/ReF5jDSHqV" target="_blank"><img src="https://github.com/alechoward-lab/Marvel-Champions-Hero-Tier-List/blob/main/images/logo/Discord-Logo.png?raw=true" alt="Discord" style="height:28px;"></a>
</div>
</div>""",
        unsafe_allow_html=True,
    )
    # Theme toggle button rendered as a Streamlit button
    st.toggle(f"{mode_icon} Light mode", value=light_mode, key="_light_mode")


def render_footer(show_card_credits=False):
    """Render a consistent footer across all pages."""
    st.markdown("---")
    credits = (
        'Built by <a href="https://www.youtube.com/channel/UCpV2UWmBTAeIKUso1LkeU2A" target="_blank" style="color:#3498db;">Daring Lime</a>'
        ' &nbsp;·&nbsp; '
        '<a href="https://discord.gg/ReF5jDSHqV" target="_blank" style="color:#3498db;">Discord</a>'
        ' &nbsp;·&nbsp; '
        'Card data by <a href="https://marvelcdb.com" target="_blank" style="color:#3498db;">MarvelCDB</a>'
    )
    if show_card_credits:
        credits += (
            ' &nbsp;·&nbsp; '
            'Card images from the Cerebro Discord bot by UnicornSnuggler'
        )
    st.markdown(
        f'<div style="text-align:center; color:#888; font-size:12px; padding:8px 0 16px 0;">{credits}</div>',
        unsafe_allow_html=True,
    )
