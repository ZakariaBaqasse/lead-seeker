<script lang="ts">
  interface Props {
    value?: string;
    placeholder?: string;
    disabled?: boolean;
    required?: boolean;
    name?: string;
    id?: string;
    label?: string;
    error?: string;
    rows?: number;
    oninput?: (e: Event) => void;
  }

  let {
    value = $bindable(''),
    placeholder = '',
    disabled = false,
    required = false,
    name,
    id,
    label,
    error,
    rows = 4,
    oninput
  }: Props = $props();

  let inputId = $derived(id ?? name ?? crypto.randomUUID());
  let classes = $derived(
    `w-full bg-bg border rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-tertiary focus:outline-none focus:ring-2 transition-colors resize-y ${
      error ? 'border-danger focus:ring-danger/30' : 'border-border focus:ring-accent/30 focus:border-accent'
    }`
  );
</script>

<div class="flex flex-col gap-1">
  {#if label}
    <label for={inputId} class="text-sm font-medium text-text-secondary">
      {label}{#if required}<span class="text-danger ml-0.5">*</span>{/if}
    </label>
  {/if}
  <textarea
    {name}
    id={inputId}
    bind:value
    {placeholder}
    {disabled}
    {required}
    {rows}
    class={classes}
    {oninput}
  ></textarea>
  {#if error}
    <p class="text-xs text-danger">{error}</p>
  {/if}
</div>
