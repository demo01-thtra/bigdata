'use client';

import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import type { TimelinePoint } from '@/lib/api';

interface TimelineChartProps {
  data: TimelinePoint[];
}

export default function TimelineChart({ data }: TimelineChartProps) {
  const formatted = data.map((d) => ({
    ...d,
    time: d.timestamp ? new Date(d.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '',
  }));

  return (
    <div className="card">
      <h3 className="text-lg font-semibold text-white mb-4">Transaction Timeline</h3>
      <ResponsiveContainer width="100%" height={300}>
        <AreaChart data={formatted}>
          <defs>
            <linearGradient id="colorTotal" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis dataKey="time" tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
          <Tooltip
            contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
            labelStyle={{ color: '#f1f5f9' }}
          />
          <Legend />
          <Area type="monotone" dataKey="total" stroke="#3b82f6" fill="url(#colorTotal)" name="Total" />
          <Area type="monotone" dataKey="frauds" stroke="#ef4444" fill="url(#colorFraud)" name="Frauds" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
