import type { PageServerLoad, Actions } from './$types';
import { getLead, updateLead, deleteLead, regenerateEmail, markFollowUpSent } from '$lib/api';
import { error, redirect, fail } from '@sveltejs/kit';
import type { LeadStatus, LeadUpdate } from '$lib/types';

export const load: PageServerLoad = async ({ params }) => {
  try {
    const lead = await getLead(params.id);
    return { lead };
  } catch (e: unknown) {
    const status = e instanceof Error && 'status' in e ? (e as { status: number }).status : 500;
    if (status === 404) {
      throw error(404, 'Lead not found');
    }
    throw error(500, 'Failed to load lead');
  }
};

export const actions: Actions = {
  'update-lead': async ({ params, request }) => {
    const data = await request.formData();
    const update: LeadUpdate = {
      cto_name: (data.get('cto_name') as string) || null,
      cto_email: (data.get('cto_email') as string) || null,
      linkedin_url: (data.get('linkedin_url') as string) || null,
      notes: (data.get('notes') as string) || null,
      status: (data.get('status') as Exclude<LeadStatus, 'no_response'>) || undefined
    };
    // Remove undefined keys
    Object.keys(update).forEach((k) => {
      if (update[k as keyof LeadUpdate] === undefined) delete update[k as keyof LeadUpdate];
    });
    try {
      const lead = await updateLead(params.id, update);
      return { success: true, lead };
    } catch (e) {
      return fail(500, { error: 'Failed to update lead' });
    }
  },

  'regenerate-email': async ({ params }) => {
    try {
      const result = await regenerateEmail(params.id);
      return { success: true, email_draft: result.email_draft };
    } catch (e) {
      return fail(500, { error: 'Failed to regenerate email draft' });
    }
  },

  'delete-lead': async ({ params }) => {
    try {
      await deleteLead(params.id);
    } catch (e) {
      return fail(500, { error: 'Failed to delete lead' });
    }
    throw redirect(303, '/');
  },

  markFollowUpSent: async ({ params }) => {
    try {
      const lead = await markFollowUpSent(params.id);
      return { success: true, lead };
    } catch (e) {
      return fail(500, { error: 'Failed to mark follow-up as sent' });
    }
  }
};
