<script lang="ts">
	import ThinkingMessage from './messages/thinking-message.svelte';
	import Overview from './messages/overview.svelte';
	import { onMount } from 'svelte';
	import PreviewMessage from './messages/preview-message.svelte';
	import type { UIMessage } from '@ai-sdk/svelte';
	import { getLock } from '$lib/hooks/lock';

	interface MessageMetadata {
		sql_query?: string;
		agent_used?: string;
		data_analyzed?: boolean;
		[key: string]: unknown;
	}

	interface ConfirmationPreview {
		description: string;
		affected_count?: number;
		warnings?: string[];
		[key: string]: unknown;
	}

	interface PendingConfirmation {
		confirmation_id: string;
		preview: ConfirmationPreview;
		[key: string]: unknown;
	}

	let containerRef = $state<HTMLDivElement | null>(null);
	let endRef = $state<HTMLDivElement | null>(null);

	let {
		readonly,
		loading,
		messages,
		messageMetadata = {},
		pendingConfirmation = null,
		onConfirmation = null
	}: {
		readonly: boolean;
		loading: boolean;
		messages: UIMessage[];
		messageMetadata?: Record<string, MessageMetadata>;
		pendingConfirmation?: PendingConfirmation | null;
		onConfirmation?: ((approved: boolean) => void) | null;
	} = $props();

	let mounted = $state(false);
	onMount(() => {
		mounted = true;
	});

	const scrollLock = getLock('messages-scroll');

	// Scroll immediately when messages change - but only if content overflows
	$effect(() => {
		if (!containerRef || scrollLock.locked) return;
		void messages.length; // Track changes for reactivity

		// Only scroll if content is actually overflowing
		if (containerRef.scrollHeight > containerRef.clientHeight) {
			containerRef.scrollTop = containerRef.scrollHeight;
		}
	});

	// Keep observer for streaming content changes
	$effect(() => {
		if (!(containerRef && endRef)) return;

		const observer = new MutationObserver(() => {
			if (!containerRef || scrollLock.locked) return;

			// Only scroll if content is actually overflowing
			if (containerRef.scrollHeight > containerRef.clientHeight) {
				containerRef.scrollTop = containerRef.scrollHeight;
			}
		});

		observer.observe(containerRef, {
			subtree: true,
			characterData: true,
			childList: true
		});

		return () => observer.disconnect();
	});
</script>

<div
	bind:this={containerRef}
	class="flex min-w-0 flex-1 flex-col gap-6 overflow-y-scroll pt-4 md:pt-12"
>
	{#if mounted && messages.length === 0}
		<Overview />
	{/if}

	{#each messages as message, index (message.id)}
		<PreviewMessage
			{message}
			{readonly}
			{loading}
			metadata={messageMetadata[message.id]}
			showConfirmation={index === messages.length - 1 &&
				message.role === 'assistant' &&
				pendingConfirmation !== null}
			confirmation={pendingConfirmation}
			{onConfirmation}
		/>
	{/each}

	{#if loading && messages.length > 0 && messages[messages.length - 1].role === 'user'}
		<ThinkingMessage />
	{/if}

	<div bind:this={endRef} class="min-h-[24px] min-w-[24px] shrink-0"></div>
</div>
