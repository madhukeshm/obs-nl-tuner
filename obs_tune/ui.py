"""Visual identity for the Streamlit app: theme CSS, mascot, hero, footer.

Streamlit strips ``class``/``id`` attributes from HTML passed to
``st.markdown``, so the two rich visual pieces (hero banner, empty-state mascot)
are rendered as self-contained documents via ``st.components.v1.html`` — an
isolated iframe where classes, keyframe animations, fonts and inline SVG all work
as written. Small bits (connection pill, footer) use inline styles, which
``st.markdown`` does preserve. The global ``theme_css`` styles Streamlit's own
widgets (buttons, inputs, sidebar, chat, expanders).

The look is a cheerful "studio" theme: a dark hero with a cartoon microphone
mascot over a soft lavender workspace, rounded sticker-style controls, and a
friendly rounded display face (Fredoka). Deliberately a single light theme.
"""

from __future__ import annotations

__version_default__ = "1.0.0"

AUTHOR = "Madhukesh Manevarthe"
YEAR = "2026"
REPO_URL = "https://github.com/madhukeshm/obs-nl-tuner"

# Clickable starter prompts shown in the empty state: (emoji, prompt text).
EXAMPLES: list[tuple[str, str]] = [
    ("🎙️", "Clean up my mic and remove background noise"),
    ("🖥️", "Set my output to 1080p at 60 fps"),
    ("🎬", "Make a 'Starting Soon' scene and switch to it"),
    ("🔉", "Lower the desktop audio by 6 dB"),
]

_FONTS = (
    '<link rel="preconnect" href="https://fonts.googleapis.com">'
    '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
    '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?'
    'family=Fredoka:wght@500;600;700&family=Hanken+Grotesk:wght@400;500;600;700&'
    'family=JetBrains+Mono:wght@400;500;700&display=swap">'
)


