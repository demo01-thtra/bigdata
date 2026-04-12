const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
}

interface DashboardStats {
  total_transactions: number;
  total_frauds: number;
  fraud_rate: number;
  total_amount: number;
  total_fraud_amount: number;
  avg_fraud_amount: number;
  detection_breakdown: Record<string, number>;
}

interface Transaction {
  id: string;
  transaction_type: string;
  amount: number;
  name_orig: string;
  name_dest: string;
  old_balance_orig: number;
  new_balance_orig: number;
  old_balance_dest: number;
  new_balance_dest: number;
  is_fraud: boolean;
  fraud_probability: number;
  detection_method: string;
  created_at: string;
}

interface FraudAlert {
  id: number;
  transaction_id: string;
  alert_type: string;
  reason: string;
  risk_score: number;
  created_at: string;
}

interface TimelinePoint {
  timestamp: string;
  total: number;
  frauds: number;
}

interface TypeBreakdown {
  transaction_type: string;
  total: number;
  frauds: number;
  fraud_rate: number;
}

async function fetchApi<T>(endpoint: string): Promise<T> {
  const res = await fetch(`${API_BASE}${endpoint}`, {
    cache: 'no-store',
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getStats(): Promise<DashboardStats> {
  return fetchApi<DashboardStats>('/api/stats');
}

export async function getTimeline(hours: number = 24): Promise<TimelinePoint[]> {
  return fetchApi<TimelinePoint[]>(`/api/stats/timeline?hours=${hours}`);
}

export async function getStatsByType(): Promise<TypeBreakdown[]> {
  return fetchApi<TypeBreakdown[]>('/api/stats/by-type');
}

export async function getTransactions(
  page: number = 1,
  perPage: number = 20,
  isFraud?: boolean,
): Promise<PaginatedResponse<Transaction>> {
  let url = `/api/transactions?page=${page}&per_page=${perPage}`;
  if (isFraud !== undefined) url += `&is_fraud=${isFraud}`;
  return fetchApi<PaginatedResponse<Transaction>>(url);
}

export async function getFraudAlerts(
  page: number = 1,
  perPage: number = 20,
): Promise<PaginatedResponse<FraudAlert>> {
  return fetchApi<PaginatedResponse<FraudAlert>>(`/api/frauds?page=${page}&per_page=${perPage}`);
}

export type {
  DashboardStats, Transaction, FraudAlert,
  TimelinePoint, TypeBreakdown, PaginatedResponse,
};
