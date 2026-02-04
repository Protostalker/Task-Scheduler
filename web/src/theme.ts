export function initTheme() {
  const saved = localStorage.getItem('theme');
  const prefersDark = window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches;

  // Only respect explicit saved values; otherwise follow system WITHOUT persisting.
  const savedMode = (saved === 'dark' || saved === 'light') ? saved : null;
  const mode = savedMode || (prefersDark ? 'dark' : 'light');
  setTheme(mode, !!savedMode);
}

export function setTheme(mode: string, persist: boolean = true) {
  const root = document.documentElement;
  if (mode === 'dark') root.classList.add('dark');
  else root.classList.remove('dark');

  if (persist) localStorage.setItem('theme', mode);
  else localStorage.removeItem('theme');
}

export function toggleTheme() {
  const isDark = document.documentElement.classList.contains('dark');
  setTheme(isDark ? 'light' : 'dark', true);
}
