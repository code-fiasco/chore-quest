import { writable } from 'svelte/store';

function createToastStore() {
	const { subscribe, update } = writable([]);

	let nextId = 0;

	function push(message, type = 'info', duration = 3000) {
		const id = ++nextId;
		update((items) => [...items, { id, message, type }]);
		setTimeout(() => {
			update((items) => items.filter((item) => item.id !== id));
		}, duration);
	}

	return {
		subscribe,
		success: (message) => push(message, 'success'),
		info: (message) => push(message, 'info'),
		error: (message) => push(message, 'error')
	};
}

export const toast = createToastStore();