def _mic_svg(width: int, animate: bool = True) -> str:
    """Cartoon microphone mascot as inline SVG (used inside component iframes)."""
    bob = "animation:bob 4.6s ease-in-out infinite;transform-origin:50% 60%;" if animate else ""
    wig = 'style="animation:wiggle 3.2s ease-in-out infinite;transform-origin:430px 150px"' if animate else ""
    return f"""
<svg viewBox="0 0 560 520" xmlns="http://www.w3.org/2000/svg"
     style="width:{width}px;height:auto;overflow:visible;{bob}"
     role="img" aria-label="A friendly cartoon microphone with an AI sparkle wand.">
  <defs>
    <linearGradient id="mic" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#9d90ff"/><stop offset="1" stop-color="#6d5cf2"/></linearGradient>
    <linearGradient id="micdark" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7c6df2"/><stop offset="1" stop-color="#5b4ae0"/></linearGradient>
    <radialGradient id="spot" cx="50%" cy="45%" r="55%"><stop offset="0" stop-color="#ffffff" stop-opacity=".14"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/></radialGradient>
    <linearGradient id="wand" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#ffd97a"/><stop offset="1" stop-color="#f5b64b"/></linearGradient>
  </defs>
  <ellipse cx="280" cy="270" rx="250" ry="205" fill="url(#spot)"/>
  <ellipse cx="280" cy="452" rx="150" ry="30" fill="#000" opacity=".22"/>
  <g stroke="#ff8a5c" stroke-width="7" stroke-linecap="round" stroke-linejoin="round" fill="none">
    <path d="M70 300 l16 -30 l16 34 l16 -40 l16 42 l16 -26" opacity=".9"/>
    <path d="M96 356 l14 -22 l14 24 l14 -26" opacity=".5"/>
  </g>
  <circle cx="86" cy="250" r="8" fill="#ff8a5c" opacity=".7"/>
  <path d="M392 296 q22 -46 44 0 q22 46 44 0 q22 -46 44 0" stroke="#34d3a6" stroke-width="8" stroke-linecap="round" fill="none"/>
  <path d="M405 340 q18 -30 36 0 q18 30 36 0" stroke="#34d3a6" stroke-width="6" stroke-linecap="round" fill="none" opacity=".55"/>
  <g stroke="#efeaff" stroke-width="6" stroke-linejoin="round">
    <ellipse cx="280" cy="452" rx="92" ry="22" fill="#3a3168"/>
    <rect x="266" y="360" width="28" height="80" rx="10" fill="#4a3f86"/>
    <rect x="205" y="150" width="150" height="228" rx="72" fill="url(#mic)"/>
    <rect x="224" y="172" width="112" height="96" rx="46" fill="url(#micdark)" stroke="none"/>
  </g>
  <g stroke="#efeaff" stroke-width="4.5" stroke-linecap="round" opacity=".55">
    <line x1="238" y1="196" x2="322" y2="196"/><line x1="234" y1="216" x2="326" y2="216"/><line x1="238" y1="236" x2="322" y2="236"/>
  </g>
  <g>
    <ellipse cx="256" cy="312" rx="15" ry="17" fill="#fff"/><ellipse cx="304" cy="312" rx="15" ry="17" fill="#fff"/>
    <circle cx="259" cy="315" r="7" fill="#241a4d"/><circle cx="307" cy="315" r="7" fill="#241a4d"/>
    <circle cx="256.5" cy="311" r="2.4" fill="#fff"/><circle cx="304.5" cy="311" r="2.4" fill="#fff"/>
    <ellipse cx="234" cy="336" rx="12" ry="7" fill="#ff9ec2" opacity=".85"/><ellipse cx="326" cy="336" rx="12" ry="7" fill="#ff9ec2" opacity=".85"/>
    <path d="M262 340 q18 22 36 0" stroke="#241a4d" stroke-width="6" stroke-linecap="round" fill="none"/>
  </g>
  <g {wig} stroke-linejoin="round" stroke-linecap="round">
    <line x1="470" y1="120" x2="410" y2="176" stroke="url(#wand)" stroke-width="12"/>
    <path d="M400 150 l10 22 l24 6 l-18 17 l4 25 l-22 -12 l-22 12 l4 -25 l-18 -17 l24 -6 z" fill="url(#wand)" stroke="#efeaff" stroke-width="5"/>
  </g>
  <g fill="#fff">
    <path d="M360 210 l4 12 l12 4 l-12 4 l-4 12 l-4 -12 l-12 -4 l12 -4 z" opacity=".95"/>
    <path d="M338 268 l3 8 l8 3 l-8 3 l-3 8 l-3 -8 l-8 -3 l8 -3 z" opacity=".8"/>
  </g>
  <path d="M150 210 l3 9 l9 3 l-9 3 l-3 9 l-3 -9 l-9 -3 l9 -3 z" fill="#9d90ff" opacity=".9"/>
</svg>
"""


# Shared CSS injected inside every component iframe (fonts + animations + resets).
_IFRAME_HEAD = f"""
{_FONTS}
<style>
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; background: transparent; font-family: "Hanken Grotesk", system-ui, sans-serif; }}
  @keyframes bob {{ 0%,100%{{ transform: translateY(0) }} 50%{{ transform: translateY(-7px) }} }}
  @keyframes wiggle {{ 0%,100%{{ transform: rotate(-6deg) }} 50%{{ transform: rotate(9deg) }} }}
  @media (prefers-reduced-motion: reduce) {{ [style*="animation"] {{ animation: none !important; }} }}
</style>
"""


