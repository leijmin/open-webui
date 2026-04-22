from open_webui.utils.videos import (
    build_openai_video_payload,
    extract_video_result_url,
    filter_video_models,
    normalize_video_task_status,
)


def test_filter_video_models_keeps_video_capable_entries_only():
    models = [
        {
            "id": "gpt-4o-mini",
            "model_type": "文本",
            "supported_endpoint_types": ["openai"],
        },
        {
            "id": "veo3.1-fast",
            "model_type": "音视频",
            "supported_endpoint_types": ["视频统一格式"],
        },
        {
            "id": "sora-2-all",
            "model_type": "音视频",
            "supported_endpoint_types": ["openAI视频格式"],
        },
    ]

    assert [model["id"] for model in filter_video_models(models)] == [
        "veo3.1-fast",
        "sora-2-all",
    ]


def test_filter_video_models_skips_audio_only_entries():
    models = [
        {
            "id": "speech-2.8-hd",
            "model_type": "音视频",
            "supported_endpoint_types": ["同步语音", "异步语音"],
        },
        {
            "id": "veo3.1-fast",
            "model_type": "音视频",
            "supported_endpoint_types": ["视频统一格式"],
        },
    ]

    assert [model["id"] for model in filter_video_models(models)] == ["veo3.1-fast"]


def test_filter_video_models_skips_audio_preview_models():
    models = [
        {
            "id": "gpt-4o-audio-preview",
            "model_type": "音视频",
            "supported_endpoint_types": ["openai"],
        },
        {
            "id": "veo3.1-fast",
            "model_type": "音视频",
            "supported_endpoint_types": ["视频统一格式"],
        },
    ]

    assert [model["id"] for model in filter_video_models(models)] == ["veo3.1-fast"]


def test_normalize_video_task_status_handles_provider_running_states():
    assert (
        normalize_video_task_status(
            {
                "status": "pending",
                "detail": {
                    "status": "video_generating",
                    "running": True,
                },
            }
        )
        == "processing"
    )


def test_extract_video_result_url_reads_nested_provider_payloads():
    assert (
        extract_video_result_url(
            {
                "detail": {
                    "result": {
                        "videos": [
                            {
                                "url": "https://cdn.example.com/generated/demo.mp4",
                            }
                        ]
                    }
                }
            }
        )
        == "https://cdn.example.com/generated/demo.mp4"
    )


def test_build_openai_video_payload_includes_duration_and_reference_images():
    payload = build_openai_video_payload(
        model="wan2.5-i2v-preview",
        prompt="让画面轻微推进",
        duration=5,
        images=["data:image/png;base64,abc123"],
        extra_params={"enable_upsample": False},
    )

    assert payload == {
        "model": "wan2.5-i2v-preview",
        "prompt": "让画面轻微推进",
        "duration": 5,
        "images": ["data:image/png;base64,abc123"],
        "enable_upsample": False,
    }
