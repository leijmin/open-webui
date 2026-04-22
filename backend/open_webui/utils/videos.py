from __future__ import annotations

from typing import Any, Iterable


VIDEO_ENDPOINT_MARKERS = (
    "video",
    "视频",
    "omni-video",
    "wan视频生成",
    "视频统一格式",
    "openai视频格式",
    "openai官方视频格式",
    "vidu文生视频",
    "vidu图生视频",
    "vidu参考生视频",
    "runway图生视频",
    "grok视频",
)

VIDEO_MODEL_TYPE_MARKERS = ("video",)
VIDEO_ID_MARKERS = ("video", "veo", "sora", "vidu", "wan", "runway", "kling")
AUDIO_ENDPOINT_MARKERS = ("audio", "speech", "语音", "音频", "transcribe")

VIDEO_SUCCESS_STATUSES = {
    "success",
    "succeeded",
    "completed",
    "complete",
    "done",
    "finished",
}

VIDEO_ERROR_STATUSES = {
    "error",
    "failed",
    "failure",
    "cancelled",
    "canceled",
    "timeout",
}

VIDEO_RUNNING_STATUSES = {
    "pending",
    "queued",
    "processing",
    "running",
    "in_progress",
    "video_generating",
    "submitting",
}

VIDEO_URL_KEYS = {
    "video",
    "video_url",
    "url",
    "download_url",
    "file_url",
    "result_url",
    "src",
}

VIDEO_FILE_EXTENSIONS = (".mp4", ".mov", ".webm", ".m4v", ".avi", ".mkv")


def normalize_video_value(value: Any) -> str:
    return str(value or "").strip().lower()


def get_supported_endpoint_types(model: dict | None) -> list[str]:
    if not isinstance(model, dict):
        return []

    values = [
        *(model.get("supported_endpoint_types") or []),
        *((model.get("openai") or {}).get("supported_endpoint_types") or []),
    ]
    return [normalize_video_value(value) for value in values]


def get_model_type(model: dict | None) -> str:
    if not isinstance(model, dict):
        return ""

    return normalize_video_value(
        model.get("model_type") or (model.get("openai") or {}).get("model_type")
    )


def is_video_generation_model(model: dict | None) -> bool:
    supported_endpoint_types = get_supported_endpoint_types(model)
    model_type = get_model_type(model)
    model_id = normalize_video_value((model or {}).get("id"))

    supports_video_endpoints = any(
        marker in endpoint_type
        for endpoint_type in supported_endpoint_types
        for marker in VIDEO_ENDPOINT_MARKERS
    )
    supports_video_model_type = any(
        marker in model_type for marker in VIDEO_MODEL_TYPE_MARKERS
    ) or (model_type.endswith("视频") and not model_type.startswith("音"))
    supports_video_model_id = any(marker in model_id for marker in VIDEO_ID_MARKERS)
    supports_audio_only_endpoints = bool(supported_endpoint_types) and all(
        any(marker in endpoint_type for marker in AUDIO_ENDPOINT_MARKERS)
        for endpoint_type in supported_endpoint_types
    )

    return supports_video_endpoints or (
        (supports_video_model_type or supports_video_model_id)
        and not supports_audio_only_endpoints
    )


def filter_video_models(models: list[dict] | None) -> list[dict]:
    if not isinstance(models, list):
        return []

    filtered_models = []
    seen_ids = set()

    for model in models:
        if not is_video_generation_model(model):
            continue

        model_id = model.get("id")
        if not model_id or model_id in seen_ids:
            continue

        filtered_models.append(
            {
                "id": model_id,
                "name": model.get("name") or model_id,
                "model_type": model.get("model_type")
                or (model.get("openai") or {}).get("model_type"),
                "supported_endpoint_types": model.get("supported_endpoint_types")
                or (model.get("openai") or {}).get("supported_endpoint_types")
                or [],
            }
        )
        seen_ids.add(model_id)

    return filtered_models


def normalize_video_task_status(task: dict | None) -> str:
    if not isinstance(task, dict):
        return "pending"

    detail = task.get("detail") if isinstance(task.get("detail"), dict) else {}

    statuses = [
        normalize_video_value(task.get("status")),
        normalize_video_value(detail.get("status")),
        normalize_video_value(detail.get("state")),
        normalize_video_value((detail.get("result") or {}).get("status")),
    ]
    statuses = [status for status in statuses if status]

    if any(status in VIDEO_ERROR_STATUSES for status in statuses):
        return "error"

    if any(status in VIDEO_SUCCESS_STATUSES for status in statuses):
        return "completed"

    if detail.get("running") is True:
        return "processing"

    if any(status in VIDEO_RUNNING_STATUSES for status in statuses):
        return "processing"

    return "pending"


def _looks_like_video_url(value: str) -> bool:
    normalized = normalize_video_value(value)
    if normalized.startswith("data:video/"):
        return True

    if normalized.startswith("http://") or normalized.startswith("https://"):
        if any(normalized.split("?")[0].endswith(ext) for ext in VIDEO_FILE_EXTENSIONS):
            return True

        return "/video/" in normalized or "video" in normalized

    return False


def _iter_nested_values(node: Any) -> Iterable[tuple[str, Any]]:
    if isinstance(node, dict):
        for key, value in node.items():
            yield key, value
            yield from _iter_nested_values(value)
    elif isinstance(node, list):
        for item in node:
            yield "", item
            yield from _iter_nested_values(item)


def extract_video_result_url(task: dict | None) -> str | None:
    if not isinstance(task, dict):
        return None

    for key, value in _iter_nested_values(task):
        normalized_key = normalize_video_value(key)

        if isinstance(value, str):
            if normalized_key in VIDEO_URL_KEYS and _looks_like_video_url(value):
                return value

            if "video" in normalized_key and (
                value.startswith("http://")
                or value.startswith("https://")
                or value.startswith("data:video/")
            ):
                return value

    return None


def build_openai_video_payload(
    *,
    model: str,
    prompt: str,
    duration: int,
    images: list[str] | None = None,
    extra_params: dict | None = None,
) -> dict:
    payload = {
        "model": model,
        "prompt": prompt,
        "duration": duration,
    }

    normalized_images = [image for image in (images or []) if image]
    if normalized_images:
        payload["images"] = normalized_images

    if isinstance(extra_params, dict):
        payload = {**payload, **extra_params}

    return payload
