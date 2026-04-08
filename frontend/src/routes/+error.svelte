<script lang="ts">
  import { page } from '$app/stores';
  import Button from '$lib/components/Button.svelte';
</script>

<div class="flex flex-col items-center justify-center min-h-screen p-8 text-center">
  <div class="text-6xl font-bold text-text-tertiary mb-4">{$page.status}</div>
  <h1 class="text-2xl font-semibold text-text-primary mb-2">
    {$page.status === 404 ? 'Page not found' : 'Something went wrong'}
  </h1>
  <p class="text-sm text-text-secondary mb-8 max-w-sm">
    {$page.error?.message ?? 'An unexpected error occurred.'}
  </p>
  <Button href="/">← Back to Leads</Button>
</div>
