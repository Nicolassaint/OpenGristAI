<script lang="ts">
	import SparklesIcon from '$lib/components/icons/sparkles.svelte';
	import { fly } from 'svelte/transition';
</script>

<div
	class="group/message mx-auto w-full max-w-3xl px-4"
	data-role="assistant"
	in:fly={{ opacity: 0, y: 5 }}
>
	<div
		class="
      flex w-full gap-4 rounded-xl group-data-[role=user]/message:ml-auto group-data-[role=user]/message:w-fit
      group-data-[role=user]/message:max-w-2xl group-data-[role=user]/message:bg-muted group-data-[role=user]/message:px-3
      group-data-[role=user]/message:py-2
    "
	>
		<div
			class="relative flex size-4 shrink-0 items-center justify-center bg-background"
			style="margin-top: 0.1rem;"
		>
			<div>
				<SparklesIcon size={12} />
			</div>
		</div>

		<div class="flex w-full flex-col gap-2">
			<div class="flex items-center" style="margin-top: -0.125rem;">
				<span class="thinking-dots">
					<span class="dot">●</span>
					<span class="dot">●</span>
					<span class="dot">●</span>
				</span>
			</div>
		</div>
	</div>
</div>

<style>
	.thinking-dots {
		display: inline-flex;
		gap: 6px;
		font-size: 1.25rem;
		color: #6b7280;
	}

	.dot {
		animation: blink 1.4s infinite;
		opacity: 0.2;
	}

	.dot:nth-child(1) {
		animation-delay: 0s;
	}

	.dot:nth-child(2) {
		animation-delay: 0.2s;
	}

	.dot:nth-child(3) {
		animation-delay: 0.4s;
	}

	@keyframes blink {
		0%,
		20% {
			opacity: 0.2;
		}
		50% {
			opacity: 1;
		}
		100% {
			opacity: 0.2;
		}
	}
</style>
