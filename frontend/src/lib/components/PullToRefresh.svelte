<script>
	let { onrefresh = async () => {}, children } = $props();

	let pulling = $state(false);
	let pullDistance = $state(0);
	let refreshing = $state(false);
	let startY = 0;

	const THRESHOLD = 70;

	async function handleRefresh() {
		refreshing = true;
		try {
			await onrefresh();
		} finally {
			refreshing = false;
			pullDistance = 0;
		}
	}

	function onTouchStart(e) {
		if (window.scrollY > 0 || refreshing) return;
		startY = e.touches[0].clientY;
		pulling = true;
	}

	function onTouchMove(e) {
		if (!pulling || refreshing) return;
		const delta = e.touches[0].clientY - startY;
		if (delta > 0) {
			pullDistance = Math.min(delta * 0.5, 100);
		}
	}

	async function onTouchEnd() {
		if (!pulling) return;
		pulling = false;
		if (pullDistance >= THRESHOLD) {
			await handleRefresh();
		} else {
			pullDistance = 0;
		}
	}
</script>

<div
	role="region"
	aria-label="Pull to refresh"
	ontouchstart={onTouchStart}
	ontouchmove={onTouchMove}
	ontouchend={onTouchEnd}
>
	<div
		class="flex items-center justify-center overflow-hidden text-xs text-quest-muted transition-all"
		style="height: {refreshing || pullDistance > 0 ? '2.5rem' : '0'}; opacity: {Math.min(pullDistance / THRESHOLD, 1)}"
	>
		{refreshing ? 'Refreshing…' : pullDistance >= THRESHOLD ? 'Release to refresh' : 'Pull to refresh'}
	</div>
	{@render children()}
</div>
