<script>
	import { toast } from '$lib/stores/toast';
	import { BADGE_ICONS } from '$lib/constants';
	import { getBadges } from '$lib/api';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';

	let loading = $state(true);
	let badges = $state([]);
	let selected = $state(null);

	$effect(() => {
		loading = true;
		getBadges()
			.then((data) => (badges = data.badges ?? []))
			.catch((err) => toast.error(err.message))
			.finally(() => (loading = false));
	});

	function badgeLabel(badge) {
		if (badge.earned || !badge.is_secret) return badge.name;
		return '?';
	}

	function badgeDescription(badge) {
		if (badge.earned || !badge.is_secret) return badge.description;
		return 'Secret badge — keep questing to unlock!';
	}

	function formatDate(iso) {
		if (!iso) return '';
		return new Date(iso).toLocaleDateString(undefined, {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<h1 class="mb-4 text-2xl font-bold text-quest-text">Badges</h1>

{#if loading}
	<LoadingSpinner />
{:else if badges.length === 0}
	<EmptyState icon="🎖️" title="No badges yet" message="Complete tasks to earn your first badge." />
{:else}
	<div class="grid grid-cols-2 gap-3">
		{#each badges as badge (badge.id)}
			<button
				type="button"
				class="min-h-[120px] rounded-xl border p-4 text-center transition
					{badge.earned
					? 'border-quest-gold/40 bg-quest-gold/10'
					: badge.is_secret
						? 'border-quest-purple/30 bg-quest-purple/5 shadow-[0_0_16px_rgba(124,58,237,0.2)]'
						: 'border-quest-border bg-quest-surface-2 opacity-50'}"
				disabled={!badge.earned}
				onclick={() => badge.earned && (selected = badge)}
			>
				<p class="text-3xl {badge.earned ? '' : badge.is_secret ? 'animate-pulse' : 'grayscale'}">
					{badge.earned || !badge.is_secret ? (BADGE_ICONS[badge.icon] ?? '🏅') : '?'}
				</p>
				<p class="mt-2 text-sm font-semibold text-quest-text">{badgeLabel(badge)}</p>
				{#if badge.earned || !badge.is_secret}
					<p class="mt-1 text-[10px] text-quest-muted line-clamp-2">{badgeDescription(badge)}</p>
				{/if}
			</button>
		{/each}
	</div>
{/if}

{#if selected}
	<div class="fixed inset-0 z-[90] flex items-end justify-center bg-black/60 p-4">
		<div class="w-full max-w-[480px] rounded-2xl border border-quest-border bg-quest-surface p-6">
			<p class="text-center text-5xl">{BADGE_ICONS[selected.icon] ?? '🏅'}</p>
			<h3 class="mt-3 text-center text-lg font-bold text-quest-gold">{selected.name}</h3>
			<p class="mt-2 text-center text-sm text-quest-muted">{selected.description}</p>
			<p class="mt-3 text-center text-xs text-quest-purple-light">
				Earned {formatDate(selected.awarded_at)}
			</p>
			<button
				type="button"
				class="mt-4 min-h-11 w-full rounded-xl border border-quest-border py-2 text-sm text-quest-muted"
				onclick={() => (selected = null)}
			>
				Close
			</button>
		</div>
	</div>
{/if}
