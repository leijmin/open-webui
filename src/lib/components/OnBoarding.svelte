<script>
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import { WEBUI_BASE_URL } from '$lib/constants';

	export let show = true;
	export let getStartedHandler = () => {};
</script>

{#if show}
	<div class="relative w-full h-screen max-h-[100dvh] overflow-hidden bg-white text-gray-900">
		<div class="fixed left-4 top-4 sm:left-6 sm:top-6 z-50">
			<img
				crossorigin="anonymous"
				src="/logo.png"
				class="h-9 w-auto rounded-md object-contain"
				alt="胡椒文旅"
			/>
		</div>

		<div class="relative z-10 flex h-full items-center justify-center px-6">
			<div
				class="w-full max-w-xl rounded-2xl border border-gray-200 bg-white px-6 py-10 text-center shadow-[0_10px_30px_rgba(0,0,0,0.06)]"
			>
				<div class="text-3xl font-semibold tracking-tight sm:text-4xl">
					胡椒文旅
				</div>
				<div class="mt-3 text-base text-gray-600">
					{$i18n.t('内部智能助手，开箱即可使用。')}
				</div>

				<div class="mt-8 flex flex-wrap justify-center gap-3 text-sm text-gray-600">
					<div class="rounded-full bg-gray-100 px-4 py-2">
						{$i18n.t('资料整理')}
					</div>
					<div class="rounded-full bg-gray-100 px-4 py-2">
						{$i18n.t('文案生成')}
					</div>
					<div class="rounded-full bg-gray-100 px-4 py-2">
						{$i18n.t('日常问答')}
					</div>
				</div>

				<div class="mt-10 flex justify-center">
					<button
						aria-label={$i18n.t('立即开始')}
						class="rounded-full bg-gray-900 px-7 py-3 text-sm font-semibold text-white transition hover:bg-gray-800"
						on:click={() => {
							getStartedHandler();
						}}
					>
						{$i18n.t('立即开始')}
					</button>
				</div>
			</div>
		</div>
	</div>
{/if}
