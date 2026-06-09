<script>
	import { goto } from '$app/navigation';
	import { auth } from '$lib/stores/auth';

	$effect(() => {
		goto($auth.token ? '/dashboard' : '/login');
	});
</script>

<div class="flex min-h-dvh items-center justify-center">
	<div
		class="h-8 w-8 animate-spin rounded-full border-2 border-quest-purple border-t-quest-gold"
	></div>
</div>
