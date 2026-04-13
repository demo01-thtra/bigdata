'use client';

import { useEffect, useState, useRef } from 'react';

interface AlertItem {
  transaction_id: string;
  transaction_type: string;
  amount: number;
  detection_method: string;
  reason: string;
  fraud_probability: number;
  risk_score: number;
  device_id: string;
  ip_address: string;
  timestamp: string;
}

export default function RealtimeAlerts() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const esRef = useRef<EventSource | null>(null);

  useEffect(() => {
    const sseUrl =
      (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000') +
      '/api/sse/alerts';

    function connectSSE() {
      const es = new EventSource(sseUrl);
      esRef.current = es;

      es.onopen = () => setIsConnected(true);
      es.onerror = () => {
        setIsConnected(false);
        es.close();
        setTimeout(connectSSE, 3000);
      };
      es.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          if (message.type === 'fraud_alert') {
            setAlerts((prev) => [message.data, ...prev].slice(0, 50));
          }
        } catch {
          /* ignore parse errors */
        }
      };
    }

    connectSSE();
    return () => esRef.current?.close();
  }, []);

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-white">Real-Time Alerts</h3>
        <div className="flex items-center gap-2">
          <span className={`h-2.5 w-2.5 rounded-full ${isConnected ? 'bg-green-500 animate-pulse' : 'bg-red-500'}`} />
          <span className="text-xs text-slate-400">
            {isConnected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      <div className="space-y-3 max-h-[400px] overflow-y-auto">
        {alerts.length === 0 && (
          <div className="text-center py-8 text-slate-500">
            Waiting for fraud alerts...
          </div>
        )}
        {alerts.map((alert, idx) => (
          <div
            key={`${alert.transaction_id}-${idx}`}
            className="flex items-start gap-3 p-3 rounded-lg bg-red-500/10 border border-red-500/20 animate-in"
          >
            <div className="mt-0.5 h-8 w-8 rounded-full bg-red-500/20 flex items-center justify-center flex-shrink-0">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 text-red-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-red-400">{alert.transaction_type}</span>
                <span className="text-xs text-slate-500">
                  {alert.detection_method}
                </span>
              </div>
              <p className="text-sm text-white font-mono">
                ${alert.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
              </p>
              {alert.reason && (
                <p className="text-xs text-slate-400 mt-1 truncate">{alert.reason}</p>
              )}
              <p className="text-xs text-slate-500 mt-1">
                {alert.timestamp ? new Date(alert.timestamp).toLocaleString() : ''}
              </p>
            </div>
            <span className="text-xs font-mono text-red-400">
              Risk: {((alert.risk_score ?? alert.fraud_probability) * 100).toFixed(0)}%
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
