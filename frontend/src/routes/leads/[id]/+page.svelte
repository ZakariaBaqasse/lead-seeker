<script lang="ts">
  import { enhance } from "$app/forms";
  import type { PageData, ActionData } from "./$types";
  import type { LeadStatus } from "$lib/types";
  import { toastStore } from "$lib/stores/toastStore";
  import { format } from "date-fns";

  import StatusBadge from "$lib/components/StatusBadge.svelte";
  import Button from "$lib/components/Button.svelte";
  import Input from "$lib/components/Input.svelte";
  import TextArea from "$lib/components/TextArea.svelte";
  import Modal from "$lib/components/Modal.svelte";

  interface Props {
    data: PageData;
    form: ActionData;
  }

  let { data, form }: Props = $props();

  // Local editable state synced from server data via $effect
  let cto_name = $state("");
  let cto_email = $state("");
  let linkedin_url = $state("");
  let notes = $state("");
  let status = $state<LeadStatus>("draft");
  let email_draft = $state("");

  // Initialize from data prop (avoids state_referenced_locally warning)
  $effect(() => {
    cto_name = data.lead.cto_name ?? "";
    cto_email = data.lead.cto_email ?? "";
    linkedin_url = data.lead.linkedin_url ?? "";
    notes = data.lead.notes ?? "";
    status = data.lead.status;
    email_draft = data.lead.email_draft ?? "";
  });

  // UI state
  let isSubmitting = $state(false);
  let isRegenerating = $state(false);
  let showDeleteModal = $state(false);
  let copied = $state(false);

  // Sync from updated form action data
  $effect(() => {
    if (form && "success" in form && form.success) {
      if ("lead" in form && form.lead) {
        cto_name = form.lead.cto_name ?? "";
        cto_email = form.lead.cto_email ?? "";
        linkedin_url = form.lead.linkedin_url ?? "";
        notes = form.lead.notes ?? "";
        status = form.lead.status;
        toastStore.addToast("Lead updated successfully", "success");
      } else if ("email_draft" in form && form.email_draft) {
        email_draft = form.email_draft;
        toastStore.addToast("Email draft regenerated", "success");
      }
    } else if (form && "error" in form && form.error) {
      toastStore.addToast(form.error as string, "error");
    }
  });

  function resetForm() {
    cto_name = data.lead.cto_name ?? "";
    cto_email = data.lead.cto_email ?? "";
    linkedin_url = data.lead.linkedin_url ?? "";
    notes = data.lead.notes ?? "";
    status = data.lead.status;
  }

  async function copyToClipboard() {
    if (!email_draft) return;
    try {
      await navigator.clipboard.writeText(email_draft);
      copied = true;
      setTimeout(() => (copied = false), 2000);
    } catch {
      toastStore.addToast("Failed to copy to clipboard", "error");
    }
  }

  function formatDate(dateStr: string | null): string {
    if (!dateStr) return "—";
    try {
      return format(new Date(dateStr), "MMM d, yyyy");
    } catch {
      return "—";
    }
  }

  function formatDateTime(dateStr: string | null): string {
    if (!dateStr) return "—";
    try {
      return format(new Date(dateStr), "MMM d, yyyy HH:mm");
    } catch {
      return "—";
    }
  }

  const statusOptions: { value: LeadStatus; label: string }[] = [
    { value: "draft", label: "Draft" },
    { value: "sent", label: "Sent" },
    { value: "replied_won", label: "Reply Won" },
    { value: "replied_lost", label: "Reply Lost" },
    { value: "archived", label: "Archived" },
  ];
</script>

