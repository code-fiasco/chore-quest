<script>
	import { THEMES } from '$lib/themes';
	import { theme } from '$lib/stores/theme';
</script>

<div class="grid grid-cols-2 gap-2">
	{#each THEMES as t}
		<button
			type="button"
			class="min-h-11 rounded-xl border-2 p-3 text-left transition-all
				{$theme === t.id
				? 'border-quest-gold shadow-[0_0_12px_rgba(245,158,11,0.25)]'
				: 'border-quest-border hover:border-quest-purple-light/50'}"
			onclick={() => theme.select(t.id)}
			aria-pressed={$theme === t.id}
		>
			<div class="mb-2 flex gap-1">
				{#each t.preview as colour}
					<svg class="h-4 w-4" viewBox="0 0 16 16" aria-hidden="true">
						<circle cx="8" cy="8" r="7" fill={colour} stroke="rgba(0,0,0,0.1)" stroke-width="1" />
					</svg>
				{/each}
			</div>
			<span class="text-sm font-medium text-quest-text">{t.name}</span>
			<span class="ml-1 text-[10px] capitalize text-quest-muted">({t.mode})</span>
		</button>
	{/each}
</div>
