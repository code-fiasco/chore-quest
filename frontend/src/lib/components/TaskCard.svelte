<script>
	import { AVATAR_EMOJI } from '$lib/constants';
	import { isOwnCompletion, isTaskCompletedByOther } from '$lib/utils/tasks';

	let {
		task,
		userId,
		isChallenge = false,
		oncomplete = () => {},
		onundo = () => {}
	} = $props();

	let showInfo = $state(false);

	const inst = $derived(task.current_instance);
	const completed = $derived(
		inst?.user_status?.is_completed || inst?.is_locked
	);
	const lockedByOther = $derived(isTaskCompletedByOther(task, userId));
	const ownDone = $derived(isOwnCompletion(task, userId));
	const strikethrough = $derived(completed);
	const description = $derived(task.description?.trim() || 'No description provided.');
</script>

<div
	class="rounded-xl border p-4 transition-all min-h-11
		{isChallenge
		? 'border-quest-gold/50 bg-quest-gold/5 shadow-[0_0_12px_rgba(245,158,11,0.15)]'
		: lockedByOther
			? 'border-quest-border/60 bg-quest-surface-2/50 opacity-80'
			: completed
				? 'border-quest-border/40 bg-quest-surface-2/30'
				: 'border-quest-border bg-quest-surface-2'}"
>
	<div class="flex items-start justify-between gap-2">
		<button
			type="button"
			class="min-h-11 min-w-11 shrink-0 rounded-full border border-quest-border bg-quest-surface text-sm font-semibold text-quest-muted transition hover:border-quest-purple-light hover:text-quest-purple-light"
			aria-label="Task info"
			onclick={() => (showInfo = true)}
		>
			i
		</button>

		<button
			type="button"
			class="min-h-11 flex-1 text-left disabled:cursor-default"
			disabled={completed}
			onclick={() => !completed && oncomplete(task)}
		>
			<p
				class="font-medium text-quest-text {strikethrough ? 'line-through opacity-60' : ''}"
			>
				{task.name}
			</p>
			<p class="mt-0.5 text-xs text-quest-muted">
				{task.room} · {task.base_points} pts
				{#if isChallenge}
					<span class="text-quest-gold"> · +50% challenge bonus</span>
				{/if}
			</p>
		</button>

		<div class="flex shrink-0 items-center gap-2">
			{#if lockedByOther && inst.completed_by}
				<span
					class="flex h-9 w-9 items-center justify-center rounded-full border border-quest-border bg-quest-surface text-lg"
					title="{inst.completed_by.display_name} completed this"
				>
					{AVATAR_EMOJI[inst.completed_by.avatar] ?? '🧙'}
				</span>
			{:else if ownDone}
				<button
					type="button"
					class="min-h-11 min-w-11 rounded-lg border border-quest-border px-3 text-xs font-medium text-quest-muted hover:border-quest-purple-light hover:text-quest-purple-light"
					onclick={() => onundo(task)}
				>
					Undo
				</button>
			{:else if !completed}
				<span class="text-quest-gold text-sm font-semibold">{task.base_points}</span>
			{/if}
		</div>
	</div>
</div>

{#if showInfo}
	<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
	<div
		class="fixed inset-0 z-[90] flex items-end justify-center bg-black/60 p-4"
		role="dialog"
		aria-labelledby="task-info-title"
		tabindex="-1"
		onclick={(e) => e.target === e.currentTarget && (showInfo = false)}
		onkeydown={(e) => e.key === 'Escape' && (showInfo = false)}
	>
		<div class="w-full max-w-[480px] rounded-2xl border border-quest-border bg-quest-surface p-6">
			<h3 id="task-info-title" class="text-lg font-bold text-quest-text">{task.name}</h3>
			<p class="mt-3 text-sm leading-relaxed text-quest-muted">{description}</p>
			<button
				type="button"
				class="mt-5 min-h-11 w-full rounded-xl border border-quest-border py-2 text-sm font-medium text-quest-muted"
				onclick={() => (showInfo = false)}
			>
				Close
			</button>
		</div>
	</div>
{/if}
