'use client';

import type { DashboardStats } from '@/lib/api';

interface StatsCardsProps {
  stats: DashboardStats;
}

const STAT_ITEMS = [
  {
    key: 'total_transactions' as const,
    label: 'Total Transactions',
    format: (v: number) => v.toLocaleString(),
    color: 'from-blue-500 to-blue-600',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
      </svg>
    ),
  },
  {
    key: 'total_frauds' as const,
    label: 'Fraud Detected',
    format: (v: number) => v.toLocaleString(),
    color: 'from-red-500 to-red-600',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    ),
  },
  {
    key: 'fraud_rate' as const,
    label: 'Fraud Rate',
    format: (v: number) => `${v.toFixed(2)}%`,
    color: 'from-yellow-500 to-orange-500',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
      </svg>
    ),
  },
  {
    key: 'total_fraud_amount' as const,
    label: 'Amount at Risk',
    format: (v: number) => `$${v.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`,
    color: 'from-purple-500 to-purple-600',
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

export default function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {STAT_ITEMS.map((item) => (
        <div key={item.key} className="stat-card">
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-400">{item.label}</span>
            <div className={`h-10 w-10 rounded-lg bg-gradient-to-br ${item.color} flex items-center justify-center text-white`}>
              {item.icon}
            </div>
          </div>
          <div className="text-2xl font-bold text-white">
            {item.format(stats[item.key])}
          </div>
        </div>
      ))}
    </div>
  );
}
