<script lang="ts">
	import { createEventDispatcher, onDestroy, onMount } from 'svelte';
	import { getLoaderVisibilityState } from '$lib/utils/loaderVisibility';

	const dispatch = createEventDispatcher();

	let loaderElement: HTMLElement;

	let observer: IntersectionObserver | null = null;
	let isVisible = false;

	onMount(() => {
		observer = new IntersectionObserver(
			(entries) => {
				entries.forEach((entry) => {
					const state = getLoaderVisibilityState(isVisible, entry.isIntersecting);
					isVisible = state.isVisible;

					if (state.shouldDispatch) {
						dispatch('visible');
					}
				});
			},
			{
				root: null, // viewport
				rootMargin: '0px',
				threshold: 0.1 // When 10% of the loader is visible
			}
		);

		observer.observe(loaderElement);
	});

	onDestroy(() => {
		if (observer) {
			observer.disconnect();
		}
	});
</script>

<div bind:this={loaderElement}>
	<slot />
</div>
