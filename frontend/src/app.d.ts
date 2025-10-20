// See https://svelte.dev/docs/kit/types#app.d.ts

// for information about these interfaces
declare global {
	namespace App {
		// interface Error {}
		// interface Locals {}
		// interface PageData {}
		// interface PageState {}
		// interface Platform {}
	}

	// Grist Plugin API types
	interface GristDocApi {
		getAccessToken(options?: { readOnly?: boolean }): Promise<{ token: string; baseUrl: string }>;
		getDocName(): Promise<string>;
	}

	interface GristTable {
		getTableId(): Promise<string>;
	}

	interface InteractionOptions {
		accessLevel?: 'none' | 'read table' | 'full';
	}

	interface Grist {
		ready(options?: { requiredAccess?: 'none' | 'read table' | 'full' }): Promise<void>;
		onOptions(callback: (options: unknown, interaction: InteractionOptions) => void): void;
		docApi: GristDocApi;
		getTable(): GristTable;
	}

	const grist: Grist;
}

export {};