def theme_css() -> str:
    """Global styles for Streamlit's own widgets. Injected with st.html (not markdown)
    so the CSS is never re-interpreted as text. Fonts load via @import."""
    return """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Fredoka:wght@500;600;700&family=Hanken+Grotesk:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
  :root {
    --bg: #f7f4ff; --panel: #ffffff; --panel-2: #f1ecff;
    --ink: #201a33; --muted: #756e93;
    --accent: #5b4ae0; --accent-2: #7c6df2; --accent-soft: #ece7fd;
    --hair: #e6e0f7; --radius: 18px;
    --shadow: 0 10px 26px rgba(46,32,110,.10);
  }
  .stApp { background:
      radial-gradient(760px 380px at 100% -6%, #efe9ff 0%, transparent 60%),
      radial-gradient(680px 360px at -6% 8%, #eafaf4 0%, transparent 55%),
      var(--bg); }
  html, body, [data-testid="stAppViewContainer"], .stMarkdown, p, li, label, input, textarea, button {
    font-family: "Hanken Grotesk", system-ui, sans-serif;
  }
  h1, h2, h3, h4 { font-family: "Fredoka", "Hanken Grotesk", sans-serif !important; letter-spacing: -.01em; color: var(--ink); }
  .block-container { padding-top: 1.2rem; max-width: 940px; }

  #MainMenu, [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
  [data-testid="stHeader"] { background: transparent; height: 0; }
  footer { visibility: hidden; }

  /* sidebar */
  section[data-testid="stSidebar"] { background: linear-gradient(180deg, #fbfaff 0%, #f3eeff 100%); border-right: 1px solid var(--hair); }
  section[data-testid="stSidebar"] h3 { font-size: 15px !important; color: var(--accent) !important; margin-bottom: .3rem; }

  /* inputs */
  .stTextInput input, .stNumberInput input, [data-baseweb="input"] input {
    border-radius: 12px !important; border: 1.5px solid var(--hair) !important; background: var(--panel) !important; color: var(--ink) !important;
  }
  .stTextInput input:focus, .stNumberInput input:focus { border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important; }
  [data-baseweb="select"] > div { border-radius: 12px !important; border: 1.5px solid var(--hair) !important; }

  /* buttons — chunky sticker style */
  .stButton > button { border-radius: 999px !important; font-weight: 700 !important; border: none !important; transition: transform .08s ease, box-shadow .15s ease; }
  .stButton > button[kind="primary"] { background: linear-gradient(180deg, var(--accent-2), var(--accent)) !important; color: #fff !important; box-shadow: 0 6px 0 #4536b8, var(--shadow) !important; }
  .stButton > button[kind="primary"]:active { transform: translateY(3px); box-shadow: 0 3px 0 #4536b8 !important; }
  .stButton > button[kind="secondary"] { background: var(--panel) !important; color: var(--ink) !important; border: 1.5px solid var(--hair) !important; box-shadow: var(--shadow) !important; font-weight: 600 !important; }
  .stButton > button:hover { transform: translateY(-1px); }

  /* chat */
  [data-testid="stChatMessage"] { background: var(--panel); border: 1.5px solid var(--hair); border-radius: var(--radius); box-shadow: var(--shadow); padding: 12px 16px; margin-bottom: 4px; }
  [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { background: var(--accent-soft); border-color: #d9d0fb; }
  [data-testid="stChatInput"] { border-radius: 16px !important; border: 1.5px solid var(--hair) !important; background: var(--panel) !important; box-shadow: var(--shadow); }
  [data-testid="stChatInput"]:focus-within { border-color: var(--accent) !important; box-shadow: 0 0 0 3px var(--accent-soft) !important; }
  [data-testid="stChatInput"] textarea { font-size: 16px; }

  /* expanders (tool step details) */
  [data-testid="stExpander"] { border: 1.5px solid var(--hair) !important; border-radius: 14px !important; background: var(--panel-2); }
  [data-testid="stExpander"] summary { font-family: "JetBrains Mono", monospace; font-size: 13px; }
  [data-testid="stStatus"] { border-radius: 14px !important; border: 1.5px solid var(--hair) !important; }
</style>
"""


