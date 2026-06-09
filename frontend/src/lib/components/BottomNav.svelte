<script>
	import { page } from '$app/state';

	const links = [
		{ href: '/dashboard', label: 'Home', icon: 'home' },
		{ href: '/leaderboard', label: 'Ranks', icon: 'trophy' },
		{ href: '/badges', label: 'Badges', icon: 'badge' },
		{ href: '/profile', label: 'Profile', icon: 'user' }
	];

	function isActive(href) {
		return page.url.pathname === href;
	}
</script>

<nav
	class="fixed bottom-0 left-1/2 z-50 w-full max-w-[480px] -translate-x-1/2 border-t border-quest-border bg-quest-surface/95 backdrop-blur-md"
>
	<div class="flex items-stretch justify-around px-2 py-1 pb-[max(0.25rem,env(safe-area-inset-bottom))]">
		{#each links as link}
			<a
				href={link.href}
				class="flex flex-1 flex-col items-center gap-0.5 rounded-lg px-2 py-2 text-xs transition-colors
					{isActive(link.href)
					? 'text-quest-gold'
					: 'text-quest-muted hover:text-quest-purple-light'}"
				aria-current={isActive(link.href) ? 'page' : undefined}
			>
				{#if link.icon === 'home'}
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M3 12l9-9 9 9M5 10v10a1 1 0 001 1h3m10-11v11a1 1 0 01-1 1h-3m-4 0h4"
						/>
					</svg>
				{:else if link.icon === 'trophy'}
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M8 21h8M12 17v4M7 4h10v3a5 5 0 01-10 0V4zM5 4H3v1a4 4 0 004 4M19 4h2v1a4 4 0 01-4 4"
						/>
					</svg>
				{:else if link.icon === 'badge'}
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M12 15l-2 5 2-1 2 1-2-5m0-3a4 4 0 100-8 4 4 0 000 8z"
						/>
					</svg>
				{:else}
					<svg class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.75">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
						/>
					</svg>
				{/if}
				<span class="font-medium">{link.label}</span>
			</a>
		{/each}
	</div>
</nav>
