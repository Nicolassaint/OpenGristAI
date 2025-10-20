<script lang="ts">
	import { cn } from '$lib/utils/shadcn';
	import type { UIMessage } from '@ai-sdk/svelte';
	import SparklesIcon from '../icons/sparkles.svelte';
	import Markdown from '../markdown/renderer.svelte';
	import SqlQueryBadge from '../sql-query-badge.svelte';
	import ConfirmationDialog from '../confirmation-dialog.svelte';

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
	}

	interface ConfirmationData {
		preview: ConfirmationPreview;
		[key: string]: unknown;
	}

	let {
		message,
		readonly: _readonly,
		loading: _loading,
		metadata,
		showConfirmation = false,
		confirmation = null,
		onConfirmation = null
	}: {
		message: UIMessage;
		readonly: boolean;
		loading: boolean;
		metadata?: MessageMetadata;
		showConfirmation?: boolean;
		confirmation?: ConfirmationData | null;
		onConfirmation?: ((approved: boolean) => void) | null;
	} = $props();

	let mode = $state<'view'>('view');
</script>

<div class="group/message mx-auto w-full max-w-3xl px-4" data-role={message.role}>
	<div
		class={cn(
			'relative flex w-full gap-4 group-data-[role=user]/message:ml-auto group-data-[role=user]/message:max-w-2xl',
			{
				'group-data-[role=user]/message:w-fit': true
			}
		)}
	>
		{#if message.role === 'assistant'}
			<div class="relative top-4 flex size-4 shrink-0 items-center justify-center bg-background">
				<div class="translate-y-px">
					<SparklesIcon size={12} />
				</div>
			</div>
		{/if}

		<div class="flex w-full flex-col gap-4">
			<!-- {#if message.experimental_attachments && message.experimental_attachments.length > 0}
				<div class="flex flex-row justify-end gap-2">
					{#each message.experimental_attachments as attachment (attachment.url)}
						<PreviewAttachment {attachment} />
					{/each}
				</div>
			{/if} -->

			{#each message.parts as part, i (`${message.id}-${i}`)}
				{@const { type } = part}
				{#if type === 'text' || !type}
					{#if mode === 'view'}
						<div class="flex flex-row items-start gap-2">
							<div
								class={cn('flex flex-col gap-4', {
									'rounded-xl bg-primary px-3 py-2 text-primary-foreground': message.role === 'user'
								})}
							>
								{#if message.role === 'assistant'}
									<!-- Backend now returns plain text instead of JSON, thanks to custom fetch -->
									<Markdown md={part.text} />

									<!-- Footer with SQL badge and timestamp aligned -->
									<div class="mt-0 flex items-center gap-2 text-xs text-gray-400/50">
										{#if metadata?.sql_query}
											<SqlQueryBadge sqlQuery={metadata.sql_query} />
										{/if}
										<div class="flex items-center gap-1">
											{#if message.createdAt}
												<span>
													{new Intl.DateTimeFormat('fr-FR', {
														timeStyle: 'short'
													}).format(new Date(message.createdAt))}
												</span>
												<span>•</span>
											{/if}
											<span>GristAI</span>
										</div>
									</div>
								{:else}
									<Markdown md={part.text} />
								{/if}
							</div>
						</div>
					{/if}
				{/if}
			{/each}

			<!-- Confirmation dialog for assistant messages -->
			{#if showConfirmation && confirmation && onConfirmation && message.role === 'assistant'}
				<ConfirmationDialog
					{confirmation}
					onConfirm={() => onConfirmation(true)}
					onReject={() => onConfirmation(false)}
				/>
			{/if}
		</div>
	</div>
</div>
