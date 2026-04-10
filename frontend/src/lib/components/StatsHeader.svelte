<script lang="ts">
  import type { StatsResponse } from '$lib/types';

  interface Props {
    stats: StatsResponse;
  }

  let { stats }: Props = $props();

  const cards = $derived([
    { label: 'Total', value: stats.total, classes: 'text-text-primary' },
    { label: 'Draft', value: stats.draft, classes: 'text-neutral' },
    { label: 'Sent', value: stats.sent, classes: 'text-accent' },
    { label: 'Reply Won', value: stats.replied_won, classes: 'text-success' },
    { label: 'Reply Lost', value: stats.replied_lost, classes: 'text-danger' },
    { label: 'Archived', value: stats.archived, classes: 'text-text-tertiary' }
  ]);
</script>

<div class="grid grid-cols-3 lg:grid-cols-6 gap-3">
  {#each cards as card}
    <div class="bg-surface border border-border rounded-md p-4 text-center">
      <div class="text-2xl font-bold {card.classes}">{card.value}</div>
      <div class="text-xs text-text-secondary mt-1">{card.label}</div>
    </div>
  {/each}
</div>
