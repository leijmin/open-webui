<script lang="ts">
	import { goto } from '$app/navigation';
	import { user } from '$lib/stores';
	import { getWorkspaceLandingPath } from '$lib/utils/workspaceNavigation';
	import { onMount } from 'svelte';

	onMount(() => {
		goto(getWorkspaceLandingPath($user));
	});
</script>
