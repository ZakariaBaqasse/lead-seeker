<script lang="ts" generics="T extends Record<string, unknown>">
  import type { Snippet } from 'svelte';
  import EmptyState from './EmptyState.svelte';

  interface Column<T> {
    key: keyof T | string;
    label: string;
    sortable?: boolean;
    width?: string;
    render?: Snippet<[T]>;
  }

  interface Props {
    columns: Column<T>[];
    rows: T[];
    sortBy?: string;
    sortDir?: 'asc' | 'desc';
    onSort?: (key: string, dir: 'asc' | 'desc') => void;
    onRowClick?: (row: T) => void;
    emptyTitle?: string;
    emptyDescription?: string;
    loading?: boolean;
  }

  let {
    columns,
    rows,
    sortBy,
    sortDir = 'asc',
    onSort,
    onRowClick,
    emptyTitle = 'No data',
    emptyDescription = '',
    loading = false
  }: Props = $props();

  function handleSort(key: string) {
    if (!onSort) return;
    const newDir = sortBy === key && sortDir === 'asc' ? 'desc' : 'asc';
    onSort(key, newDir);
  }

  function getCellValue(row: T, key: string): unknown {
    return (row as Record<string, unknown>)[key];
  }
</script>

<div class="w-full overflow-x-auto">
  <table class="w-full border-collapse text-sm">
    <thead>
      <tr class="bg-bg-subtle border-b border-border">
        {#each columns as col}
          <th
            class="px-4 py-3 text-left text-xs font-medium text-text-secondary uppercase tracking-wider whitespace-nowrap
              {col.sortable ? 'cursor-pointer select-none hover:text-text-primary' : ''}"
            style={col.width ? `width: ${col.width}` : ''}
            onclick={() => col.sortable && handleSort(String(col.key))}
          >
            <span class="inline-flex items-center gap-1">
              {col.label}
              {#if col.sortable}
                <span class="text-text-tertiary">
                  {#if sortBy === String(col.key)}
                    {#if sortDir === 'asc'}↑{:else}↓{/if}
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
      {#if !loading && rows.length === 0}
        <tr>
          <td colspan={columns.length} class="px-4 py-12">
            <EmptyState title={emptyTitle} description={emptyDescription} />
          </td>
        </tr>
      {:else}
        {#each rows as row}
          <tr
            class="border-b border-border transition-colors duration-[--duration-fast]
              {onRowClick ? 'cursor-pointer hover:bg-surface-hover' : ''}"
            onclick={() => onRowClick?.(row)}
          >
            {#each columns as col}
              <td class="px-4 py-3 text-text-primary">
                {#if col.render}
                  {@render col.render(row)}
                {:else}
                  {getCellValue(row, String(col.key)) ?? '—'}
                {/if}
              </td>
            {/each}
          </tr>
        {/each}
      {/if}
    </tbody>
  </table>
</div>
