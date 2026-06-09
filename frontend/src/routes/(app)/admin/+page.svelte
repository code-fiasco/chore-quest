<script>
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
		setGoals,
		updateCategory,
		updateTask
	} from '$lib/api';
	import ConfirmDialog from '$lib/components/ConfirmDialog.svelte';
	import LoadingSpinner from '$lib/components/LoadingSpinner.svelte';
	import { flattenTasks } from '$lib/utils/tasks';

	let tab = $state('tasks');
	let loading = $state(true);
	let tasks = $state({ daily: [], weekly: [], monthly: [] });
	let categories = $state([]);
	let goalTarget = $state(100);
	let resetOpen = $state(false);

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
			await setGoals(Number(goalTarget));
			toast.success('Weekly goal updated');
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

	const allTasks = $derived(flattenTasks(tasks));
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
		<div class="space-y-2">
			{#each allTasks as task (task.id)}
				<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4">
					<p class="font-medium text-quest-text">{task.name}</p>
					<p class="text-xs text-quest-muted">{task.frequency} · {task.room} · {task.base_points} pts</p>
					<div class="mt-2 flex gap-2">
						<button type="button" class="min-h-11 flex-1 rounded-lg border border-quest-border text-sm" onclick={() => openEditTask(task)}>Edit</button>
						<button type="button" class="min-h-11 flex-1 rounded-lg border border-red-500/30 text-sm text-red-300" onclick={() => removeTask(task)}>Delete</button>
					</div>
				</div>
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
	<div class="rounded-xl border border-quest-border bg-quest-surface-2 p-4">
		<label for="goal-target" class="block text-sm text-quest-muted">Weekly points target</label>
		<input id="goal-target" type="number" min="1" class="mt-2 min-h-11 w-full rounded-xl border border-quest-border bg-quest-bg px-3" bind:value={goalTarget} />
		<button type="button" class="mt-3 min-h-11 w-full rounded-xl bg-quest-purple font-semibold text-white" onclick={saveGoal}>Save goal</button>
	</div>
{:else}
	<div class="rounded-xl border border-red-500/30 bg-red-500/10 p-4">
		<h3 class="font-semibold text-red-200">Master reset</h3>
		<p class="mt-2 text-sm text-red-200/80">
			This permanently deletes all tasks, completions, badges, and leaderboard data for your household. This cannot be undone.
		</p>
		<button type="button" class="mt-4 min-h-11 w-full rounded-xl bg-red-600 font-semibold text-white" onclick={() => (resetOpen = true)}>
			Reset household
		</button>
	</div>
{/if}

<ConfirmDialog
	bind:open={resetOpen}
	title="Master reset?"
	message="This will permanently delete all tasks, completions, badges, and scores. This cannot be undone."
	confirmLabel="Reset everything"
	danger
	onconfirm={handleReset}
/>
