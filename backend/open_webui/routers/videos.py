import asyncio
import base64
import io
import json
import logging
import mimetypes
import re
import time
from typing import Optional
from urllib.parse import urlencode

import requests
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile
from pydantic import BaseModel

from open_webui.constants import ERROR_MESSAGES
from open_webui.env import ENABLE_FORWARD_USER_INFO_HEADERS
from open_webui.models.chats import Chats
from open_webui.routers.files import upload_file_handler
from open_webui.retrieval.web.utils import validate_url
from open_webui.utils.access_control import has_permission
from open_webui.utils.auth import get_admin_user, get_verified_user
from open_webui.utils.files import get_image_base64_from_url
from open_webui.utils.headers import include_user_info_headers
from open_webui.utils.videos import (
    build_openai_video_payload,
    extract_video_result_url,
    filter_video_models,
    normalize_video_task_status,
)

log = logging.getLogger(__name__)

router = APIRouter()

VIDEO_TASK_TIMEOUT_SECONDS = 300
VIDEO_TASK_POLL_INTERVAL_SECONDS = 5
VIDEO_DOWNLOAD_TIMEOUT_SECONDS = 180
FILE_CONTENT_ID_PATTERN = re.compile(r"/api/v1/files/([^/]+)/content")


class VideosConfig(BaseModel):
    ENABLE_VIDEO_GENERATION: bool
    VIDEO_GENERATION_ENGINE: str
    VIDEO_GENERATION_MODEL: str
    VIDEO_GENERATION_DURATION: int
    VIDEOS_OPENAI_API_BASE_URL: str
    VIDEOS_OPENAI_API_KEY: str
    VIDEOS_OPENAI_API_VERSION: str
    VIDEOS_OPENAI_API_PARAMS: Optional[dict | str]


class CreateVideoForm(BaseModel):
    model: Optional[str] = None
    prompt: str
    duration: Optional[int] = None
    image: Optional[str] = None
    images: Optional[list[str]] = None


GenerateVideoForm = CreateVideoForm


def get_video_model(request: Request):
    if request.app.state.config.VIDEO_GENERATION_ENGINE == "openai":
        return request.app.state.config.VIDEO_GENERATION_MODEL or "veo3.1-fast"

    raise HTTPException(
        status_code=400,
        detail=ERROR_MESSAGES.DEFAULT("Unsupported video generation engine"),
    )


def get_video_headers(request: Request, user=None):
    headers = {
        "Authorization": f"Bearer {request.app.state.config.VIDEOS_OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }

    if ENABLE_FORWARD_USER_INFO_HEADERS and user is not None:
        headers = include_user_info_headers(headers, user)

    return headers


def get_video_endpoint_url(request: Request, path: str, params: Optional[dict] = None):
    base_url = request.app.state.config.VIDEOS_OPENAI_API_BASE_URL.rstrip("/")
    query_params = dict(params or {})

    if request.app.state.config.VIDEOS_OPENAI_API_VERSION:
        query_params["api-version"] = request.app.state.config.VIDEOS_OPENAI_API_VERSION

    if query_params:
        return f"{base_url}{path}?{urlencode(query_params)}"

    return f"{base_url}{path}"


def get_provider_error_message(payload: Optional[dict], fallback: str = "") -> str:
    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            return error.get("message") or json.dumps(error, ensure_ascii=False)
        if isinstance(error, str):
            return error

        detail = payload.get("detail")
        if isinstance(detail, dict):
            detail_error = detail.get("error")
            if isinstance(detail_error, str):
                return detail_error

    return fallback or "Video generation failed"


def normalize_reference_image(image: str) -> Optional[str]:
    if not image:
        return None

    if image.startswith("data:image/"):
        return image

    if image.startswith("http://") or image.startswith("https://"):
        match = FILE_CONTENT_ID_PATTERN.search(image)
        if match:
            return get_image_base64_from_url(match.group(1)) or image

        return image

    match = FILE_CONTENT_ID_PATTERN.search(image)
    if match:
        image = match.group(1)

    return get_image_base64_from_url(image) or image


def get_reference_images(form_data: CreateVideoForm) -> list[str]:
    images = []

    if form_data.image:
        images.append(form_data.image)

    if form_data.images:
        images.extend(form_data.images)

    normalized_images = []
    for image in images:
        normalized_image = normalize_reference_image(image)
        if normalized_image and normalized_image not in normalized_images:
            normalized_images.append(normalized_image)

    return normalized_images


def get_video_data(data: str, headers: Optional[dict] = None):
    try:
        if data.startswith("http://") or data.startswith("https://"):
            validate_url(data)
            response = requests.get(
                data,
                headers=headers,
                timeout=VIDEO_DOWNLOAD_TIMEOUT_SECONDS,
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type") or mimetypes.guess_type(
                data
            )[0]
            return response.content, content_type or "video/mp4"

        if data.startswith("data:video/"):
            header, encoded = data.split(",", 1)
            content_type = header.split(";")[0].lstrip("data:")
            return base64.b64decode(encoded), content_type
    except Exception as e:
        log.exception(f"Error loading video data: {e}")

    return None, None


def upload_video(request, video_data, content_type, metadata, user, db=None):
    video_format = mimetypes.guess_extension(content_type) or ".mp4"
    file = UploadFile(
        file=io.BytesIO(video_data),
        filename=f"generated-video{video_format}",
        headers={
            "content-type": content_type,
        },
    )
    file_item = upload_file_handler(
        request,
        file=file,
        metadata=metadata,
        process=False,
        user=user,
    )

    if file_item and file_item.id:
        chat_id = metadata.get("chat_id")
        message_id = metadata.get("message_id")

        if chat_id and message_id:
            Chats.insert_chat_files(
                chat_id=chat_id,
                message_id=message_id,
                file_ids=[file_item.id],
                user_id=user.id,
                db=db,
            )

    url = request.app.url_path_for("get_file_content_by_id", id=file_item.id)
    return file_item, url


async def fetch_video_models(request: Request, user=None):
    headers = {
        key: value
        for key, value in get_video_headers(request, user).items()
        if key != "Content-Type"
    }

    response = await asyncio.to_thread(
        requests.get,
        get_video_endpoint_url(request, "/models"),
        headers=headers,
        timeout=60,
    )

    payload = response.json()
    if not response.ok:
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.DEFAULT(get_provider_error_message(payload, response.text)),
        )

    models = payload.get("data") if isinstance(payload, dict) else payload
    return filter_video_models(models if isinstance(models, list) else [])


