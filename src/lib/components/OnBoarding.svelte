<script>
	import { getContext } from 'svelte';
	const i18n = getContext('i18n');

	import { WEBUI_BASE_URL } from '$lib/constants';

	export let show = true;
	export let getStartedHandler = () => {};

	function setLogoImage() {
		const logo = document.getElementById('logo');

		if (logo) {
			logo.src = `${WEBUI_BASE_URL}/static/logo.jpg`;
			logo.style.filter = '';
		}
	}

	$: if (show) {
		setLogoImage();
	}
</script>

{#if show}
	<div class="relative w-full h-screen max-h-[100dvh] overflow-hidden bg-[#4da98a] text-white">
		<div class="absolute inset-0 bg-[radial-gradient(circle_at_top,_rgba(255,255,255,0.22),_transparent_45%)]"></div>
		<div class="absolute inset-0 bg-[linear-gradient(135deg,_rgba(0,0,0,0.08),_transparent_45%,_rgba(0,0,0,0.14))]"></div>

		<div class="fixed left-6 top-6 z-50">
			<img
				id="logo"
				crossorigin="anonymous"
				src="{WEBUI_BASE_URL}/static/logo.jpg"
				class="w-16 rounded-2xl object-contain shadow-lg"
				alt="胡椒文旅"
			/>
		</div>

		<div class="relative z-10 flex h-full items-center justify-center px-6">
			<div class="w-full max-w-5xl text-center">
				<div class="mx-auto flex justify-center">
					<img
						src="{WEBUI_BASE_URL}/static/logo.jpg"
						class="w-full max-w-3xl rounded-[2rem] object-contain shadow-[0_32px_120px_rgba(0,0,0,0.18)]"
						alt="胡椒文旅"
					/>
				</div>

				<div class="mt-10 text-4xl font-secondary font-bold tracking-[0.08em] lg:text-6xl">
					胡椒文旅
				</div>
				<div class="mt-3 text-base text-white/90 lg:text-xl">
					{$i18n.t('内部智能助手，开箱即可使用。')}
				</div>

				<div class="mt-8 flex flex-wrap justify-center gap-3 text-sm text-white/90">
					<div class="rounded-full bg-white/12 px-4 py-2 backdrop-blur-sm">
						{$i18n.t('资料整理')}
					</div>
					<div class="rounded-full bg-white/12 px-4 py-2 backdrop-blur-sm">
						{$i18n.t('文案生成')}
					</div>
					<div class="rounded-full bg-white/12 px-4 py-2 backdrop-blur-sm">
						{$i18n.t('日常问答')}
					</div>
				</div>

				<div class="mt-10 flex justify-center">
					<button
						aria-label={$i18n.t('立即开始')}
						class="rounded-full bg-white px-7 py-3 text-sm font-semibold text-[#2d6f5f] shadow-lg transition hover:bg-white/90"
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
