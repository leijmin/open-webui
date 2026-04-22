from types import SimpleNamespace

from open_webui.utils.images.config import (
    can_use_image_edit,
    get_effective_image_edit_settings,
    get_effective_image_generation_size,
    get_first_image_generation_model_id,
)


def build_config(**overrides):
    defaults = {
        "ENABLE_IMAGE_EDIT": False,
        "IMAGE_EDIT_ENGINE": "openai",
        "IMAGE_EDIT_MODEL": "",
        "IMAGE_EDIT_SIZE": "",
        "IMAGES_EDIT_OPENAI_API_BASE_URL": "",
        "IMAGES_EDIT_OPENAI_API_KEY": "",
        "IMAGES_EDIT_OPENAI_API_VERSION": "",
        "IMAGE_GENERATION_ENGINE": "openai",
        "IMAGE_GENERATION_MODEL": "gpt-image-2",
        "IMAGES_OPENAI_API_BASE_URL": "",
        "IMAGES_OPENAI_API_KEY": "",
        "IMAGES_OPENAI_API_VERSION": "",
        "OPENAI_API_BASE_URLS": ["https://api3.wlai.vip/v1"],
        "OPENAI_API_KEYS": ["sk-test"],
    }
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


def test_image_edit_settings_fall_back_to_current_openai_connection():
    config = build_config()

    settings = get_effective_image_edit_settings(config)

    assert settings == {
        "enabled": True,
        "engine": "openai",
        "model": "gpt-image-2",
        "size": "",
        "openai_api_base_url": "https://api3.wlai.vip/v1",
        "openai_api_key": "sk-test",
        "openai_api_version": "",
    }


def test_image_edit_falls_back_even_when_toggle_is_unset():
    config = build_config()

    assert can_use_image_edit(config) is True


def test_get_first_image_generation_model_id_reads_provider_capabilities():
    models = [
        {
            "id": "gpt-4o-mini",
            "model_type": "chat",
            "supported_endpoint_types": ["chat-completions"],
        },
        {
            "id": "generic-image-model",
            "model_type": "图像",
            "supported_endpoint_types": ["image-generation"],
        },
        {
            "id": "gpt-image-2",
            "model_type": "图像",
            "supported_endpoint_types": ["openai编辑图片", "image-generation"],
        },
    ]

    assert get_first_image_generation_model_id(models) == "gpt-image-2"


def test_gpt_image_models_use_auto_size_when_default_size_was_not_tuned():
    config = build_config(IMAGE_SIZE="512x512")

    assert get_effective_image_generation_size(
        config, model="gpt-image-2", requested_size=None
    ) == "auto"


def test_explicit_image_size_is_preserved():
    config = build_config(IMAGE_SIZE="1536x1024")

    assert get_effective_image_generation_size(
        config, model="gpt-image-2", requested_size="1024x1024"
    ) == "1024x1024"
