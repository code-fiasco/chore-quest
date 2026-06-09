<script>
	import { toast } from '$lib/stores/toast';
</script>

<div class="fixed left-1/2 top-4 z-[100] flex w-full max-w-[480px] -translate-x-1/2 flex-col gap-2 px-4">
	{#each $toast as item (item.id)}
		<div
			class="rounded-xl border px-4 py-3 text-sm font-medium shadow-lg backdrop-blur-md animate-[page-in_0.2s_ease-out]
				{item.type === 'success'
				? 'border-emerald-500/40 bg-emerald-500/20 text-emerald-200'
				: item.type === 'error'
					? 'border-red-500/40 bg-red-500/20 text-red-200'
					: 'border-quest-purple/40 bg-quest-surface/95 text-quest-text'}"
			role="status"
		>
			{item.message}
		</div>
	{/each}
</div>
