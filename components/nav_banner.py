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

    # Background images — dark uses v4 (faded), light uses v5 (colored)
    _gh_base = ("https://github.com/alechoward-lab/"
                "Marvel-Champions-Hero-Tier-List/blob/main/"
                "images/background/")

    # Dark mode — bright v5 served locally via Streamlit static
    _bg_url = "./app/static/bg_v5.jpg"

    # Light mode — same bright v5
    _bg_url_light = "./app/static/bg_v5.jpg"

    st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Bangers&display=swap');

.stApp {{
    background: url({_bg_url}) no-repeat center center fixed;
    background-size: cover;
}}
[data-testid="stMainBlockContainer"] {{
    background: rgba(10, 10, 28, 0.96);
}}

/* ── Nav Banner — Comic Book Tab Bar ── */
.nav-banner {{
    display: flex;
    align-items: center;
    gap: 4px;
    background: #0d0d1a;
    padding: 6px 10px;
    border-radius: 0px;
    margin-bottom: 18px;
    flex-wrap: wrap;
    justify-content: center;
    border: 3px solid #222;
    border-bottom: 4px solid #ed1c24;
    box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.6);
    position: relative;
}}
.nav-link {{
    color: #c8cdd5;
    text-decoration: none;
    padding: 6px 14px;
    border-radius: 3px;
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    transition: all 0.2s ease;
    white-space: nowrap;
    position: relative;
    z-index: 1;
}}
.nav-link:hover {{
    background: rgba(255, 255, 255, 0.08);
    color: #ffffff;
    text-decoration: none;
}}
.nav-active {{
    background: #ed1c24 !important;
    color: #ffffff !important;
    border: none;
    box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.5);
}}

/* ── Comic-style borders on key containers ── */
[data-testid="stExpander"] {{
    border: 2px solid rgba(237, 28, 36, 0.3) !important;
    border-radius: 4px !important;
    box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.4);
}}
[data-testid="stExpander"] summary {{
    font-weight: 700 !important;
    letter-spacing: 0.3px;
}}

/* ── Buttons — Bold Comic Style ── */
.stButton > button, [data-testid="stBaseButton-secondary"] {{
    border: 2px solid rgba(255, 255, 255, 0.2) !important;
    border-radius: 4px !important;
    font-weight: 700 !important;
    text-transform: none !important;
    letter-spacing: 0.5px !important;
    font-size: 11px !important;
    transition: all 0.15s ease !important;
    box-shadow: 2px 2px 0 rgba(0, 0, 0, 0.4) !important;
}}
.stButton > button:hover, [data-testid="stBaseButton-secondary"]:hover {{
    transform: translate(-1px, -1px) !important;
    box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.5) !important;
}}
.stButton > button:active, [data-testid="stBaseButton-secondary"]:active {{
    transform: translate(1px, 1px) !important;
    box-shadow: 1px 1px 0 rgba(0, 0, 0, 0.3) !important;
}}
[data-testid="stBaseButton-primary"] {{
    background: linear-gradient(180deg, #ed1c24 0%, #b71c1c 100%) !important;
    border-color: #ff3333 !important;
    color: #ffffff !important;
    text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5) !important;
}}
[data-testid="stBaseButton-primary"]:hover {{
    background: linear-gradient(180deg, #ff3333 0%, #d32f2f 100%) !important;
}}

/* ── Headings — Comic Book Feel ── */
.stApp h1, .stApp h2, .stApp h3,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {{
    font-family: 'Bangers', cursive, Impact, sans-serif !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
}}
.stApp h2, [data-testid="stMarkdownContainer"] h2 {{
    color: #ed1c24 !important;
    text-shadow: 2px 2px 0 #000 !important;
    font-size: 28px !important;
}}
.stApp h3, [data-testid="stMarkdownContainer"] h3 {{
    color: #f7c948 !important;
    text-shadow: 1px 1px 0 #000 !important;
}}

/* ── Horizontal Rules — Comic Panel Dividers ── */
hr {{
    border: none !important;
    height: 3px !important;
    background: #ed1c24 !important;
    margin: 16px 0 !important;
    box-shadow: 1px 1px 0 rgba(0, 0, 0, 0.4) !important;
}}

/* ── Hero Card Images — Comic Panel Style ── */
/* Random rotation via nth-child for a scattered comic-page feel */
.hero-card:nth-child(5n+1) {{ --hover-rotate: -2.5deg; }}
.hero-card:nth-child(5n+2) {{ --hover-rotate: 1.8deg; }}
.hero-card:nth-child(5n+3) {{ --hover-rotate: -1.2deg; }}
.hero-card:nth-child(5n+4) {{ --hover-rotate: 3deg; }}
.hero-card:nth-child(5n+5) {{ --hover-rotate: -0.5deg; }}
.hero-card:nth-child(7n+1) {{ --hover-rotate: 2.2deg; }}
.hero-card:nth-child(7n+3) {{ --hover-rotate: -3deg; }}
.hero-card:nth-child(7n+6) {{ --hover-rotate: 1deg; }}

[data-testid="stImage"] img {{
    border-radius: 2px;
    border: 3px solid #111;
    box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.6);
    transition: border-color 0.15s ease, box-shadow 0.15s ease, transform 0.15s ease;
}}
[data-testid="stImage"] img:hover {{
    border-color: #ed1c24;
    box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.7);
}}
/* Tier list hero cards — random rotation on hover */
.hero-card {{
    transition: transform 0.15s ease;
}}
.hero-card:hover {{
    transform: scale(1.08) rotate(var(--hover-rotate, -1deg));
    z-index: 10;
}}

