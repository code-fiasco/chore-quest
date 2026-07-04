<script>
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import AvatarPicker from '$lib/components/AvatarPicker.svelte';
	import { getRegistrationStatus } from '$lib/api';
	import { auth } from '$lib/stores/auth';

	let display_name = $state('');
	let avatar = $state('Tiger');
	let email = $state('');
	let password = $state('');
	let confirmPassword = $state('');
	let error = $state('');
	let loading = $state(false);
	let registrationOpen = $state(true);
	let checkingStatus = $state(true);

	onMount(async () => {
		try {
			const status = await getRegistrationStatus();
			registrationOpen = status.open;
		} catch {
			// If status check fails, still allow trying register (backend enforces the limit).
			registrationOpen = true;
		} finally {
			checkingStatus = false;
		}
	});

	async function handleSubmit(event) {
		event.preventDefault();
		error = '';

		if (password !== confirmPassword) {
			error = 'Passwords do not match';
			return;
		}

		loading = true;

		try {
			await auth.register({ email, password, display_name, avatar });
			goto('/dashboard');
		} catch (err) {
			error = err.message || 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<form
	onsubmit={handleSubmit}
	class="rounded-2xl border border-quest-border bg-quest-surface p-6 shadow-xl shadow-black/20"
>
	<h2 class="mb-6 text-xl font-semibold text-quest-text">Join the quest</h2>

	{#if checkingStatus}
		<p class="text-sm text-quest-muted">Checking availability…</p>
	{:else if !registrationOpen}
		<div
			class="mb-4 rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-sm text-amber-200"
		>
			Registration is closed — this household already has two members.
		</div>
		<p class="text-center text-sm text-quest-muted">
			<a href="/login" class="font-medium text-quest-purple-light hover:underline">Sign in instead</a>
		</p>
	{:else}
	{#if error}
		<div
			class="mb-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300"
		>
			{error}
		</div>
	{/if}

	<label class="mb-4 block">
		<span class="mb-1 block text-sm text-quest-muted">Display name</span>
		<input
			type="text"
			bind:value={display_name}
			required
			maxlength="255"
			autocomplete="name"
			class="w-full rounded-xl border border-quest-border bg-quest-surface-2 px-4 py-3 text-quest-text outline-none transition focus:border-quest-purple focus:ring-1 focus:ring-quest-purple"
		/>
	</label>

	<div class="mb-4">
		<span class="mb-2 block text-sm text-quest-muted">Choose your avatar</span>
		<AvatarPicker bind:selected={avatar} />
	</div>

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

	<label class="mb-4 block">
		<span class="mb-1 block text-sm text-quest-muted">Password</span>
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
		class="w-full rounded-xl bg-linear-to-r from-quest-gold to-amber-500 py-3 font-semibold text-quest-bg transition hover:brightness-110 disabled:opacity-60"
	>
		{loading ? 'Creating account…' : 'Start your quest'}
	</button>

	<p class="mt-6 text-center text-sm text-quest-muted">
		Already have an account?
		<a href="/login" class="font-medium text-quest-purple-light hover:underline">Sign in</a>
	</p>
	{/if}
</form>
