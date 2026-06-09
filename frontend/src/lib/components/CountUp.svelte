<script>
	import { onMount } from 'svelte';

	let { value = 0, duration = 600 } = $props();
	let display = $state(0);

	onMount(() => {
		const start = performance.now();
		const from = 0;
		const to = value;

		function frame(now) {
			const progress = Math.min((now - start) / duration, 1);
			const eased = 1 - Math.pow(1 - progress, 3);
			display = Math.round(from + (to - from) * eased);
			if (progress < 1) requestAnimationFrame(frame);
		}

		requestAnimationFrame(frame);
	});

	$effect(() => {
		display = value;
	});
</script>

<span>{display}</span>
