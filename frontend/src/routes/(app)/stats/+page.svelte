<script>
	import { toast } from '$lib/stores/toast';
	import { getStats } from '$lib/api';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let loading = $state(true);
	let stats = $state(null);

	$effect(() => {
		loading = true;
		getStats()
			.then((data) => (stats = data))
			.catch((err) => toast.error(err.message))
			.finally(() => (loading = false));
	});
</script>

<div class="mb-4 flex items-center gap-2">
	<a href="/profile" class="text-quest-muted">←</a>
	<h1 class="text-2xl font-bold text-quest-text">Statistics</h1>
</div>

{#if loading}
	<LoadingSpinner />
{:else if stats}
	<div class="space-y-4">
		<div class="rounded-2xl border border-orange-500/30 bg-orange-500/10 p-5 text-center">
			<p class="text-4xl">🔥</p>
			<p class="mt-1 text-3xl font-bold text-orange-300">{stats.streak}</p>
			<p class="text-sm text-quest-muted">Day streak</p>
		</div>

		<div class="grid grid-cols-2 gap-3">
			<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4 text-center">
				<p class="text-2xl font-bold text-quest-gold">{stats.total_completions}</p>
				<p class="text-xs text-quest-muted">Tasks completed</p>
			</div>
			<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4 text-center">
				<p class="text-2xl font-bold text-quest-purple-light">{stats.badges_earned}</p>
				<p class="text-xs text-quest-muted">Badges earned</p>
			</div>
		</div>

		{#if stats.favourite_room}
			<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4">
				<p class="text-xs uppercase tracking-wide text-quest-muted">Favourite room</p>
				<p class="mt-1 font-semibold text-quest-text">{stats.favourite_room}</p>
			</div>
		{/if}

		{#if stats.best_category}
			<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4">
				<p class="text-xs uppercase tracking-wide text-quest-muted">Best category</p>
				<p class="mt-1 font-semibold text-quest-text">{stats.best_category}</p>
			</div>
		{/if}

		<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4">
			<div class="flex justify-between text-sm">
				<span class="text-quest-muted">Weekly completion rate</span>
				<span class="font-semibold text-quest-gold">{stats.weekly_completion_rate}%</span>
			</div>
			<progress
				class="stats-bar mt-2 h-3 w-full"
				value={stats.weekly_completion_rate}
				max="100"
				aria-label="Weekly completion rate"
			></progress>
		</div>

		<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4">
			<p class="mb-3 text-xs uppercase tracking-wide text-quest-muted">Points breakdown</p>
			<div class="space-y-2 text-sm">
				{#each [{ key: 'daily', label: 'Today' }, { key: 'weekly', label: 'This week' }, { key: 'monthly', label: 'This month' }, { key: 'lifetime', label: 'All time' }] as row}
					<div class="flex justify-between">
						<span class="text-quest-muted">{row.label}</span>
						<span class="font-semibold text-quest-text">{stats.points[row.key]} pts</span>
					</div>
				{/each}
			</div>
		</div>
	</div>
{/if}
