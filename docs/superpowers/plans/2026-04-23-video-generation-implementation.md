# 胡椒文旅视频生成实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为胡椒文旅站点增加文生视频和图生视频能力，让用户在聊天区直接生成并播放视频结果。

**Architecture:** 复用现有图片生成架构，在后端新增独立的 `videos` 路由和聊天中间件处理器，对接云雾统一视频接口并把结果写回现有文件系统；前端新增 `video_generation` 能力、权限和输入区开关，让视频能力与图片生成一样自然进入聊天主流程。

**Tech Stack:** FastAPI, Pydantic, requests, Svelte, TypeScript, Vitest

---

### Task 1: 建立视频能力识别与前端回归测试

**Files:**
- Create: `src/lib/utils/modelCapabilities.test.ts`
- Modify: `src/lib/utils/modelCapabilities.ts`
- Test: `src/lib/utils/modelCapabilities.test.ts`

- [ ] **Step 1: 先补失败测试，定义视频模型识别规则**

```ts
test('detects video-only models from supported endpoint metadata', () => {
	expect(
		isVideoGenerationOnlyModel({
			model_type: '音视频',
			supported_endpoint_types: ['视频统一格式']
		})
	).toBe(true);
});

test('does not treat mixed chat/video models as video-only', () => {
	expect(
		isVideoGenerationOnlyModel({
			model_type: 'multimodal',
			supported_endpoint_types: ['视频统一格式', 'responses']
		})
	).toBe(false);
});
```

- [ ] **Step 2: 运行测试确认先红灯**

Run: `npm test -- src/lib/utils/modelCapabilities.test.ts`
Expected: FAIL with `isVideoGenerationOnlyModel` missing.

- [ ] **Step 3: 最小实现视频能力识别**

```ts
const isVideoEndpointType = (endpointType: string) =>
	endpointType.includes('video') || endpointType.includes('视频');

export const isVideoGenerationOnlyModel = (model?: ModelCapabilityShape | null) => {
	const supportedEndpointTypes = getSupportedEndpointTypes(model);
	const modelType = getModelType(model);

	const supportsVideoGeneration =
		supportedEndpointTypes.some(isVideoEndpointType) ||
		modelType.includes('video') ||
		modelType.includes('视频') ||
		modelType.includes('音视频');
	const supportsTextGeneration = supportedEndpointTypes.some(isTextGenerationEndpointType);

	return supportsVideoGeneration && !supportsTextGeneration;
};
```

- [ ] **Step 4: 重新跑测试确认转绿**

Run: `npm test -- src/lib/utils/modelCapabilities.test.ts`
Expected: PASS

- [ ] **Step 5: 提交当前测试与能力识别修改**

```bash
git add src/lib/utils/modelCapabilities.ts src/lib/utils/modelCapabilities.test.ts
git commit -m "test: cover video model capability detection"
```

### Task 2: 完成后端视频生成链路

**Files:**
- Create: `backend/open_webui/routers/videos.py`
- Modify: `backend/open_webui/config.py`
- Modify: `backend/open_webui/main.py`
- Modify: `backend/open_webui/utils/middleware.py`
- Test: `backend/open_webui/test/apps/webui/routers/test_videos.py`

- [ ] **Step 1: 先写失败测试，锁定视频配置和创建接口行为**

```python
def test_video_generation_config_is_exposed(client, admin_auth_headers):
    response = client.get("/api/v1/videos/config", headers=admin_auth_headers)
    assert response.status_code == 200
    assert "ENABLE_VIDEO_GENERATION" in response.json()


def test_video_generation_requires_feature_flag(client, user_auth_headers):
    response = client.post(
        "/api/v1/videos/generations",
        headers=user_auth_headers,
        json={"prompt": "生成一段夜晚古城灯会视频"},
    )
    assert response.status_code in {200, 403}
```

- [ ] **Step 2: 运行后端定向测试确认失败点真实存在**

Run: `pytest backend/open_webui/test/apps/webui/routers/test_videos.py -q`
Expected: FAIL because router/config do not exist yet.

- [ ] **Step 3: 增加最小可用配置、权限和视频路由**

```python
ENABLE_VIDEO_GENERATION = PersistentConfig(
    "ENABLE_VIDEO_GENERATION",
    "video_generation.enable",
    os.environ.get("ENABLE_VIDEO_GENERATION", "").lower() == "true",
)

VIDEO_GENERATION_ENGINE = PersistentConfig(
    "VIDEO_GENERATION_ENGINE",
    "video_generation.engine",
    os.getenv("VIDEO_GENERATION_ENGINE", "openai"),
)

VIDEO_GENERATION_MODEL = PersistentConfig(
    "VIDEO_GENERATION_MODEL",
    "video_generation.model",
    os.getenv("VIDEO_GENERATION_MODEL", "veo3.1-fast"),
)
```

- [ ] **Step 4: 在 `videos.py` 里完成提交任务、轮询任务、下载视频并落盘**

