<script>
	import { flip } from 'svelte/animate';
	import { goto } from '$app/navigation';
	import { isAdmin } from '$lib/stores/auth';
	import { toast } from '$lib/stores/toast';
	import { FREQUENCIES, ROOMS } from '$lib/constants';
	import {
		createCategory,
		createTask,
		deleteCategory,
		deleteTask,
		getCategories,
		getGoals,
		getTasks,
		masterReset,
		resetProgress,
		reorderTasks,
		setGoals,
		updateCategory,
		updateTask
	} from '$lib/api';
	import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import { dndzone } from 'svelte-dnd-action';

	let tab = $state('tasks');
	let loading = $state(true);
	let tasks = $state({ daily: [], weekly: [], monthly: [] });
	let categories = $state([]);
	let goalTarget = $state(100);
	let dailyChallengesEnabled = $state(true);
	let dailyChallengeCount = $state(3);
	let resetOpen = $state(false);
	let progressResetOpen = $state(false);

	let showTaskForm = $state(false);
	let editingTask = $state(null);
	let taskForm = $state(emptyTaskForm());

	let categoryName = $state('');
	let editingCategory = $state(null);

	const tabs = [
		{ key: 'tasks', label: 'Tasks' },
		{ key: 'categories', label: 'Categories' },
		{ key: 'goals', label: 'Goals' },
		{ key: 'reset', label: 'Reset' }
	];

	const frequencySections = [
		{ key: 'daily', label: 'Daily Tasks', icon: '☀️' },
		{ key: 'weekly', label: 'Weekly Tasks', icon: '📅' },
		{ key: 'monthly', label: 'Monthly Tasks', icon: '🗓️' }
	];

	function emptyTaskForm() {
		return {
			name: '',
			description: '',
			frequency: 'daily',
			base_points: 10,
			category_id: categories[0]?.id ?? 1,
			room: 'Kitchen',
			is_required: true
		};
	}

	$effect(() => {
		if (!$isAdmin) {
			goto('/dashboard');
			return;
		}
		loadAll();
	});

	async function loadAll() {
		loading = true;
		try {
			const [taskData, catData, goalData] = await Promise.all([
				getTasks(),
				getCategories(),
				getGoals()
			]);
			tasks = taskData;
			categories = catData;
			goalTarget = goalData.points_target ?? 100;
			dailyChallengesEnabled = goalData.daily_challenges_enabled ?? true;
			dailyChallengeCount = goalData.daily_challenge_count ?? 3;
			if (!editingTask && !showTaskForm) {
				taskForm.category_id = categories[0]?.id ?? 1;
			}
		} catch (err) {
			toast.error(err.message);
		} finally {
			loading = false;
		}
	}

	function openNewTask() {
		editingTask = null;
		taskForm = emptyTaskForm();
		showTaskForm = true;
	}

	function openEditTask(task) {
		editingTask = task;
		taskForm = {
			name: task.name,
			description: task.description ?? '',
			frequency: task.frequency,
			base_points: task.base_points,
			category_id: task.category.id,
			room: task.room,
			is_required: task.is_required
		};
		showTaskForm = true;
	}

	async function saveTask() {
		const payload = {
			...taskForm,
			base_points: Number(taskForm.base_points),
			description: taskForm.description || null
		};
		try {
			if (editingTask) {
				await updateTask(editingTask.id, payload);
				toast.success('Task updated');
			} else {
				await createTask(payload);
				toast.success('Task created');
			}
			showTaskForm = false;
			await loadAll();
		} catch (err) {
			toast.error(err.message);
		}
	}

	async function removeTask(task) {
		if (!confirm(`Delete "${task.name}"?`)) return;
		try {
			await deleteTask(task.id);
			toast.success('Task deleted');
			await loadAll();
		} catch (err) {
			toast.error(err.message);
		}
	}

	async function saveCategory() {
		if (!categoryName.trim()) return;
		try {
			if (editingCategory) {
				await updateCategory(editingCategory.id, categoryName.trim());
				toast.success('Category updated');
			} else {
				await createCategory(categoryName.trim());
				toast.success('Category created');
			}
			categoryName = '';
			editingCategory = null;
			await loadAll();
		} catch (err) {
			toast.error(err.message);
		}
	}

	async function removeCategory(category) {
		if (!confirm(`Delete category "${category.name}"?`)) return;
		try {
			await deleteCategory(category.id);
			toast.success('Category deleted');
			await loadAll();
		} catch (err) {
			toast.error(err.message);
		}
	}

	async function saveGoal() {
		try {
			await setGoals({
				points_target: Number(goalTarget),
				daily_challenges_enabled: dailyChallengesEnabled,
				daily_challenge_count: Number(dailyChallengeCount)
			});
			toast.success('Game settings updated');
		} catch (err) {
			toast.error(err.message);
		}
	}

	async function handleReset() {
		try {
			await masterReset();
			toast.success('Household reset complete');
			await loadAll();
		} catch (err) {
			toast.error(err.message);
		}
	}

	async function handleProgressReset() {
		try {
			await resetProgress();
			toast.success('Progress and points cleared');
			await loadAll();
		} catch (err) {
			toast.error(err.message);
		}
	}

	function handleDndConsider(key, event) {
		tasks = { ...tasks, [key]: event.detail.items };
	}

	async function handleDndFinalize(key, event) {
		tasks = { ...tasks, [key]: event.detail.items };
		try {
			const data = await reorderTasks(event.detail.items.map((task) => task.id));
			tasks = data;
		} catch (err) {
			toast.error(err.message);
			await loadAll();
		}
	}
