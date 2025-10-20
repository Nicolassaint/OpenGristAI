import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export const apiKey = writable('');

let tokenRefreshInterval: ReturnType<typeof setInterval> | null = null;

/**
 * Decode JWT token to extract expiration time
 */
function decodeJWT(token: string): { exp?: number } | null {
	try {
		const parts = token.split('.');
		if (parts.length !== 3) return null;

		const payload = JSON.parse(atob(parts[1]));
		return payload;
	} catch (error) {
		console.error('Failed to decode JWT:', error);
		return null;
	}
}

/**
 * Get time remaining until token expiration (in milliseconds)
 */
function getTokenExpiryTime(token: string): number | null {
	const decoded = decodeJWT(token);
	if (!decoded?.exp) return null;

	const expiryTime = decoded.exp * 1000;
	const now = Date.now();
	return expiryTime - now;
}

/**
 * Fetches an access token automatically from Grist using the plugin API.
 * This eliminates the need for users to manually copy/paste their API key.
 *
 * @returns The generated access token or empty string if unavailable
 */
export async function fetchGristToken(): Promise<string> {
	if (!browser || typeof grist === 'undefined') {
		console.warn('Grist API not available in this context');
		return '';
	}

	try {
		// Request an access token from Grist with full permissions
		// This token is automatically scoped to the document and widget permissions
		const tokenInfo = await grist.docApi.getAccessToken({ readOnly: false });
		const token = tokenInfo.token;

		// Store the token for use in API requests
		apiKey.set(token);
		sessionStorage.setItem('apikey', token);

		console.log('✅ Grist token fetched successfully');

		// Setup automatic token refresh
		setupTokenRefresh(token);

		return token;
	} catch (error) {
		console.error('❌ Error fetching Grist token:', error);
		return '';
	}
}

/**
 * Setup automatic token refresh before expiration
 */
function setupTokenRefresh(token: string): void {
	// Clear any existing refresh interval
	if (tokenRefreshInterval) {
		clearInterval(tokenRefreshInterval);
		tokenRefreshInterval = null;
	}

	const timeRemaining = getTokenExpiryTime(token);

	if (!timeRemaining || timeRemaining <= 0) {
		console.warn('⚠️ Token already expired or invalid expiry time');
		return;
	}

	// Refresh token 2 minutes before expiration (or at 80% of its lifetime, whichever is sooner)
	const refreshTime = Math.min(timeRemaining * 0.8, timeRemaining - 2 * 60 * 1000);

	if (refreshTime <= 0) {
		// Token expires very soon, refresh immediately
		console.log('🔄 Token expires soon, refreshing immediately...');
		fetchGristToken();
		return;
	}

	console.log(`🔄 Token refresh scheduled in ${Math.round(refreshTime / 1000)}s`);

	// Schedule token refresh
	tokenRefreshInterval = setTimeout(async () => {
		console.log('🔄 Refreshing Grist token...');
		await fetchGristToken();
	}, refreshTime);
}

/**
 * Initialize token management - call this on app startup
 */
export function initTokenManagement(): void {
	if (!browser) return;

	// Try to get existing token from session storage
	const existingToken = sessionStorage.getItem('apikey');

	if (existingToken) {
		const timeRemaining = getTokenExpiryTime(existingToken);

		if (timeRemaining && timeRemaining > 0) {
			console.log(`📝 Existing token found, expires in ${Math.round(timeRemaining / 1000)}s`);
			apiKey.set(existingToken);
			setupTokenRefresh(existingToken);
		} else {
			console.log('🔄 Existing token expired, fetching new one...');
			fetchGristToken();
		}
	} else {
		console.log('🔄 No existing token, fetching new one...');
		fetchGristToken();
	}
}

/**
 * Get the stored API key from session storage
 */
export function getApiKey(): string {
	if (browser) {
		return sessionStorage.getItem('apikey') || '';
	}
	return '';
}

/**
 * Cleanup token refresh interval
 */
export function cleanupTokenManagement(): void {
	if (tokenRefreshInterval) {
		clearInterval(tokenRefreshInterval);
		tokenRefreshInterval = null;
	}
}
