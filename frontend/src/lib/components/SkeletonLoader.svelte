<script lang="ts">
  interface Props {
    count?: number;
    type?: 'row' | 'card' | 'line';
  }

  let { count = 5, type = 'row' }: Props = $props();
</script>

<div class="space-y-2 w-full">
  {#each Array(count) as _, i}
    {#if type === 'row'}
      <div class="flex gap-4 px-4 py-3 border-b border-border animate-pulse">
        <div class="h-4 bg-border rounded w-1/4"></div>
        <div class="h-4 bg-border rounded w-1/6"></div>
        <div class="h-4 bg-border rounded w-1/5"></div>
        <div class="h-4 bg-border rounded w-1/6"></div>
        <div class="h-4 bg-border rounded w-1/4"></div>
      </div>
    {:else if type === 'card'}
      <div class="p-4 border border-border rounded-lg animate-pulse">
        <div class="h-5 bg-border rounded w-1/3 mb-3"></div>
        <div class="h-4 bg-border rounded w-2/3 mb-2"></div>
        <div class="h-4 bg-border rounded w-1/2"></div>
      </div>
    {:else}
      <div class="h-4 bg-border rounded animate-pulse" style="width: {70 + (i % 3) * 10}%"></div>
    {/if}
  {/each}
</div>
