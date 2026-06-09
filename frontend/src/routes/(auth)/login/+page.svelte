<script>
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';

	let email = $state('');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function handleSubmit(event) {
		event.preventDefault();
		error = '';
		loading = true;

		try {
			await auth.login(email, password);
			goto('/dashboard');
		} catch (err) {
			error = err.message || 'Login failed';
		} finally {
			loading = false;
		}
	}
</script>

<form
	onsubmit={handleSubmit}
	class="rounded-2xl border border-quest-border bg-quest-surface p-6 shadow-xl shadow-black/20"
>
	<h2 class="mb-6 text-xl font-semibold text-quest-text">Welcome back</h2>

	{#if error}
		<div
			class="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300"
		>
			{error}
		</div>
	{/if}

	<label class="mb-4 block">
		<span class="mb-1 block text-sm text-quest-muted">Email</span>
		<input
			type="email"
			bind:value={email}
			required
			autocomplete="email"
			class="w-full rounded-xl border border-quest-border bg-quest-surface-2 px-4 py-3 text-quest-text outline-none transition focus:border-quest-purple focus:ring-1 focus:ring-quest-purple"
		/>
	</label>

	<label class="mb-6 block">
		<span class="mb-1 block text-sm text-quest-muted">Password</span>
		<input
			type="password"
			bind:value={password}
			required
			autocomplete="current-password"
			class="w-full rounded-xl border border-quest-border bg-quest-surface-2 px-4 py-3 text-quest-text outline-none transition focus:border-quest-purple focus:ring-1 focus:ring-quest-purple"
		/>
	</label>

	<button
		type="submit"
		disabled={loading}
		class="w-full rounded-xl bg-linear-to-r from-quest-purple to-violet-600 py-3 font-semibold text-white transition hover:brightness-110 disabled:opacity-60"
	>
		{loading ? 'Signing in…' : 'Sign in'}
	</button>

	<p class="mt-4 text-center text-sm text-quest-muted">
		<a href="/password-reset" class="text-quest-purple-light hover:underline">Forgot password?</a>
	</p>

	<p class="mt-6 text-center text-sm text-quest-muted">
		No account?
		<a href="/register" class="font-medium text-quest-gold hover:underline">Create one</a>
	</p>
</form>
