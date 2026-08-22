"""Visual identity for the Streamlit app: a restrained, professional theme.

An ivory canvas with warm near-black ink, a single deep-teal accent, and
full-bleed dark banners at the top (masthead) and bottom (footer). Type is
shared with the project's writeup — Fraunces (display), Hanken Grotesk (UI),
JetBrains Mono (labels/technical) — so the app and article read as one brand.

Streamlit strips class/id from ``st.markdown`` HTML and mangles large ``<style>``
blocks, so: the global widget stylesheet is injected with ``st.html``; the two
dark banners render as self-contained ``components.html`` iframes; small inline
pieces (connection pill) use inline styles, which markdown preserves.
"""

from __future__ import annotations

AUTHOR = "Madhukesh Manevarthe"
YEAR = "2026"
REPO_URL = "https://github.com/madhukeshm/obs-nl-tuner"

# Starter prompts shown in the empty state (plain text — no decorative icons).
EXAMPLES: list[str] = [
    "Clean up my mic and remove background noise",
    "Set my output to 1080p at 60 fps",
    "Make a 'Starting Soon' scene and switch to it",
    "Lower the desktop audio by 6 dB",
]

# Palette (single source of truth, mirrored into the iframe CSS below).
IVORY = "#F5F1E7"
IVORY_2 = "#EFEADB"
PAPER = "#FBF8F1"
INK = "#1E1D1A"
INK_2 = "#2A2824"
MUTED = "#6B665B"
LINE = "#E1D9C7"
ACCENT = "#1F6E5B"          # deep teal on ivory
ACCENT_ON_DARK = "#5FBBA1"  # lighter teal on the dark banners
CLAUDE = "#C2603E"
CHATGPT = "#2E9E7C"

_FONTS_IMPORT = (
    "@import url('https://fonts.googleapis.com/css2?"
    "family=Fraunces:opsz,wght@9..144,500;9..144,600&"
    "family=Hanken+Grotesk:wght@400;500;600;700&"
    "family=JetBrains+Mono:wght@400;500&display=swap');"
)

_FONTS_LINK = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Fraunces:opsz,wght@9..144,500;9..144,600&'
    'family=Hanken+Grotesk:wght@400;500;600;700&'
    'family=JetBrains+Mono:wght@400;500&display=swap">'
)


