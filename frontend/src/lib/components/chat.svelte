<script lang="ts">
	import { Chat } from '@ai-sdk/svelte';
	import { toast } from 'svelte-sonner';
	import type { UIMessage } from '@ai-sdk/svelte';
	import { onMount, untrack, tick } from 'svelte';
	import ChatHeader from './chat-header.svelte';
	import Messages from './messages.svelte';
	import MultimodalInput from './multimodal-input.svelte';

	import { PUBLIC_CHAT_URL } from '$env/static/public';
	import { apiKey, fetchGristToken } from '$lib/hooks/useApiKey';

	// Types for Grist API
	interface GristDocApi {
		getDocName: () => Promise<string>;
		[key: string]: unknown;
	}

	interface GristTable {
		getTableId: () => Promise<string>;
		[key: string]: unknown;
	}

	interface GristInteraction {
		accessLevel?: string;
		[key: string]: unknown;
	}

	interface GristAPI {
		ready: (options: { requiredAccess: string }) => Promise<void>;
		onOptions: (callback: (options: unknown, interaction: GristInteraction) => void) => void;
		getTable: () => Promise<GristTable>;
		docApi?: GristDocApi;
		[key: string]: unknown;
	}

	// Grist global is provided by Grist widget API
	const grist = (globalThis as Record<string, unknown>).grist as GristAPI;

	// Types for metadata and confirmation
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

	let {
		chat,
		readonly,
		initialMessages
	}: {
		chat: unknown | undefined;
		initialMessages: UIMessage[];
		readonly: boolean;
	} = $props();

	// Limite de messages pour préserver le contexte
	const MAX_MESSAGES = 20;

	let documentId = $state('');
	let tableId = $state('');
	let tableName = $state(''); // Human-readable table name
	let token = $state('');
	let accessLevel = $state<string>('none');
	let hasFullAccess = $derived(accessLevel === 'full');

	// Helper to save only confirmation
	function saveConfirmationToStorage() {
		if (documentId && tableId) {
			try {
				const confKey = `grist-chat-confirmation-${documentId}-${tableId}`;
				if (pendingConfirmation) {
					localStorage.setItem(confKey, JSON.stringify(pendingConfirmation));
					console.log('Saved pending confirmation to storage');
				} else {
					localStorage.removeItem(confKey);
					console.log('Cleared pending confirmation from storage');
				}
			} catch (error) {
				console.error('Error saving confirmation to localStorage:', error);
			}
		}
	}

	// Fonctions pour sauvegarder et charger les messages
	function saveMessagesToStorage() {
		if (documentId && tableId && chatClient.messages.length > 0) {
			try {
				// Build keys directly to avoid timing issues with $derived
				const msgKey = `grist-chat-${documentId}-${tableId}`;
				const metaKey = `grist-chat-metadata-${documentId}-${tableId}`;

				localStorage.setItem(msgKey, JSON.stringify(chatClient.messages));
				localStorage.setItem(metaKey, JSON.stringify(messageMetadata));
			} catch (error) {
				console.error('Error saving messages to localStorage:', error);
			}
		}
	}

	function loadMessagesFromStorage(): UIMessage[] {
		if (documentId && tableId) {
			try {
				// Build keys directly to avoid timing issues with $derived
				const msgKey = `grist-chat-${documentId}-${tableId}`;
				const metaKey = `grist-chat-metadata-${documentId}-${tableId}`;
				const confKey = `grist-chat-confirmation-${documentId}-${tableId}`;

				const stored = localStorage.getItem(msgKey);
				const storedMetadata = localStorage.getItem(metaKey);
				const storedConfirmation = localStorage.getItem(confKey);

				if (storedMetadata) {
					messageMetadata = JSON.parse(storedMetadata);
				}

				// Restore pending confirmation if it exists
				if (storedConfirmation) {
					pendingConfirmation = JSON.parse(storedConfirmation);
					console.log('Restored pending confirmation from storage:', pendingConfirmation);
				}

				if (stored) {
					const messages = JSON.parse(stored);
					console.log(`Loaded ${messages.length} messages from storage`);
					return messages;
				}
			} catch (error) {
				console.error('Error loading messages from localStorage:', error);
			}
		}
		return [];
	}

	function clearMessagesFromStorage() {
		if (documentId && tableId) {
			try {
				// Build keys directly to avoid timing issues with $derived
				const msgKey = `grist-chat-${documentId}-${tableId}`;
				const metaKey = `grist-chat-metadata-${documentId}-${tableId}`;
				const confKey = `grist-chat-confirmation-${documentId}-${tableId}`;

				localStorage.removeItem(msgKey);
				localStorage.removeItem(metaKey);
				localStorage.removeItem(confKey);
			} catch (error) {
				console.error('Error clearing messages from localStorage:', error);
			}
		}
	}

	// Function to reset the conversation
	async function resetConversation() {
		chatClient.messages = [];
		messageMetadata = {};
		lastResponseMetadata = null;
		pendingConfirmation = null;
		clearMessagesFromStorage();
		await syncMessages();
		toast.success('Conversation réinitialisée');
	}

	// Function to handle confirmation decision
	async function handleConfirmation(approved: boolean) {
		if (!pendingConfirmation) return;

		try {
			const response = await fetch(`${PUBLIC_CHAT_URL}/confirm`, {
				method: 'POST',
				headers: {
					'x-api-key': token,
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({
					confirmation_id: pendingConfirmation.confirmation_id,
					approved,
					reason: approved ? null : 'Utilisateur a rejeté'
				})
			});

			if (!response.ok) {
				const errorText = await response.text();
				throw new Error(`Erreur: ${response.status} - ${errorText}`);
			}

			const result = await response.json();

			// Save confirmation for message formatting before clearing
			const savedConfirmation = pendingConfirmation;

			// Clear pending confirmation
			pendingConfirmation = null;
			saveConfirmationToStorage(); // Explicitly save (will remove from storage)

			if (approved && result.status === 'approved') {
				// Format a nice user-friendly message
				let message = '✓ ';

				// Extract operation details from preview description if available
				if (savedConfirmation) {
					const desc = savedConfirmation.preview.description;

					// Make it more natural in French
					if (desc.includes('Supprimer la colonne')) {
						const match = desc.match(/Supprimer la colonne '(.+?)' de la table '(.+?)'/);
						if (match) {
							message += `La colonne "${match[1]}" a été supprimée de la table "${match[2]}".`;
						} else {
							message += 'La colonne a été supprimée avec succès.';
						}
					} else if (desc.includes('Supprimer') && desc.includes('enregistrement')) {
						const match = desc.match(/Supprimer (\d+) enregistrement/);
						if (match) {
							const count = parseInt(match[1]);
							message += `${count} enregistrement${count > 1 ? 's ont' : ' a'} été supprimé${count > 1 ? 's' : ''}.`;
						} else {
							message += 'Les enregistrements ont été supprimés.';
						}
					} else if (desc.includes('Modifier') && desc.includes('enregistrement')) {
						const match = desc.match(/Modifier (\d+) enregistrement/);
						if (match) {
							const count = parseInt(match[1]);
							message += `${count} enregistrement${count > 1 ? 's ont' : ' a'} été modifié${count > 1 ? 's' : ''}.`;
						} else {
							message += 'Les enregistrements ont été modifiés.';
						}
					} else {
						message += 'Opération terminée avec succès.';
					}
				} else {
					message += 'Opération terminée avec succès.';
				}

				const successMessage: UIMessage = {
					id: crypto.randomUUID(),
					role: 'assistant',
					content: message,
					createdAt: new Date(),
					parts: [{ type: 'text', text: message }]
				};
				chatClient.messages = [...chatClient.messages, successMessage];
				toast.success('Opération réussie');
			} else {
				// Add rejection message
				const rejectionMessage: UIMessage = {
					id: crypto.randomUUID(),
					role: 'assistant',
					content: "✗ Opération annulée par l'utilisateur.",
					createdAt: new Date(),
					parts: [{ type: 'text', text: "✗ Opération annulée par l'utilisateur." }]
				};
				chatClient.messages = [...chatClient.messages, rejectionMessage];
				toast.info('Opération annulée');
			}

			await syncMessages();
		} catch (error) {
			console.error('Confirmation error:', error);
			const errorMessage = error instanceof Error ? error.message : 'Erreur inconnue';
			toast.error(`Erreur: ${errorMessage}`);
			pendingConfirmation = null;
			saveConfirmationToStorage(); // Explicitly save (will remove from storage)
		}
	}

	// Sync token with apiKey store
	$effect(() => {
		const currentApiKey = $apiKey;
		if (currentApiKey && currentApiKey !== token) {
			token = currentApiKey;
		}
	});

	// Store metadata for each message (keyed by message ID)
	let messageMetadata = $state<Record<string, MessageMetadata>>({});
	let lastResponseMetadata = $state<MessageMetadata | null>(null);

	// Pending confirmation state
	let pendingConfirmation = $state<PendingConfirmation | null>(null);

	// Local reactive copy of messages
	let localMessages = $state<UIMessage[]>([]);

	// Create chatClient (will be recreated with proper values in onMount)
	let chatClient = $state(
		new Chat({
			id: typeof chat === 'object' && chat !== null && 'id' in chat ? String(chat.id) : undefined,
			api: PUBLIC_CHAT_URL,
			headers: {
				'x-api-key': untrack(() => token) || '',
				'Content-Type': 'application/json'
			},
			initialMessages: untrack(() => initialMessages),
			sendExtraMessageFields: true,
			streamProtocol: 'text',
			generateId: crypto.randomUUID.bind(crypto),
			fetch: async (url, options) => {
				const response = await fetch(url, options);

				if (!response.ok) {
					const errorText = await response.text();
					console.error('HTTP error:', response.status, errorText);
					throw new Error(`HTTP error! status: ${response.status}`);
				}

				const data = await response.json();

				// Check if confirmation is required
				if (data.requires_confirmation && data.confirmation_request) {
					console.log('Confirmation required:', data.confirmation_request);
					pendingConfirmation = data.confirmation_request;
					saveConfirmationToStorage(); // Explicitly save new confirmation

					// Return a simple confirmation message
					const confirmationMessage = `⚠️ Confirmation requise - Veuillez valider l'opération ci-dessous.`;
					return new Response(confirmationMessage, {
						status: 200,
						headers: {
							'Content-Type': 'text/plain; charset=utf-8'
						}
					});
				}

				// Store metadata temporarily
				lastResponseMetadata = {
					sql_query: data.sql_query,
					agent_used: data.agent_used,
					data_analyzed: data.data_analyzed
				};

				const text = data.response || '';
				return new Response(text, {
					status: 200,
					headers: {
						'Content-Type': 'text/plain; charset=utf-8'
					}
				});
			},
			body: {
				documentId: untrack(() => documentId),
				currentTableId: untrack(() => tableId),
				currentTableName: untrack(() => tableName),
				executionMode: 'production-or-is-it',
				webhookUrl: 'https://why-do-you-need-me.so'
			},
			onFinish: async (event) => {
				const lastMessage = chatClient.messages[chatClient.messages.length - 1];

				// Add message manually if not in list
				if (!lastMessage || lastMessage.id !== event.id) {
					chatClient.messages = [...chatClient.messages, event];
				}

				// Associate metadata with message
				const assistantMessage = chatClient.messages[chatClient.messages.length - 1];
				if (lastResponseMetadata && assistantMessage && assistantMessage.role === 'assistant') {
					messageMetadata[assistantMessage.id] = lastResponseMetadata;
					lastResponseMetadata = null;
				}

				// Sync messages to show assistant response
				syncMessages();
			},
			onError: (error) => {
				console.error('Chat error:', error);
				toast.error(error.message);
			}
		})
	);

	// Helper function to sync messages and force UI update
	async function syncMessages() {
		localMessages = [...chatClient.messages];
		saveMessagesToStorage(); // Sauvegarder automatiquement
		await tick();
	}

	// Auto-save messages when they change
	$effect(() => {
		// Watch for changes in chatClient.messages
		if (chatClient.messages.length > 0) {
			saveMessagesToStorage();
		}
	});

	// Watch chatClient.status to sync messages when user submits
	$effect(() => {
		const status = chatClient.status;

		// When status becomes 'submitted' or 'streaming', sync to show user message
		if (status === 'submitted' || status === 'streaming') {
			syncMessages();
		}
	});

	// Fonction pour compter les messages
	const messageCount = $derived(chatClient.messages.length);
	const isLimitReached = $derived(messageCount >= MAX_MESSAGES);

	onMount(async () => {
		// Register onOptions callback BEFORE calling ready()
		grist.onOptions(async (_options: unknown, interaction: GristInteraction) => {
			// Log all interaction options to see what's available
			console.log('=== GRIST INTERACTION OPTIONS ===');
			console.log(JSON.stringify(interaction, null, 2));

			// Update accessLevel state
			accessLevel = interaction.accessLevel || 'none';

			// Force Svelte to flush state changes
			await tick();

			if (accessLevel !== 'full') {
				toast.error(
					'Accès incomplet détecté. Veuillez activer "Full document access" dans les paramètres du widget.'
				);
			} else {
				// Fetch document info FIRST
				documentId = (await grist?.docApi?.getDocName()) || '';
				const gristTable = await grist.getTable();
				tableId = await gristTable.getTableId();

				// Use tableId as tableName for now (Grist API limitation)
				tableName = tableId;

				console.log(`Current table: ${tableName} (id: ${tableId})`);

				// Then fetch access token
				const fetchedToken = await fetchGristToken();

				// Update token state
				token = fetchedToken;

				// Load saved messages from localStorage
				const savedMessages = loadMessagesFromStorage();
				const messagesForInit = savedMessages.length > 0 ? savedMessages : initialMessages;

				if (savedMessages.length > 0) {
					toast.success(`${savedMessages.length} messages restaurés`, { duration: 2000 });
				}

				// Now recreate chatClient with token AND documentId
				chatClient = new Chat({
					id:
						typeof chat === 'object' && chat !== null && 'id' in chat ? String(chat.id) : undefined,
					api: PUBLIC_CHAT_URL,
					headers: {
						'x-api-key': token || '',
						'Content-Type': 'application/json'
					},
					initialMessages: messagesForInit,
					sendExtraMessageFields: true,
					streamProtocol: 'text',
					generateId: crypto.randomUUID.bind(crypto),
					fetch: async (url, options) => {
						// Add the token to headers at request time
						const headers = {
							...(options?.headers || {}),
							'x-api-key': token,
							'Content-Type': 'application/json'
						};

						const response = await fetch(url, { ...options, headers });
						if (!response.ok) {
							const errorText = await response.text();
							console.error('HTTP error:', response.status, errorText);
							throw new Error(`HTTP error! status: ${response.status}`);
						}

						const data = await response.json();

						// Check if confirmation is required
						if (data.requires_confirmation && data.confirmation_request) {
							console.log('Confirmation required:', data.confirmation_request);
							pendingConfirmation = data.confirmation_request;
							saveConfirmationToStorage(); // Explicitly save new confirmation

							// Return a simple confirmation message
							const confirmationMessage = `⚠️ Confirmation requise - Veuillez valider l'opération ci-dessous.`;
							return new Response(confirmationMessage, {
								status: 200,
								headers: { 'Content-Type': 'text/plain; charset=utf-8' }
							});
						}

						lastResponseMetadata = {
							sql_query: data.sql_query,
							agent_used: data.agent_used,
							data_analyzed: data.data_analyzed
						};

						const text = data.response || '';
						return new Response(text, {
							status: 200,
							headers: { 'Content-Type': 'text/plain; charset=utf-8' }
						});
					},
					body: {
						documentId,
						currentTableId: tableId,
						currentTableName: tableName,
						executionMode: 'production-or-is-it',
						webhookUrl: 'https://why-do-you-need-me.so'
					},
					onFinish: async (event) => {
						const lastMessage = chatClient.messages[chatClient.messages.length - 1];

						if (!lastMessage || lastMessage.id !== event.id) {
							chatClient.messages = [...chatClient.messages, event];
						}

						const assistantMessage = chatClient.messages[chatClient.messages.length - 1];
						if (lastResponseMetadata && assistantMessage && assistantMessage.role === 'assistant') {
							messageMetadata[assistantMessage.id] = lastResponseMetadata;
							lastResponseMetadata = null;
						}

						// Sync messages to show assistant response
						syncMessages();
					},
					onError: (error) => {
						console.error('Chat error:', error);
						toast.error(error.message);
					}
				});

				// Sync messages to update the UI with loaded messages
				await syncMessages();
			}
		});

		await grist.ready({
			requiredAccess: 'full'
		});
	});
</script>

<div class="flex h-dvh min-w-0 flex-col bg-background">
	<ChatHeader onReset={resetConversation} />

	{#if !hasFullAccess}
		<!-- Avertissement si l'accès n'est pas accordé -->
		<div class="mx-auto w-full max-w-3xl px-4 py-8">
			<div
				class="rounded-lg border-2 border-orange-400 bg-orange-50 p-6 text-center dark:bg-orange-900/20"
			>
				<div class="mb-4 text-5xl">🔒</div>
				<h3 class="mb-2 text-xl font-bold text-orange-800 dark:text-orange-200">
					Accès complet requis
				</h3>
				<p class="mb-4 text-orange-700 dark:text-orange-300">
					Grist AI nécessite l'accès complet au document pour fonctionner.
				</p>
				<div class="rounded bg-white p-4 text-left text-sm dark:bg-gray-800">
					<p class="mb-2 font-semibold">Pour activer l'accès :</p>
					<ol class="list-decimal space-y-1 pl-5">
						<li>Cliquez sur les trois points (⋯) en haut à droite du widget</li>
						<li>Sélectionnez "Widget options"</li>
						<li>Sélectionnez "Full document access"</li>
						<li>Le widget se rechargera automatiquement</li>
					</ol>
				</div>
			</div>
		</div>
	{:else}
		<!-- Interface de chat normale -->
		<Messages
			{readonly}
			loading={chatClient.status === 'streaming' || chatClient.status === 'submitted'}
			messages={localMessages}
			{messageMetadata}
			{pendingConfirmation}
			onConfirmation={handleConfirmation}
		/>

		<form class="mx-auto flex w-full gap-2 bg-background px-4 pb-4 md:max-w-3xl md:pb-6">
			{#if !readonly}
				{#if isLimitReached}
					<div
						class="flex w-full flex-col gap-3 rounded-2xl border-2 border-orange-400 bg-orange-50 p-4 dark:bg-orange-900/20"
					>
						<div class="flex items-center gap-2 text-orange-800 dark:text-orange-200">
							<span class="text-lg">⚠️</span>
							<span class="font-medium">Limite de {MAX_MESSAGES} messages atteinte</span>
						</div>
						<p class="text-sm text-orange-700 dark:text-orange-300">
							Pour préserver la qualité des réponses et optimiser le contexte, veuillez démarrer une
							nouvelle conversation.
						</p>
						<button
							onclick={resetConversation}
							class="rounded-lg bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700 dark:bg-orange-700 dark:hover:bg-orange-600"
						>
							Nouvelle conversation
						</button>
					</div>
				{:else}
					<MultimodalInput {chatClient} {messageCount} {MAX_MESSAGES} class="flex-1" />
				{/if}
			{/if}
		</form>
	{/if}
</div>
