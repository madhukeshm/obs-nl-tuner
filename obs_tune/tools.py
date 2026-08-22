"""Provider-agnostic tool definitions and dispatch for OBS control.

One canonical list of tools (`TOOLS`) is defined here with JSON-Schema
parameters. It is converted to the Anthropic and OpenAI wire formats on demand,
and `execute_tool` routes a tool call to the matching `OBSController` method.

Tools tagged ``"streaming"`` in ``TOOL_TAGS`` are side-effectful / outward-facing
(they can start a public broadcast or rewrite the stream key). The UI can gate
these behind an explicit opt-in by filtering the tool list with
``visible_tools(allow_streaming=...)``.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from .obs_actions import OBSController, OBSError


# --- canonical tool catalogue --------------------------------------------
# Each entry: name, description, JSON-schema `parameters`, and a handler that
# takes (controller, **args) and returns a JSON-serialisable result.

def _obj(properties: dict, required: list[str] | None = None) -> dict:
    return {
        "type": "object",
        "properties": properties,
        "required": required or [],
        "additionalProperties": False,
    }


_STR = {"type": "string"}
_BOOL = {"type": "boolean"}
_NUM = {"type": "number"}
_INT = {"type": "integer"}


# Tools that can start/stop a broadcast or change stream credentials/encoder.
STREAMING_TAG = "streaming"

_CATALOGUE: list[dict[str, Any]] = [
    {
        "name": "get_obs_overview",
        "description": (
            "Snapshot of current OBS state: version, current scene, all scene names, "
            "all audio/video inputs with their kinds, output resolution & fps, and "
            "whether streaming/recording is active. Call this FIRST to learn real "
            "source/scene names before making changes."
        ),
        "parameters": _obj({}),
        "handler": lambda c: c.get_overview(),
    },
    {
        "name": "list_inputs",
        "description": "List all inputs (mic, desktop audio, camera, capture sources) with their input kinds.",
        "parameters": _obj({}),
        "handler": lambda c: c.list_inputs(),
    },
    {
        "name": "list_input_kinds",
        "description": "List the input kind identifiers this OBS build supports (e.g. coreaudio_input_capture). Use before create_input.",
        "parameters": _obj({}),
        "handler": lambda c: c.list_input_kinds(),
    },
    {
        "name": "list_filters",
        "description": "List the audio/video filters currently on a source, including their kind and settings.",
        "parameters": _obj({"source_name": _STR}, ["source_name"]),
        "handler": lambda c, source_name: c.list_filters(source_name),
    },
    {
        "name": "apply_audio_filter",
        "description": (
            "Create or update (idempotent) a filter on a source. Reuses the filter by name if it "
            "already exists, updating only the keys you pass. Common filter_kind values and their "
            "settings keys:\n"
            "- noise_suppress_filter: {\"method\": \"rnnoise\"}  (or \"speex\" with \"suppress_level\": -30)\n"
            "- noise_gate_filter: {\"open_threshold\": -35, \"close_threshold\": -45, \"attack_time\": 25, \"hold_time\": 200, \"release_time\": 150}  (dB, ms)\n"
            "- compressor_filter: {\"ratio\": 4.0, \"threshold\": -18, \"attack_time\": 6, \"release_time\": 60, \"output_gain\": 0}\n"
            "- gain_filter: {\"db\": 0.0}\n"
            "- basic_eq_filter: {\"low\": 0.0, \"mid\": 0.0, \"high\": 0.0}  (dB per band)\n"
            "- limiter_filter: {\"threshold\": -6, \"release_time\": 60}\n"
            "- expander_filter: {\"ratio\": 2.0, \"threshold\": -40, \"attack_time\": 10, \"release_time\": 50}\n"
            "Recommended mic cleanup order: Noise Suppression -> Noise Gate -> Compressor -> EQ."
        ),
        "parameters": _obj(
            {
                "source_name": _STR,
                "filter_kind": _STR,
                "settings": {"type": "object", "description": "Filter settings keys per the filter_kind."},
                "filter_name": {"type": "string", "description": "Optional display name; defaults to a readable name per kind."},
            },
            ["source_name", "filter_kind"],
        ),
        "handler": lambda c, source_name, filter_kind, settings=None, filter_name=None: c.apply_filter(
            source_name, filter_kind, settings, filter_name
        ),
    },
    {
        "name": "set_filter_enabled",
        "description": "Enable or disable an existing filter on a source without deleting it.",
        "parameters": _obj({"source_name": _STR, "filter_name": _STR, "enabled": _BOOL}, ["source_name", "filter_name", "enabled"]),
        "handler": lambda c, source_name, filter_name, enabled: c.set_filter_enabled(source_name, filter_name, enabled),
    },
    {
        "name": "remove_filter",
        "description": "Permanently remove a filter from a source.",
        "parameters": _obj({"source_name": _STR, "filter_name": _STR}, ["source_name", "filter_name"]),
        "handler": lambda c, source_name, filter_name: c.remove_filter(source_name, filter_name),
    },
    {
        "name": "set_input_volume",
        "description": "Set an input's volume in decibels (0 = unity/full, negative = quieter, e.g. -6).",
        "parameters": _obj({"input_name": _STR, "volume_db": _NUM}, ["input_name", "volume_db"]),
        "handler": lambda c, input_name, volume_db: c.set_input_volume(input_name, volume_db),
    },
    {
        "name": "set_input_mute",
        "description": "Mute or unmute an input.",
        "parameters": _obj({"input_name": _STR, "muted": _BOOL}, ["input_name", "muted"]),
        "handler": lambda c, input_name, muted: c.set_input_mute(input_name, muted),
    },
    {
        "name": "set_video_settings",
        "description": (
            "Set canvas (base) and/or output (scaled) resolution and fps. Pass only what changes. "
            "base_* is the compositing canvas; output_* is what gets encoded/streamed. "
            "Common: 1920x1080 base, 1280x720 output, fps 30 or 60."
        ),
        "parameters": _obj(
            {
                "base_width": _INT,
                "base_height": _INT,
                "output_width": _INT,
                "output_height": _INT,
                "fps": {"type": "number", "description": "Frames per second, e.g. 30, 60, or 59.94."},
            }
        ),
        "handler": lambda c, base_width=None, base_height=None, output_width=None, output_height=None, fps=None: c.set_video_settings(
            base_width, base_height, output_width, output_height, fps
        ),
    },
    {
        "name": "list_scenes",
        "description": "List all scenes and which one is currently active (program).",
        "parameters": _obj({}),
        "handler": lambda c: c.list_scenes(),
    },
    {
        "name": "create_scene",
        "description": "Create a new empty scene.",
        "parameters": _obj({"scene_name": _STR}, ["scene_name"]),
        "handler": lambda c, scene_name: c.create_scene(scene_name),
    },
    {
        "name": "set_current_scene",
        "description": "Switch the active (program) scene.",
        "parameters": _obj({"scene_name": _STR}, ["scene_name"]),
        "handler": lambda c, scene_name: c.set_current_scene(scene_name),
    },
    {
        "name": "list_scene_items",
        "description": "List the sources (scene items) inside a scene, with their ids and enabled state.",
        "parameters": _obj({"scene_name": _STR}, ["scene_name"]),
        "handler": lambda c, scene_name: c.list_scene_items(scene_name),
    },
    {
        "name": "set_scene_item_enabled",
        "description": "Show or hide a source within a scene. Identify it by source_name (preferred) or scene_item_id.",
        "parameters": _obj(
            {"scene_name": _STR, "enabled": _BOOL, "source_name": _STR, "scene_item_id": _INT},
            ["scene_name", "enabled"],
        ),
        "handler": lambda c, scene_name, enabled, source_name=None, scene_item_id=None: c.set_scene_item_enabled(
            scene_name, enabled, source_name, scene_item_id
        ),
    },
    {
        "name": "create_input",
        "description": (
            "Add a new source to a scene. input_kind must be a valid kind from list_input_kinds. "
            "macOS examples: coreaudio_input_capture (mic), coreaudio_output_capture (desktop audio), "
            "screen_capture (screen), av_capture_input_v2 (camera), browser_source, color_source_v3, "
            "text_ft2_source_v2, image_source."
        ),
        "parameters": _obj(
            {
                "scene_name": _STR,
                "input_name": _STR,
                "input_kind": _STR,
                "input_settings": {"type": "object", "description": "Optional kind-specific settings."},
            },
            ["scene_name", "input_name", "input_kind"],
        ),
        "handler": lambda c, scene_name, input_name, input_kind, input_settings=None: c.create_input(
            scene_name, input_name, input_kind, input_settings
        ),
    },
    {
        "name": "get_stream_service",
        "description": "Get the current streaming service config (server/service). The stream key is redacted.",
        "parameters": _obj({}),
        "handler": lambda c: c.get_stream_service(),
        "tags": [STREAMING_TAG],
    },
    {
        "name": "set_stream_service",
        "description": (
            "Configure the streaming destination. For a known platform use service_type='rtmp_common' with "
            "settings {\"service\": \"Twitch\", \"server\": \"auto\", \"key\": \"<key>\"}. For a custom RTMP "
            "server use service_type='rtmp_custom' with {\"server\": \"rtmp://...\", \"key\": \"<key>\"}."
        ),
        "parameters": _obj(
            {"service_type": _STR, "settings": {"type": "object"}},
            ["service_type", "settings"],
        ),
        "handler": lambda c, service_type, settings: c.set_stream_service(service_type, settings),
        "tags": [STREAMING_TAG],
    },
    {
        "name": "control_stream",
        "description": "Start, stop, or check the live stream. action is one of: start, stop, status.",
        "parameters": _obj({"action": {"type": "string", "enum": ["start", "stop", "status"]}}, ["action"]),
        "handler": lambda c, action: _control(c, "stream", action),
        "tags": [STREAMING_TAG],
    },
    {
        "name": "control_record",
        "description": "Start, stop, or check local recording. action is one of: start, stop, status.",
        "parameters": _obj({"action": {"type": "string", "enum": ["start", "stop", "status"]}}, ["action"]),
        "handler": lambda c, action: _control(c, "record", action),
        "tags": [STREAMING_TAG],
    },
    {
        "name": "set_profile_parameter",
        "description": (
            "Set a low-level profile config value — this is how encoder/bitrate are changed (obs-websocket "
            "has no dedicated bitrate request). Simple output mode examples: category 'SimpleOutput' with "
            "name 'VBitrate' value '6000' (video kbps), name 'ABitrate' value '160' (audio kbps), "
            "name 'StreamEncoder' value 'x264'. Changes apply to the active profile."
        ),
        "parameters": _obj({"category": _STR, "name": _STR, "value": _STR}, ["category", "name", "value"]),
        "handler": lambda c, category, name, value: c.set_profile_parameter(category, name, value),
        "tags": [STREAMING_TAG],
    },
    {
        "name": "get_profile_parameter",
        "description": "Read a profile config value (e.g. category 'SimpleOutput', name 'VBitrate').",
        "parameters": _obj({"category": _STR, "name": _STR}, ["category", "name"]),
        "handler": lambda c, category, name: c.get_profile_parameter(category, name),
    },
    {
        "name": "obs_raw_request",
        "description": (
            "Escape hatch: send any raw obs-websocket v5 request by type and data dict. Use only when no "
            "specific tool fits. request_type is a protocol name like 'GetStats'; request_data is its params."
        ),
        "parameters": _obj(
            {"request_type": _STR, "request_data": {"type": "object"}},
            ["request_type"],
        ),
        "handler": lambda c, request_type, request_data=None: c.raw_request(request_type, request_data),
    },
]


def _control(c: OBSController, kind: str, action: str) -> dict[str, Any]:
    if kind == "stream":
        return {"start": c.start_stream, "stop": c.stop_stream, "status": c.get_stream_status}[action]()
    return {"start": c.start_record, "stop": c.stop_record, "status": c.get_record_status}[action]()


# name -> spec, for fast dispatch
_BY_NAME: dict[str, dict[str, Any]] = {t["name"]: t for t in _CATALOGUE}


def visible_tools(allow_streaming: bool = False) -> list[dict[str, Any]]:
    """Return the catalogue, optionally hiding streaming/record side-effect tools."""
    out = []
    for t in _CATALOGUE:
        if not allow_streaming and STREAMING_TAG in t.get("tags", []):
            continue
        out.append(t)
    return out


def to_anthropic_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {"name": t["name"], "description": t["description"], "input_schema": t["parameters"]}
        for t in tools
    ]


def to_openai_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            },
        }
        for t in tools
    ]


def execute_tool(controller: OBSController, name: str, args: dict[str, Any]) -> tuple[str, bool]:
    """Run a tool by name. Returns (result_text, is_error)."""
    spec = _BY_NAME.get(name)
    if spec is None:
        return json.dumps({"error": f"Unknown tool '{name}'"}), True
    handler: Callable = spec["handler"]
    try:
        result = handler(controller, **(args or {}))
        return json.dumps(result, default=str), False
    except OBSError as e:
        payload = {"error": str(e)}
        if e.code is not None:
            payload["obs_code"] = e.code
        return json.dumps(payload), True
    except TypeError as e:
        return json.dumps({"error": f"Bad arguments for {name}: {e}"}), True
    except Exception as e:  # pragma: no cover - defensive
        return json.dumps({"error": f"{type(e).__name__}: {e}"}), True
