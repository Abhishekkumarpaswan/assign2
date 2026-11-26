import React, { useState, useEffect } from 'react';
import { ReturnPolicy } from '../types';
import { api } from '../services/api';
import { X, BookOpen, Search, Clock, CheckCircle, AlertTriangle } from 'lucide-react';

interface PolicyModalProps {
  onClose: () => void;
}

export const PolicyModal: React.FC<PolicyModalProps> = ({ onClose }) => {
  const [policies, setPolicies] = useState<ReturnPolicy[]>([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.getPolicies().then((res) => {
      setPolicies(res);
      setLoading(false);
    }).catch((err: unknown) => {
      setError(err instanceof Error ? err.message : 'Unable to load return policies.');
      setLoading(false);
    });
  }, []);

  const filtered = policies.filter((p) => {
    if (!search.trim()) return true;
    const q = search.toLowerCase();
    return p.category.toLowerCase().includes(q) || p.notes.toLowerCase().includes(q);
  });

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/50 backdrop-blur-xs">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden">
        <div className="p-4 sm:px-6 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600">
              <BookOpen className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-bold text-slate-900 text-sm sm:text-base">Return & Refund Policies</h2>
              <p className="text-xs text-slate-500">Transparent return windows and eligibility guidelines by category</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-4 border-b border-slate-100 bg-slate-50/60">
          <div className="relative">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search category (e.g. Wellness, Health Tech, Herbal)..."
              className="w-full bg-white border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-xs sm:text-sm text-slate-900 focus:outline-hidden focus:border-brand-500"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
          {loading ? (
            <div className="text-center py-8 text-xs text-slate-400">Loading policy rules...</div>
          ) : error ? (
            <div role="alert" className="py-8 text-center text-sm text-rose-700">{error}</div>
          ) : filtered.length === 0 ? (
            <div className="text-center py-8 text-xs text-slate-400">No policy rules matched your query.</div>
          ) : (
            filtered.map((pol, idx) => (
              <div key={idx} className="bg-slate-50 border border-slate-200/90 rounded-xl p-4 text-xs space-y-2.5">
                <div className="flex items-center justify-between">
                  <h3 className="font-bold text-sm text-slate-900">{pol.category}</h3>
                  <span className="font-semibold px-2.5 py-0.5 rounded-full bg-brand-50 text-brand-700 border border-brand-200 flex items-center gap-1 text-[11px]">
                    <Clock className="w-3 h-3 text-brand-500" />
                    {pol.window_days} Days Window
                  </span>
                </div>

                <p className="text-slate-700 leading-relaxed">{pol.notes}</p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 border-t border-slate-200/80">
                  <div>
                    <span className="font-semibold text-slate-800 flex items-center gap-1 mb-1">
                      <CheckCircle className="w-3 h-3 text-emerald-600" /> Eligible Reasons
                    </span>
                    <ul className="list-disc list-inside text-slate-600 space-y-0.5 text-[11px]">
                      {pol.allowed_reasons.map((r, i) => (
                        <li key={i}>{r}</li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <span className="font-semibold text-slate-800 flex items-center gap-1 mb-1">
                      <AlertTriangle className="w-3 h-3 text-amber-600" /> Exceptions
                    </span>
                    <ul className="list-disc list-inside text-slate-600 space-y-0.5 text-[11px]">
                      {pol.non_refundable_items.map((nr, i) => (
                        <li key={i}>{nr}</li>
                      ))}
                    </ul>
                  </div>
                </div>

                <div className="text-[11px] text-slate-500 pt-1">
                  <strong>Condition:</strong> {pol.condition_required}
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
