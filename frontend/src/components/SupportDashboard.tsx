import React, { useState, useEffect } from 'react';
import { Ticket, User } from '../types';
import { api } from '../services/api';
import {
  ShieldAlert,
  CheckCircle,
  XCircle,
  HelpCircle,
  MessageSquare,
  Search,
  RefreshCw,
  Package,
  Lock,
  Send
} from 'lucide-react';

interface SupportDashboardProps {
  currentUser: User;
  tickets: Ticket[];
  loading: boolean;
  onRefresh: () => void;
}

function formatMessageText(text: string): React.ReactNode {
  const parts = text.split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part, i) => {
    if (part.startsWith('**') && part.endsWith('**')) {
      return (
        <strong key={i} className="font-semibold">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <React.Fragment key={i}>{part}</React.Fragment>;
  });
}

export const SupportDashboard: React.FC<SupportDashboardProps> = ({
  tickets,
  loading,
  onRefresh,
}) => {
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);
  const [selectedTicketDetail, setSelectedTicketDetail] = useState<Ticket | null>(null);
  const [statusFilter, setStatusFilter] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');

  const [internalNote, setInternalNote] = useState('');
  const [agentReply, setAgentReply] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  const filteredTickets = tickets.filter((t) => {
    if (statusFilter !== 'all' && t.status !== statusFilter) return false;
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      const matchId = t.id.toLowerCase().includes(q);
      const matchSubject = t.subject.toLowerCase().includes(q);
      const matchOrder = t.order_id?.toLowerCase().includes(q);
      if (!matchId && !matchSubject && !matchOrder) return false;
    }
    return true;
  });

  const loadTicketDetail = async (ticket: Ticket) => {
    setSelectedTicket(ticket);
    try {
      const detail = await api.getSupportTicketDetails(ticket.id);
      setSelectedTicketDetail(detail);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    if (selectedTicket) {
      loadTicketDetail(selectedTicket);
    }
  }, [tickets]);

  const handleEscalationDecision = async (
    escalationId: string,
    decision: 'approved' | 'rejected' | 'info_requested'
  ) => {
    setActionLoading(true);
    try {
      await api.decideEscalation(escalationId, decision, internalNote);
      setInternalNote('');
      onRefresh();
      if (selectedTicket) {
        await loadTicketDetail(selectedTicket);
      }
    } catch (e: any) {
      alert(`Error updating escalation: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleUpdateStatus = async (newStatus: string) => {
    if (!selectedTicketDetail) return;
    setActionLoading(true);
    try {
      await api.updateTicket(selectedTicketDetail.id, { status: newStatus });
      onRefresh();
      await loadTicketDetail(selectedTicketDetail);
    } catch (e: any) {
      alert(`Error updating status: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSendAgentReply = async () => {
    if (!selectedTicketDetail || !agentReply.trim()) return;
    setActionLoading(true);
    try {
      await api.addMessage(selectedTicketDetail.id, agentReply);
      setAgentReply('');
      await loadTicketDetail(selectedTicketDetail);
      onRefresh();
    } catch (e: any) {
      alert(`Error sending message: ${e.message}`);
    } finally {
      setActionLoading(false);
    }
  };

  const escalatedCount = tickets.filter((t) => t.status === 'escalated').length;
  const openCount = tickets.filter((t) => t.status === 'open' || t.status === 'in_progress').length;
  const resolvedCount = tickets.filter((t) => t.status === 'resolved' || t.status === 'closed').length;

  return (
    <div className="space-y-6 pb-12">
      {/* Metrics */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs">
          <div className="text-xs font-medium text-slate-500">Total Tickets</div>
          <div className="text-2xl font-extrabold text-slate-900 mt-1">{tickets.length}</div>
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 shadow-2xs">
          <div className="text-xs font-semibold text-amber-800 flex items-center gap-1.5">
            <ShieldAlert className="w-4 h-4 text-amber-600" />
            Pending Escalations
          </div>
          <div className="text-2xl font-extrabold text-amber-900 mt-1">{escalatedCount}</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs">
          <div className="text-xs font-medium text-slate-500">Active</div>
          <div className="text-2xl font-extrabold text-brand-600 mt-1">{openCount}</div>
        </div>
        <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs">
          <div className="text-xs font-medium text-slate-500">Resolved</div>
          <div className="text-2xl font-extrabold text-emerald-600 mt-1">{resolvedCount}</div>
        </div>
      </div>

      {/* Main Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Ticket Queue */}
        <div className="lg:col-span-5 space-y-4">
          <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-2xs space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <Lock className="w-4 h-4 text-brand-500" />
                Support Queue
              </h2>
              <button
                onClick={onRefresh}
                className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition"
                title="Refresh"
              >
                <RefreshCw className="w-4 h-4" />
              </button>
            </div>

            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by ticket, order, subject..."
                className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-9 pr-3 py-2 text-xs text-slate-900 focus:outline-hidden focus:border-brand-500"
              />
            </div>

            <div className="flex flex-wrap items-center gap-1.5 text-xs pt-1">
              {['all', 'escalated', 'open', 'resolved'].map((s) => (
                <button
                  key={s}
                  onClick={() => setStatusFilter(s)}
                  className={`px-2.5 py-1 rounded-full text-[11px] font-medium capitalize transition ${
                    statusFilter === s
                      ? 'bg-brand-500 text-white font-semibold'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="space-y-2.5 max-h-[68vh] overflow-y-auto pr-1">
            {filteredTickets.length === 0 && loading ? (
              <div role="status" className="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">
                <RefreshCw className="h-4 w-4 animate-spin text-brand-600" />
                Loading support queue...
              </div>
            ) : filteredTickets.length === 0 ? (
              <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-xs text-slate-500">
                No tickets match the selected filter.
              </div>
            ) : (
              filteredTickets.map((t) => {
                const isSelected = selectedTicket?.id === t.id;
                const isEscalated = t.status === 'escalated';

                return (
                  <div
                    key={t.id}
                    onClick={() => loadTicketDetail(t)}
                    className={`bg-white border rounded-2xl p-4 transition cursor-pointer shadow-2xs ${
                      isSelected
                        ? 'border-brand-500 ring-2 ring-brand-100'
                        : isEscalated
                        ? 'border-amber-300 hover:border-amber-400'
                        : 'border-slate-200 hover:border-brand-300'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-1.5">
                          <span className="font-bold text-xs text-slate-900">{t.id}</span>
                          {t.order_id && (
                            <span className="font-semibold text-[11px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                              {t.order_id}
                            </span>
                          )}
                        </div>
                        <h4 className="font-semibold text-xs sm:text-sm text-slate-800 line-clamp-1 mt-1">
                          {t.subject}
                        </h4>
                      </div>

                      <span
                        className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase ${
                          t.status === 'escalated'
                            ? 'bg-amber-100 text-amber-800'
                            : t.status === 'resolved'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-slate-100 text-slate-700'
                        }`}
                      >
                        {t.status}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-[11px] text-slate-400 mt-2.5 pt-2 border-t border-slate-100">
                      <span>Priority: <strong className="text-slate-600 uppercase">{t.priority}</strong></span>
                      <span>{new Date(t.updated_at).toLocaleDateString()}</span>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* Ticket Detail & Review */}
        <div className="lg:col-span-7">
          {!selectedTicketDetail ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-12 text-center text-slate-400">
              <MessageSquare className="w-12 h-12 mx-auto text-slate-300 mb-3" />
              <h3 className="font-bold text-sm text-slate-700">Select a ticket to inspect</h3>
              <p className="text-xs text-slate-500 mt-1">
                Review order context, customer messages, and approve or reject refund escalations.
              </p>
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-2xl shadow-2xs overflow-hidden flex flex-col h-full max-h-[80vh]">
              <div className="p-4 sm:px-6 border-b border-slate-200 bg-slate-50/70 flex flex-wrap items-center justify-between gap-2">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="font-extrabold text-base text-slate-900">{selectedTicketDetail.id}</span>
                    <span className="text-xs px-2.5 py-0.5 rounded-full bg-slate-200/80 text-slate-700 font-medium capitalize">
                      {selectedTicketDetail.category.replace('_', ' ')}
                    </span>
                  </div>
                  <h3 className="font-semibold text-sm text-slate-800 mt-0.5">{selectedTicketDetail.subject}</h3>
                </div>

                <div className="flex items-center gap-2">
                  <span className="text-xs font-medium text-slate-500">Status:</span>
                  <select
                    value={selectedTicketDetail.status}
                    onChange={(e) => handleUpdateStatus(e.target.value)}
                    disabled={actionLoading}
                    className="text-xs font-semibold border border-slate-300 rounded-lg px-2.5 py-1.5 bg-white text-slate-800 focus:outline-hidden focus:border-brand-500"
                  >
                    <option value="open">Open</option>
                    <option value="in_progress">In Progress</option>
                    <option value="escalated">Escalated</option>
                    <option value="resolved">Resolved</option>
                    <option value="closed">Closed</option>
                  </select>
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-5">
                {selectedTicketDetail.order && (
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 text-xs space-y-2">
                    <div className="flex items-center justify-between font-bold text-slate-900 border-b border-slate-200 pb-2">
                      <span className="flex items-center gap-1.5">
                        <Package className="w-4 h-4 text-brand-500" />
                        Order {selectedTicketDetail.order.id}
                      </span>
                      <span className="text-brand-600 font-extrabold">
                        ₹{selectedTicketDetail.order.total_amount.toLocaleString('en-IN')}
                      </span>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-slate-600 pt-1">
                      <div>Category: <strong>{selectedTicketDetail.order.category}</strong></div>
                      <div>Status: <strong className="capitalize">{selectedTicketDetail.order.status.replace('_', ' ')}</strong></div>
                      <div>
                        Delivered:{' '}
                        <strong>
                          {selectedTicketDetail.order.delivery_date
                            ? new Date(selectedTicketDetail.order.delivery_date).toLocaleDateString()
                            : 'In Transit'}
                        </strong>
                      </div>
                      <div>
                        Return Window:{' '}
                        <strong>
                          {selectedTicketDetail.order.is_return_window_open ? 'Eligible' : 'Closed'}
                        </strong>
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-200 space-y-1">
                      {selectedTicketDetail.order.item_details.map((item, idx) => (
                        <div key={idx} className="flex justify-between text-slate-600">
                          <span>{item.name} × {item.qty}</span>
                          <span>₹{(item.price * item.qty).toLocaleString('en-IN')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {selectedTicketDetail.escalations && selectedTicketDetail.escalations.length > 0 && (
                  <div className="border border-amber-300 bg-amber-50/70 rounded-xl p-4 space-y-3">
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-xs text-amber-900 flex items-center gap-1.5">
                        <ShieldAlert className="w-4 h-4 text-amber-600" />
                        Refund Escalation Review
                      </span>
                      <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full bg-amber-200 text-amber-900">
                        {selectedTicketDetail.escalations[0].decision}
                      </span>
                    </div>

                    <div className="text-xs text-amber-950 bg-white border border-amber-200 p-3 rounded-lg">
                      <div className="font-semibold">{selectedTicketDetail.escalations[0].summary}</div>
                      {selectedTicketDetail.escalations[0].internal_note && (
                        <div className="text-slate-600 text-[11px] mt-1">
                          {selectedTicketDetail.escalations[0].internal_note}
                        </div>
                      )}
                    </div>

                    {selectedTicketDetail.escalations[0].decision === 'pending' && (
                      <div className="space-y-2.5 pt-2 border-t border-amber-200">
                        <input
                          type="text"
                          value={internalNote}
                          onChange={(e) => setInternalNote(e.target.value)}
                          placeholder="Add an internal review note..."
                          className="w-full bg-white border border-amber-300 rounded-lg px-3 py-2 text-xs text-slate-900 focus:outline-hidden"
                        />
                        <div className="flex flex-wrap items-center gap-2">
                          <button
                            onClick={() => handleEscalationDecision(selectedTicketDetail.escalations![0].id, 'approved')}
                            disabled={actionLoading}
                            className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold px-3.5 py-1.5 rounded-lg text-xs flex items-center gap-1 transition"
                          >
                            <CheckCircle className="w-3.5 h-3.5" />
                            <span>Approve Refund</span>
                          </button>
                          <button
                            onClick={() => handleEscalationDecision(selectedTicketDetail.escalations![0].id, 'rejected')}
                            disabled={actionLoading}
                            className="bg-rose-600 hover:bg-rose-700 text-white font-semibold px-3.5 py-1.5 rounded-lg text-xs flex items-center gap-1 transition"
                          >
                            <XCircle className="w-3.5 h-3.5" />
                            <span>Reject Refund</span>
                          </button>
                          <button
                            onClick={() => handleEscalationDecision(selectedTicketDetail.escalations![0].id, 'info_requested')}
                            disabled={actionLoading}
                            className="bg-slate-700 hover:bg-slate-800 text-white font-semibold px-3.5 py-1.5 rounded-lg text-xs flex items-center gap-1 transition"
                          >
                            <HelpCircle className="w-3.5 h-3.5" />
                            <span>Request Info</span>
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                <div className="space-y-3">
                  <div className="font-bold text-xs text-slate-600 uppercase tracking-wider">
                    Conversation History
                  </div>

                  {selectedTicketDetail.messages?.map((msg) => (
                    <div
                      key={msg.id}
                      className={`p-3.5 rounded-xl text-xs space-y-1 ${
                        msg.sender_type === 'customer'
                          ? 'bg-slate-100 border border-slate-200'
                          : msg.sender_type === 'ai'
                          ? 'bg-brand-50/50 border border-brand-200'
                          : 'bg-slate-900 text-white'
                      }`}
                    >
                      <div className="flex items-center justify-between text-[10px] font-bold uppercase opacity-60">
                        <span>
                          {msg.sender_type === 'customer'
                            ? 'Customer'
                            : msg.sender_type === 'ai'
                            ? 'Kinetic Assistant'
                            : 'Support Specialist'}
                        </span>
                        <span>{new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                      </div>
                      <div className="whitespace-pre-line leading-relaxed">{formatMessageText(msg.content)}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="p-3.5 bg-white border-t border-slate-200 flex items-center gap-2">
                <input
                  type="text"
                  value={agentReply}
                  onChange={(e) => setAgentReply(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleSendAgentReply();
                  }}
                  placeholder="Reply to customer..."
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs text-slate-900 focus:outline-hidden focus:border-brand-500"
                />
                <button
                  onClick={handleSendAgentReply}
                  disabled={!agentReply.trim() || actionLoading}
                  className="bg-brand-500 hover:bg-brand-600 disabled:opacity-40 text-white font-semibold px-4 py-2 rounded-xl text-xs flex items-center gap-1.5 transition"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