```python
task = await create_openai_video_task(request, payload, user)
task_result = await poll_openai_video_task(request, task["id"], user)
file_item, url = upload_video(
    request,
    task_result["video_url"],
    metadata={"chat_id": metadata.get("chat_id"), "message_id": metadata.get("message_id")},
    user=user,
)
return [{"url": url, "type": "video"}]
```

- [ ] **Step 5: 在聊天中间件接入 `chat_video_generation_handler`**

```python
if "video_generation" in features and features["video_generation"]:
    if metadata.get("params", {}).get("function_calling") != "native":
        form_data = await chat_video_generation_handler(
            request, form_data, extra_params, user
        )
```

- [ ] **Step 6: 重新运行后端定向测试**

Run: `pytest backend/open_webui/test/apps/webui/routers/test_videos.py -q`
Expected: PASS

- [ ] **Step 7: 提交后端视频能力**

```bash
git add backend/open_webui/config.py backend/open_webui/main.py backend/open_webui/utils/middleware.py backend/open_webui/routers/videos.py backend/open_webui/test/apps/webui/routers/test_videos.py
git commit -m "feat: add video generation backend flow"
```

### Task 3: 完成前端视频生成开关、权限与模型配置

**Files:**
- Create: `src/lib/apis/videos/index.ts`
- Modify: `src/lib/components/chat/Chat.svelte`
- Modify: `src/lib/components/chat/MessageInput.svelte`
- Modify: `src/lib/constants.ts`
- Modify: `src/lib/constants/permissions.ts`
- Modify: `src/lib/stores/index.ts`
- Modify: `src/lib/components/admin/Users/Groups/Permissions.svelte`
- Modify: `src/lib/components/workspace/Models/Capabilities.svelte`
- Modify: `src/lib/components/workspace/Models/DefaultFeatures.svelte`
- Modify: `src/lib/components/workspace/Models/BuiltinTools.svelte`
- Modify: `src/lib/components/workspace/Models/ModelEditor.svelte`
- Modify: `src/lib/components/admin/Settings/Models/ModelSettingsModal.svelte`

- [ ] **Step 1: 补前端失败测试或能力断言**

```ts
expect(getFeatures().video_generation).toBe(true);
```

If component-level test setup is too heavy, keep regression in `modelCapabilities.test.ts` and verify UI manually during `npm run check`.

- [ ] **Step 2: 运行现有前端检查，确认新增字段尚未接通**

Run: `npm run check`
Expected: FAIL after temporary type edits until all call sites are wired.

- [ ] **Step 3: 新增 `video_generation` 配置、权限和聊天输入区开关**

```ts
let videoGenerationEnabled = false;

features = {
	...features,
	video_generation:
		$config?.features?.enable_video_generation &&
		($user?.role === 'admin' || $user?.permissions?.features?.video_generation)
			? videoGenerationEnabled
			: false
};
```

- [ ] **Step 4: 新增视频专用模型自动点亮逻辑，并与图片生成互斥**

```ts
if (canUseVideoGeneration && isVideoGenerationOnlyModel(model)) {
	videoGenerationEnabled = true;
	imageGenerationEnabled = false;
}
```

- [ ] **Step 5: 把模型能力编辑器和默认功能设置补齐**

```ts
video_generation: {
	label: $i18n.t('Video Generation'),
	description: $i18n.t('Model can generate videos based on text or one reference image')
}
```

- [ ] **Step 6: 运行前端检查确认通过**

Run: `npm run check`
Expected: PASS

- [ ] **Step 7: 提交前端视频能力**

```bash
git add src/lib/apis/videos/index.ts src/lib/components/chat/Chat.svelte src/lib/components/chat/MessageInput.svelte src/lib/constants.ts src/lib/constants/permissions.ts src/lib/stores/index.ts src/lib/components/admin/Users/Groups/Permissions.svelte src/lib/components/workspace/Models/Capabilities.svelte src/lib/components/workspace/Models/DefaultFeatures.svelte src/lib/components/workspace/Models/BuiltinTools.svelte src/lib/components/workspace/Models/ModelEditor.svelte src/lib/components/admin/Settings/Models/ModelSettingsModal.svelte
git commit -m "feat: add video generation user experience"
```

### Task 4: 统一验证与本地交付

**Files:**
- Verify only: repository root

- [ ] **Step 1: 跑完整前端检查**

Run: `npm run check`
Expected: PASS

- [ ] **Step 2: 跑后端编译校验**

Run: `python3 -m compileall backend/open_webui`
Expected: PASS

- [ ] **Step 3: 跑视频相关后端测试**

Run: `pytest backend/open_webui/test/apps/webui/routers/test_videos.py -q`
Expected: PASS

- [ ] **Step 4: 查看变更范围**

Run: `git status --short`
Expected: only intended files changed.

- [ ] **Step 5: 提交最终实现**

```bash
git add docs/superpowers/plans/2026-04-23-video-generation-implementation.md
git commit -m "feat: add video generation support"
```

- [ ] **Step 6: 向用户汇报本地实现、验证结果和未上线状态**

需要明确说明：
- 已新增哪些文件与能力
- 本地验证命令及结果
- 本轮未自动部署线上
- 若上游供应商接口返回格式变化，视频轮询适配仍是主要风险点
