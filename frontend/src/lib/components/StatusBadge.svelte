<script lang="ts">
  import type { LeadStatus } from '$lib/types';

  interface Props {
    status: LeadStatus;
  }

  let { status }: Props = $props();

  const config: Record<LeadStatus, { label: string; classes: string }> = {
    draft: { label: 'Draft', classes: 'bg-neutral-subtle text-neutral' },
    sent: { label: 'Sent', classes: 'bg-accent-subtle text-accent' },
    replied_won: { label: 'Reply Won', classes: 'bg-success-subtle text-success' },
    replied_lost: { label: 'Reply Lost', classes: 'bg-danger-subtle text-danger' },
    archived: { label: 'Archived', classes: 'bg-neutral-subtle text-neutral' }
  };

  let current = $derived(config[status] ?? config.draft);
</script>

<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium {current.classes}">
  {current.label}
</span>
