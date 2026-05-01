import type { PageServerLoad, Actions } from "./$types";
import {
  getLeads,
  getStats,
  getPipelineStatus,
  updateLead,
  deleteLead,
  runPipeline,
} from "$lib/api";
import type { LeadStatus, LeadFilters } from "$lib/types";
import { fail } from "@sveltejs/kit";

export const load: PageServerLoad = async ({ url }) => {
  const status = url.searchParams.get("status") as LeadStatus | null;
  const region = url.searchParams.get("region") ?? undefined;
  const from = url.searchParams.get("from") ?? undefined;
  const to = url.searchParams.get("to") ?? undefined;
  const search = url.searchParams.get("search") ?? undefined;
  const page = parseInt(url.searchParams.get("page") ?? "1", 10);
  const limit = parseInt(url.searchParams.get("limit") ?? "20", 10);
  const sort_by = url.searchParams.get("sort_by") ?? "created_at";
  const sort_dir = (url.searchParams.get("sort_dir") ?? "desc") as
    | "asc"
    | "desc";

  const filters: LeadFilters = {
    ...(status ? { status } : {}),
    region,
    from,
    to,
    search,
    page,
    limit,
    sort_by,
    sort_dir,
  };

  const [leadsData, stats, pipelineStatus] = await Promise.all([
    getLeads(filters).catch(() => ({ items: [], total: 0 })),
    getStats().catch(() => ({
      draft: 0,
      sent: 0,
      replied_won: 0,
      replied_lost: 0,
      archived: 0,
      no_response: 0,
      total: 0,
    })),
    getPipelineStatus().catch(() => ({
      last_run: null,
      leads_found: 0,
      errors: [],
      is_running: false,
    })),
  ]);

  return {
    leads: leadsData.items,
    total: leadsData.total,
    page,
    limit,
    sort_by,
    sort_dir,
    stats,
    pipelineStatus,
    filters: { status, region, from, to, search },
  };
};

export const actions: Actions = {
  "advance-status": async ({ request }) => {
    const data = await request.formData();
    const id = data.get("id") as string;
    const status = data.get("status") as Exclude<LeadStatus, "no_response">;
    if (!id || !status) return fail(400, { error: "Missing id or status" });
    try {
      await updateLead(id, { status });
      return { success: true };
    } catch {
      return fail(500, { error: "Failed to update status" });
    }
  },

  archive: async ({ request }) => {
    const data = await request.formData();
    const id = data.get("id") as string;
    if (!id) return fail(400, { error: "Missing id" });
    try {
      await deleteLead(id);
      return { success: true };
    } catch {
      return fail(500, { error: "Failed to archive lead" });
    }
  },

  "run-pipeline": async () => {
    try {
      await runPipeline();
      return { success: true, message: "Pipeline started successfully" };
    } catch (e) {
      console.error("Failed to start pipeline:", e);
      return fail(500, { error: "Failed to start pipeline" });
    }
  },
};