/* ── Comic Section Banner (campaign-log inspired) ── */
.comic-banner {{
    background: linear-gradient(180deg, #1a1a2e 0%, #0d0d1a 100%);
    color: #fff;
    font-family: 'Bangers', cursive, Impact, sans-serif;
    font-size: 20px;
    letter-spacing: 3px;
    text-transform: uppercase;
    text-align: center;
    padding: 10px 24px;
    margin: 18px 0 12px 0;
    border: 3px solid #333;
    border-left: 5px solid #ed1c24;
    box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.5);
}}

/* ── Selectboxes — Subtle Comic Borders ── */
[data-baseweb="select"] > div {{
    border: 2px solid rgba(237, 28, 36, 0.25) !important;
    border-radius: 4px !important;
}}
[data-baseweb="select"] > div:hover {{
    border-color: rgba(237, 28, 36, 0.5) !important;
}}

/* ── Tier Row Labels — Bolder Comic Feel ── */
.tier-label-block {{
    font-family: 'Bangers', cursive, Impact, sans-serif !important;
    font-size: 36px !important;
    letter-spacing: 2px;
    text-shadow: 2px 2px 0 rgba(0, 0, 0, 0.7);
    border-right: 3px solid rgba(0, 0, 0, 0.5);
}}
.tier-row {{
    border-bottom: 2px solid rgba(0, 0, 0, 0.3);
}}
.home-tier-section {{
    border: 3px solid rgba(255, 255, 255, 0.3);
    border-radius: 4px;
    overflow: hidden;
    box-shadow: 4px 4px 0 rgba(0, 0, 0, 0.5);
}}

/* ── Animations ── */
.stMainBlockContainer {{
    animation: fadeIn 0.4s ease-in;
}}
@keyframes fadeIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{
    width: 8px;
}}
::-webkit-scrollbar-track {{
    background: rgba(0, 0, 0, 0.2);
}}
::-webkit-scrollbar-thumb {{
    background: rgba(237, 28, 36, 0.4);
    border-radius: 4px;
}}
::-webkit-scrollbar-thumb:hover {{
    background: rgba(237, 28, 36, 0.6);
}}

/* ── Mobile-friendly adjustments ── */
@media (max-width: 768px) {{
    .nav-banner {{
        gap: 2px;
        padding: 6px 8px;
    }}
    .nav-link {{
        padding: 4px 8px;
        font-size: 10px;
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
        border-width: 2px;
    }}
    [data-testid="stImage"] img:hover {{
        transform: none;
    }}
    #onboarding-overlay {{
        padding: 14px 12px !important;
    }}
    #onboarding-overlay > div:first-child {{
        font-size: 16px !important;
    }}
    .hero-hover-panel {{ display: none !important; }}
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
        font-size: 9px;
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
    # Also intercept nav-link clicks to use Streamlit's client-side
    # routing (via sidebar links) so session state is preserved.
    _nav_urls = [href for _, href, _ in NAV_PAGES]
    _shortcut_js = "".join(
        f'case "{i+1}": _stNav("{url}"); break;'
        for i, url in enumerate(_nav_urls[:9])
    )
    components.html(
        f"""<script>
(function() {{
    var pd = window.parent.document;
    function _stNav(targetPath) {{
        var ls = pd.querySelectorAll('[data-testid=stSidebarNavLink]');
        for (var i = 0; i < ls.length; i++) {{
            if (new URL(ls[i].href).pathname === targetPath) {{ ls[i].click(); return; }}
        }}
        // Fallback if sidebar link not found
        window.parent.location.href = targetPath;
    }}
    // Intercept clicks on custom nav-banner links
    pd.addEventListener('click', function(e) {{
        var a = e.target.closest && e.target.closest('.nav-link');
        if (!a) return;
        var href = a.getAttribute('href');
        if (!href || href.startsWith('http')) return;
        e.preventDefault();
        e.stopPropagation();
        _stNav(href);
    }}, true);
    // Keyboard shortcuts
    pd.addEventListener('keydown', function(e) {{
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.isContentEditable) return;
        if (e.key === '?') {{
            var el = pd.getElementById('keyboard-help');
            if (el) el.style.display = el.style.display === 'none' ? 'block' : 'none';
            e.preventDefault();
        }}
        switch(e.key) {{ {_shortcut_js} }}
    }});
}})();
</script>""",
        height=0,
    )


