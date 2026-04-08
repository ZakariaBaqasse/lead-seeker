<script lang="ts">
  interface Props {
    title: string;
    description?: string;
    action?: { label: string; onclick: () => void };
  }

  let { title, description, action }: Props = $props();
</script>

<div class="flex flex-col items-center justify-center text-center py-12">
  <div class="w-12 h-12 text-text-tertiary mb-4 flex items-center justify-center">
    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
  </div>
  <h3 class="text-lg font-semibold text-text-primary mb-2">{title}</h3>
  {#if description}
    <p class="text-sm text-text-secondary mb-6 max-w-xs">{description}</p>
  {/if}
  {#if action}
    <button
      onclick={action.onclick}
      class="inline-flex items-center justify-center rounded-md font-medium text-sm px-3 py-1.5 bg-accent text-text-on-accent hover:bg-accent-hover transition-colors"
    >
      {action.label}
    </button>
  {/if}
</div>