def hero_component(version: str) -> str:
    """Self-contained hero banner for st.components.v1.html (isolated iframe)."""
    return f"""{_IFRAME_HEAD}
<div style="position:relative;overflow:hidden;border-radius:22px;padding:22px 26px;display:flex;
     align-items:center;gap:20px;box-shadow:0 20px 44px rgba(46,32,110,.18);border:1px solid rgba(255,255,255,.08);
     background:radial-gradient(520px 300px at 88% -30%, rgba(124,109,242,.42), transparent 60%),
     radial-gradient(420px 260px at 6% 130%, rgba(16,163,127,.20), transparent 60%),
     linear-gradient(150deg,#14152b 0%,#1c2140 60%,#121229 100%);">
  <div style="position:relative;z-index:1;flex:1;min-width:0;">
    <div style="font-family:'JetBrains Mono',monospace;font-size:11.5px;letter-spacing:.18em;text-transform:uppercase;color:#a9b4dc;display:flex;align-items:center;gap:8px;">
      <span style="width:8px;height:8px;border-radius:50%;background:#9d90ff;box-shadow:0 0 12px #9d90ff;"></span>OBS · obs-websocket v5</div>
    <div style="font-family:'Fredoka',sans-serif;font-weight:700;font-size:40px;line-height:1.02;margin:8px 0 0;color:#fff;">
      OBS <span style="color:#b3a8ff;">Tuner</span></div>
    <div style="margin:9px 0 0;color:#c4ccea;font-size:16px;max-width:42ch;">Just say what you want — <b style="color:#fff;">Claude</b> or <b style="color:#fff;">ChatGPT</b> tunes OBS for you.</div>
    <div style="margin-top:13px;display:flex;gap:8px;flex-wrap:wrap;font-family:'JetBrains Mono',monospace;font-size:12px;">
      <span style="color:#d7dcf3;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);padding:4px 11px;border-radius:999px;">v{version}</span>
      <span style="color:#d7dcf3;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);padding:4px 11px;border-radius:999px;"><span style="color:#d97757;">●</span> Claude</span>
      <span style="color:#d7dcf3;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.14);padding:4px 11px;border-radius:999px;"><span style="color:#38c9a0;">●</span> ChatGPT</span>
    </div>
  </div>
  <div style="position:relative;z-index:1;flex:0 0 150px;display:flex;justify-content:center;">{_mic_svg(150)}</div>
</div>
"""


def empty_component() -> str:
    """Self-contained empty-state (mascot + welcome) for st.components.v1.html."""
    return f"""{_IFRAME_HEAD}
<div style="text-align:center;padding:10px 0 0;">
  <div style="display:flex;justify-content:center;">{_mic_svg(124)}</div>
  <div style="font-family:'Fredoka',sans-serif;font-weight:600;font-size:23px;color:#201a33;margin:6px 0 4px;">Your studio assistant is ready 🎙️</div>
  <div style="color:#756e93;font-size:15.5px;max-width:46ch;margin:0 auto;">Connect to OBS, add your API key, then tell me what to change — or tap a starter below.</div>
</div>
"""


def footer_html(version: str) -> str:
    """Copyright footer using inline styles (st.markdown preserves inline style)."""
    s = "color:#c9c2e6;"
    return (
        '<div style="margin:30px 0 6px;padding-top:18px;border-top:1px solid #e6e0f7;'
        'display:flex;flex-wrap:wrap;gap:6px 12px;align-items:center;justify-content:center;'
        'font-size:13px;color:#756e93;">'
        f'<span>© {YEAR} {AUTHOR}</span><span style="{s}">·</span>'
        '<span>MIT License</span>'
        f'<span style="{s}">·</span><span style="font-family:\'JetBrains Mono\',monospace;">v{version}</span>'
        f'<span style="{s}">·</span>'
        f'<a href="{REPO_URL}" target="_blank" rel="noopener" style="color:#5b4ae0;text-decoration:none;font-weight:600;">GitHub ↗</a>'
        "</div>"
    )


def conn_pill_html(connected: bool, version_text: str = "") -> str:
    """Connection status pill (inline styles)."""
    if connected:
        label = f"Connected{(' — ' + version_text) if version_text else ''}"
        return (
            '<span style="display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:700;'
            'padding:6px 12px;border-radius:999px;color:#0b7a5e;background:#daf6ec;border:1px solid #a9e6d3;">'
            '<span style="width:8px;height:8px;border-radius:50%;background:#12b98c;box-shadow:0 0 8px #12b98c;"></span>'
            f"{label}</span>"
        )
    return (
        '<span style="display:inline-flex;align-items:center;gap:8px;font-size:13px;font-weight:700;'
        'padding:6px 12px;border-radius:999px;color:#8a4b16;background:#fdeede;border:1px solid #f2d3a8;">'
        '<span style="width:8px;height:8px;border-radius:50%;background:#e08a3c;"></span>Not connected</span>'
    )
