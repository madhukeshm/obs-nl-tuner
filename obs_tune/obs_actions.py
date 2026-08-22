"""Thin, protocol-accurate wrapper around obs-websocket v5 via obsws-python.

Every request goes through :meth:`OBSController._req`, which calls
``ReqClient.send(request_type, request_data, raw=True)`` and returns the raw
``responseData`` dict with the exact camelCase field names from the
obs-websocket v5 protocol. This keeps the mapping between our code and the
published protocol 1:1, so there is no guesswork about method signatures.

Verified against OBS 32.2.2 / obs-websocket 5.x.
"""

from __future__ import annotations

from typing import Any

import obsws_python as obs
from obsws_python.error import OBSSDKRequestError, OBSSDKError


class OBSError(Exception):
    """Raised for connection or request failures, with an OBS error code when known."""

    def __init__(self, message: str, code: int | None = None):
        super().__init__(message)
        self.code = code


# fps values that OBS represents as N/1001 rather than N/1
_FRACTIONAL_FPS = {
    23.976: (24000, 1001),
    29.97: (30000, 1001),
    47.952: (48000, 1001),
    59.94: (60000, 1001),
    119.88: (120000, 1001),
}


def _fps_to_fraction(fps: float) -> tuple[int, int]:
    """Convert a plain fps number to (numerator, denominator)."""
    rounded = round(fps, 3)
    if rounded in _FRACTIONAL_FPS:
        return _FRACTIONAL_FPS[rounded]
    if float(fps).is_integer():
        return int(fps), 1
    # Fallback: express as thousandths.
    return int(round(fps * 1000)), 1000


