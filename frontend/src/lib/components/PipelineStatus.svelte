<script lang="ts">
  import { formatDistanceToNow } from 'date-fns';
  import type { PipelineStatus } from '$lib/types';

  interface Props {
    pipelineStatus: PipelineStatus;
  }

  let { pipelineStatus }: Props = $props();

  let lastRunText = $derived(
    pipelineStatus.last_run
      ? formatDistanceToNow(new Date(pipelineStatus.last_run), { addSuffix: true })
      : 'Never'
  );
</script>

<div class="flex items-center gap-4 text-sm text-text-secondary">
  <span>
    Last run: <span class="text-text-primary font-medium">{lastRunText}</span>
  </span>
  {#if pipelineStatus.last_run}
    <span>
      Leads found: <span class="text-text-primary font-medium">{pipelineStatus.leads_found}</span>
    </span>
  {/if}
  {#if pipelineStatus.errors.length > 0}
    <span class="text-danger">
      {pipelineStatus.errors.length} error{pipelineStatus.errors.length > 1 ? 's' : ''}
    </span>
  {/if}
  {#if pipelineStatus.is_running}
    <span class="text-accent font-medium animate-pulse">● Running...</span>
  {/if}
</div>
