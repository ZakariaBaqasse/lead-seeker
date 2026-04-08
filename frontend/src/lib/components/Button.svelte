<script lang="ts">
  import LoadingSpinner from './LoadingSpinner.svelte';
  import type { Snippet } from 'svelte';

  interface Props {
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    loading?: boolean;
    type?: 'button' | 'submit' | 'reset';
    href?: string;
    onclick?: (e: MouseEvent) => void;
    children?: Snippet;
    class?: string;
  }

  let {
    variant = 'primary',
    size = 'md',
    disabled = false,
    loading = false,
    type = 'button',
    href,
    onclick,
    children,
    class: extraClass = ''
  }: Props = $props();

  const variantClasses = {
    primary: 'bg-accent text-text-on-accent hover:bg-accent-hover',
    secondary: 'bg-bg-subtle text-text-primary border border-border hover:bg-surface-hover',
    ghost: 'bg-transparent text-accent hover:bg-accent-subtle',
    danger: 'bg-danger text-text-on-accent hover:opacity-90'
  };

  const sizeClasses = {
    sm: 'text-xs px-2 py-1 gap-1',
    md: 'text-sm px-3 py-1.5 gap-1.5',
    lg: 'text-base px-4 py-2 gap-2'
  };

  const baseClasses = 'inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-accent/30';

  let classes = $derived(
    `${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${(disabled || loading) ? 'opacity-50 cursor-not-allowed pointer-events-none' : ''} ${extraClass}`.trim()
  );
</script>

{#if href}
  <a {href} class={classes}>
    {#if loading}<LoadingSpinner size="sm" />{/if}
    {@render children?.()}
  </a>
{:else}
  <button {type} class={classes} disabled={disabled || loading} {onclick}>
    {#if loading}<LoadingSpinner size="sm" />{/if}
    {@render children?.()}
  </button>
{/if}
