/**
 * REST API client for the backend.
 */

const API_BASE = import.meta.env.VITE_API_URL || '';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export interface CallOut {
  id: string;
  customer_id: string | null;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_seconds: number | null;
}

export interface CustomerOut {
  id: string;
  name: string;
  email: string;
  phone: string;
  account_status: string;
  membership_tier: string;
  join_date: string;
  total_orders: number;
}

export const api = {
  // Calls
  startCall: (customerId?: string) =>
    request<CallOut>('/api/calls/', {
      method: 'POST',
      body: JSON.stringify({ customer_id: customerId || null }),
    }),

  endCallRest: (callId: string) =>
    request<{ message: string }>(`/api/calls/${callId}/end`, { method: 'POST' }),

  getCall: (callId: string) => request<CallOut>(`/api/calls/${callId}`),

  listCalls: () => request<CallOut[]>('/api/calls/'),

  // Customers
  listCustomers: () =>
    request<{ id: string; name: string; email: string; membership_tier: string }[]>('/api/customers'),

  getCustomer: (id: string) => request<CustomerOut>(`/api/customers/${id}`),

  // Health
  health: () => request<{ status: string }>('/health'),
};
