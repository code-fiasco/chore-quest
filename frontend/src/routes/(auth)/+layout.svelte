<script>
	let { children } = $props();
</script>

<div class="flex min-h-dvh flex-col items-center justify-center px-6 py-10">
	<div class="mb-8 text-center">
		<h1
			class="bg-linear-to-r from-quest-purple-light to-quest-gold bg-clip-text text-3xl font-bold tracking-tight text-transparent"
		>
			Chore Quest
		</h1>
		<p class="mt-1 text-sm text-quest-muted">Level up your household</p>
	</div>

	<div class="page-enter w-full max-w-sm">
		{@render children()}
	</div>
</div>
