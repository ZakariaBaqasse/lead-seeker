<script lang="ts">
  import '../app.css';
  import { page } from '$app/stores';

  let { children } = $props();
</script>

<div class="flex min-h-screen bg-bg">
  <!-- Sidebar -->
  <aside class="w-60 shrink-0 border-r border-border bg-bg-subtle flex flex-col">
    <div class="p-4 border-b border-border">
      <h1 class="text-base font-semibold text-text-primary">Lead Seeker</h1>
      <p class="text-xs text-text-tertiary mt-0.5">GenAI Outreach Dashboard</p>
    </div>

    <nav class="p-3 flex-1">
      <ul class="space-y-1">
        <li>
          <a
            href="/"
            class="flex items-center gap-2.5 px-3 py-2 rounded-md text-sm transition-colors duration-[--duration-fast]
              {$page.url.pathname === '/' || $page.url.pathname.startsWith('/leads')
                ? 'bg-accent-subtle text-accent font-medium'
                : 'text-text-secondary hover:text-text-primary hover:bg-surface-hover'}"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
              <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
              <circle cx="9" cy="7" r="4"/>
              <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
              <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
            </svg>
            Leads
          </a>
        </li>
      </ul>
    </nav>

    <div class="p-3 border-t border-border">
      <p class="text-xs text-text-tertiary">Lead Seeker v1.0</p>
    </div>
  </aside>

  <!-- Main Content -->
  <main class="flex-1 min-w-0 overflow-auto">
    {@render children()}
  </main>
</div>
