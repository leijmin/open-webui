from __future__ import annotations

from typing import Any


OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
IMAGE_ENDPOINT_MARKERS = ("image", "图像", "图片")
TEXT_ENDPOINT_MARKERS = ("chat", "response", "completion", "text")
OPENAI_IMAGE_ENDPOINT_MARKERS = (
    "openai编辑图片",
    "openai image",
    "image edit",
)
OPENAI_IMAGE_MODEL_PREFIXES = ("gpt-image", "dall-e")


def normalize_value(value: Any) -> str:
    return str(value or "").strip()


def normalize_base_url(value: Any) -> str:
    return normalize_value(value).rstrip("/")


def _first_non_empty(values: list[Any] | tuple[Any, ...] | None) -> str:
    for value in values or []:
        normalized = normalize_value(value)
        if normalized:
            return normalized
    return ""


def get_supported_endpoint_types(model: dict | None) -> list[str]:
    if not isinstance(model, dict):
        return []

    values = [
        *(model.get("supported_endpoint_types") or []),
        *((model.get("openai") or {}).get("supported_endpoint_types") or []),
    ]
    return [normalize_value(value).lower() for value in values]


def get_model_type(model: dict | None) -> str:
    if not isinstance(model, dict):
        return ""

    return normalize_value(
        model.get("model_type") or (model.get("openai") or {}).get("model_type")
    ).lower()


def is_image_generation_model(model: dict | None) -> bool:
    supported_endpoint_types = get_supported_endpoint_types(model)
    model_type = get_model_type(model)

    supports_image_generation = any(
        marker in endpoint_type
        for endpoint_type in supported_endpoint_types
        for marker in IMAGE_ENDPOINT_MARKERS
    ) or any(marker in model_type for marker in IMAGE_ENDPOINT_MARKERS)

    supports_text_generation = any(
        marker in endpoint_type
        for endpoint_type in supported_endpoint_types
        for marker in TEXT_ENDPOINT_MARKERS
    )

    return supports_image_generation and not supports_text_generation


def is_openai_image_generation_model(model: dict | None) -> bool:
    supported_endpoint_types = get_supported_endpoint_types(model)
    model_id = normalize_value((model or {}).get("id")).lower()

    supports_openai_image_endpoints = any(
        marker in endpoint_type
        for endpoint_type in supported_endpoint_types
        for marker in OPENAI_IMAGE_ENDPOINT_MARKERS
    )
    matches_openai_image_prefix = any(
        model_id.startswith(prefix) for prefix in OPENAI_IMAGE_MODEL_PREFIXES
    )

    return is_image_generation_model(model) and (
        supports_openai_image_endpoints or matches_openai_image_prefix
    )


def get_first_image_generation_model_id(models: list[dict] | None) -> str | None:
    if not isinstance(models, list):
        return None

    for model in models:
        if not is_openai_image_generation_model(model):
            continue

        model_id = normalize_value((model or {}).get("id"))
        if model_id:
            return model_id

    for model in models:
        if not is_image_generation_model(model):
            continue

        model_id = normalize_value((model or {}).get("id"))
        if model_id:
            return model_id

    return None


def get_default_openai_connection(config) -> dict[str, str]:
    base_url = normalize_base_url(
        _first_non_empty(getattr(config, "OPENAI_API_BASE_URLS", []))
    )
    api_key = _first_non_empty(getattr(config, "OPENAI_API_KEYS", []))

    return {
        "base_url": base_url or OPENAI_DEFAULT_BASE_URL,
        "api_key": api_key,
    }


def get_effective_image_generation_settings(
    config, models: list[dict] | None = None
) -> dict[str, Any]:
    default_connection = get_default_openai_connection(config)

    engine = normalize_value(getattr(config, "IMAGE_GENERATION_ENGINE", "openai"))
    if not engine:
        engine = "openai"

    model = normalize_value(getattr(config, "IMAGE_GENERATION_MODEL", ""))
    if not model:
        if engine == "openai":
            model = get_first_image_generation_model_id(models) or "gpt-image-1"
        elif engine == "gemini":
            model = "imagen-3.0-generate-002"

    return {
        "enabled": bool(getattr(config, "ENABLE_IMAGE_GENERATION", False)),
        "engine": engine,
        "model": model,
        "size": normalize_value(getattr(config, "IMAGE_SIZE", "")),
        "openai_api_base_url": normalize_base_url(
            getattr(config, "IMAGES_OPENAI_API_BASE_URL", "")
        )
        or default_connection["base_url"],
        "openai_api_key": normalize_value(
            getattr(config, "IMAGES_OPENAI_API_KEY", "")
        )
        or default_connection["api_key"],
        "openai_api_version": normalize_value(
            getattr(config, "IMAGES_OPENAI_API_VERSION", "")
        ),
    }


def get_effective_image_generation_size(
    config, model: str, requested_size: str | None = None
) -> str:
    requested_size = normalize_value(requested_size)
    if requested_size:
        return requested_size

    configured_size = normalize_value(getattr(config, "IMAGE_SIZE", ""))
    if configured_size == "auto":
        return configured_size

    normalized_model = normalize_value(model).lower()
    if any(
        normalized_model.startswith(prefix) for prefix in OPENAI_IMAGE_MODEL_PREFIXES
    ) and configured_size in ("", "512x512"):
        return "auto"

    return configured_size or "512x512"


def get_effective_image_edit_settings(
    config, models: list[dict] | None = None
) -> dict[str, Any]:
    generation_settings = get_effective_image_generation_settings(config, models=models)

    engine = normalize_value(getattr(config, "IMAGE_EDIT_ENGINE", ""))
    if not engine:
        engine = generation_settings["engine"] or "openai"

    model = normalize_value(getattr(config, "IMAGE_EDIT_MODEL", ""))
    if not model:
        model = generation_settings["model"]

    openai_api_base_url = normalize_base_url(
        getattr(config, "IMAGES_EDIT_OPENAI_API_BASE_URL", "")
    ) or generation_settings["openai_api_base_url"]
    openai_api_key = normalize_value(
        getattr(config, "IMAGES_EDIT_OPENAI_API_KEY", "")
    ) or generation_settings["openai_api_key"]
    openai_api_version = normalize_value(
        getattr(config, "IMAGES_EDIT_OPENAI_API_VERSION", "")
    ) or generation_settings["openai_api_version"]

    enabled = bool(getattr(config, "ENABLE_IMAGE_EDIT", False))
    if not enabled:
        if engine == "openai":
            enabled = bool(model and openai_api_base_url and openai_api_key)
        elif engine == "gemini":
            enabled = bool(
                model
                and normalize_value(getattr(config, "IMAGES_EDIT_GEMINI_API_BASE_URL", ""))
                and normalize_value(getattr(config, "IMAGES_EDIT_GEMINI_API_KEY", ""))
            )
        elif engine == "comfyui":
            enabled = bool(
                model
                and normalize_base_url(getattr(config, "IMAGES_EDIT_COMFYUI_BASE_URL", ""))
            )

    return {
        "enabled": enabled,
        "engine": engine,
        "model": model,
        "size": normalize_value(getattr(config, "IMAGE_EDIT_SIZE", "")),
        "openai_api_base_url": openai_api_base_url,
        "openai_api_key": openai_api_key,
        "openai_api_version": openai_api_version,
    }


def can_use_image_edit(config, models: list[dict] | None = None) -> bool:
    settings = get_effective_image_edit_settings(config, models=models)
    return bool(settings["enabled"] and settings["model"])
