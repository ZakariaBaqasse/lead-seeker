export type LeadStatus = 'draft' | 'sent' | 'replied_won' | 'replied_lost' | 'archived' | 'no_response';

export interface Lead {
  id: string;
  company_name: string;
  company_domain: string | null;
  company_description: string | null;
  region: string | null;
  country: string | null;
  employee_count: number | null;
  funding_amount: string | null;
  funding_date: string | null;
  funding_round: string | null;
  news_headline: string | null;
  news_url: string | null;
  cto_name: string | null;
  cto_email: string | null;
  linkedin_url: string | null;
  product_description: string | null;
  tech_stack: string | null;
  status: LeadStatus;
  email_draft: string | null;
  notes: string | null;
  sent_at: string | null;
  last_contact_at: string | null;
  follow_up_count: number;
  follow_up_due_date: string | null;
  follow_up_ready: boolean;
  follow_up_generated_at: string | null;
  follow_up_draft: string | null;
  created_at: string;
  updated_at: string;
}

export interface LeadsResponse {
  items: Lead[];
  total: number;
}

export interface StatsResponse {
  draft: number;
  sent: number;
  replied_won: number;
  replied_lost: number;
  archived: number;
  no_response: number;
  total: number;
}

export interface PipelineStatus {
  last_run: string | null;
  leads_found: number;
  errors: string[];
  is_running: boolean;
}

export interface RegenerateEmailResponse {
  email_draft: string;
}

export interface LeadFilters {
  status?: LeadStatus;
  region?: string;
  from?: string;
  to?: string;
  page?: number;
  limit?: number;
  sort_by?: string;
  sort_dir?: 'asc' | 'desc';
}

export interface LeadUpdate {
  cto_name?: string | null;
  cto_email?: string | null;
  linkedin_url?: string | null;
  notes?: string | null;
  status?: Exclude<LeadStatus, 'no_response'>;
}