async def create_openai_video_task(
    request: Request, payload: dict, user=None
) -> dict:
    response = await asyncio.to_thread(
        requests.post,
        get_video_endpoint_url(request, "/video/create"),
        json=payload,
        headers=get_video_headers(request, user),
        timeout=120,
    )

    try:
        response_payload = response.json()
    except Exception:
        response_payload = None

    if not response.ok or normalize_video_task_status(response_payload) == "error":
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.DEFAULT(
                get_provider_error_message(response_payload, response.text)
            ),
        )

    return response_payload


async def query_openai_video_task(request: Request, task_id: str, user=None) -> dict:
    headers = {
        key: value
        for key, value in get_video_headers(request, user).items()
        if key != "Content-Type"
    }

    response = await asyncio.to_thread(
        requests.get,
        get_video_endpoint_url(request, "/video/query", {"id": task_id}),
        headers=headers,
        timeout=60,
    )

    try:
        response_payload = response.json()
    except Exception:
        response_payload = None

    if not response.ok and normalize_video_task_status(response_payload) != "processing":
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.DEFAULT(
                get_provider_error_message(response_payload, response.text)
            ),
        )

    return response_payload


async def wait_for_video_task_result(
    request: Request, task_id: str, user=None
) -> dict:
    deadline = time.monotonic() + VIDEO_TASK_TIMEOUT_SECONDS

    while time.monotonic() < deadline:
        payload = await query_openai_video_task(request, task_id, user=user)
        normalized_status = normalize_video_task_status(payload)

        if normalized_status == "completed":
            return payload

        if normalized_status == "error":
            raise HTTPException(
                status_code=400,
                detail=ERROR_MESSAGES.DEFAULT(get_provider_error_message(payload)),
            )

        await asyncio.sleep(VIDEO_TASK_POLL_INTERVAL_SECONDS)

    raise HTTPException(
        status_code=504,
        detail=ERROR_MESSAGES.DEFAULT("Video generation timed out"),
    )


@router.get("/config", response_model=VideosConfig)
async def get_config(request: Request, user=Depends(get_admin_user)):
    return {
        "ENABLE_VIDEO_GENERATION": request.app.state.config.ENABLE_VIDEO_GENERATION,
        "VIDEO_GENERATION_ENGINE": request.app.state.config.VIDEO_GENERATION_ENGINE,
        "VIDEO_GENERATION_MODEL": request.app.state.config.VIDEO_GENERATION_MODEL,
        "VIDEO_GENERATION_DURATION": request.app.state.config.VIDEO_GENERATION_DURATION,
        "VIDEOS_OPENAI_API_BASE_URL": request.app.state.config.VIDEOS_OPENAI_API_BASE_URL,
        "VIDEOS_OPENAI_API_KEY": request.app.state.config.VIDEOS_OPENAI_API_KEY,
        "VIDEOS_OPENAI_API_VERSION": request.app.state.config.VIDEOS_OPENAI_API_VERSION,
        "VIDEOS_OPENAI_API_PARAMS": request.app.state.config.VIDEOS_OPENAI_API_PARAMS,
    }


