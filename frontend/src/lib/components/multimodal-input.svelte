<script lang="ts">
	import type { Chat } from '@ai-sdk/svelte';
	import { Textarea } from './ui/textarea';
	import { cn } from '$lib/utils/shadcn';
	import { onMount } from 'svelte';
	import { LocalStorage } from '$lib/hooks/local-storage.svelte';
	import { innerWidth } from 'svelte/reactivity/window';
	import { toast } from 'svelte-sonner';
	import { Button } from './ui/button';
	import StopIcon from './icons/stop.svelte';
	import ArrowUpIcon from './icons/arrow-up.svelte';

	let {
		chatClient,
		messageCount = 0,
		MAX_MESSAGES = 20,
		class: c
	}: {
		chatClient: Chat;
		messageCount?: number;
		MAX_MESSAGES?: number;
		class?: string;
	} = $props();

	// Avertissement si proche de la limite (80% de la limite)
	const isNearLimit = $derived(messageCount >= MAX_MESSAGES * 0.8);

	let _mounted = $state(false);
	let textareaRef = $state<HTMLTextAreaElement | null>(null);
	const storedInput = new LocalStorage('input', '');
	const loading = $derived(chatClient.status === 'streaming' || chatClient.status === 'submitted');

	const adjustHeight = () => {
		if (textareaRef) {
			textareaRef.style.height = 'auto';
			textareaRef.style.height = `${textareaRef.scrollHeight + 2}px`;
		}
	};

	const resetHeight = () => {
		if (textareaRef) {
			textareaRef.style.height = 'auto';
			textareaRef.style.height = '98px';
		}
	};

	function setInput(value: string) {
		chatClient.input = value;
		adjustHeight();
	}

	async function submitForm(event?: Event) {
		await chatClient.handleSubmit(event, {
			experimental_attachments: []
		});

		resetHeight();

		if (innerWidth.current && innerWidth.current > 768) {
			textareaRef?.focus();
		}
	}

	onMount(() => {
		chatClient.input = storedInput.value;
		adjustHeight();
		_mounted = true;
	});
	$effect.pre(() => {
		storedInput.value = chatClient.input;
	});
</script>

<div class="relative flex w-full flex-col gap-4">
	{#if isNearLimit}
		<div
			class="rounded-lg bg-yellow-50 px-3 py-2 text-xs text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-200"
		>
			⚠️ {messageCount}/{MAX_MESSAGES} messages - La limite approche
		</div>
	{/if}

	<Textarea
		bind:ref={textareaRef}
		placeholder="Envoyer un message..."
		bind:value={() => chatClient.input, setInput}
		class={cn(
			'max-h-[calc(75dvh)] min-h-[24px] resize-none overflow-hidden rounded-2xl bg-muted pb-10 !text-base dark:border-zinc-700',
			c
		)}
		rows={2}
		autofocus
		onkeydown={(event) => {
			if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
				event.preventDefault();

				if (loading) {
					toast.error('Veuillez attendre que le modèle termine sa réponse !');
				} else {
					submitForm();
				}
			}
		}}
	/>

	<div class="absolute bottom-0 right-0 flex w-fit flex-row justify-end p-2">
		{#if loading}
			{@render stopButton()}
		{:else}
			{@render sendButton()}
		{/if}
	</div>
</div>

{#snippet stopButton()}
	<Button
		class="h-fit rounded-full border p-1.5 dark:border-zinc-600"
		onclick={(event) => {
			event.preventDefault();
			chatClient.stop();
			chatClient.messages = chatClient.messages;
		}}
	>
		<StopIcon size={14} />
	</Button>
{/snippet}

{#snippet sendButton()}
	<Button
		class="h-fit rounded-full border p-1.5 dark:border-zinc-600"
		onclick={(event) => {
			event.preventDefault();
			submitForm();
		}}
		disabled={chatClient.input.length === 0}
	>
		<ArrowUpIcon size={14} />
	</Button>
{/snippet}
