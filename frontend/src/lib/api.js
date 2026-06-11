const API_BASE = import.meta.env.VITE_API_URL || '/api';
const TOKEN_KEY = 'cq_token';
const AUTH_STORAGE_KEY = 'cq_auth';

let sessionInvalidatedCallback = null;
let invalidatingSession = false;

/** @param {() => void} callback */
export function onSessionInvalidated(callback) {
	sessionInvalidatedCallback = callback;
}

function getToken() {
	if (typeof localStorage === 'undefined') return null;
	return localStorage.getItem(TOKEN_KEY);
}

export function setApiToken(token) {
	if (typeof localStorage === 'undefined') return;
	if (token) {
		invalidatingSession = false;
		localStorage.setItem(TOKEN_KEY, token);
	} else {
		localStorage.removeItem(TOKEN_KEY);
	}
}

function invalidateSession() {
	if (invalidatingSession) return;
	invalidatingSession = true;
	setApiToken(null);
	if (typeof localStorage !== 'undefined') {
		localStorage.removeItem(AUTH_STORAGE_KEY);
	}
	sessionInvalidatedCallback?.();
}

async function request(path, options = {}) {
	const token = getToken();
	const headers = {
		'Content-Type': 'application/json',
		...options.headers
	};

	if (token) {
		headers.Authorization = `Bearer ${token}`;
	}

	const response = await fetch(`${API_BASE}${path}`, {
		credentials: 'include',
		...options,
		headers
	});

	if (response.status === 401) {
		invalidateSession();
		throw new Error('Unauthorized');
	}

	if (!response.ok) {
		let detail = response.statusText;
		try {
			const body = await response.json();
			detail = typeof body.detail === 'string' ? body.detail : detail;
		} catch {
			// ignore parse errors
		}
		throw new Error(detail);
	}

	if (response.status === 204) {
		return null;
	}

	return response.json();
}

// Auth
export function login(email, password) {
	return request('/auth/login', {
		method: 'POST',
		body: JSON.stringify({ email, password })
	});
}

export function register({ email, password, display_name, avatar }) {
	return request('/auth/register', {
		method: 'POST',
		body: JSON.stringify({ email, password, display_name, avatar })
	});
}

export function logout() {
	return request('/auth/logout', { method: 'POST' });
}

export function updateProfile({ avatar }) {
	return request('/auth/me', {
		method: 'PUT',
		body: JSON.stringify({ avatar })
	});
}

export function requestPasswordReset(email) {
	return request('/auth/password-reset/request', {
		method: 'POST',
		body: JSON.stringify({ email })
	});
}

export function confirmPasswordReset(token, new_password) {
	return request('/auth/password-reset/confirm', {
		method: 'POST',
		body: JSON.stringify({ token, new_password })
	});
}

export function getAvatars() {
	return request('/auth/avatars');
}

// Tasks
export function getTasks() {
	return request('/tasks');
}

export function createTask(data) {
	return request('/tasks', { method: 'POST', body: JSON.stringify(data) });
}

export function updateTask(taskId, data) {
	return request(`/tasks/${taskId}`, { method: 'PUT', body: JSON.stringify(data) });
}

export function deleteTask(taskId) {
	return request(`/tasks/${taskId}`, { method: 'DELETE' });
}

export function reorderTasks(taskIds) {
	return request('/tasks/reorder', {
		method: 'PUT',
		body: JSON.stringify({ task_ids: taskIds })
	});
}

export function completeTask(taskInstanceId) {
	return request(`/tasks/${taskInstanceId}/complete`, { method: 'POST' });
}

export function undoTask(taskInstanceId) {
	return request(`/tasks/${taskInstanceId}/undo`, { method: 'POST' });
}

// Categories
export function getCategories() {
	return request('/categories');
}

export function createCategory(name) {
	return request('/categories', { method: 'POST', body: JSON.stringify({ name }) });
}

export function updateCategory(categoryId, name) {
	return request(`/categories/${categoryId}`, {
		method: 'PUT',
		body: JSON.stringify({ name })
	});
}

export function deleteCategory(categoryId) {
	return request(`/categories/${categoryId}`, { method: 'DELETE' });
}

// Scores
export function getScores() {
	return request('/scores/me');
}

export function getHouseholdScores() {
	return request('/scores');
}

// Gamification
export function getChallenges() {
	return request('/challenges/today');
}

export function getLeaderboards() {
	return request('/leaderboards');
}

export function getBadges() {
	return request('/badges');
}

export function getStreaks() {
	return request('/streaks');
}

export function getGoals() {
	return request('/goals');
}

export function setGoals(points_target) {
	return request('/goals', {
		method: 'PUT',
		body: JSON.stringify({ points_target })
	});
}

// Stats & Admin
export function getStats() {
	return request('/stats');
}

export function masterReset() {
	return request('/admin/reset', { method: 'POST' });
}