class OBSController:
    """Connects to OBS and exposes high-level actions used by the tool layer."""

    def __init__(self, host: str = "localhost", port: int = 4455, password: str = "", timeout: int = 5):
        self.host = host
        self.port = port
        self._password = password
        self._timeout = timeout
        self.client: obs.ReqClient | None = None

    # -- connection ---------------------------------------------------------
    def connect(self) -> dict[str, Any]:
        try:
            self.client = obs.ReqClient(
                host=self.host, port=self.port, password=self._password, timeout=self._timeout
            )
        except Exception as e:  # connection/handshake/auth failures
            raise OBSError(f"Could not connect to OBS at {self.host}:{self.port} — {e}") from e
        return self.get_version()

    def close(self) -> None:
        if self.client is not None:
            try:
                self.client.disconnect()
            except Exception:
                pass
            self.client = None

    def _req(self, request_type: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.client is None:
            raise OBSError("Not connected to OBS. Call connect() first.")
        try:
            resp = self.client.send(request_type, data or {}, raw=True)
        except OBSSDKRequestError as e:
            raise OBSError(str(e), code=getattr(e, "code", None)) from e
        except OBSSDKError as e:
            raise OBSError(str(e)) from e
        return resp if isinstance(resp, dict) else {}

    # -- general / discovery ------------------------------------------------
    def get_version(self) -> dict[str, Any]:
        r = self._req("GetVersion")
        return {
            "obsVersion": r.get("obsVersion"),
            "obsWebSocketVersion": r.get("obsWebSocketVersion"),
            "platform": r.get("platform"),
        }

    def get_overview(self) -> dict[str, Any]:
        """A single snapshot of the most relevant OBS state for planning."""
        scenes = self._req("GetSceneList")
        inputs = self._req("GetInputList")
        video = self._req("GetVideoSettings")
        try:
            stream = self._req("GetStreamStatus")
        except OBSError:
            stream = {}
        try:
            record = self._req("GetRecordStatus")
        except OBSError:
            record = {}
        return {
            "version": self.get_version(),
            "currentProgramScene": scenes.get("currentProgramSceneName"),
            "scenes": [s.get("sceneName") for s in scenes.get("scenes", [])],
            "inputs": [
                {"name": i.get("inputName"), "kind": i.get("inputKind")}
                for i in inputs.get("inputs", [])
            ],
            "video": {
                "baseWidth": video.get("baseWidth"),
                "baseHeight": video.get("baseHeight"),
                "outputWidth": video.get("outputWidth"),
                "outputHeight": video.get("outputHeight"),
                "fps": _round_fps(video.get("fpsNumerator"), video.get("fpsDenominator")),
            },
            "streaming": stream.get("outputActive"),
            "recording": record.get("outputActive"),
        }

    def list_inputs(self) -> list[dict[str, Any]]:
        r = self._req("GetInputList")
        return [
            {"name": i.get("inputName"), "kind": i.get("inputKind")}
            for i in r.get("inputs", [])
        ]

    def list_input_kinds(self) -> list[str]:
        return self._req("GetInputKindList").get("inputKinds", [])

    # -- audio: filters, volume, mute --------------------------------------
    def list_filters(self, source_name: str) -> list[dict[str, Any]]:
        r = self._req("GetSourceFilterList", {"sourceName": source_name})
        return [
            {
                "name": f.get("filterName"),
                "kind": f.get("filterKind"),
                "enabled": f.get("filterEnabled"),
                "settings": f.get("filterSettings"),
            }
            for f in r.get("filters", [])
        ]

    def get_filter(self, source_name: str, filter_name: str) -> dict[str, Any]:
        return self._req("GetSourceFilter", {"sourceName": source_name, "filterName": filter_name})

    def apply_filter(
        self,
        source_name: str,
        filter_kind: str,
        settings: dict[str, Any] | None = None,
        filter_name: str | None = None,
    ) -> dict[str, Any]:
        """Idempotently create or update a filter on a source.

        If a filter with ``filter_name`` already exists, its settings are
        updated (overlaid); otherwise it is created. Returns a status dict.
        """
        settings = settings or {}
        name = filter_name or _default_filter_name(filter_kind)
        existing = self.list_filters(source_name)
        match = next((f for f in existing if f["name"] == name), None)
        if match is None:
            self._req(
                "CreateSourceFilter",
                {
                    "sourceName": source_name,
                    "filterName": name,
                    "filterKind": filter_kind,
                    "filterSettings": settings,
                },
            )
            return {"action": "created", "source": source_name, "filter": name, "kind": filter_kind}
        # Update in place. overlay=True merges provided keys over current ones.
        self._req(
            "SetSourceFilterSettings",
            {
                "sourceName": source_name,
                "filterName": name,
                "filterSettings": settings,
                "overlay": True,
            },
        )
        return {"action": "updated", "source": source_name, "filter": name, "kind": match["kind"]}

    def set_filter_enabled(self, source_name: str, filter_name: str, enabled: bool) -> dict[str, Any]:
        self._req(
            "SetSourceFilterEnabled",
            {"sourceName": source_name, "filterName": filter_name, "filterEnabled": enabled},
        )
        return {"source": source_name, "filter": filter_name, "enabled": enabled}

    def remove_filter(self, source_name: str, filter_name: str) -> dict[str, Any]:
        self._req("RemoveSourceFilter", {"sourceName": source_name, "filterName": filter_name})
        return {"removed": filter_name, "source": source_name}

    def set_input_volume(self, input_name: str, volume_db: float) -> dict[str, Any]:
        self._req("SetInputVolume", {"inputName": input_name, "inputVolumeDb": volume_db})
        return {"input": input_name, "volumeDb": volume_db}

    def set_input_mute(self, input_name: str, muted: bool) -> dict[str, Any]:
        self._req("SetInputMute", {"inputName": input_name, "inputMuted": muted})
        return {"input": input_name, "muted": muted}

    # -- video --------------------------------------------------------------
    def set_video_settings(
        self,
        base_width: int | None = None,
        base_height: int | None = None,
        output_width: int | None = None,
        output_height: int | None = None,
        fps: float | None = None,
    ) -> dict[str, Any]:
        data: dict[str, Any] = {}
        if base_width is not None:
            data["baseWidth"] = int(base_width)
        if base_height is not None:
            data["baseHeight"] = int(base_height)
        if output_width is not None:
            data["outputWidth"] = int(output_width)
        if output_height is not None:
            data["outputHeight"] = int(output_height)
        if fps is not None:
            num, den = _fps_to_fraction(fps)
            data["fpsNumerator"] = num
            data["fpsDenominator"] = den
        if not data:
            raise OBSError("set_video_settings called with nothing to change.")
        self._req("SetVideoSettings", data)
        v = self._req("GetVideoSettings")
        return {
            "baseWidth": v.get("baseWidth"),
            "baseHeight": v.get("baseHeight"),
            "outputWidth": v.get("outputWidth"),
            "outputHeight": v.get("outputHeight"),
            "fps": _round_fps(v.get("fpsNumerator"), v.get("fpsDenominator")),
        }

    # -- scenes & sources ---------------------------------------------------
    def list_scenes(self) -> dict[str, Any]:
        r = self._req("GetSceneList")
        return {
            "current": r.get("currentProgramSceneName"),
            "scenes": [s.get("sceneName") for s in r.get("scenes", [])],
        }

    def create_scene(self, scene_name: str) -> dict[str, Any]:
        self._req("CreateScene", {"sceneName": scene_name})
        return {"created": scene_name}

    def set_current_scene(self, scene_name: str) -> dict[str, Any]:
        self._req("SetCurrentProgramScene", {"sceneName": scene_name})
        return {"currentScene": scene_name}

    def list_scene_items(self, scene_name: str) -> list[dict[str, Any]]:
        r = self._req("GetSceneItemList", {"sceneName": scene_name})
        return [
            {
                "sceneItemId": it.get("sceneItemId"),
                "sourceName": it.get("sourceName"),
                "enabled": it.get("sceneItemEnabled"),
            }
            for it in r.get("sceneItems", [])
        ]

    def _scene_item_id(self, scene_name: str, source_name: str) -> int:
        r = self._req("GetSceneItemId", {"sceneName": scene_name, "sourceName": source_name})
        return r["sceneItemId"]

    def set_scene_item_enabled(
        self,
        scene_name: str,
        enabled: bool,
        source_name: str | None = None,
        scene_item_id: int | None = None,
    ) -> dict[str, Any]:
        if scene_item_id is None:
            if source_name is None:
                raise OBSError("Provide either source_name or scene_item_id.")
            scene_item_id = self._scene_item_id(scene_name, source_name)
        self._req(
            "SetSceneItemEnabled",
            {"sceneName": scene_name, "sceneItemId": scene_item_id, "sceneItemEnabled": enabled},
        )
        return {"scene": scene_name, "sceneItemId": scene_item_id, "enabled": enabled}

    def create_input(
        self,
        scene_name: str,
        input_name: str,
        input_kind: str,
        input_settings: dict[str, Any] | None = None,
        enabled: bool = True,
    ) -> dict[str, Any]:
        r = self._req(
            "CreateInput",
            {
                "sceneName": scene_name,
                "inputName": input_name,
                "inputKind": input_kind,
                "inputSettings": input_settings or {},
                "sceneItemEnabled": enabled,
            },
        )
        return {"created": input_name, "kind": input_kind, "sceneItemId": r.get("sceneItemId")}

    # -- streaming & recording ---------------------------------------------
    def get_stream_status(self) -> dict[str, Any]:
        r = self._req("GetStreamStatus")
        return {"active": r.get("outputActive"), "timecode": r.get("outputTimecode")}

    def start_stream(self) -> dict[str, Any]:
        self._req("StartStream")
        return {"streaming": True}

    def stop_stream(self) -> dict[str, Any]:
        self._req("StopStream")
        return {"streaming": False}

    def get_record_status(self) -> dict[str, Any]:
        r = self._req("GetRecordStatus")
        return {"active": r.get("outputActive"), "timecode": r.get("outputTimecode")}

    def start_record(self) -> dict[str, Any]:
        self._req("StartRecord")
        return {"recording": True}

    def stop_record(self) -> dict[str, Any]:
        r = self._req("StopRecord")
        return {"recording": False, "outputPath": r.get("outputPath")}

    def get_stream_service(self) -> dict[str, Any]:
        r = self._req("GetStreamServiceSettings")
        settings = dict(r.get("streamServiceSettings", {}))
        # Never surface the stream key back to the model / UI.
        if "key" in settings:
            settings["key"] = "***redacted***"
        return {"type": r.get("streamServiceType"), "settings": settings}

    def set_stream_service(self, service_type: str, settings: dict[str, Any]) -> dict[str, Any]:
        self._req(
            "SetStreamServiceSettings",
            {"streamServiceType": service_type, "streamServiceSettings": settings},
        )
        safe = {k: ("***" if k == "key" else v) for k, v in settings.items()}
        return {"type": service_type, "settings": safe}

    # -- profile parameters (encoder / bitrate live here) ------------------
    def get_profile_parameter(self, category: str, name: str) -> dict[str, Any]:
        r = self._req("GetProfileParameter", {"parameterCategory": category, "parameterName": name})
        return {
            "category": category,
            "name": name,
            "value": r.get("parameterValue"),
            "default": r.get("defaultParameterValue"),
        }

    def set_profile_parameter(self, category: str, name: str, value: str) -> dict[str, Any]:
        self._req(
            "SetProfileParameter",
            {"parameterCategory": category, "parameterName": name, "parameterValue": str(value)},
        )
        return {"category": category, "name": name, "value": str(value)}

    # -- escape hatch -------------------------------------------------------
    def raw_request(self, request_type: str, request_data: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._req(request_type, request_data or {})


def _round_fps(num: int | None, den: int | None) -> float | None:
    if not num or not den:
        return None
    return round(num / den, 3)


def _default_filter_name(filter_kind: str) -> str:
    return {
        "noise_suppress_filter": "Noise Suppression",
        "noise_gate_filter": "Noise Gate",
        "compressor_filter": "Compressor",
        "gain_filter": "Gain",
        "basic_eq_filter": "3-Band EQ",
        "limiter_filter": "Limiter",
        "expander_filter": "Expander",
    }.get(filter_kind, filter_kind)