</script>

<div class="mb-4 flex items-center gap-2">
	<a href="/profile" class="min-h-11 min-w-11 flex items-center justify-center text-quest-muted">←</a>
	<h1 class="text-2xl font-bold text-quest-text">Admin Panel</h1>
</div>

<div class="mb-4 flex flex-wrap gap-1 rounded-xl border border-quest-border bg-quest-surface-2 p-1">
	{#each tabs as t}
		<button
			type="button"
			class="min-h-11 flex-1 rounded-lg px-2 py-2 text-xs font-semibold
				{tab === t.key ? 'bg-quest-purple text-white' : 'text-quest-muted'}"
			onclick={() => (tab = t.key)}
		>
			{t.label}
		</button>
	{/each}
</div>

{#if loading}
	<LoadingSpinner />
{:else if tab === 'tasks'}
	{#if showTaskForm}
		<form
			onsubmit={(e) => {
				e.preventDefault();
				saveTask();
			}}
			class="space-y-3 rounded-xl border border-quest-border bg-quest-surface-2 p-4"
		>
			<h3 class="font-semibold text-quest-text">{editingTask ? 'Edit task' : 'New task'}</h3>
			<input
				class="min-h-11 w-full rounded-xl border border-quest-border bg-quest-bg px-3"
				placeholder="Task name"
				bind:value={taskForm.name}
				required
			/>
			<textarea
				class="w-full rounded-xl border border-quest-border bg-quest-bg px-3 py-2"
				placeholder="Description (optional)"
				bind:value={taskForm.description}
				rows="2"
			></textarea>
			<select class="min-h-11 w-full rounded-xl border border-quest-border bg-quest-bg px-3" bind:value={taskForm.frequency}>
				{#each FREQUENCIES as f}
					<option value={f.value}>{f.label}</option>
				{/each}
			</select>
			<input
				type="number"
				min="1"
				class="min-h-11 w-full rounded-xl border border-quest-border bg-quest-bg px-3"
				bind:value={taskForm.base_points}
			/>
			<select class="min-h-11 w-full rounded-xl border border-quest-border bg-quest-bg px-3" bind:value={taskForm.category_id}>
				{#each categories as cat}
					<option value={cat.id}>{cat.name}</option>
				{/each}
			</select>
			<select class="min-h-11 w-full rounded-xl border border-quest-border bg-quest-bg px-3" bind:value={taskForm.room}>
				{#each ROOMS as room}
					<option value={room}>{room}</option>
				{/each}
			</select>
			<label class="flex min-h-11 items-center gap-2 text-sm">
				<input type="checkbox" bind:checked={taskForm.is_required} />
				Required for streak
			</label>
			<div class="flex gap-2">
				<button type="button" class="min-h-11 flex-1 rounded-xl border border-quest-border" onclick={() => (showTaskForm = false)}>Cancel</button>
				<button type="submit" class="min-h-11 flex-1 rounded-xl bg-quest-purple font-semibold text-white">Save</button>
			</div>
		</form>
	{:else}
		<button type="button" class="mb-3 min-h-11 w-full rounded-xl bg-quest-gold font-semibold text-quest-bg" onclick={openNewTask}>
			+ Add task
		</button>
		<p class="mb-4 text-xs text-quest-muted">Drag tasks to reorder how they appear on the dashboard.</p>
		<div class="space-y-6">
			{#each frequencySections as section}
				<section>
					<h2 class="mb-3 flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-quest-purple-light">
						<span>{section.icon}</span> {section.label}
					</h2>
					{#if (tasks[section.key] ?? []).length === 0}
						<p class="rounded-xl border border-dashed border-quest-border px-4 py-6 text-center text-sm text-quest-muted">
							No {section.label.toLowerCase()} yet.
						</p>
					{:else}
						<div
							class="space-y-2"
							use:dndzone={{
								items: tasks[section.key],
								flipDurationMs: 200,
								type: section.key,
								dropTargetStyle: { outline: '2px dashed rgba(167, 139, 250, 0.5)' }
							}}
							onconsider={(event) => handleDndConsider(section.key, event)}
							onfinalize={(event) => handleDndFinalize(section.key, event)}
						>
							{#each tasks[section.key] as task (task.id)}
								<div
									animate:flip={{ duration: 200 }}
									class="rounded-xl border border-quest-border bg-quest-surface-2 p-4"
								>
									<div class="flex items-start gap-3">
										<span class="mt-1 cursor-grab text-quest-muted active:cursor-grabbing" aria-hidden="true">⠿</span>
										<div class="min-w-0 flex-1">
											<p class="font-medium text-quest-text">{task.name}</p>
											<p class="text-xs text-quest-muted">{task.room} · {task.base_points} pts · {task.category?.name}</p>
											<div class="mt-2 flex gap-2">
												<button type="button" class="min-h-11 flex-1 rounded-lg border border-quest-border text-sm" onclick={() => openEditTask(task)}>Edit</button>
												<button type="button" class="min-h-11 flex-1 rounded-lg border border-red-500/30 text-sm text-red-300" onclick={() => removeTask(task)}>Delete</button>
											</div>
										</div>
									</div>
								</div>
							{/each}
						</div>
					{/if}
				</section>
			{/each}
		</div>
	{/if}
{:else if tab === 'categories'}
	<div class="mb-3 flex gap-2">
		<input
			class="min-h-11 flex-1 rounded-xl border border-quest-border bg-quest-surface-2 px-3"
			placeholder="Category name"
			bind:value={categoryName}
		/>
		<button type="button" class="min-h-11 rounded-xl bg-quest-purple px-4 font-semibold text-white" onclick={saveCategory}>
			{editingCategory ? 'Update' : 'Add'}
		</button>
	</div>
	<div class="space-y-2">
		{#each categories as cat (cat.id)}
			<div class="flex min-h-11 items-center justify-between rounded-xl border border-quest-border bg-quest-surface-2 px-4">
				<span class="text-quest-text">{cat.name}</span>
				<div class="flex gap-2">
					<button type="button" class="text-xs text-quest-purple-light" onclick={() => { editingCategory = cat; categoryName = cat.name; }}>Edit</button>
					<button type="button" class="text-xs text-red-300" onclick={() => removeCategory(cat)}>Delete</button>
				</div>
			</div>
		{/each}
	</div>
{:else if tab === 'goals'}
	<div class="space-y-4">
		<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4">
			<label for="goal-target" class="block text-sm text-quest-muted">Weekly points target</label>
			<input id="goal-target" type="number" min="1" class="mt-2 min-h-11 w-full rounded-xl border border-quest-border bg-quest-bg px-3" bind:value={goalTarget} />
		</div>

		<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4">
			<div class="flex items-start justify-between gap-4">
				<div>
					<p class="font-medium text-quest-text">Daily challenges</p>
					<p class="mt-1 text-sm text-quest-muted">
						Random tasks highlighted each day with a 50% point bonus. Turn this off to show all tasks in the regular lists only.
					</p>
				</div>
				<label class="flex shrink-0 items-center gap-2">
					<input
						type="checkbox"
						class="h-5 w-5 rounded border-quest-border"
						bind:checked={dailyChallengesEnabled}
					/>
					<span class="text-sm text-quest-muted">{dailyChallengesEnabled ? 'On' : 'Off'}</span>
				</label>
			</div>

			{#if dailyChallengesEnabled}
				<label for="challenge-count" class="mt-4 block text-sm text-quest-muted">
					Number of daily challenges
				</label>
				<select
					id="challenge-count"
					class="mt-2 min-h-11 w-full rounded-xl border border-quest-border bg-quest-bg px-3"
					bind:value={dailyChallengeCount}
				>
					{#each [1, 2, 3, 4, 5] as count}
						<option value={count}>{count}</option>
					{/each}
				</select>
			{/if}
		</div>

		<button type="button" class="min-h-11 w-full rounded-xl bg-quest-purple font-semibold text-white" onclick={saveGoal}>
			Save settings
		</button>
	</div>
{:else}
	<div class="space-y-4">
		<div class="rounded-xl border border-orange-500/30 bg-orange-500/10 p-4">
			<h3 class="font-semibold text-orange-200">Clear progress</h3>
			<p class="mt-2 text-sm text-orange-200/80">
				Removes all completions, points, badges, streaks, and leaderboard scores. Your tasks, categories, and weekly goal target stay as they are.
			</p>
			<button
				type="button"
				class="mt-4 min-h-11 w-full rounded-xl bg-orange-600 font-semibold text-white"
				onclick={() => (progressResetOpen = true)}
			>
				Clear progress and points
			</button>
		</div>

		<div class="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
			<h3 class="font-semibold text-red-200">Master reset</h3>
			<p class="mt-2 text-sm text-red-200/80">
				Permanently deletes all tasks, completions, badges, leaderboard data, and weekly goals for your household. Categories and user accounts are kept. This cannot be undone.
			</p>
			<button type="button" class="mt-4 min-h-11 w-full rounded-xl bg-red-600 font-semibold text-white" onclick={() => (resetOpen = true)}>
				Reset everything
			</button>
		</div>
	</div>
{/if}

<ConfirmDialog
	bind:open={progressResetOpen}
	title="Clear progress?"
	message="This will delete all completions, points, badges, and scores. Your tasks will not be changed."
	confirmLabel="Clear progress"
	danger
	onconfirm={handleProgressReset}
/>

<ConfirmDialog
	bind:open={resetOpen}
	title="Master reset?"
	message="This will permanently delete all tasks, completions, badges, scores, and weekly goals. This cannot be undone."
	confirmLabel="Reset everything"
	danger
	onconfirm={handleReset}
/>
