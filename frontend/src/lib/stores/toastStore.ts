import { writable } from 'svelte/store';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  message: string;
  type: ToastType;
  duration: number;
}

function createToastStore() {
  const { subscribe, update } = writable<Toast[]>([]);

  function addToast(message: string, type: ToastType = 'info', duration = 3000) {
    const id = crypto.randomUUID();
    update((toasts) => [...toasts, { id, message, type, duration }]);

    if (duration > 0) {
      setTimeout(() => dismissToast(id), duration);
    }
    return id;
  }

  function dismissToast(id: string) {
    update((toasts) => toasts.filter((t) => t.id !== id));
  }

  return { subscribe, addToast, dismissToast };
}

export const toastStore = createToastStore();
