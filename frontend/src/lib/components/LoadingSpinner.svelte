<script>
	let { label = 'Loading…' } = $props();
</script>

<div class="flex flex-col items-center justify-center gap-3 py-12" role="status">
	<div
		class="h-10 w-10 animate-spin rounded-full border-2 border-quest-purple border-t-quest-gold"
	></div>
	<p class="text-sm text-quest-muted">{label}</p>
</div>
