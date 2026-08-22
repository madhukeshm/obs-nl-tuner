"""Streamlit front end: tune OBS with natural language via Claude or ChatGPT.

Run with:  uv run streamlit run app.py
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from obs_tune.agents import CLAUDE_MODELS, OPENAI_MODELS, run_agent
from obs_tune.obs_actions import OBSController, OBSError

load_dotenv()

st.set_page_config(page_title="OBS Natural-Language Tuner", page_icon="🎛️", layout="centered")

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


def _connect(host: str, port: int, password: str) -> None:
    if ss.controller is not None:
        ss.controller.close()
    ctrl = OBSController(host=host, port=port, password=password)
    ss.obs_info = ctrl.connect()  # raises OBSError on failure
    ss.controller = ctrl


# --- sidebar --------------------------------------------------------------
with st.sidebar:
    st.header("🔌 OBS connection")
    host = st.text_input("Host", value="localhost")
    port = st.number_input("Port", value=4455, step=1)
    password = st.text_input("Password", value=_default_obs_password(), type="password")
    if st.button("Connect", use_container_width=True):
        try:
            _connect(host, int(port), password)
            st.success(f"Connected — OBS {ss.obs_info.get('obsVersion')}")
        except OBSError as e:
            ss.controller = None
            st.error(str(e))

    if ss.controller is not None and ss.obs_info:
        st.caption(f"● Connected to OBS {ss.obs_info.get('obsVersion')}")
    else:
        st.caption("○ Not connected")

    st.divider()
    st.header("🤖 Model")
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

    st.divider()
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


# --- main -----------------------------------------------------------------
st.title("🎛️ OBS Natural-Language Tuner")
st.caption("Describe what you want; Claude or ChatGPT configures OBS for you over obs-websocket.")

if ss.controller is None:
    st.info("Connect to OBS in the sidebar to begin.")
    st.markdown(
        "**Try things like:**\n"
        "- *Clean up my mic — remove background noise*\n"
        "- *Set my output to 1080p at 60fps*\n"
        "- *Make a scene called 'Starting Soon' and switch to it*\n"
        "- *Lower the desktop audio by 6 dB*"
    )


def _render_steps(steps: list[dict]) -> None:
    for s in steps:
        icon = "❌" if s["is_error"] else "🔧"
        with st.expander(f"{icon} {s['tool']}", expanded=False):
            st.markdown("**Arguments**")
            st.json(s["args"] or {})
            st.markdown("**Result**")
            try:
                st.json(json.loads(s["result"]))
            except (json.JSONDecodeError, TypeError):
                st.code(s["result"])


# Replay transcript
for turn in ss.transcript:
    with st.chat_message(turn["role"]):
        if turn.get("steps"):
            _render_steps(turn["steps"])
        st.markdown(turn["text"])


prompt = st.chat_input("Tell me what to change in OBS…")
if prompt:
    if ss.controller is None:
        st.error("Connect to OBS first (sidebar).")
        st.stop()
    if not api_key:
        st.error(f"Enter your {'Anthropic' if provider == 'claude' else 'OpenAI'} API key in the sidebar.")
        st.stop()

    ss.transcript.append({"role": "user", "text": prompt, "steps": []})
    with st.chat_message("user"):
        st.markdown(prompt)

    history_key = "history_claude" if provider == "claude" else "history_openai"
    with st.chat_message("assistant"):
        status = st.status("Working with OBS…", expanded=True)

        def on_step(step):
            icon = "❌" if step.is_error else "✅"
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
