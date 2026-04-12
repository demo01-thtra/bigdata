'use client';

import { useEffect, useState, useCallback } from 'react';
import StatsCards from '@/components/StatsCards';
import FraudByTypeChart from '@/components/FraudByTypeChart';
import TimelineChart from '@/components/TimelineChart';
import TransactionTable from '@/components/TransactionTable';
import RealtimeAlerts from '@/components/RealtimeAlerts';
import type { DashboardStats, TypeBreakdown, TimelinePoint, Transaction } from '@/lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [typeData, setTypeData] = useState<TypeBreakdown[]>([]);
  const [timeline, setTimeline] = useState<TimelinePoint[]>([]);
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboardData = useCallback(async () => {
    try {
      const [statsRes, typeRes, timelineRes, txnRes] = await Promise.all([
        fetch(`${API_BASE}/api/stats`),
        fetch(`${API_BASE}/api/stats/by-type`),
        fetch(`${API_BASE}/api/stats/timeline?hours=24`),
        fetch(`${API_BASE}/api/transactions?page=1&per_page=10`),
      ]);

      if (statsRes.ok) setStats(await statsRes.json());
      if (typeRes.ok) setTypeData(await typeRes.json());
      if (timelineRes.ok) setTimeline(await timelineRes.json());
      if (txnRes.ok) {
        const data = await txnRes.json();
        setTransactions(data.items || []);
      }

      setError(null);
    } catch (err) {
      setError('Cannot connect to API. Make sure the backend is running.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 5000);
    return () => clearInterval(interval);
  }, [fetchDashboardData]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="flex flex-col items-center gap-4">
          <div className="h-12 w-12 rounded-full border-4 border-blue-500 border-t-transparent animate-spin" />
          <p className="text-slate-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="card max-w-md text-center">
          <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-yellow-500/20 flex items-center justify-center">
            <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-white mb-2">Connection Error</h2>
          <p className="text-slate-400 mb-4">{error}</p>
          <button
            onClick={fetchDashboardData}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 transition-colors"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400 mt-1">Real-time fraud detection monitoring</p>
        </div>
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
          Auto-refreshing every 5s
        </div>
      </div>

      {stats && <StatsCards stats={stats} />}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TimelineChart data={timeline} />
        </div>
        <div>
          <RealtimeAlerts />
        </div>
      </div>

      {typeData.length > 0 && <FraudByTypeChart data={typeData} />}

      <TransactionTable transactions={transactions} />
    </div>
  );
}
