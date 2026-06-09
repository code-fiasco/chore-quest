<script>
	import { AVATARS } from '$lib/stores/auth';

	const AVATAR_EMOJI = {
		Tiger: '🐯',
		Kitten: '🐱',
		Fox: '🦊',
		Panda: '🐼',
		Rabbit: '🐰',
		Bear: '🐻',
		Wolf: '🐺',
		Owl: '🦉'
	};

	let { selected = $bindable('Tiger') } = $props();
</script>

<div class="grid grid-cols-4 gap-2">
	{#each AVATARS as avatar}
		<button
			type="button"
			class="flex flex-col items-center gap-1 rounded-xl border-2 p-2 transition-all
				{selected === avatar
				? 'border-quest-gold bg-quest-gold/10 shadow-[0_0_12px_rgba(245,158,11,0.3)]'
				: 'border-quest-border bg-quest-surface-2 hover:border-quest-purple-light/50'}"
			onclick={() => (selected = avatar)}
			aria-pressed={selected === avatar}
		>
			<span class="text-2xl">{AVATAR_EMOJI[avatar]}</span>
			<span class="text-[10px] font-medium text-quest-muted">{avatar}</span>
		</button>
	{/each}
</div>
