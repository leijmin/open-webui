<script lang="ts">
	import { getOllamaVersion } from '$lib/apis/ollama';
	import { WEBUI_BUILD_HASH, WEBUI_VERSION } from '$lib/constants';
	import { WEBUI_NAME } from '$lib/stores';
	import { onMount, getContext } from 'svelte';

	import Tooltip from '$lib/components/common/Tooltip.svelte';

	const i18n = getContext('i18n');

	let ollamaVersion = '';

	onMount(async () => {
		ollamaVersion = await getOllamaVersion(localStorage.token).catch(() => {
			return '';
		});
	});
</script>

<div id="tab-about" class="flex flex-col h-full justify-between space-y-3 text-sm mb-6">
	<div class="space-y-4 overflow-y-scroll max-h-[28rem] md:max-h-full">
		<div>
			<div class="mb-2.5 text-sm font-medium">{$i18n.t('站点信息')}</div>

			<div class="rounded-2xl bg-gray-50 p-4 dark:bg-gray-900/60">
				<div class="text-base font-medium text-gray-900 dark:text-white">{$WEBUI_NAME}</div>
				<div class="mt-1 text-xs text-gray-500 dark:text-gray-400">
					{$i18n.t('胡椒文旅内部使用版本')}
				</div>

				<div class="mt-4 space-y-2 text-xs text-gray-700 dark:text-gray-200">
					<div class="flex items-center justify-between gap-4">
						<span>{$i18n.t('当前版本')}</span>
						<Tooltip content={WEBUI_BUILD_HASH}>
							<span class="font-medium">v{WEBUI_VERSION}</span>
						</Tooltip>
					</div>

					{#if ollamaVersion}
						<div class="flex items-center justify-between gap-4">
							<span>{$i18n.t('模型服务版本')}</span>
							<span class="font-medium">{ollamaVersion}</span>
						</div>
					{/if}
				</div>
			</div>
		</div>

		<div class="rounded-2xl border border-gray-100 p-4 text-xs text-gray-500 dark:border-gray-800 dark:text-gray-400">
			{$i18n.t('如需调整站点功能、账号权限或接入配置，请联系系统管理员。')}
		</div>
	</div>
</div>
