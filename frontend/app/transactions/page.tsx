'use client';

import { useEffect, useState, useCallback } from 'react';
import TransactionTable from '@/components/TransactionTable';
import type { Transaction } from '@/lib/api';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function TransactionsPage() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState<string>('all');
  const [isLoading, setIsLoading] = useState(true);

  const fetchTransactions = useCallback(async () => {
    setIsLoading(true);
    try {
      let url = `${API_BASE}/api/transactions?page=${page}&per_page=20`;
      if (filter === 'fraud') url += '&is_fraud=true';
      if (filter === 'safe') url += '&is_fraud=false';

      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setTransactions(data.items || []);
        setTotalPages(data.pages || 1);
      }
    } catch {
      /* handle silently */
    } finally {
      setIsLoading(false);
    }
  }, [page, filter]);

  useEffect(() => {
    fetchTransactions();
  }, [fetchTransactions]);

  const handleFilterChange = (newFilter: string) => {
    setFilter(newFilter);
    setPage(1);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Transactions</h1>
          <p className="text-slate-400 mt-1">Browse all processed transactions</p>
        </div>
        <div className="flex gap-2">
          {['all', 'fraud', 'safe'].map((f) => (
            <button
              key={f}
              onClick={() => handleFilterChange(f)}
              className={`px-4 py-2 text-sm rounded-lg transition-colors ${
                filter === f
                  ? 'bg-blue-600 text-white'
                  : 'bg-slate-800 text-slate-300 hover:bg-slate-700'
              }`}
            >
              {f.charAt(0).toUpperCase() + f.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="h-10 w-10 rounded-full border-4 border-blue-500 border-t-transparent animate-spin" />
        </div>
      ) : (
        <TransactionTable
          transactions={transactions}
          showPagination
          page={page}
          totalPages={totalPages}
          onPageChange={setPage}
        />
      )}
    </div>
  );
}
