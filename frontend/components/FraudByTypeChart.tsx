'use client';

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import type { TypeBreakdown } from '@/lib/api';

interface FraudByTypeChartProps {
  data: TypeBreakdown[];
}

const COLORS = ['#3b82f6', '#ef4444', '#22c55e', '#eab308', '#a855f7'];

export default function FraudByTypeChart({ data }: FraudByTypeChartProps) {
  const pieData = data
    .filter((d) => d.frauds > 0)
    .map((d) => ({ name: d.transaction_type, value: d.frauds }));

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Fraud Rate by Type</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
            <XAxis dataKey="transaction_type" tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <YAxis tick={{ fill: '#94a3b8', fontSize: 12 }} />
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
              labelStyle={{ color: '#f1f5f9' }}
            />
            <Legend />
            <Bar dataKey="total" fill="#3b82f6" name="Total" radius={[4, 4, 0, 0]} />
            <Bar dataKey="frauds" fill="#ef4444" name="Frauds" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Fraud Distribution</h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={pieData}
              cx="50%"
              cy="50%"
              innerRadius={60}
              outerRadius={100}
              paddingAngle={5}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(1)}%`}
            >
              {pieData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155', borderRadius: '8px' }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