<div class="p-8 max-w-225 mx-auto space-y-8">
  <!-- Header -->
  <div class="flex items-start justify-between gap-4">
    <div>
      <a
        href="/"
        class="text-sm text-text-secondary hover:text-accent transition-colors inline-flex items-center gap-1 mb-3"
      >
        ← Back to Leads
      </a>
      <div class="flex items-center gap-3">
        <h1 class="text-3xl font-bold text-text-primary">
          {data.lead.company_name}
        </h1>
        <StatusBadge {status} />
      </div>
      {#if data.lead.company_domain}
        <a
          href="https://{data.lead.company_domain}"
          target="_blank"
          rel="noopener noreferrer"
          class="text-sm text-accent hover:underline mt-1 inline-block"
          >{data.lead.company_domain}</a
        >
      {/if}
    </div>
  </div>

  <!-- Two-column layout: main content + sidebar -->
  <div class="grid grid-cols-1 lg:grid-cols-[1fr_260px] gap-8">
    <!-- Main content -->
    <div class="space-y-8">
      <!-- Company Information -->
      <section>
        <h2
          class="text-base font-semibold text-text-primary mb-4 pb-2 border-b border-border"
        >
          Company Information
        </h2>
        <dl class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt class="text-text-secondary mb-1">Company</dt>
            <dd class="text-text-primary font-medium">
              {data.lead.company_name}
            </dd>
          </div>
          <div>
            <dt class="text-text-secondary mb-1">Region / Country</dt>
            <dd class="text-text-primary">
              {[data.lead.region, data.lead.country]
                .filter(Boolean)
                .join(", ") || "—"}
            </dd>
          </div>
          <div>
            <dt class="text-text-secondary mb-1">Employees</dt>
            <dd class="text-text-primary">{data.lead.employee_count ?? "—"}</dd>
          </div>
          {#if data.lead.company_description}
            <div class="col-span-2">
              <dt class="text-text-secondary mb-1">Description</dt>
              <dd class="text-text-primary leading-relaxed">
                {data.lead.company_description}
              </dd>
            </div>
          {/if}
          {#if data.lead.product_description}
            <div class="col-span-2">
              <dt class="text-text-secondary mb-1">Product Description</dt>
              <dd class="text-text-primary leading-relaxed">
                {data.lead.product_description}
              </dd>
            </div>
          {/if}
          {#if data.lead.tech_stack}
            <div class="col-span-2">
              <dt class="text-text-secondary mb-1">Tech Stack</dt>
              <dd class="text-text-primary leading-relaxed">
                {data.lead.tech_stack}
              </dd>
            </div>
          {/if}
        </dl>
      </section>

      <!-- Funding Information -->
      <section>
        <h2
          class="text-base font-semibold text-text-primary mb-4 pb-2 border-b border-border"
        >
          Funding
        </h2>
        <dl class="grid grid-cols-2 gap-4 text-sm">
          <div>
            <dt class="text-text-secondary mb-1">Amount</dt>
            <dd class="text-text-primary font-medium">
              {data.lead.funding_amount ?? "—"}
            </dd>
          </div>
          <div>
            <dt class="text-text-secondary mb-1">Round</dt>
            <dd class="text-text-primary">{data.lead.funding_round ?? "—"}</dd>
          </div>
          <div>
            <dt class="text-text-secondary mb-1">Date</dt>
            <dd class="text-text-primary">
              {formatDate(data.lead.funding_date)}
            </dd>
          </div>
        </dl>
      </section>

      <!-- News Source -->
      {#if data.lead.news_headline}
        <section>
          <h2
            class="text-base font-semibold text-text-primary mb-4 pb-2 border-b border-border"
          >
            Source
          </h2>
          <div class="text-sm">
            {#if data.lead.news_url}
              <a
                href={data.lead.news_url}
                target="_blank"
                rel="noopener noreferrer"
                class="text-accent hover:underline leading-relaxed"
                >{data.lead.news_headline}</a
              >
            {:else}
              <p class="text-text-secondary leading-relaxed">
                {data.lead.news_headline}
              </p>
            {/if}
          </div>
        </section>
      {/if}

      <!-- Editable Form: CTO Details, Notes, Status -->
      <section>
        <h2
          class="text-base font-semibold text-text-primary mb-4 pb-2 border-b border-border"
        >
          Contact & Status
        </h2>
        <form
          method="POST"
          action="?/update-lead"
          class="space-y-4"
          use:enhance={() => {
            isSubmitting = true;
            return async ({ update }) => {
              isSubmitting = false;
              await update({ reset: false });
            };
          }}
        >
          <!-- Status selector -->
          <div class="flex flex-col gap-1">
            <label
              for="status-select"
              class="text-sm font-medium text-text-secondary">Status</label
            >
            <select
              id="status-select"
              name="status"
              bind:value={status}
              class="w-full bg-bg border border-border rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
            >
              {#each statusOptions as opt}
                <option value={opt.value}>{opt.label}</option>
              {/each}
            </select>
          </div>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              bind:value={cto_name}
              name="cto_name"
              label="CTO Name"
              placeholder="Jane Smith"
            />
            <Input
              bind:value={cto_email}
              name="cto_email"
              type="email"
              label="CTO Email"
              placeholder="jane@company.com"
            />
          </div>
          <Input
            bind:value={linkedin_url}
            name="linkedin_url"
            type="url"
            label="LinkedIn URL"
            placeholder="https://linkedin.com/in/..."
          />
          <TextArea
            bind:value={notes}
            name="notes"
            label="Notes"
            placeholder="Add your notes here..."
            rows={4}
          />

          <div class="flex gap-2 pt-2">
            <Button type="submit" loading={isSubmitting}>Save Changes</Button>
            <Button variant="secondary" onclick={resetForm} type="button"
              >Cancel</Button
            >
          </div>
        </form>
      </section>

      <!-- Email Draft -->
      <section>
        <div
          class="flex items-center justify-between mb-4 pb-2 border-b border-border"
        >
          <h2 class="text-base font-semibold text-text-primary">Email Draft</h2>
          <div class="flex gap-2">
            <Button
              size="sm"
              variant="ghost"
              onclick={copyToClipboard}
              type="button"
            >
              {copied ? "✓ Copied" : "Copy"}
            </Button>
            <form
              method="POST"
              action="?/regenerate-email"
              use:enhance={() => {
                isRegenerating = true;
                return async ({ update }) => {
                  isRegenerating = false;
                  await update({ reset: false });
                };
              }}
            >
              <Button
                size="sm"
                variant="secondary"
                type="submit"
                loading={isRegenerating}
              >
                Regenerate
              </Button>
            </form>
          </div>
        </div>

        {#if email_draft}
          <pre
            class="bg-bg-subtle border border-border rounded-md p-4 text-sm font-mono text-text-primary whitespace-pre-wrap leading-relaxed min-h-50 overflow-auto">{email_draft}</pre>
        {:else}
          <div
            class="bg-bg-subtle border border-border rounded-md p-8 text-center text-sm text-text-tertiary"
          >
            Awaiting email generation
          </div>
        {/if}
      </section>

      <!-- Delete -->
      <section class="pt-4 border-t border-border">
        <Button
          variant="danger"
          onclick={() => (showDeleteModal = true)}
          type="button"
        >
          Archive Lead
        </Button>
      </section>
    </div>

    <!-- Sidebar: Metadata -->
    <aside class="space-y-4">
      <div
        class="bg-bg-subtle border border-border rounded-md p-4 space-y-3 text-sm"
      >
        <h3
          class="font-semibold text-text-primary text-xs uppercase tracking-wider"
        >
          Metadata
        </h3>
        <dl class="space-y-3">
          <div>
            <dt class="text-text-tertiary text-xs mb-0.5">Lead ID</dt>
            <dd class="font-mono text-text-secondary text-xs break-all">
              {data.lead.id}
            </dd>
          </div>
          <div>
            <dt class="text-text-tertiary text-xs mb-0.5">Created</dt>
            <dd class="text-text-primary">
              {formatDateTime(data.lead.created_at)}
            </dd>
          </div>
          <div>
            <dt class="text-text-tertiary text-xs mb-0.5">Updated</dt>
            <dd class="text-text-primary">
              {formatDateTime(data.lead.updated_at)}
            </dd>
          </div>
          {#if data.lead.sent_at}
            <div>
              <dt class="text-text-tertiary text-xs mb-0.5">Sent At</dt>
              <dd class="text-text-primary">
                {formatDateTime(data.lead.sent_at)}
              </dd>
            </div>
          {/if}
        </dl>
      </div>
    </aside>
  </div>
</div>

<!-- Delete Confirmation Modal -->
<Modal
  isOpen={showDeleteModal}
  title="Archive this lead?"
  onClose={() => (showDeleteModal = false)}
>
  <p class="text-sm text-text-secondary mb-6">
    This will permanently remove <strong class="text-text-primary"
      >{data.lead.company_name}</strong
    > from your pipeline. This action cannot be undone.
  </p>
  <form method="POST" action="?/delete-lead" use:enhance>
    <div class="flex gap-2 justify-end">
      <Button
        variant="secondary"
        onclick={() => (showDeleteModal = false)}
        type="button">Cancel</Button
      >
      <Button variant="danger" type="submit">Archive Lead</Button>
    </div>
  </form>
</Modal>
