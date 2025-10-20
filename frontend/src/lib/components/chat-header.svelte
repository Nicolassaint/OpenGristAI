<script lang="ts">
	import { innerWidth } from 'svelte/reactivity/window';
	import { Button } from './ui/button';
	import { RotateCcw } from 'lucide-svelte';

	let { onReset }: { onReset?: () => void } = $props();
</script>

<header class="sticky top-0 flex items-center justify-between gap-2 border-b bg-background p-2">
	<div class="flex items-center gap-2">
		<img src="/bercyhub_logo.png" alt="BercyHub" class="h-8 w-auto object-contain" />
		{#if (innerWidth.current ?? 768) < 768}
			<span class="text-sm font-medium text-muted-foreground">Grist ♥️ AI</span>
		{:else}
			<span class="text-sm font-medium text-muted-foreground">Grist AI Assistant</span>
		{/if}
	</div>

	<div class="flex items-center gap-2">
		{#if onReset}
			<Button
				variant="ghost"
				size="sm"
				type="button"
				class="h-8 gap-2 px-3"
				onclick={onReset}
				title="Réinitialiser la conversation"
			>
				<RotateCcw size={16} />
				<span class="hidden sm:inline">Réinitialiser</span>
			</Button>
		{/if}
	</div>
	<!-- Token is now automatically fetched from Grist, no manual configuration needed -->
</header>
