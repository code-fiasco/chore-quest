<script>
	let {
		open = $bindable(false),
		title = 'Confirm',
		message = 'Are you sure?',
		confirmLabel = 'Confirm',
		cancelLabel = 'Cancel',
		danger = false,
		onconfirm = () => {}
	} = $props();

	function cancel() {
		open = false;
	}

	function confirm() {
		onconfirm();
		open = false;
	}
</script>

{#if open}
	<div class="fixed inset-0 z-[90] flex items-center justify-center bg-black/60 p-4">
		<div class="w-full max-w-sm rounded-2xl border border-quest-border bg-quest-surface p-6 shadow-xl">
			<h3 class="text-lg font-semibold text-quest-text">{title}</h3>
			<p class="mt-2 text-sm text-quest-muted">{message}</p>
			<div class="mt-6 flex gap-3">
				<button
					type="button"
					class="min-h-11 flex-1 rounded-xl border border-quest-border px-4 py-2 text-sm font-medium text-quest-muted"
					onclick={cancel}
				>
					{cancelLabel}
				</button>
				<button
					type="button"
					class="min-h-11 flex-1 rounded-xl px-4 py-2 text-sm font-semibold text-white
						{danger ? 'bg-red-600 hover:bg-red-500' : 'bg-quest-purple hover:brightness-110'}"
					onclick={confirm}
				>
					{confirmLabel}
				</button>
			</div>
		</div>
	</div>
{/if}