def theme_css() -> str:
    """Global styles for Streamlit's own widgets. Injected via st.html."""
    return f"""
<style>
  {_FONTS_IMPORT}
  :root {{
    --ivory: {IVORY}; --ivory-2: {IVORY_2}; --paper: {PAPER};
    --ink: {INK}; --muted: {MUTED}; --line: {LINE};
    --accent: {ACCENT}; --accent-soft: #E6EFEA;
    --radius: 12px; --shadow: 0 6px 18px rgba(30,29,26,.06);
  }}

  .stApp, [data-testid="stMain"] {{ background: var(--ivory); }}
  html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, li, label, input, textarea, button {{
    font-family: "Hanken Grotesk", system-ui, sans-serif; color: var(--ink);
  }}
  /* full-bleed banners + sticky footer: the main column fills the viewport height,
     banners span its full width, the body re-centers itself, and the last child
     (footer) is pushed to the bottom. */
  .block-container {{ padding: 0 !important; max-width: 100% !important;
    min-height: 100vh; display: flex; flex-direction: column; }}
  .block-container > [data-testid="stVerticalBlock"] {{ flex: 1 1 auto; }}
  .block-container > [data-testid="stVerticalBlock"] > *:last-child {{ margin-top: auto; }}
  .st-key-bodywrap {{ max-width: 980px; width: 100%; margin: 0 auto;
    padding: 16px clamp(20px, 5vw, 40px) 30px; }}

  #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"] {{ display: none !important; }}
  [data-testid="stHeader"] {{ background: transparent; height: 0; }}
  footer {{ visibility: hidden; }}

  /* sidebar — ivory, hairline, mono labels */
  section[data-testid="stSidebar"] {{ background: var(--ivory-2); border-right: 1px solid var(--line); }}
  section[data-testid="stSidebar"] .block-container {{ padding: 1.4rem 1rem !important; }}
  section[data-testid="stSidebar"] h3 {{
    font-family: "JetBrains Mono", monospace !important; font-size: 11.5px !important;
    letter-spacing: .16em; text-transform: uppercase; color: var(--muted) !important;
    font-weight: 500 !important; margin: .4rem 0 .5rem; border-bottom: 1px solid var(--line); padding-bottom: .5rem;
  }}

  /* inputs */
  .stTextInput input, .stNumberInput input, [data-baseweb="input"] input {{
    border-radius: 10px !important; border: 1px solid var(--line) !important;
    background: var(--paper) !important; color: var(--ink) !important;
  }}
  .stTextInput input:focus, .stNumberInput input:focus {{ border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important; }}
  [data-baseweb="select"] > div {{ border-radius: 10px !important; border: 1px solid var(--line) !important; background: var(--paper) !important; }}
  label, .stMarkdown p {{ color: var(--ink); }}

  /* buttons — restrained; primary is solid ink, secondary is paper w/ hairline */
  .stButton > button {{ border-radius: 10px !important; font-weight: 600 !important; transition: all .12s ease; }}
  .stButton > button[kind="primary"], .stButton > button[kind="primary"] * {{ background: var(--ink) !important; color: var(--ivory) !important; border-color: var(--ink) !important; }}
  .stButton > button[kind="primary"] {{ border: 1px solid var(--ink) !important; }}
  .stButton > button[kind="primary"]:hover, .stButton > button[kind="primary"]:hover * {{ background: {INK_2} !important; }}
  .stButton > button[kind="secondary"] {{
    background: var(--paper) !important; color: var(--ink) !important; border: 1px solid var(--line) !important;
    font-weight: 500 !important; text-align: left !important; box-shadow: var(--shadow) !important;
  }}
  .stButton > button[kind="secondary"]:hover {{ border-color: var(--accent) !important; color: var(--accent) !important; }}

  /* toggle accent */
  [data-baseweb="checkbox"] div[aria-checked="true"] {{ background: var(--accent) !important; border-color: var(--accent) !important; }}

  /* chat */
  [data-testid="stChatMessage"] {{
    background: var(--paper); border: 1px solid var(--line); border-radius: var(--radius);
    box-shadow: var(--shadow); padding: 12px 16px; margin-bottom: 6px;
  }}
  [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {{ background: var(--ivory-2); }}
  [data-testid="stChatInput"] {{ border-radius: 12px !important; border: 1px solid var(--line) !important; background: var(--paper) !important; box-shadow: var(--shadow); }}
  [data-testid="stChatInput"]:focus-within {{ border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important; }}
  [data-testid="stChatInput"] textarea {{ font-size: 16px; }}

  /* expanders (tool step details) */
  [data-testid="stExpander"] {{ border: 1px solid var(--line) !important; border-radius: 10px !important; background: var(--ivory-2); }}
  [data-testid="stExpander"] summary {{ font-family: "JetBrains Mono", monospace; font-size: 13px; }}
  [data-testid="stStatus"] {{ border-radius: 10px !important; border: 1px solid var(--line) !important; background: var(--paper) !important; }}

  a {{ color: var(--accent); }}
</style>
"""


# CSS shared inside both banner iframes.
_BANNER_HEAD = f"""
{_FONTS_LINK}
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; height: 100%; background: transparent; font-family: "Hanken Grotesk", system-ui, sans-serif; }}
  .bar {{ background: linear-gradient(180deg, {INK} 0%, {INK_2} 100%); color: {IVORY};
          padding: 0; position: relative; min-height: 100%; display: flex; align-items: center; }}
  .inner {{ max-width: 980px; width: 100%; margin: 0 auto; padding: 0 clamp(20px, 5vw, 40px); }}
  .bar::before {{ content:""; position:absolute; left:0; right:0; top:0; height:3px;
          background: linear-gradient(90deg, {ACCENT_ON_DARK}, transparent 62%); }}
  .eyebrow {{ font-family:"JetBrains Mono",monospace; font-size:11px; letter-spacing:.22em;
          text-transform:uppercase; color:#9a9384; }}
  .wordmark {{ font-family:"Fraunces",Georgia,serif; font-weight:600; color:#f3eddf; letter-spacing:-.01em; }}
  .muted {{ color:#9a9384; }}
  .mono {{ font-family:"JetBrains Mono",monospace; }}
  .dot {{ display:inline-block; width:7px; height:7px; border-radius:50%; vertical-align:middle; margin-right:6px; }}
  a {{ color:{ACCENT_ON_DARK}; text-decoration:none; font-weight:600; }}
</style>
"""


