<script>
	import { auth } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { AVATAR_EMOJI } from '$lib/constants';
	import { completeTask, getChallenges, getScores, getTasks, undoTask } from '$lib/api';
	import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';
	import EmptyState from '$lib/components/EmptyState.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import PullToRefresh from '$lib/components/PullToRefresh.svelte';
	import TaskCard from '$lib/components/TaskCard.svelte';
	import { sortTasks } from '$lib/utils/tasks';

	let loading = $state(true);
	let tasks = $state({ daily: [], weekly: [], monthly: [] });
	let challenges = $state([]);
	let scores = $state(null);
	let confirmOpen = $state(false);
	let pendingTask = $state(null);
	let loadGeneration = 0;

	const today = new Date().toLocaleDateString(undefined, {
		weekday: 'long',
		month: 'long',
		day: 'numeric'
	});

	const challengeTaskIds = $derived(new Set(challenges.map((c) => c.task_id)));

	function applyTaskData(taskData) {
		tasks = {
			daily: [...(taskData.daily ?? [])],
			weekly: [...(taskData.weekly ?? [])],
			monthly: [...(taskData.monthly ?? [])]
		};
	}

	async function loadData() {
		const generation = ++loadGeneration;
		const [challengeData, taskData, scoreData] = await Promise.all([
			getChallenges(),
			getTasks(),
			getScores()
		]);
		if (generation !== loadGeneration) return;
		challenges = challengeData.challenges ?? [];
		applyTaskData(taskData);
		scores = scoreData;
	}

	async function refresh() {
		try {
			await loadData();
		} catch (err) {
			toast.error(err.message);
		}
	}

	$effect(() => {
		loading = true;
		loadData()
			.catch((err) => toast.error(err.message))
			.finally(() => (loading = false));
	});

	function requestComplete(task) {
		pendingTask = task;
		confirmOpen = true;
	}

	async function handleComplete() {
		if (!pendingTask) return;
		const instanceId = pendingTask.current_instance.id;
		try {
			const result = await completeTask(instanceId);
			toast.success(`+${result.points_awarded} pts!`);
			if (result.badges_earned?.length) {
				toast.success(`Badge earned: ${result.badges_earned.join(', ')}`);
			}
			await loadData();
		} catch (err) {
			toast.error(err.message);
		}
		pendingTask = null;
	}

	async function handleUndo(task) {
		try {
			await undoTask(task.current_instance.id);
			toast.success('Task undone');
			await loadData();
		} catch (err) {
			toast.error(err.message);
		}
	}

	function sectionTasks(key) {
		return sortTasks(
			(tasks[key] ?? []).filter((t) => !challengeTaskIds.has(t.id))
		);
	}
</script>

<PullToRefresh onrefresh={refresh}>
	<header class="mb-6">
		<p class="text-sm text-quest-muted">{today}</p>
		<div class="mt-1 flex items-center gap-3">
			<span class="text-3xl">{AVATAR_EMOJI[$auth.user?.avatar] ?? '🧙'}</span>
			<div>
				<h1 class="text-2xl font-bold text-quest-text">
					Hey, {$auth.user?.display_name}!
				</h1>
				{#if scores}
					<p class="text-sm text-quest-muted">
						<span class="text-quest-gold font-semibold">{scores.daily.total} pts</span> today
						·
						<span class="text-orange-400 font-semibold">🔥 {scores.streak.current}</span> day streak
					</p>
				{/if}
			</div>
		</div>
	</header>

	{#if loading}
		<LoadingSpinner label="Loading your quest…" />
	{:else}
		{#if challenges.length > 0}
			<section class="mb-6">
				<h2 class="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-quest-gold">
					<span>⚡</span> Daily Challenges
				</h2>
				<div class="space-y-2">
					{#each challenges as challenge}
						{@const task = {
							id: challenge.task_id,
							name: challenge.task_name,
							description: challenge.description,
							room: challenge.room,
							base_points: challenge.base_points,
							current_instance: {
								id: challenge.task_instance_id,
								is_locked: challenge.is_done ?? challenge.is_locked,
								completed_by_id: challenge.completed_by?.id ?? null,
								user_status: { is_completed: challenge.is_completed },
								completed_by: challenge.completed_by ?? null
							}
						}}
						<TaskCard
							{task}
							userId={$auth.user?.id}
							isChallenge
							oncomplete={() => requestComplete(task)}
							onundo={() => handleUndo(task)}
						/>
					{/each}
				</div>
			</section>
		{/if}

		{#each [{ key: 'daily', label: 'Daily Tasks', icon: '☀️' }, { key: 'weekly', label: 'Weekly Tasks', icon: '📅' }, { key: 'monthly', label: 'Monthly Tasks', icon: '🗓️' }] as section}
			<section class="mb-6">
				<h2 class="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-quest-purple-light">
					<span>{section.icon}</span> {section.label}
				</h2>
				{#if sectionTasks(section.key).length === 0}
					<EmptyState icon="✅" title="All clear!" message="No {section.label.toLowerCase()} right now." />
				{:else}
					<div class="space-y-2">
						{#each sectionTasks(section.key) as task (task.id)}
							<TaskCard
								{task}
								userId={$auth.user?.id}
								oncomplete={() => requestComplete(task)}
								onundo={() => handleUndo(task)}
							/>
						{/each}
					</div>
				{/if}
			</section>
		{/each}
	{/if}
</PullToRefresh>

<ConfirmDialog
	bind:open={confirmOpen}
	title="Complete task?"
	message={pendingTask
		? `Mark "${pendingTask.name}" as done? Base ${pendingTask.base_points} pts${challenges.some((c) => c.task_id === pendingTask.id) ? ' (+50% challenge bonus)' : ''}.`
		: ''}
	confirmLabel="Complete"
	onconfirm={handleComplete}
/>
