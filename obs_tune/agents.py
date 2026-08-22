"""Unified natural-language -> OBS agent, backed by Claude or ChatGPT.

Both providers run a manual agentic loop (rather than a provider SDK's tool
runner) so the two paths stay symmetric, avoid a beta dependency, and can emit a
uniform per-step log the UI can render.

The Claude path uses the Anthropic SDK; the ChatGPT path uses the OpenAI SDK.
The two are never mixed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable

from .obs_actions import OBSController
from .prompts import SYSTEM_PROMPT
from .tools import execute_tool, to_anthropic_tools, to_openai_tools, visible_tools

# Model choices surfaced in the UI (first entry is the default).
CLAUDE_MODELS = ["claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"]
OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4.1"]

MAX_ITERS = 12  # safety cap on tool-call rounds per user message


@dataclass
class Step:
    """One tool invocation and its outcome, for display."""

    tool: str
    args: dict[str, Any]
    result: str
    is_error: bool = False


@dataclass
class AgentResult:
    text: str
    steps: list[Step] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)


StepCallback = Callable[[Step], None]


def run_agent(
    provider: str,
    api_key: str,
    model: str,
    user_message: str,
    controller: OBSController,
    history: list[dict[str, Any]] | None = None,
    allow_streaming: bool = False,
    on_step: StepCallback | None = None,
) -> AgentResult:
    """Route to the correct provider. `history` is that provider's native message list."""
    tools = visible_tools(allow_streaming=allow_streaming)
    if provider == "claude":
        return _run_claude(api_key, model, user_message, controller, tools, history or [], on_step)
    if provider == "openai":
        return _run_openai(api_key, model, user_message, controller, tools, history or [], on_step)
    raise ValueError(f"Unknown provider: {provider}")


# --- Claude (Anthropic SDK) ----------------------------------------------
def _run_claude(api_key, model, user_message, controller, tools, history, on_step) -> AgentResult:
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)
    wire_tools = to_anthropic_tools(tools)
    messages = list(history)
    messages.append({"role": "user", "content": user_message})
    steps: list[Step] = []

    for _ in range(MAX_ITERS):
        resp = client.messages.create(
            model=model,
            max_tokens=16000,
            system=SYSTEM_PROMPT,
            tools=wire_tools,
            messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason == "pause_turn":
            # Server-side pause; resend to continue.
            continue

        tool_uses = [b for b in resp.content if getattr(b, "type", None) == "tool_use"]
        if resp.stop_reason != "tool_use" or not tool_uses:
            text = _anthropic_text(resp.content)
            return AgentResult(text=text, steps=steps, history=messages)

        tool_results = []
        for block in tool_uses:
            args = block.input if isinstance(block.input, dict) else {}
            result_text, is_error = execute_tool(controller, block.name, args)
            step = Step(tool=block.name, args=args, result=result_text, is_error=is_error)
            steps.append(step)
            if on_step:
                on_step(step)
            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": result_text,
                    "is_error": is_error,
                }
            )
        messages.append({"role": "user", "content": tool_results})

    return AgentResult(
        text="Stopped after too many tool-call rounds. Please refine the request.",
        steps=steps,
        history=messages,
    )


def _anthropic_text(content) -> str:
    parts = [b.text for b in content if getattr(b, "type", None) == "text"]
    return "\n".join(p for p in parts if p).strip() or "(no text response)"


# --- ChatGPT (OpenAI SDK) -------------------------------------------------
def _run_openai(api_key, model, user_message, controller, tools, history, on_step) -> AgentResult:
    from openai import OpenAI

    client = OpenAI(api_key=api_key)
    wire_tools = to_openai_tools(tools)

    messages = list(history)
    if not any(m.get("role") == "system" for m in messages):
        messages.insert(0, {"role": "system", "content": SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_message})
    steps: list[Step] = []

    for _ in range(MAX_ITERS):
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=wire_tools,
            tool_choice="auto",
        )
        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []

        # Record the assistant turn (with any tool calls) in wire form.
        assistant_msg: dict[str, Any] = {"role": "assistant", "content": msg.content or ""}
        if tool_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                }
                for tc in tool_calls
            ]
        messages.append(assistant_msg)

        if not tool_calls:
            return AgentResult(text=(msg.content or "(no text response)").strip(), steps=steps, history=messages)

        for tc in tool_calls:
            try:
                args = json.loads(tc.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}
            result_text, is_error = execute_tool(controller, tc.function.name, args)
            step = Step(tool=tc.function.name, args=args, result=result_text, is_error=is_error)
            steps.append(step)
            if on_step:
                on_step(step)
            messages.append(
                {"role": "tool", "tool_call_id": tc.id, "content": result_text}
            )

    return AgentResult(
        text="Stopped after too many tool-call rounds. Please refine the request.",
        steps=steps,
        history=messages,
    )
