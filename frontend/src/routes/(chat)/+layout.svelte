<script lang="ts">
	import { initTokenManagement, cleanupTokenManagement } from '$lib/hooks/useApiKey';
	import { onMount, onDestroy } from 'svelte';

	let { children } = $props();

	// Initialize token management on mount
	onMount(() => {
		initTokenManagement();
	});

	// Cleanup on destroy
	onDestroy(() => {
		cleanupTokenManagement();
	});
</script>

{@render children?.()}
