<script lang="ts">
	import { Button } from '$lib/components/ui/button';

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
		confirmation,
		onConfirm,
		onReject
	}: {
		confirmation: ConfirmationData;
		onConfirm: () => void;
		onReject: () => void;
	} = $props();
</script>

<div
	class="mt-3 rounded-lg border border-zinc-200 bg-zinc-50 dark:border-zinc-700 dark:bg-zinc-800/50"
>
	<!-- Header -->
	<div class="border-b border-zinc-200 px-4 py-3 dark:border-zinc-700">
		<div class="flex items-center gap-2">
			<span class="text-lg">⚠️</span>
			<span class="font-medium text-zinc-900 dark:text-zinc-100">Confirmation requise</span>
		</div>
	</div>

	<!-- Content -->
	<div class="space-y-3 px-4 py-3">
		<!-- Description -->
		<p class="text-sm text-zinc-700 dark:text-zinc-300">
			{confirmation.preview.description}
		</p>

		<!-- Affected count if relevant -->
		{#if confirmation.preview.affected_count && confirmation.preview.affected_count > 0}
			<p class="text-xs text-zinc-600 dark:text-zinc-400">
				{confirmation.preview.affected_count} élément{confirmation.preview.affected_count > 1
					? 's'
					: ''} concerné{confirmation.preview.affected_count > 1 ? 's' : ''}
			</p>
		{/if}

		<!-- Warnings -->
		{#if confirmation.preview.warnings && confirmation.preview.warnings.length > 0}
			<div class="space-y-1 rounded-md bg-red-50 px-3 py-2 dark:bg-red-950/30">
				{#each confirmation.preview.warnings as warning}
					<p class="text-xs text-red-800 dark:text-red-300">{warning}</p>
				{/each}
			</div>
		{/if}
	</div>

	<!-- Actions -->
	<div class="flex gap-2 border-t border-zinc-200 px-4 py-3 dark:border-zinc-700">
		<Button
			onclick={onConfirm}
			class="flex-1 bg-zinc-900 text-zinc-50 hover:bg-zinc-800 dark:bg-zinc-100 dark:text-zinc-900 dark:hover:bg-zinc-200"
		>
			Confirmer
		</Button>
		<Button
			onclick={onReject}
			variant="outline"
			class="flex-1 border-zinc-300 text-zinc-700 hover:bg-zinc-100 dark:border-zinc-600 dark:text-zinc-300 dark:hover:bg-zinc-800"
		>
			Annuler
		</Button>
	</div>
</div>
