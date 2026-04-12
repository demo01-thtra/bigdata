'use client';

import { useEffect, useState, useCallback } from 'react';
import RealtimeAlerts from '@/components/RealtimeAlerts';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

interface FraudAlert {
  id: number;
  transaction_id: string;
  alert_type: string;
  reason: string;
  risk_score: number;
  created_at: string;
}

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<FraudAlert[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [isLoading, setIsLoading] = useState(true);

  const fetchAlerts = useCallback(async () => {
    setIsLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/frauds?page=${page}&per_page=20`);
      if (res.ok) {
        const data = await res.json();
        setAlerts(data.items || []);
        setTotalPages(data.pages || 1);
      }
    } catch {
      /* handle silently */
    } finally {
      setIsLoading(false);
    }
  }, [page]);

  useEffect(() => {
    fetchAlerts();
    const interval = setInterval(fetchAlerts, 10000);
    return () => clearInterval(interval);
  }, [fetchAlerts]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-white">Fraud Alerts</h1>
        <p className="text-slate-400 mt-1">Monitor fraud alerts in real-time</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div>
          <RealtimeAlerts />
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-white mb-4">Alert History</h3>
          {isLoading ? (
            <div className="flex items-center justify-center h-48">
              <div className="h-8 w-8 rounded-full border-4 border-blue-500 border-t-transparent animate-spin" />
            </div>
          ) : (
            <div className="space-y-3 max-h-[500px] overflow-y-auto">
              {alerts.length === 0 && (
                <p className="text-center py-8 text-slate-500">No alerts yet</p>
              )}
              {alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-3 rounded-lg bg-slate-700/50 border border-slate-600"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-white">{alert.alert_type}</span>
                    <span className="text-xs font-mono text-red-400">
                      Risk: {(alert.risk_score * 100).toFixed(0)}%
                    </span>
                  </div>
                  {alert.reason && (
                    <p className="text-xs text-slate-400 mt-1">{alert.reason}</p>
                  )}
                  <div className="flex items-center justify-between mt-2">
                    <span className="text-xs text-slate-500 font-mono">
                      {alert.transaction_id.substring(0, 8)}...
                    </span>
                    <span className="text-xs text-slate-500">
                      {new Date(alert.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-700">
              <span className="text-sm text-slate-400">Page {page} / {totalPages}</span>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page <= 1}
                  className="px-3 py-1 text-xs rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50 transition-colors"
                >
                  Prev
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page >= totalPages}
                  className="px-3 py-1 text-xs rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50 transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
