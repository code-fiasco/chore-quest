/** Sort tasks: incomplete first, completed at bottom. */
export function sortTasks(tasks) {
	return [...tasks].sort((a, b) => {
		const aDone = a.current_instance?.user_status?.is_completed || a.current_instance?.is_locked;
		const bDone = b.current_instance?.user_status?.is_completed || b.current_instance?.is_locked;
		if (aDone === bDone) return a.name.localeCompare(b.name);
		return aDone ? 1 : -1;
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
