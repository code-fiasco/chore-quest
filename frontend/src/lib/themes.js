/** @typedef {{ id: string, name: string, mode: 'dark' | 'light', preview: [string, string, string], vars: Record<string, string> }} Theme */

/** @type {Theme[]} */
export const THEMES = [
	{
		id: 'night-quest',
		name: 'Night Quest',
		mode: 'dark',
		preview: ['#0c0a12', '#7c3aed', '#f59e0b'],
		vars: {
			'--cq-bg': '#0c0a12',
			'--cq-surface': '#161222',
			'--cq-surface-2': '#1f1a2e',
			'--cq-border': '#2d2640',
			'--cq-purple': '#7c3aed',
			'--cq-purple-light': '#a78bfa',
			'--cq-gold': '#f59e0b',
			'--cq-gold-light': '#fcd34d',
			'--cq-text': '#f3f0ff',
			'--cq-muted': '#9b8ec4'
		}
	},
	{
		id: 'midnight',
		name: 'Midnight',
		mode: 'dark',
		preview: ['#0a0f1a', '#0ea5e9', '#22d3ee'],
		vars: {
			'--cq-bg': '#0a0f1a',
			'--cq-surface': '#111827',
			'--cq-surface-2': '#1a2332',
			'--cq-border': '#243044',
			'--cq-purple': '#0284c7',
			'--cq-purple-light': '#38bdf8',
			'--cq-gold': '#22d3ee',
			'--cq-gold-light': '#67e8f9',
			'--cq-text': '#e0f2fe',
			'--cq-muted': '#7dd3fc'
		}
	},
	{
		id: 'ember',
		name: 'Ember',
		mode: 'dark',
		preview: ['#140a0a', '#dc2626', '#fb923c'],
		vars: {
			'--cq-bg': '#140a0a',
			'--cq-surface': '#1f1210',
			'--cq-surface-2': '#2a1814',
			'--cq-border': '#3d221c',
			'--cq-purple': '#b91c1c',
			'--cq-purple-light': '#f87171',
			'--cq-gold': '#f97316',
			'--cq-gold-light': '#fdba74',
			'--cq-text': '#fff1f0',
			'--cq-muted': '#fca5a5'
		}
	},
	{
		id: 'daylight',
		name: 'Daylight',
		mode: 'light',
		preview: ['#e8edf2', '#2563eb', '#d97706'],
		vars: {
			'--cq-bg': '#e8edf2',
			'--cq-surface': '#f1f4f8',
			'--cq-surface-2': '#dce3eb',
			'--cq-border': '#b0bcc9',
			'--cq-purple': '#1d4ed8',
			'--cq-purple-light': '#2563eb',
			'--cq-gold': '#c2620a',
			'--cq-gold-light': '#d97706',
			'--cq-text': '#0f172a',
			'--cq-muted': '#526077'
		}
	},
	{
		id: 'meadow',
		name: 'Meadow',
		mode: 'light',
		preview: ['#e8f5ec', '#15803d', '#b45309'],
		vars: {
			'--cq-bg': '#e8f5ec',
			'--cq-surface': '#f0f9f2',
			'--cq-surface-2': '#d0e8d6',
			'--cq-border': '#94c9a4',
			'--cq-purple': '#166534',
			'--cq-purple-light': '#15803d',
			'--cq-gold': '#b45309',
			'--cq-gold-light': '#ca8a04',
			'--cq-text': '#14532d',
			'--cq-muted': '#3f6b4f'
		}
	},
	{
		id: 'lavender',
		name: 'Lavender',
		mode: 'light',
		preview: ['#ede4f7', '#7e22ce', '#c0266a'],
		vars: {
			'--cq-bg': '#ede4f7',
			'--cq-surface': '#f5f0fa',
			'--cq-surface-2': '#ddd0ee',
			'--cq-border': '#b89fd4',
			'--cq-purple': '#7e22ce',
			'--cq-purple-light': '#9333ea',
			'--cq-gold': '#be185d',
			'--cq-gold-light': '#db2777',
			'--cq-text': '#3b0764',
			'--cq-muted': '#6b21a8'
		}
	},
	{
		id: 'blush',
		name: 'Blush',
		mode: 'light',
		preview: ['#fce8f0', '#e8a4c0', '#d4a574'],
		vars: {
			'--cq-bg': '#fce8f0',
			'--cq-surface': '#fef4f8',
			'--cq-surface-2': '#f5d4e2',
			'--cq-border': '#e8b4cc',
			'--cq-purple': '#d4789a',
			'--cq-purple-light': '#e8a4c0',
			'--cq-gold': '#c9956a',
			'--cq-gold-light': '#d4a574',
			'--cq-text': '#5c3a4a',
			'--cq-muted': '#9a7080'
		}
	},
	{
		id: 'high-contrast',
		name: 'High Contrast',
		mode: 'dark',
		preview: ['#000000', '#ffffff', '#ffff00'],
		vars: {
			'--cq-bg': '#000000',
			'--cq-surface': '#0a0a0a',
			'--cq-surface-2': '#141414',
			'--cq-border': '#ffffff',
			'--cq-purple': '#ffffff',
			'--cq-purple-light': '#ffffff',
			'--cq-gold': '#ffff00',
			'--cq-gold-light': '#ffff66',
			'--cq-text': '#ffffff',
			'--cq-muted': '#d4d4d4'
		}
	}
];

export const DEFAULT_THEME_ID = 'night-quest';

/** @param {string} id */
export function getThemeById(id) {
	return THEMES.find((t) => t.id === id) ?? THEMES[0];
}
