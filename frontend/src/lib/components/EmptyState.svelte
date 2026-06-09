<script>
	let { icon = '📭', title = 'Nothing here yet', message = '' } = $props();
</script>

<div class="rounded-2xl border border-dashed border-quest-border bg-quest-surface/50 px-6 py-10 text-center">
	<p class="text-4xl">{icon}</p>
	<h3 class="mt-3 font-semibold text-quest-text">{title}</h3>
	{#if message}
		<p class="mt-1 text-sm text-quest-muted">{message}</p>
	{/if}
</div>
