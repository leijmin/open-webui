<script lang="ts">
	import { WEBUI_BASE_URL } from '$lib/constants';

	export let className = 'size-8';
	export let src = `${WEBUI_BASE_URL}/static/logo.jpg`;

	const defaultBrandLogo = `${WEBUI_BASE_URL}/static/logo.jpg`;
</script>

<img
	aria-hidden="true"
	src={src === ''
		? defaultBrandLogo
		: src.startsWith(WEBUI_BASE_URL) ||
			  src.startsWith('https://www.gravatar.com/avatar/') ||
			  src.startsWith('data:') ||
			  src.startsWith('/')
			? src
			: `${WEBUI_BASE_URL}/user.png`}
	class="{className} {(src === '' || src === defaultBrandLogo || src === '/static/logo.jpg')
		? 'object-contain rounded-lg bg-white p-0.5'
		: 'object-cover rounded-full'}"
	alt="profile"
	draggable="false"
/>