def render_page_header(title, subtitle=""):
    """Render a styled page header bar with logo and optional subtitle."""
    sub_html = f'<div class="page-subtitle">{html_escape(subtitle)}</div>' if subtitle else ""

    # Light mode background
    _bg_url_light = "./app/static/bg_v5.jpg"

    # Dark/light mode toggle
    light_mode = st.session_state.get("_light_mode", False)
    mode_icon = "☀️" if not light_mode else "🌙"

    # Build light-mode CSS block (separate var so f-string interpolation works)
    if light_mode:
        _light_css = f"""<style>
/* ── Light-mode overrides — Vintage Comic Page ── */

/* Kill Streamlit's dark body background so the image shows */
html, body {{
    background-color: transparent !important;
}}

/* Main background — colored image for light mode */
.stApp {{
    background: url({_bg_url_light}) no-repeat center center fixed !important;
    background-size: cover !important;
    color: #1a1a1a !important;
}}
.stApp > header, [data-testid="stAppViewContainer"],
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stBottomBlockContainer"],
[data-testid="stAppViewBlockContainer"] {{
    background-color: transparent !important;
    color: #1a1a1a !important;
}}
/* Content area — semi-transparent so background colors show on edges */
[data-testid="stMainBlockContainer"] {{
    background: rgba(245, 240, 228, 0.96) !important;
}}

/* Sidebar — slightly darker aged paper */
[data-testid="stSidebar"], [data-testid="stSidebarContent"] {{
    background-color: #ece7d8 !important;
    color: #1a1a1a !important;
    border-right: 3px solid #222 !important;
}}

/* Body text */
.stApp p, .stApp li, .stApp label, .stApp span, .stApp div,
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] div,
[data-testid="stText"] {{
    color: #1a1a1a !important;
}}

/* Headings — bold black, no shadows */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6,
[data-testid="stMarkdownContainer"] h1,
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3,
[data-testid="stMarkdownContainer"] h4 {{
    color: #111 !important;
    text-shadow: none !important;
}}

/* Links — Marvel red */
.stApp a:not(.nav-active), [data-testid="stMarkdownContainer"] a {{
    color: #c41018 !important;
}}
.stApp a:hover:not(.nav-active), [data-testid="stMarkdownContainer"] a:hover {{
    color: #ed1c24 !important;
}}

/* Nav banner — white paper with red accent */
.nav-banner {{
    background: #fff !important;
    border: 3px solid #222 !important;
    border-bottom: 4px solid #ed1c24 !important;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.15) !important;
}}
.nav-link {{
    color: #333 !important;
    text-transform: none !important;
}}
.nav-link:hover {{
    background: rgba(237,28,36,0.08) !important;
    color: #111 !important;
}}
.nav-active, .nav-active *,
.stApp a.nav-active,
.stApp .nav-active,
a.nav-active {{
    background: #ed1c24 !important;
    color: #fff !important;
    border-color: #c41018 !important;
}}

/* Page header — white with dark text */
.page-header {{
    background: #fff !important;
    border: 3px solid #222 !important;
    border-bottom: 4px solid #ed1c24 !important;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.15) !important;
}}
.page-title {{
    color: #111 !important;
    text-shadow: none !important;
}}
.page-subtitle {{
    color: #555 !important;
    text-shadow: none !important;
}}

/* Comic section banners — keep bold, invert */
.comic-banner {{
    background: linear-gradient(180deg, #222 0%, #111 100%) !important;
    color: #fff !important;
    border: 3px solid #111 !important;
    border-left: 5px solid #ed1c24 !important;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.2) !important;
}}

/* Expanders — clean white cards */
[data-testid="stExpander"] {{
    border: 2px solid #ddd !important;
    background: #fff !important;
    box-shadow: 2px 2px 0 rgba(0,0,0,0.08) !important;
}}
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary span {{
    color: #1a1a1a !important;
}}
[data-testid="stExpander"] [data-testid="stExpanderDetails"] {{
    background: #fff !important;
}}

/* Buttons — white with dark borders (comic panel style) */
.stButton > button, [data-testid="stBaseButton-secondary"] {{
    background: #fff !important;
    color: #1a1a1a !important;
    border: 2px solid #333 !important;
    box-shadow: 2px 2px 0 rgba(0,0,0,0.15) !important;
}}
.stButton > button:hover, [data-testid="stBaseButton-secondary"]:hover {{
    background: #ece7d8 !important;
    border-color: #ed1c24 !important;
    color: #ed1c24 !important;
}}
[data-testid="stBaseButton-primary"] {{
    background: #ed1c24 !important;
    color: white !important;
    border-color: #c41018 !important;
    text-shadow: none !important;
    box-shadow: 2px 2px 0 rgba(0,0,0,0.15) !important;
}}
[data-testid="stBaseButton-primary"]:hover {{
    background: #d41920 !important;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.2) !important;
}}

/* Selectboxes */
[data-testid="stSelectbox"] > div > div,
[data-baseweb="select"] > div {{
    background: #fff !important;
    border: 2px solid #ccc !important;
    color: #1a1a1a !important;
}}
[data-baseweb="select"] span {{
    color: #1a1a1a !important;
}}
[data-baseweb="select"] > div:hover {{
    border-color: #ed1c24 !important;
}}

/* Text inputs */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {{
    background: #fff !important;
    color: #1a1a1a !important;
    border: 2px solid #ccc !important;
}}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {{
    border-color: #ed1c24 !important;
}}

/* Sliders */
[data-testid="stSlider"] label,
[data-testid="stSlider"] div[data-testid="stTickBarMin"],
[data-testid="stSlider"] div[data-testid="stTickBarMax"] {{
    color: #1a1a1a !important;
}}
[data-testid="stSlider"] [data-testid="stThumbValue"] {{
    color: #1a1a1a !important;
}}

/* Tabs */
[data-testid="stTabs"] button {{
    color: #555 !important;
}}
[data-testid="stTabs"] button[aria-selected="true"] {{
    color: #ed1c24 !important;
    border-bottom-color: #ed1c24 !important;
}}

/* Checkboxes & toggles */
[data-testid="stCheckbox"] label span {{
    color: #1a1a1a !important;
}}

/* Radio buttons */
[data-testid="stRadio"] label {{
    color: #1a1a1a !important;
}}

/* Card images — solid dark borders on light background */
[data-testid="stImage"] img {{
    border-color: #222 !important;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.2) !important;
}}
[data-testid="stImage"] img:hover {{
    border-color: #ed1c24 !important;
    box-shadow: 4px 4px 0 rgba(0,0,0,0.25) !important;
}}

/* Metrics */
[data-testid="stMetric"] {{
    background: #fff !important;
    border: 2px solid #ddd !important;
    box-shadow: 2px 2px 0 rgba(0,0,0,0.08) !important;
}}
[data-testid="stMetricValue"] {{
    color: #111 !important;
}}
[data-testid="stMetricLabel"] {{
    color: #555 !important;
}}

/* Horizontal dividers — solid red like dark mode */
hr {{
    border-color: #ed1c24 !important;
    box-shadow: 1px 1px 0 rgba(0,0,0,0.1) !important;
}}

/* Alerts */
[data-testid="stAlert"] {{
    background: #fff !important;
    color: #1a1a1a !important;
    border: 2px solid #ddd !important;
}}

/* Inline code */
code {{
    background: #ece7d8 !important;
    color: #111 !important;
    border: 1px solid #ddd !important;
}}

/* Scrollbar */
::-webkit-scrollbar-track {{
    background: #ece7d8 !important;
}}
::-webkit-scrollbar-thumb {{
    background: #bbb !important;
    border: 1px solid #999 !important;
}}
::-webkit-scrollbar-thumb:hover {{
    background: #999 !important;
}}

/* Deck list page */
.card-row:hover {{
    background: rgba(237,28,36,0.04) !important;
}}
.card-qty {{ color: #1a1a1a !important; }}
.stApp .card-name, .stApp .card-name a {{ color: #1a1a1a !important; }}
.stApp .card-name a:hover {{ color: #ed1c24 !important; }}
.card-cost {{ color: #666 !important; }}
.deck-title {{ color: #111 !important; }}
.deck-stat {{
    background: #ece7d8 !important;
    color: #555 !important;
    border: 1px solid #ddd !important;
}}
.deck-stat strong {{ color: #111 !important; }}
.deck-summary-note {{ color: #555 !important; }}
.stApp a.mcdb-link, .stApp .mcdb-link {{ color: white !important; }}

/* Floating hero cards */
.card-float img {{
    border-color: #222 !important;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.15) !important;
}}
.card-float:hover img {{
    border-color: #ed1c24 !important;
    box-shadow: 4px 4px 0 rgba(0,0,0,0.2) !important;
}}

/* Keyboard help overlay */
#keyboard-help {{
    background: rgba(245,240,225,0.97) !important;
    border: 3px solid #222 !important;
    color: #1a1a1a !important;
    box-shadow: 4px 4px 0 rgba(0,0,0,0.2) !important;
}}

/* Tier list section — bold borders */
.home-tier-section {{
    border: 3px solid #222 !important;
    box-shadow: 3px 3px 0 rgba(0,0,0,0.15) !important;
}}
.tier-row {{
    border-bottom: 2px solid rgba(0,0,0,0.15) !important;
}}
.home-tier-section .tier-row .tier-label-block,
.tier-label-block {{
    border-right: 3px solid rgba(0,0,0,0.3) !important;
    color: #fff !important;
    text-shadow: 2px 2px 0 #000, -1px -1px 0 rgba(0,0,0,0.3) !important;
}}
/* Hero name hover overlay */
.hero-card .hero-name-overlay,
.hero-name-overlay {{
    color: #fff !important;
}}

/* Footer — dark on light */
.site-footer {{
    background: #fff !important;
    color: #555 !important;
    border: 2px solid #ddd !important;
    box-shadow: 2px 2px 0 rgba(0,0,0,0.08) !important;
}}
.site-footer a {{
    color: #c41018 !important;
}}

/* Multiselect tags */
[data-baseweb="tag"] {{
    background: #ed1c24 !important;
    color: #fff !important;
}}

/* Buttons — prevent text wrapping */
.stButton > button {{
    white-space: nowrap !important;
}}
</style>"""
    else:
        _light_css = ""

    st.markdown(
        f"""<style>
.page-header {{
    display: flex;
    justify-content: center;
    align-items: center;
    background: #0d0d1a;
    padding: 14px 20px;
    border: 3px solid #222;
    border-bottom: 4px solid #ed1c24;
    border-radius: 0px;
    box-shadow: 3px 3px 0 rgba(0, 0, 0, 0.6);
    margin-bottom: 16px;
    text-align: center;
    position: relative;
}}
.page-header .logo {{
    height: 50px;
    margin-right: 16px;
    filter: drop-shadow(2px 2px 0 rgba(0, 0, 0, 0.6));
}}
.page-title {{
    font-family: 'Bangers', cursive, Impact, sans-serif;
    font-size: 32px;
    font-weight: 900;
    color: #ffffff;
    text-shadow: 2px 2px 0 #000, -1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000;
    letter-spacing: 2px;
    text-transform: uppercase;
}}
.page-subtitle {{
    font-size: 13px;
    color: #f7c948;
    margin-top: 2px;
    letter-spacing: 1px;
    font-weight: 600;
    text-transform: uppercase;
    text-shadow: 1px 1px 0 #000;
}}
.social-icons {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-left: auto;
    padding-left: 16px;
}}
.social-icons a {{
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
}}
.social-icons a:hover {{
    opacity: 0.8;
    transform: scale(1.1);
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
{"" if not light_mode else _light_css}
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
        '<span style="font-family:Bangers,cursive;font-size:14px;letter-spacing:1px;color:#f7c948;">CREATED BY</span> '
        '<a href="https://www.youtube.com/channel/UCpV2UWmBTAeIKUso1LkeU2A" target="_blank" style="color:#ed1c24;font-weight:bold;">DARING LIME</a>'
        ' &nbsp;·&nbsp; '
        '<a href="https://discord.gg/ReF5jDSHqV" target="_blank" style="color:#ed1c24;font-weight:bold;">DISCORD</a>'
        ' &nbsp;·&nbsp; '
        '<span style="color:#888;">Card data by</span> <a href="https://marvelcdb.com" target="_blank" style="color:#ed1c24;">MarvelCDB</a>'
    )
    if show_card_credits:
        credits += (
            ' &nbsp;·&nbsp; '
            '<span style="color:#888;">Card images from the Cerebro Discord bot by UnicornSnuggler</span>'
        )
    st.markdown(
        f'<div style="text-align:center; font-size:12px; padding:8px 0 16px 0; '
        f'border-top: 2px solid rgba(237,28,36,0.3);">{credits}</div>',
        unsafe_allow_html=True,
    )
