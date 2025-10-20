<script lang="ts">
	import { Code2 } from 'lucide-svelte';
	import { onMount } from 'svelte';

	let { sqlQuery }: { sqlQuery: string } = $props();

	let hideTimeout: ReturnType<typeof setTimeout> | null = null;
	let badgeElement: HTMLDivElement | null = $state(null);
	let tooltipElement: HTMLDivElement | null = null;

	onMount(() => {
		return () => {
			// Cleanup: remove tooltip from body on unmount
			if (tooltipElement && document.body.contains(tooltipElement)) {
				document.body.removeChild(tooltipElement);
				tooltipElement = null;
			}
		};
	});

	function createTooltipElement(): HTMLDivElement {
		const tooltip = document.createElement('div');
		tooltip.setAttribute('role', 'tooltip');
		tooltip.style.position = 'fixed';
		tooltip.style.zIndex = '9999';
		tooltip.style.width = 'max-content';
		tooltip.style.maxWidth = '28rem'; // max-w-md
		tooltip.className =
			'rounded-lg border border-blue-200 bg-white p-3 shadow-xl dark:border-blue-800 dark:bg-gray-900';

		const title = document.createElement('div');
		title.className = 'mb-1 text-xs font-semibold text-blue-700 dark:text-blue-300';
		title.textContent = 'Requête SQL générée :';

		const pre = document.createElement('pre');
		pre.className =
			'overflow-x-auto whitespace-pre-wrap break-all text-xs font-mono text-gray-700 dark:text-gray-300 select-text cursor-text';
		pre.style.maxHeight = '150px';
		pre.textContent = sqlQuery;

		tooltip.appendChild(title);
		tooltip.appendChild(pre);

		// Handle mouse events on tooltip
		tooltip.addEventListener('mouseenter', handleTooltipMouseEnter);
		tooltip.addEventListener('mouseleave', handleTooltipMouseLeave);

		return tooltip;
	}

	function updateTooltipPosition(tooltip: HTMLDivElement) {
		if (!badgeElement) return;

		const rect = badgeElement.getBoundingClientRect();
		const tooltipWidth = 400; // max-w-md approximativement
		const tooltipHeight = 150; // estimation

		let left = rect.left;
		let top = rect.bottom + 8; // 8px de marge

		// Vérifier si le tooltip dépasse à droite
		if (left + tooltipWidth > window.innerWidth) {
			left = window.innerWidth - tooltipWidth - 16;
		}

		// Si pas assez de place en bas, afficher au-dessus
		if (top + tooltipHeight > window.innerHeight) {
			top = rect.top - tooltipHeight - 8;
		}

		// S'assurer que left n'est pas négatif
		if (left < 16) {
			left = 16;
		}

		tooltip.style.top = `${top}px`;
		tooltip.style.left = `${left}px`;
	}

	function showTooltip() {
		if (!tooltipElement) {
			tooltipElement = createTooltipElement();
			updateTooltipPosition(tooltipElement);
			document.body.appendChild(tooltipElement);
		}
	}

	function hideTooltip() {
		if (tooltipElement && document.body.contains(tooltipElement)) {
			document.body.removeChild(tooltipElement);
			tooltipElement = null;
		}
	}

	function handleMouseEnter() {
		if (hideTimeout) {
			clearTimeout(hideTimeout);
			hideTimeout = null;
		}
		showTooltip();
	}

	function handleMouseLeave() {
		hideTimeout = setTimeout(() => {
			hideTooltip();
		}, 100);
	}

	function handleTooltipMouseEnter() {
		if (hideTimeout) {
			clearTimeout(hideTimeout);
			hideTimeout = null;
		}
	}

	function handleTooltipMouseLeave() {
		hideTimeout = setTimeout(() => {
			hideTooltip();
		}, 100);
	}
</script>

{#if sqlQuery}
	<div class="inline-block">
		<!-- Badge - Le tooltip est créé manuellement en JS pour éviter le MutationObserver -->
		<div
			bind:this={badgeElement}
			role="img"
			aria-label="Badge SQL avec requête"
			onmouseenter={handleMouseEnter}
			onmouseleave={handleMouseLeave}
			class="inline-flex cursor-default items-center gap-1.5 rounded-md bg-blue-100 px-2 py-1 font-mono text-xs text-blue-800 transition-colors hover:bg-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:hover:bg-blue-900/50"
		>
			<Code2 size={12} />
			<span>SQL</span>
		</div>
	</div>
{/if}