def header_component(version: str) -> str:
    """Full-bleed dark masthead (background bleeds edge-to-edge, content aligned to body)."""
    return f"""{_BANNER_HEAD}
<div class="bar">
  <div class="inner" style="display:flex;align-items:center;justify-content:space-between;gap:20px;
       padding-top:22px;padding-bottom:22px;">
    <div>
      <div class="eyebrow">Studio control · obs-websocket v5</div>
      <div class="wordmark" style="font-size:34px;line-height:1.05;margin-top:5px;">OBS&nbsp;Tuner</div>
      <div class="muted" style="font-size:14.5px;margin-top:4px;">
        Natural-language control for OBS Studio — powered by Claude or ChatGPT.</div>
    </div>
    <div style="text-align:right;flex:0 0 auto;">
      <div class="mono" style="font-size:12px;color:#b8b1a2;">v{version}</div>
      <div class="mono" style="font-size:12.5px;color:#c9c2b3;margin-top:10px;">
        <span class="dot" style="background:{CLAUDE};"></span>Claude<br>
        <span class="dot" style="background:{CHATGPT};"></span>ChatGPT</div>
    </div>
  </div>
</div>
"""


def footer_component(version: str) -> str:
    """Full-bleed dark footer, matching the masthead."""
    return f"""{_BANNER_HEAD}
<div class="bar">
  <div class="inner" style="display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;
       padding-top:20px;padding-bottom:20px;">
    <div>
      <span class="wordmark" style="font-size:16px;">OBS Tuner</span>
      <span class="muted" style="font-size:13px;margin-left:10px;">© {YEAR} {AUTHOR}</span>
    </div>
    <div class="mono" style="font-size:12.5px;color:#b8b1a2;display:flex;gap:14px;align-items:center;flex-wrap:wrap;">
      <span>MIT License</span><span style="color:#4a473f;">·</span>
      <span>v{version}</span><span style="color:#4a473f;">·</span>
      <a href="{REPO_URL}" target="_blank" rel="noopener">GitHub ↗</a>
    </div>
  </div>
</div>
"""


def empty_component() -> str:
    """Professional empty state: a thin monochrome waveform, heading, subtext."""
    bars = ""
    heights = [16, 26, 40, 22, 50, 34, 46, 20, 38, 28, 18, 30, 44, 24]
    for i, h in enumerate(heights):
        x = i * 15
        y = (56 - h) / 2
        col = ACCENT if i in (4, 6, 12) else "#c7bfad"
        bars += f'<rect x="{x}" y="{y:.0f}" width="7" height="{h}" rx="3.5" fill="{col}"/>'
    return f"""{_FONTS_LINK}
<style>html,body{{margin:0;background:transparent;font-family:"Hanken Grotesk",sans-serif;}}</style>
<div style="text-align:center;padding:20px 0 0;">
  <svg width="210" height="56" viewBox="0 0 210 56" aria-hidden="true">{bars}</svg>
  <div style="font-family:'Fraunces',Georgia,serif;font-weight:600;font-size:24px;color:{INK};margin:14px 0 5px;">
    Ready when you are</div>
  <div style="color:{MUTED};font-size:15.5px;max-width:48ch;margin:0 auto;">
    Connect to OBS, add your API key, then describe what you'd like changed — or pick a starting point below.</div>
</div>
"""


def conn_pill_html(connected: bool, version_text: str = "") -> str:
    """Connection status pill (inline styles; markdown preserves these)."""
    if connected:
        label = f"Connected{(' — ' + version_text) if version_text else ''}"
        return (
            '<span style="display:inline-flex;align-items:center;gap:8px;font-size:12.5px;font-weight:600;'
            f'padding:6px 12px;border-radius:999px;color:{ACCENT};background:#E6EFEA;border:1px solid #bcd8ce;">'
            f'<span style="width:7px;height:7px;border-radius:50%;background:{ACCENT};"></span>{label}</span>'
        )
    return (
        '<span style="display:inline-flex;align-items:center;gap:8px;font-size:12.5px;font-weight:600;'
        f'padding:6px 12px;border-radius:999px;color:{MUTED};background:{IVORY};border:1px solid {LINE};">'
        f'<span style="width:7px;height:7px;border-radius:50%;background:#b8b1a2;"></span>Not connected</span>'
    )
