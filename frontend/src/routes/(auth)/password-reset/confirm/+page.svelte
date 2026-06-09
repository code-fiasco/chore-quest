<script>
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { confirmPasswordReset } from '$lib/api';

	let password = $state('');
	let confirmPassword = $state('');
	let error = $state('');
	let loading = $state(false);

	const token = $derived(page.url.searchParams.get('token') ?? '');

	async function handleSubmit(event) {
		event.preventDefault();
		error = '';

		if (!token) {
			error = 'Invalid or missing reset token';
			return;
		}

		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		loading = true;

		try {
			await confirmPasswordReset(token, password);
			goto('/login');
		} catch (err) {
			error = err.message || 'Reset failed';
		} finally {
			loading = false;
		}
	}
</script>

<form
	onsubmit={handleSubmit}
	class="rounded-2xl border border-quest-border bg-quest-surface p-6 shadow-xl shadow-black/20"
>
	<h2 class="mb-6 text-xl font-semibold text-quest-text">Choose a new password</h2>

	{#if error}
		<div
			class="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300"
		>
			{error}
		</div>
	{/if}

	<label class="mb-4 block">
		<span class="mb-1 block text-sm text-quest-muted">New password</span>
		<input
			type="password"
			bind:value={password}
			required
			minlength="8"
			autocomplete="new-password"
			class="w-full rounded-xl border border-quest-border bg-quest-surface-2 px-4 py-3 text-quest-text outline-none transition focus:border-quest-purple focus:ring-1 focus:ring-quest-purple"
		/>
	</label>

	<label class="mb-6 block">
		<span class="mb-1 block text-sm text-quest-muted">Confirm password</span>
		<input
			type="password"
			bind:value={confirmPassword}
			required
			minlength="8"
			autocomplete="new-password"
			class="w-full rounded-xl border border-quest-border bg-quest-surface-2 px-4 py-3 text-quest-text outline-none transition focus:border-quest-purple focus:ring-1 focus:ring-quest-purple"
		/>
	</label>

	<button
		type="submit"
		disabled={loading}
		class="w-full rounded-xl bg-linear-to-r from-quest-purple to-violet-600 py-3 font-semibold text-white transition hover:brightness-110 disabled:opacity-60"
	>
		{loading ? 'Updating…' : 'Update password'}
	</button>
</form>
