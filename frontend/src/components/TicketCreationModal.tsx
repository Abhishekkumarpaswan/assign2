import React, { useState } from 'react';
import { Order } from '../types';
import { api } from '../services/api';
import { X, MessageSquare, AlertCircle, Sparkles } from 'lucide-react';

interface TicketCreationModalProps {
  orders: Order[];
  preselectedOrderId?: string;
  onClose: () => void;
  onCreated: (ticketId: string) => void;
}

export const TicketCreationModal: React.FC<TicketCreationModalProps> = ({
  orders,
  preselectedOrderId,
  onClose,
  onCreated,
}) => {
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('refund');
  const [orderId, setOrderId] = useState(preselectedOrderId || '');
  const [priority, setPriority] = useState('medium');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!subject.trim() || !description.trim()) {
      setError('Please fill in subject and description.');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const ticket = await api.createTicket({
        subject,
        description,
        category,
        order_id: orderId || undefined,
        priority,
      });
      onCreated(ticket.id);
    } catch (err: any) {
      setError(err.message || 'Failed to create ticket');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-lg shadow-2xl overflow-hidden">
        <div className="p-4 sm:px-6 border-b border-slate-200 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-50 border border-brand-200 flex items-center justify-center text-brand-600">
              <MessageSquare className="w-4 h-4" />
            </div>
            <div>
              <h2 className="font-extrabold text-slate-900 text-sm sm:text-base">Open Support Ticket</h2>
              <p className="text-xs text-slate-500">Connect with our automated AI assistant or human support</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100">
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-4 sm:p-6 space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Subject</label>
            <input
              type="text"
              required
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="e.g. Broken seal upon arrival, defective item..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs sm:text-sm text-slate-900 focus:outline-hidden focus:border-brand-500 focus:bg-white"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-900 focus:outline-hidden focus:border-brand-500"
              >
                <option value="refund">Refund / Return Request</option>
                <option value="order_status">Order & Delivery Tracking</option>
                <option value="product_issue">Product / Hardware Issue</option>
                <option value="general">General Support</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Linked Order (Optional)</label>
              <select
                value={orderId}
                onChange={(e) => setOrderId(e.target.value)}
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs sm:text-sm text-slate-900 focus:outline-hidden focus:border-brand-500"
              >
                <option value="">None / Not Order Specific</option>
                {orders.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.id} (₹{o.total_amount.toLocaleString('en-IN')})
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Description / Inquiry</label>
            <textarea
              required
              rows={4}
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Describe what occurred with your order or product..."
              className="w-full bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs sm:text-sm text-slate-900 focus:outline-hidden focus:border-brand-500 focus:bg-white"
            />
          </div>

          <div className="pt-2 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white font-semibold px-5 py-2 rounded-xl text-xs sm:text-sm shadow-xs transition flex items-center gap-1.5"
            >
              <Sparkles className="w-4 h-4" />
              <span>{loading ? 'Creating...' : 'Submit & Start AI Chat'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
