"""Streamlit front end: tune OBS with natural language via Claude or ChatGPT.

Run with:  uv run streamlit run app.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

from obs_tune import __version__
from obs_tune.agents import CLAUDE_MODELS, OPENAI_MODELS, run_agent
from obs_tune.obs_actions import OBSController, OBSError
from obs_tune import ui

load_dotenv()

st.set_page_config(page_title="OBS Tuner", page_icon="🎛️", layout="centered")
st.html(ui.theme_css())

OBS_WS_CONFIG = Path.home() / "Library/Application Support/obs-studio/plugin_config/obs-websocket/config.json"


def _default_obs_password() -> str:
    """Best-effort prefill of the local obs-websocket password (user's own machine)."""
    try:
        return json.loads(OBS_WS_CONFIG.read_text()).get("server_password", "") or ""
    except Exception:
        return ""


# --- session state --------------------------------------------------------
ss = st.session_state
ss.setdefault("controller", None)
ss.setdefault("obs_info", None)
ss.setdefault("transcript", [])          # UI-facing list of {role, text, steps}
ss.setdefault("history_claude", [])       # Anthropic-native messages
ss.setdefault("history_openai", [])       # OpenAI-native messages
ss.setdefault("pending_prompt", None)     # set by starter chips


def _connect(host: str, port: int, password: str) -> None:
    if ss.controller is not None:
        ss.controller.close()
    ctrl = OBSController(host=host, port=port, password=password)
    ss.obs_info = ctrl.connect()  # raises OBSError on failure
    ss.controller = ctrl


# --- sidebar --------------------------------------------------------------
with st.sidebar:
    st.markdown("### OBS connection")
    host = st.text_input("Host", value="localhost")
    port = st.number_input("Port", value=4455, step=1)
    password = st.text_input("Password", value=_default_obs_password(), type="password")
    if st.button("Connect", use_container_width=True, type="primary"):
        try:
            _connect(host, int(port), password)
            st.toast(f"Connected to OBS {ss.obs_info.get('obsVersion')}", icon="✅")
        except OBSError as e:
            ss.controller = None
            st.error(str(e))

    connected = ss.controller is not None and ss.obs_info is not None
    vtext = f"OBS {ss.obs_info.get('obsVersion')}" if connected else ""
    st.markdown(ui.conn_pill_html(connected, vtext), unsafe_allow_html=True)

    st.markdown("### Model")
    provider_label = st.radio("Provider", ["Claude (Anthropic)", "ChatGPT (OpenAI)"], index=0)
    provider = "claude" if provider_label.startswith("Claude") else "openai"

    if provider == "claude":
        model = st.selectbox("Model", CLAUDE_MODELS, index=0)
        api_key = st.text_input(
            "Anthropic API key", value=os.getenv("ANTHROPIC_API_KEY", ""), type="password"
        )
    else:
        model = st.selectbox("Model", OPENAI_MODELS, index=0)
        api_key = st.text_input(
            "OpenAI API key", value=os.getenv("OPENAI_API_KEY", ""), type="password"
        )

    st.markdown("### Options")
    allow_streaming = st.toggle(
        "Allow streaming / recording controls",
        value=False,
        help="When on, the assistant may start/stop the stream or recording, change the "
        "stream service/key, and change encoder/bitrate. Off by default for safety.",
    )
    if st.button("Clear conversation", use_container_width=True):
        ss.transcript = []
        ss.history_claude = []
        ss.history_openai = []
        st.rerun()


def _render_steps(steps: list[dict]) -> None:
    for s in steps:
        icon = "✕" if s["is_error"] else "›"
        with st.expander(f"{icon}  {s['tool']}", expanded=False):
            st.markdown("**Arguments**")
            st.json(s["args"] or {})
            st.markdown("**Result**")
            try:
                st.json(json.loads(s["result"]))
            except (json.JSONDecodeError, TypeError):
                st.code(s["result"])


# --- full-bleed masthead --------------------------------------------------
components.html(ui.header_component(__version__), height=150)


# --- padded body ----------------------------------------------------------
with st.container(key="bodywrap"):
    # empty state + starter chips
    if not ss.transcript:
        components.html(ui.empty_component(), height=196)
        st.markdown(
            '<div style="font-family:\'JetBrains Mono\',monospace;font-size:11px;letter-spacing:.16em;'
            'text-transform:uppercase;color:#6B665B;text-align:center;margin:4px 0 8px;">Starting points</div>',
            unsafe_allow_html=True,
        )
        cols = st.columns(2)
        for i, text in enumerate(ui.EXAMPLES):
            if cols[i % 2].button(text, key=f"ex_{i}", use_container_width=True):
                ss.pending_prompt = text
                st.rerun()

    # replay transcript
    for turn in ss.transcript:
        with st.chat_message(turn["role"]):
            if turn.get("steps"):
                _render_steps(turn["steps"])
            st.markdown(turn["text"])

    # input (inline, so the footer sits below it)
    typed = st.chat_input("Describe what to change in OBS…")
    prompt = typed or ss.pop("pending_prompt", None)

    if prompt:
        if ss.controller is None:
            st.toast("Connect to OBS first (sidebar).", icon="🔌")
            st.stop()
        if not api_key:
            st.toast(f"Add your {'Anthropic' if provider == 'claude' else 'OpenAI'} API key in the sidebar.", icon="🔑")
            st.stop()

        ss.transcript.append({"role": "user", "text": prompt, "steps": []})
        with st.chat_message("user"):
            st.markdown(prompt)

        history_key = "history_claude" if provider == "claude" else "history_openai"
        with st.chat_message("assistant"):
            status = st.status("Working with OBS…", expanded=True)

            def on_step(step):
                icon = "✕" if step.is_error else "✓"
                status.write(f"{icon} `{step.tool}`")

            try:
                result = run_agent(
                    provider=provider,
                    api_key=api_key,
                    model=model,
                    user_message=prompt,
                    controller=ss.controller,
                    history=ss[history_key],
                    allow_streaming=allow_streaming,
                    on_step=on_step,
                )
                ss[history_key] = result.history
                status.update(label=f"Done — {len(result.steps)} action(s)", state="complete", expanded=False)
                steps_payload = [
                    {"tool": s.tool, "args": s.args, "result": s.result, "is_error": s.is_error}
                    for s in result.steps
                ]
                if steps_payload:
                    _render_steps(steps_payload)
                st.markdown(result.text)
                ss.transcript.append({"role": "assistant", "text": result.text, "steps": steps_payload})
            except Exception as e:
                status.update(label="Failed", state="error")
                msg = f"**Error:** {e}"
                st.error(msg)
                ss.transcript.append({"role": "assistant", "text": msg, "steps": []})
        st.rerun()


# --- full-bleed footer ----------------------------------------------------
components.html(ui.footer_component(__version__), height=76)
