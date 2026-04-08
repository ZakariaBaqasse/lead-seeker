<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    isOpen: boolean;
    title: string;
    size?: 'sm' | 'md' | 'lg';
    onClose: () => void;
    children?: Snippet;
  }

  let { isOpen, title, size = 'md', onClose, children }: Props = $props();

  const maxWidths = {
    sm: 'max-w-sm',
    md: 'max-w-lg',
    lg: 'max-w-2xl'
  };

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === 'Escape') onClose();
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#if isOpen}
  <!-- Backdrop -->
  <div
    class="fixed inset-0 bg-black/20 z-40 flex items-center justify-center p-4"
    onclick={onClose}
    onkeydown={(e) => e.key === 'Enter' && onClose()}
    role="dialog"
    aria-modal="true"
    aria-label={title}
    tabindex="-1"
  >
    <!-- Modal box -->
    <div
      class="bg-surface rounded-lg shadow-lg p-6 w-full {maxWidths[size]} z-50 relative"
      onclick={(e) => e.stopPropagation()}
      role="presentation"
    >
      <!-- Header -->
      <div class="flex items-center justify-between mb-4">
        <h2 class="text-lg font-semibold text-text-primary">{title}</h2>
        <button
          onclick={onClose}
          class="text-text-tertiary hover:text-text-primary transition-colors rounded-md p-1 hover:bg-surface-hover"
          aria-label="Close modal"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>

      <!-- Body -->
      {@render children?.()}
    </div>
  </div>
{/if}
