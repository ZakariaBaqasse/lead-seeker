<script lang="ts">
  import type { Toast } from '$lib/stores/toastStore';

  interface Props {
    toast: Toast;
    onClose: (id: string) => void;
  }

  let { toast, onClose }: Props = $props();

  const typeConfig = {
    success: { classes: 'bg-success-subtle text-success border-success/20', icon: '✓' },
    error: { classes: 'bg-danger-subtle text-danger border-danger/20', icon: '✕' },
    warning: { classes: 'bg-warning-subtle text-warning border-warning/20', icon: '⚠' },
    info: { classes: 'bg-accent-subtle text-accent border-accent/20', icon: 'ℹ' }
  };

  let config = $derived(typeConfig[toast.type]);
</script>

<div class="flex items-start gap-3 p-4 rounded-md shadow-md border min-w-64 max-w-sm {config.classes}">
  <span class="text-sm font-bold shrink-0">{config.icon}</span>
  <p class="text-sm flex-1">{toast.message}</p>
  <button
    onclick={() => onClose(toast.id)}
    class="text-current opacity-60 hover:opacity-100 transition-opacity shrink-0"
    aria-label="Dismiss"
  >
    <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  </button>
</div>
