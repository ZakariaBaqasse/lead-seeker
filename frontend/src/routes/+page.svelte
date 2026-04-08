<script lang="ts">
  import { goto } from '$app/navigation';
  import { enhance } from '$app/forms';
  import { page } from '$app/stores';
  import type { PageData, ActionData } from './$types';
  import type { LeadStatus } from '$lib/types';
  import { toastStore } from '$lib/stores/toastStore';

  import StatusBadge from '$lib/components/StatusBadge.svelte';
  import Button from '$lib/components/Button.svelte';
  import StatsHeader from '$lib/components/StatsHeader.svelte';
  import PipelineStatus from '$lib/components/PipelineStatus.svelte';
  import EmptyState from '$lib/components/EmptyState.svelte';
  import { format } from 'date-fns';

  interface Props {
    data: PageData;
    form: ActionData;
  }

  let { data, form }: Props = $props();

  let pipelineRunning = $state(false);
  let activeFilters = $state({ status: '', region: '', from: '', to: '' });

  // Sync filter UI with URL-driven data whenever navigation updates data
  $effect(() => {
    activeFilters = {
      status: data.filters.status ?? '',
      region: data.filters.region ?? '',
      from: data.filters.from ?? '',
      to: data.filters.to ?? ''
    };
  });

  $effect(() => {
    if (!form) return;
    if ('message' in form && form.message) {
      toastStore.addToast(String(form.message), 'success');
    } else if ('error' in form && form.error) {
      toastStore.addToast(String(form.error), 'error');
    }
  });

  function updateUrl(params: Record<string, string>) {
    const current = new URLSearchParams($page.url.searchParams);
    for (const [k, v] of Object.entries(params)) {
      if (v) current.set(k, v);
      else current.delete(k);
    }
    if (!params.page) current.delete('page');
    goto(`?${current.toString()}`, { invalidateAll: true });
  }

  function applyFilters() {
    updateUrl({
      status: activeFilters.status,
      region: activeFilters.region,
      from: activeFilters.from,
      to: activeFilters.to
    });
  }

  function resetFilters() {
    activeFilters = { status: '', region: '', from: '', to: '' };
    goto('/', { invalidateAll: true });
  }

  function handleSort(key: string, dir: 'asc' | 'desc') {
    updateUrl({ sort_by: key, sort_dir: dir, page: data.page.toString() });
  }

  function goToPage(p: number) {
    updateUrl({ page: p.toString() });
  }

  const totalPages = $derived(Math.ceil(data.total / data.limit));

  function formatDate(dateStr: string | null | undefined): string {
    if (!dateStr) return '—';
    try {
      return format(new Date(dateStr), 'MMM d, yyyy');
    } catch {
      return '—';
    }
  }

  const statusOptions: { value: LeadStatus | ''; label: string }[] = [
    { value: '', label: 'All Statuses' },
    { value: 'draft', label: 'Draft' },
    { value: 'sent', label: 'Sent' },
    { value: 'replied_won', label: 'Reply Won' },
    { value: 'replied_lost', label: 'Reply Lost' },
    { value: 'archived', label: 'Archived' }
  ];

  const regionOptions = [
    { value: '', label: 'All Regions' },
    { value: 'Europe', label: 'Europe' },
    { value: 'USA', label: 'USA' }
  ];

  const columns = [
    { key: 'company_name', label: 'Company', sortable: true },
    { key: 'company_domain', label: 'Domain', sortable: false },
    { key: 'funding_amount', label: 'Funding', sortable: false },
    { key: 'funding_date', label: 'Funded', sortable: true },
    { key: 'cto_name', label: 'CTO', sortable: false },
    { key: 'status', label: 'Status', sortable: true },
    { key: 'created_at', label: 'Added', sortable: true },
    { key: 'actions', label: '', sortable: false }
  ];
</script>

