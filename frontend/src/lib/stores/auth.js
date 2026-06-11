import { browser } from '$app/environment';
import { goto } from '$app/navigation';
import { derived, writable } from 'svelte/store';
import * as api from '$lib/api';

const STORAGE_KEY = 'cq_auth';

const AVATARS = ['Tiger', 'Kitten', 'Fox', 'Panda', 'Rabbit', 'Bear', 'Wolf', 'Owl'];

function loadStored() {
	if (!browser) {
		return { user: null, token: null };
	}

	try {
		const raw = localStorage.getItem(STORAGE_KEY);
		if (!raw) {
			return { user: null, token: null };
		}
		const parsed = JSON.parse(raw);
		if (parsed.token) {
			api.setApiToken(parsed.token);
		}
		return {
			user: parsed.user ?? null,
			token: parsed.token ?? null
		};
	} catch {
		return { user: null, token: null };
	}
}

function persist(state) {
	if (!browser) return;
	if (state.user && state.token) {
		localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
		api.setApiToken(state.token);
	} else {
		localStorage.removeItem(STORAGE_KEY);
		api.setApiToken(null);
	}
}

function createAuthStore() {
	const { subscribe, set, update } = writable(loadStored());

	subscribe((state) => persist(state));

	api.onSessionInvalidated(() => {
		set({ user: null, token: null });
		if (browser && !window.location.pathname.startsWith('/login')) {
			goto('/login', { replaceState: true });
		}
	});

	return {
		subscribe,
		async login(email, password) {
			const data = await api.login(email, password);
			set({ user: data.user, token: data.access_token });
			return data.user;
		},
		async register({ email, password, display_name, avatar }) {
			await api.register({ email, password, display_name, avatar });
			return this.login(email, password);
		},
		async logout() {
			try {
				await api.logout();
			} catch {
				// clear local session even if API call fails
			}
			set({ user: null, token: null });
			goto('/login');
		},
		async updateAvatar(avatar) {
			const data = await api.updateProfile({ avatar });
			update((state) => ({ ...state, user: data.user }));
			return data.user;
		},
		hydrate() {
			set(loadStored());
		}
	};
}

export const auth = createAuthStore();
export const isAdmin = derived(auth, ($auth) => $auth.user?.role === 'admin');
export const isLoggedIn = derived(auth, ($auth) => Boolean($auth.token));
export { AVATARS };
