'use client';

import type { Transaction } from '@/lib/api';

interface TransactionTableProps {
  transactions: Transaction[];
  showPagination?: boolean;
  page?: number;
  totalPages?: number;
  onPageChange?: (page: number) => void;
}

export default function TransactionTable({
  transactions,
  showPagination = false,
  page = 1,
  totalPages = 1,
  onPageChange,
}: TransactionTableProps) {
  return (
    <div className="card overflow-hidden">
      <h3 className="text-lg font-semibold text-white mb-4">Recent Transactions</h3>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-slate-700 text-slate-400">
              <th className="text-left py-3 px-4">Type</th>
              <th className="text-right py-3 px-4">Amount</th>
              <th className="text-left py-3 px-4">From</th>
              <th className="text-left py-3 px-4">To</th>
              <th className="text-center py-3 px-4">Status</th>
              <th className="text-center py-3 px-4">Method</th>
              <th className="text-right py-3 px-4">Probability</th>
              <th className="text-left py-3 px-4">Time</th>
            </tr>
          </thead>
          <tbody>
            {transactions.length === 0 && (
              <tr>
                <td colSpan={8} className="text-center py-8 text-slate-500">
                  No transactions found. Waiting for data...
                </td>
              </tr>
            )}
            {transactions.map((txn) => (
              <tr key={txn.id} className={`border-b border-slate-700/50 hover:bg-slate-700/30 transition-colors ${txn.is_fraud ? 'bg-red-500/5' : ''}`}>
                <td className="py-3 px-4">
                  <span className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-slate-700 text-slate-300">
                    {txn.transaction_type}
                  </span>
                </td>
                <td className="py-3 px-4 text-right font-mono font-medium">
                  ${txn.amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                </td>
                <td className="py-3 px-4 text-slate-400 font-mono text-xs">
                  {txn.name_orig?.substring(0, 12) || '-'}
                </td>
                <td className="py-3 px-4 text-slate-400 font-mono text-xs">
                  {txn.name_dest?.substring(0, 12) || '-'}
                </td>
                <td className="py-3 px-4 text-center">
                  {txn.is_fraud ? (
                    <span className="badge-fraud">FRAUD</span>
                  ) : (
                    <span className="badge-safe">SAFE</span>
                  )}
                </td>
                <td className="py-3 px-4 text-center text-xs text-slate-400">
                  {txn.detection_method}
                </td>
                <td className="py-3 px-4 text-right font-mono text-xs">
                  <span className={txn.fraud_probability > 0.5 ? 'text-red-400' : 'text-green-400'}>
                    {(txn.fraud_probability * 100).toFixed(1)}%
                  </span>
                </td>
                <td className="py-3 px-4 text-xs text-slate-400">
                  {new Date(txn.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {showPagination && totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-700">
          <span className="text-sm text-slate-400">Page {page} of {totalPages}</span>
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange?.(page - 1)}
              disabled={page <= 1}
              className="px-3 py-1.5 text-sm rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange?.(page + 1)}
              disabled={page >= totalPages}
              className="px-3 py-1.5 text-sm rounded-lg bg-slate-700 text-slate-300 hover:bg-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
