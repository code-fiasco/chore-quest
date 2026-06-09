<script>
	import { auth } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { AVATAR_EMOJI } from '$lib/constants';
	import { getLeaderboards } from '$lib/api';
	import CountUp from '$lib/components/CountUp.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let loading = $state(true);
	let data = $state({ weekly: [], monthly: [], lifetime: [] });
	let tab = $state('weekly');

	const tabs = [
		{ key: 'weekly', label: 'This Week' },
		{ key: 'monthly', label: 'This Month' },
		{ key: 'lifetime', label: 'All Time' }
	];

	const entries = $derived(data[tab] ?? []);

	$effect(() => {
		loading = true;
		getLeaderboards()
			.then((result) => (data = result))
			.catch((err) => toast.error(err.message))
			.finally(() => (loading = false));
	});
</script>

<h1 class="mb-4 text-2xl font-bold text-quest-text">Leaderboard</h1>

<div class="mb-4 flex rounded-xl border border-quest-border bg-quest-surface-2 p-1">
	{#each tabs as t}
		<button
			type="button"
			class="min-h-11 flex-1 rounded-lg px-2 py-2 text-xs font-semibold transition
				{tab === t.key ? 'bg-quest-purple text-white' : 'text-quest-muted'}"
			onclick={() => (tab = t.key)}
		>
			{t.label}
		</button>
	{/each}
</div>

{#if loading}
	<LoadingSpinner />
{:else if entries.length === 0}
	<p class="py-8 text-center text-sm text-quest-muted">No scores yet — complete tasks to rank up!</p>
{:else}
	<div class="space-y-2">
		{#each entries as entry (entry.user_id)}
			<div
				class="flex min-h-11 items-center gap-3 rounded-xl border px-4 py-3
					{entry.user_id === $auth.user?.id
					? 'border-quest-gold/50 bg-quest-gold/10'
					: 'border-quest-border bg-quest-surface-2'}"
			>
				<span class="w-8 text-center text-lg font-bold text-quest-gold">
					<CountUp value={entry.rank} />
				</span>
				<span class="text-2xl">{AVATAR_EMOJI[entry.avatar] ?? '🧙'}</span>
				<span class="flex-1 font-medium text-quest-text">{entry.display_name}</span>
				<span class="font-semibold text-quest-purple-light">
					<CountUp value={entry.score} /> pts
				</span>
			</div>
		{/each}
	</div>
{/if}