<div class="p-6 max-w-[1100px] mx-auto space-y-6">
  <!-- Header row -->
  <div class="flex items-center justify-between">
    <div>
      <h1 class="text-2xl font-bold text-text-primary">Leads</h1>
      <p class="text-sm text-text-secondary mt-1">
        {data.total} total lead{data.total !== 1 ? 's' : ''}
      </p>
    </div>

    <div class="flex items-center gap-4">
      <PipelineStatus pipelineStatus={data.pipelineStatus} />
      <form
        method="POST"
        action="?/run-pipeline"
        use:enhance={() => {
          pipelineRunning = true;
          return async ({ update }) => {
            pipelineRunning = false;
            await update();
          };
        }}
      >
        <Button type="submit" variant="secondary" size="sm" loading={pipelineRunning}>
          Run Discovery
        </Button>
      </form>
    </div>
  </div>

  <!-- Stats -->
  <StatsHeader stats={data.stats} />

  <!-- Filters -->
  <div class="flex flex-wrap items-end gap-3 p-4 bg-bg-subtle border border-border rounded-md">
    <div class="flex flex-col gap-1">
      <label for="filter-status" class="text-xs font-medium text-text-secondary">Status</label>
      <select
        id="filter-status"
        bind:value={activeFilters.status}
        class="bg-bg border border-border rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/30"
      >
        {#each statusOptions as opt (opt.value)}
          <option value={opt.value}>{opt.label}</option>
        {/each}
      </select>
    </div>

    <div class="flex flex-col gap-1">
      <label for="filter-region" class="text-xs font-medium text-text-secondary">Region</label>
      <select
        id="filter-region"
        bind:value={activeFilters.region}
        class="bg-bg border border-border rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/30"
      >
        {#each regionOptions as opt (opt.value)}
          <option value={opt.value}>{opt.label}</option>
        {/each}
      </select>
    </div>

    <div class="flex flex-col gap-1">
      <label for="filter-from" class="text-xs font-medium text-text-secondary">From</label>
      <input
        id="filter-from"
        type="date"
        bind:value={activeFilters.from}
        class="bg-bg border border-border rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/30"
      />
    </div>

    <div class="flex flex-col gap-1">
      <label for="filter-to" class="text-xs font-medium text-text-secondary">To</label>
      <input
        id="filter-to"
        type="date"
        bind:value={activeFilters.to}
        class="bg-bg border border-border rounded-md px-3 py-1.5 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/30"
      />
    </div>

    <div class="flex gap-2">
      <Button size="sm" onclick={applyFilters}>Apply</Button>
      <Button size="sm" variant="secondary" onclick={resetFilters}>Reset</Button>
    </div>
  </div>

  <!-- Table -->
  <div class="bg-surface border border-border rounded-md overflow-hidden shadow-sm">
    {#if data.leads.length === 0}
      <EmptyState
        title="No leads found"
        description={Object.values(data.filters).some(Boolean)
          ? 'No leads match the current filters. Try resetting them.'
          : 'Run the discovery pipeline to find new leads.'}
        action={Object.values(data.filters).some(Boolean)
          ? { label: 'Clear Filters', onclick: resetFilters }
          : undefined}
      />
    {:else}
      <table class="w-full text-sm border-collapse">
        <thead>
          <tr class="bg-bg-subtle border-b border-border">
            {#each columns as col (col.key)}
              <th
                class="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider whitespace-nowrap
                  {col.sortable ? 'cursor-pointer hover:text-text-primary select-none' : ''}"
                onclick={() =>
                  col.sortable &&
                  handleSort(
                    col.key,
                    data.sort_by === col.key && data.sort_dir === 'asc' ? 'desc' : 'asc'
                  )}
              >
                <span class="inline-flex items-center gap-1">
                  {col.label}
                  {#if col.sortable}
                    <span class="text-text-tertiary text-xs">
                      {#if data.sort_by === col.key}
                        {data.sort_dir === 'asc' ? '↑' : '↓'}
                      {:else}
                        <span class="opacity-30">↕</span>
                      {/if}
                    </span>
                  {/if}
                </span>
              </th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each data.leads as lead (lead.id)}
            <tr
              class="border-b border-border hover:bg-surface-hover transition-colors cursor-pointer"
              onclick={() => goto(`/leads/${lead.id}`)}
            >
              <td class="px-4 py-3 font-medium text-text-primary">{lead.company_name}</td>
              <td class="px-4 py-3 text-text-secondary">
                {#if lead.company_domain}
                  <a
                    href="https://{lead.company_domain}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="text-accent hover:underline"
                    onclick={(e) => e.stopPropagation()}
                  >{lead.company_domain}</a>
                {:else}
                  —
                {/if}
              </td>
              <td class="px-4 py-3 text-text-secondary">{lead.funding_amount ?? '—'}</td>
              <td class="px-4 py-3 text-text-secondary">{formatDate(lead.funding_date)}</td>
              <td class="px-4 py-3 text-text-secondary">{lead.cto_name ?? '—'}</td>
              <td class="px-4 py-3"><StatusBadge status={lead.status} /></td>
              <td class="px-4 py-3 text-text-secondary">{formatDate(lead.created_at)}</td>
              <td class="px-4 py-3" onclick={(e) => e.stopPropagation()}>
                <Button href="/leads/{lead.id}" size="sm" variant="ghost">View</Button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>

  <!-- Pagination -->
  {#if totalPages > 1}
    <div class="flex items-center justify-between text-sm text-text-secondary">
      <span>Page {data.page} of {totalPages}</span>
      <div class="flex gap-2">
        <Button
          size="sm"
          variant="secondary"
          disabled={data.page <= 1}
          onclick={() => goToPage(data.page - 1)}
        >← Previous</Button>
        <Button
          size="sm"
          variant="secondary"
          disabled={data.page >= totalPages}
          onclick={() => goToPage(data.page + 1)}
        >Next →</Button>
      </div>
    </div>
  {/if}
</div>
