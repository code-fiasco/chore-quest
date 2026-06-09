<script>
	import { auth, isAdmin } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { AVATAR_EMOJI } from '$lib/constants';
	import { getBadges } from '$lib/api';
	import AvatarPicker from '$lib/components/AvatarPicker.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import ThemePicker from '$lib/components/ThemePicker.svelte';

	let loading = $state(true);
	let badgeSummary = $state({ earned_count: 0, total_count: 0 });
	let editingAvatar = $state(false);
	let selectedAvatar = $state($auth.user?.avatar ?? 'Tiger');
	let saving = $state(false);

	$effect(() => {
		loading = true;
		getBadges()
			.then((data) => {
				badgeSummary = {
					earned_count: data.earned_count ?? 0,
					total_count: data.total_count ?? 0
				};
			})
			.catch((err) => toast.error(err.message))
			.finally(() => (loading = false));
	});

	async function saveAvatar() {
		saving = true;
		try {
			await auth.updateAvatar(selectedAvatar);
			editingAvatar = false;
			toast.success('Avatar updated');
		} catch (err) {
			toast.error(err.message);
		} finally {
			saving = false;
		}
	}
</script>

<div class="rounded-2xl border border-quest-border bg-quest-surface p-6">
	<div class="flex flex-col items-center text-center">
		<div
			class="mb-4 flex h-20 w-20 items-center justify-center rounded-full border-2 border-quest-gold bg-quest-surface-2 text-4xl shadow-[0_0_20px_rgba(245,158,11,0.2)]"
		>
			{AVATAR_EMOJI[$auth.user?.avatar] ?? '🧙'}
		</div>
		<h1 class="text-xl font-bold text-quest-text">{$auth.user?.display_name}</h1>
		<p class="text-sm text-quest-muted">{$auth.user?.email}</p>
		{#if $isAdmin}
			<span
				class="mt-2 rounded-full border border-quest-purple/50 bg-quest-purple/20 px-3 py-0.5 text-xs font-medium text-quest-purple-light"
			>
				Household Admin
			</span>
		{/if}
	</div>

	{#if loading}
		<LoadingSpinner label="Loading profile…" />
	{:else}
		<div class="mt-6 rounded-xl border border-quest-border bg-quest-surface-2 p-4 text-center">
			<p class="text-2xl font-bold text-quest-gold">
				{badgeSummary.earned_count}/{badgeSummary.total_count}
			</p>
			<p class="text-xs text-quest-muted">Badges collected</p>
			<a href="/badges" class="mt-2 inline-block text-sm text-quest-purple-light hover:underline">
				View all badges →
			</a>
		</div>
	{/if}

	<div class="mt-6">
		<p class="mb-2 text-sm font-medium text-quest-text">Colour scheme</p>
		<ThemePicker />
	</div>

	<div class="mt-4">
		{#if editingAvatar}
			<p class="mb-2 text-sm text-quest-muted">Choose a new avatar</p>
			<AvatarPicker bind:selected={selectedAvatar} />
			<div class="mt-3 flex gap-2">
				<button
					type="button"
					class="min-h-11 flex-1 rounded-xl border border-quest-border text-sm text-quest-muted"
					onclick={() => (editingAvatar = false)}
				>
					Cancel
				</button>
				<button
					type="button"
					class="min-h-11 flex-1 rounded-xl bg-quest-purple text-sm font-semibold text-white disabled:opacity-60"
					disabled={saving}
					onclick={saveAvatar}
				>
					{saving ? 'Saving…' : 'Save'}
				</button>
			</div>
		{:else}
			<button
				type="button"
				class="min-h-11 w-full rounded-xl border border-quest-border py-3 text-sm font-medium text-quest-text hover:border-quest-purple-light"
				onclick={() => {
					selectedAvatar = $auth.user?.avatar ?? 'Tiger';
					editingAvatar = true;
				}}
			>
				Change avatar
			</button>
		{/if}
	</div>

	<a
		href="/stats"
		class="mt-3 flex min-h-11 w-full items-center justify-center rounded-xl border border-quest-border py-3 text-sm font-medium text-quest-text hover:border-quest-purple-light"
	>
		View statistics
	</a>

	{#if $isAdmin}
		<a
			href="/admin"
			class="mt-3 flex min-h-11 w-full items-center justify-center rounded-xl border border-quest-gold/40 bg-quest-gold/10 py-3 text-sm font-semibold text-quest-gold"
		>
			Admin Panel
		</a>
	{/if}

	<button
		type="button"
		onclick={() => auth.logout()}
		class="mt-6 min-h-11 w-full rounded-xl border border-red-500/30 bg-red-500/10 py-3 font-medium text-red-300 transition hover:bg-red-500/20"
	>
		Sign out
	</button>
</div>
