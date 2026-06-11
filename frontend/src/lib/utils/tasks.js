/** Incomplete tasks first (admin sort_order), then completed tasks (admin sort_order). */
export function sortTasks(tasks) {
	return [...tasks].sort((a, b) => {
		const aDone = a.current_instance?.user_status?.is_completed || a.current_instance?.is_locked;
		const bDone = b.current_instance?.user_status?.is_completed || b.current_instance?.is_locked;
		if (aDone !== bDone) return aDone ? 1 : -1;
		const orderDiff = (a.sort_order ?? 0) - (b.sort_order ?? 0);
		if (orderDiff !== 0) return orderDiff;
		return a.id - b.id;
	});
}

export function isTaskCompletedByOther(task, userId) {
	const inst = task.current_instance;
	return inst?.is_locked && inst.completed_by_id !== userId && !inst.user_status?.is_completed;
}

export function isOwnCompletion(task, userId) {
	const inst = task.current_instance;
	return inst?.user_status?.is_completed && inst.completed_by_id === userId;
}

export function flattenTasks(grouped) {
	return [
		...(grouped?.daily ?? []),
		...(grouped?.weekly ?? []),
		...(grouped?.monthly ?? [])
	];
}
