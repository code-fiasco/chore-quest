<script>
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import { requestPasswordReset } from '$lib/api';

	let email = $state('');
	let error = $state('');
	let success = $state('');
	let loading = $state(false);

	// Older reset emails linked here with ?token=; the form lives at /confirm.
	$effect(() => {
		if (!browser) return;
		const token = page.url.searchParams.get('token');
		if (token) {
			goto(`/password-reset/confirm?token=${encodeURIComponent(token)}`, {
				replaceState: true
			});
		}
	});

	async function handleSubmit(event) {
		event.preventDefault();
		error = '';
		success = '';
		loading = true;

		try {
			await requestPasswordReset(email);
			success = 'If an account exists for that email, a reset link has been sent.';
		} catch (err) {
			error = err.message || 'Request failed';
		} finally {
			loading = false;
		}
	}
</script>

<form
	onsubmit={handleSubmit}
	class="rounded-2xl border border-quest-border bg-quest-surface p-6 shadow-xl shadow-black/20"
>
	<h2 class="mb-2 text-xl font-semibold text-quest-text">Reset password</h2>
	<p class="mb-6 text-sm text-quest-muted">We'll email you a link to choose a new password.</p>

	{#if error}
		<div
			class="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300"
		>
			{error}
		</div>
	{/if}

	{#if success}
		<div
			class="mb-4 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-300"
		>
			{success}
		</div>
	{/if}

	<label class="mb-6 block">
		<span class="mb-1 block text-sm text-quest-muted">Email</span>
		<input
			type="email"
			bind:value={email}
			required
			autocomplete="email"
			class="w-full rounded-xl border border-quest-border bg-quest-surface-2 px-4 py-3 text-quest-text outline-none transition focus:border-quest-purple focus:ring-1 focus:ring-quest-purple"
		/>
	</label>

	<button
		type="submit"
		disabled={loading}
		class="w-full rounded-xl bg-linear-to-r from-quest-purple to-violet-600 py-3 font-semibold text-white transition hover:brightness-110 disabled:opacity-60"
	>
		{loading ? 'Sending…' : 'Send reset link'}
	</button>

	<p class="mt-6 text-center text-sm text-quest-muted">
		<a href="/login" class="font-medium text-quest-purple-light hover:underline">Back to sign in</a>
	</p>
</form>
