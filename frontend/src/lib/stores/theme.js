import { browser } from '$app/environment';
import { writable } from 'svelte/store';
import { DEFAULT_THEME_ID, getThemeById } from '$lib/themes';

const STORAGE_KEY = 'cq_theme';

function loadStored() {
	if (!browser) return DEFAULT_THEME_ID;
	return localStorage.getItem(STORAGE_KEY) || DEFAULT_THEME_ID;
}

/** @param {string} themeId */
export function applyTheme(themeId) {
	if (!browser) return;
	const theme = getThemeById(themeId);
	const root = document.documentElement;
	root.dataset.theme = theme.id;
	root.dataset.mode = theme.mode;
	for (const [key, value] of Object.entries(theme.vars)) {
		root.style.setProperty(key, value);
	}
	const meta = document.querySelector('meta[name="theme-color"]');
	if (meta) {
		meta.setAttribute('content', theme.vars['--cq-bg']);
	}
}

function createThemeStore() {
	const { subscribe, set } = writable(loadStored());

	if (browser) {
		subscribe((id) => {
			localStorage.setItem(STORAGE_KEY, id);
			applyTheme(id);
		});
		applyTheme(loadStored());
	}

	return {
		subscribe,
		/** @param {string} themeId */
		select(themeId) {
			set(themeId);
		}
	};
}

export const theme = createThemeStore();
