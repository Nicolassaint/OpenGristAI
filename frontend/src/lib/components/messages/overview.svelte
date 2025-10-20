<script lang="ts">
	import { apiKey } from '$lib/hooks/useApiKey';
	import { fade } from 'svelte/transition';
</script>

<div class="mx-auto mt-12 max-w-3xl md:mt-20" in:fade={{ duration: 200 }}>
	<div class="flex max-w-xl flex-col gap-8 rounded-xl p-6 text-center leading-relaxed">
		{#if !$apiKey}
			<p class="flex flex-row items-center justify-center gap-4">
				<li>1. Le widget a-t-il accès à la table?</li>
				<li>2. La clé API est-elle renseignée?</li>
			</p>
		{:else}
			<div class="flex flex-col gap-6">
				<p class="text-2xl font-medium">Grist ♥️ AI</p>

				<div
					class="rounded-lg border border-gray-200/60 bg-gray-50/50 p-6 shadow-sm dark:border-gray-700/60 dark:bg-gray-800/30"
				>
					<div class="space-y-4 text-left text-sm text-gray-700 dark:text-gray-300">
						<p class="text-base font-medium text-gray-900 dark:text-gray-100">
							Bonjour, je suis l'assistant IA de Grist.
						</p>

						<p class="font-medium text-gray-800 dark:text-gray-200">
							Voici ce que je peux faire pour vous :
						</p>

						<ul class="space-y-3 pl-2">
							<li class="flex gap-3">
								<span class="mt-0.5 flex-shrink-0 text-green-600 dark:text-green-400">✓</span>
								<span
									>Analyser vos données et répondre à vos questions (requêtes SQL automatiques)</span
								>
							</li>
							<li class="flex gap-3">
								<span class="mt-0.5 flex-shrink-0 text-green-600 dark:text-green-400">✓</span>
								<span>Créer et structurer des tables avec leurs colonnes</span>
							</li>
							<li class="flex gap-3">
								<span class="mt-0.5 flex-shrink-0 text-green-600 dark:text-green-400">✓</span>
								<span>Ajouter, modifier ou supprimer des enregistrements</span>
							</li>
							<li class="flex gap-3">
								<span class="mt-0.5 flex-shrink-0 text-red-600 dark:text-red-400">✗</span>
								<span>Je ne peux pas gérer les pages, widgets, graphiques ou formules</span>
							</li>
							<li class="flex gap-3">
								<span class="mt-0.5 flex-shrink-0 text-blue-600 dark:text-blue-400">💬</span>
								<span
									>Parlez-moi naturellement : "Crée une table Clients avec nom, email et téléphone"</span
								>
							</li>
						</ul>

						<div class="border-t border-gray-200 pt-3 dark:border-gray-600">
							<p class="text-xs text-gray-600 dark:text-gray-400">
								🔒 Vos données ne sont pas stockées. L'IA fonctionne sur une infrastructure
								SecNumCloud française.
							</p>
						</div>
					</div>
				</div>
			</div>
		{/if}
	</div>
</div>