@router.post("/config/update")
async def update_config(
    request: Request, form_data: VideosConfig, user=Depends(get_admin_user)
):
    if form_data.VIDEO_GENERATION_DURATION <= 0:
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.INCORRECT_FORMAT("  (e.g., 5)."),
        )

    request.app.state.config.ENABLE_VIDEO_GENERATION = form_data.ENABLE_VIDEO_GENERATION
    request.app.state.config.VIDEO_GENERATION_ENGINE = form_data.VIDEO_GENERATION_ENGINE
    request.app.state.config.VIDEO_GENERATION_MODEL = form_data.VIDEO_GENERATION_MODEL
    request.app.state.config.VIDEO_GENERATION_DURATION = form_data.VIDEO_GENERATION_DURATION
    request.app.state.config.VIDEOS_OPENAI_API_BASE_URL = (
        form_data.VIDEOS_OPENAI_API_BASE_URL.strip("/")
    )
    request.app.state.config.VIDEOS_OPENAI_API_KEY = form_data.VIDEOS_OPENAI_API_KEY
    request.app.state.config.VIDEOS_OPENAI_API_VERSION = (
        form_data.VIDEOS_OPENAI_API_VERSION
    )
    request.app.state.config.VIDEOS_OPENAI_API_PARAMS = (
        form_data.VIDEOS_OPENAI_API_PARAMS
    )

    return await get_config(request, user)


@router.get("/models")
async def get_models(request: Request, user=Depends(get_verified_user)):
    if request.app.state.config.VIDEO_GENERATION_ENGINE != "openai":
        return []

    try:
        return await fetch_video_models(request, user=user)
    except Exception as e:
        request.app.state.config.ENABLE_VIDEO_GENERATION = False
        raise HTTPException(status_code=400, detail=ERROR_MESSAGES.DEFAULT(e))


@router.get("/tasks/{task_id}")
async def get_video_task(
    request: Request, task_id: str, user=Depends(get_verified_user)
):
    if not request.app.state.config.ENABLE_VIDEO_GENERATION:
        raise HTTPException(
            status_code=403,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    if user.role != "admin" and not has_permission(
        user.id, "features.video_generation", request.app.state.config.USER_PERMISSIONS
    ):
        raise HTTPException(
            status_code=403,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    return await query_openai_video_task(request, task_id, user=user)


@router.post("/generations")
async def generate_videos(
    request: Request, form_data: CreateVideoForm, user=Depends(get_verified_user)
):
    if not request.app.state.config.ENABLE_VIDEO_GENERATION:
        raise HTTPException(
            status_code=403,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    if user.role != "admin" and not has_permission(
        user.id, "features.video_generation", request.app.state.config.USER_PERMISSIONS
    ):
        raise HTTPException(
            status_code=403,
            detail=ERROR_MESSAGES.ACCESS_PROHIBITED,
        )

    return await video_generations(request, form_data, user=user)


async def video_generations(
    request: Request,
    form_data: CreateVideoForm,
    metadata: Optional[dict] = None,
    user=None,
):
    metadata = metadata or {}

    model = form_data.model or get_video_model(request)
    images = get_reference_images(form_data)
    if len(images) > 1:
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.DEFAULT("当前仅支持一张参考图片生成视频"),
        )

    payload = build_openai_video_payload(
        model=model,
        prompt=form_data.prompt,
        duration=form_data.duration
        or request.app.state.config.VIDEO_GENERATION_DURATION
        or 5,
        images=images,
        extra_params=request.app.state.config.VIDEOS_OPENAI_API_PARAMS or {},
    )

    task = await create_openai_video_task(request, payload, user=user)
    task_id = task.get("id") or task.get("task_id")
    if not task_id:
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.DEFAULT("Video task id was not returned"),
        )

    task_result = await wait_for_video_task_result(request, task_id, user=user)
    video_url = extract_video_result_url(task_result)
    if not video_url:
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.DEFAULT("Video result URL was not returned"),
        )

    headers = {
        key: value
        for key, value in get_video_headers(request, user).items()
        if key != "Content-Type"
    }
    video_data, content_type = get_video_data(video_url, headers=headers)
    if not video_data or not content_type:
        raise HTTPException(
            status_code=400,
            detail=ERROR_MESSAGES.DEFAULT("Unable to download generated video"),
        )

    _, url = upload_video(
        request,
        video_data,
        content_type,
        {
            **payload,
            **metadata,
            "task_id": task_id,
            "source_url": video_url,
        },
        user,
    )
    return [{"url": url}]
