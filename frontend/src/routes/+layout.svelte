<script>
	import { browser } from '$app/environment';
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	import '../app.css';
	import favicon from '$lib/assets/favicon.svg';
	import { auth } from '$lib/stores/auth';
	import '$lib/stores/theme';

	let { children } = $props();

	const publicPaths = ['/login', '/register'];
	const publicPrefixes = ['/password-reset'];

	function isPublicPath(pathname) {
		if (publicPaths.includes(pathname)) return true;
		return publicPrefixes.some((prefix) => pathname.startsWith(prefix));
	}

	$effect(() => {
		if (!browser) return;

		const pathname = page.url.pathname;
		const loggedIn = Boolean($auth.token);

		if (pathname === '/') return;

		if (!loggedIn && !isPublicPath(pathname)) {
			goto('/login');
			return;
		}

		if (loggedIn && (pathname === '/login' || pathname === '/register')) {
			goto('/dashboard');
		}
	});
</script>

<svelte:head>
	<link rel="icon" href={favicon} />
	<title>Chore Quest</title>
	<meta name="theme-color" content="#0c0a12" />
</svelte:head>

<div class="mx-auto min-h-dvh w-full max-w-[480px] bg-quest-bg">
	{@render children()}
</div>
