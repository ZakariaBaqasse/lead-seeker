<script lang="ts">
  import { toastStore } from '$lib/stores/toastStore';
  import Toast from './Toast.svelte';
</script>

<div class="fixed top-4 right-4 z-50 flex flex-col gap-2 pointer-events-none">
  {#each $toastStore as toast (toast.id)}
    <div class="pointer-events-auto">
      <Toast {toast} onClose={toastStore.dismissToast} />
    </div>
  {/each}
</div>
