import React from 'react';
import { Order, Ticket, Refund, User } from '../types';
import {
  Package,
  Clock,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  ArrowRight,
  Sparkles,
  ChevronRight,
  RefreshCw,
  ShieldCheck,
  Leaf,
  Activity,
  Droplets,
  HeartPulse
} from 'lucide-react';

interface CustomerDashboardProps {
  currentUser: User;
  orders: Order[];
  tickets: Ticket[];
  refunds: Refund[];
  loading: boolean;
  onRefresh: () => void;
  onOpenTicket: (ticket: Ticket) => void;
  onNewTicketForOrder: (orderId: string) => void;
  onOpenNewTicket: () => void;
  onOpenPolicies: () => void;
}

const CATEGORIES = [
  { name: 'Wellness & Care', icon: HeartPulse, color: 'bg-emerald-50 text-emerald-600 border-emerald-100' },
  { name: 'Health Tech', icon: Activity, color: 'bg-teal-50 text-teal-600 border-teal-100' },
  { name: 'Botanicals', icon: Leaf, color: 'bg-green-50 text-green-600 border-green-100' },
  { name: 'Clinical Care', icon: Droplets, color: 'bg-cyan-50 text-cyan-600 border-cyan-100' },
];

export const CustomerDashboard: React.FC<CustomerDashboardProps> = ({
  currentUser,
  orders,
  tickets,
  refunds,
  loading,
  onRefresh,
  onOpenTicket,
  onNewTicketForOrder,
  onOpenNewTicket,
  onOpenPolicies,
}) => {
  const activeTickets = tickets.filter((ticket) =>
    ['open', 'in_progress', 'escalated'].includes(ticket.status)
  ).length;
  const activeRefunds = refunds.filter((refund) =>
    ['pending_review', 'escalated'].includes(refund.status)
  ).length;

  return (
    <div className="space-y-7 pb-12">
      <section className="relative isolate overflow-hidden rounded-[2rem] bg-gradient-to-br from-brand-900 via-brand-800 to-[#027866] p-6 text-white shadow-xl sm:p-10">
        <div aria-hidden="true" className="pointer-events-none absolute -right-20 -top-32 -z-10 h-96 w-96 rounded-full bg-brand-300/20 blur-3xl" />
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-36 left-1/3 -z-10 h-72 w-72 rounded-full bg-cyan-300/10 blur-3xl" />
        <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-12">
          <div className="space-y-5 lg:col-span-7">
            <div className="inline-flex items-center gap-2 rounded-full border border-white/20 bg-white/10 px-3 py-1.5 text-[11px] font-semibold tracking-wide text-emerald-50 backdrop-blur">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-300" />
              YOUR KINETIC SUPPORT SPACE
            </div>
            <h1 className="max-w-2xl text-3xl font-bold leading-tight tracking-tight sm:text-5xl">
              Good care should come with <span className="text-emerald-200">peace of mind.</span>
            </h1>
            <p className="max-w-xl text-sm leading-relaxed text-emerald-50/80 sm:text-base">
              Hi {currentUser.name.split(' ')[0]}, find your order updates, get clear return guidance, and reach our care team whenever you need us.
            </p>

            <div className="flex flex-wrap items-center gap-3 pt-1">
              <button
                onClick={onOpenNewTicket}
                className="flex items-center gap-2 rounded-xl bg-white px-5 py-3 text-sm font-bold text-brand-900 shadow-lg transition hover:-translate-y-0.5 hover:bg-emerald-50"
              >
                <MessageSquare className="h-4 w-4" />
                <span>Start a conversation</span>
              </button>
              <button
                onClick={onOpenPolicies}
                className="flex items-center gap-2 rounded-xl border border-white/25 bg-white/10 px-5 py-3 text-sm font-semibold text-white transition hover:bg-white/20"
              >
                <Sparkles className="h-4 w-4 text-emerald-200" />
                <span>Explore return guidance</span>
              </button>
            </div>
            <div className="flex items-center gap-2 pt-1 text-xs text-emerald-50/75">
              <ShieldCheck className="h-4 w-4 text-emerald-200" />
              Your orders and conversations stay in your account.
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 lg:col-span-5">
            {CATEGORIES.map((cat) => {
              const Icon = cat.icon;
              return (
                <button
                  type="button"
                  key={cat.name}
                  onClick={onOpenPolicies}
                  className="flex min-h-28 flex-col items-center justify-center gap-3 rounded-2xl border border-white/15 bg-white/[0.08] p-4 text-center transition hover:-translate-y-0.5 hover:border-white/30 hover:bg-white/[0.14]"
                >
                  <div className={`flex h-11 w-11 items-center justify-center rounded-full border ${cat.color}`}>
                    <Icon className="h-5 w-5" />
                  </div>
                  <span className="text-xs font-semibold text-white">{cat.name}</span>
                </button>
              );
            })}
          </div>
        </div>
      </section>

      <section aria-label="Account overview" className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        {[
          { label: 'Orders', value: orders.length, detail: 'Your recent purchases', icon: Package },
          { label: 'Conversations', value: activeTickets, detail: 'Need your attention', icon: MessageSquare },
          { label: 'Returns in progress', value: activeRefunds, detail: 'Being reviewed', icon: RefreshCw },
        ].map((item) => {
          const Icon = item.icon;
          return (
            <div key={item.label} className="flex items-center gap-4 rounded-2xl border border-slate-200/80 bg-white p-4 shadow-sm sm:p-5">
              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-700">
                <Icon className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <div className="text-xs font-medium text-slate-500">{item.label}</div>
                <div className="mt-0.5 flex items-baseline gap-2">
                  <span className="text-2xl font-bold tracking-tight text-slate-900">{item.value}</span>
                  <span className="truncate text-[11px] text-slate-500">{item.detail}</span>
                </div>
              </div>
            </div>
          );
        })}
      </section>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 gap-7 lg:grid-cols-12">
        {/* Left: Orders (7 cols) */}
        <div className="space-y-4 lg:col-span-7">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Package className="w-5 h-5 text-brand-500" />
                Your Orders
              </h2>
              <p className="text-xs text-slate-500">Track delivery status or request a return</p>
            </div>
            <button
              onClick={onRefresh}
              title="Refresh Orders"
              className="p-2 text-slate-500 hover:text-slate-800 rounded-xl bg-white hover:bg-slate-50 transition border border-slate-200"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
            </button>
          </div>

          {orders.length === 0 && loading ? (
            <div role="status" className="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white p-10 text-sm text-slate-500">
              <RefreshCw className="h-4 w-4 animate-spin text-brand-600" />
              Loading your orders...
            </div>
          ) : orders.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-10 text-center text-slate-500">
              <Package className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p className="font-medium text-sm">No orders found for {currentUser.name}.</p>
            </div>
          ) : (
            <div className="space-y-3.5">
              {orders.map((order) => {
                const associatedRefund = refunds.find((r) => r.order_id === order.id);

                return (
                  <div
                    key={order.id}
                    className="bg-white border border-slate-200/90 hover:border-brand-300 rounded-2xl p-5 transition shadow-2xs hover:shadow-sm"
                  >
                    <div className="flex flex-wrap items-start justify-between gap-2 pb-3.5 border-b border-slate-100">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-sm text-slate-900">{order.id}</span>
                          <span className="text-[11px] px-2.5 py-0.5 rounded-full font-medium bg-slate-100 text-slate-600">
                            {order.category}
                          </span>
                        </div>
                        <div className="text-xs text-slate-500 mt-1">
                          {order.delivery_date ? (
                            <span>Delivered on {new Date(order.delivery_date).toLocaleDateString()}</span>
                          ) : (
                            <span className="capitalize">Status: {order.status.replace('_', ' ')}</span>
                          )}
                        </div>
                      </div>

                      <div className="text-right">
                        <div className="font-bold text-base text-slate-900">
                          ₹{order.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}
                        </div>
                      </div>
                    </div>

                    {/* Items */}
                    <div className="py-3.5 space-y-1.5">
                      {order.item_details.map((item, idx) => (
                        <div key={idx} className="flex justify-between text-xs sm:text-sm">
                          <span className="text-slate-700 font-medium">
                            {item.name} <span className="text-slate-400 font-normal">× {item.qty}</span>
                          </span>
                          <span className="text-slate-600">₹{(item.price * item.qty).toLocaleString('en-IN')}</span>
                        </div>
                      ))}
                    </div>

                    {/* Footer Badges & Actions */}
                    <div className="flex flex-wrap items-center justify-between gap-2 pt-3.5 border-t border-slate-100">
                      <div className="flex items-center gap-2 flex-wrap">
                        {order.delivery_date && order.is_return_window_open ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200/80">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            Eligible for Return
                          </span>
                        ) : order.delivery_date && !order.is_return_window_open ? (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 border border-slate-200">
                            <AlertCircle className="w-3.5 h-3.5 text-slate-500" />
                            Return Window Closed
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full bg-brand-50 text-brand-700 border border-brand-200">
                            <Clock className="w-3.5 h-3.5 text-brand-600" />
                            In Transit
                          </span>
                        )}

                        {associatedRefund && (
                          <span
                            className={`inline-flex items-center gap-1 text-[11px] font-semibold px-2.5 py-1 rounded-full ${
                              associatedRefund.status === 'approved'
                                ? 'bg-emerald-100 text-emerald-800'
                                : associatedRefund.status === 'escalated'
                                ? 'bg-amber-100 text-amber-800'
                                : associatedRefund.status === 'rejected'
                                ? 'bg-rose-100 text-rose-800'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            Refund: {associatedRefund.status === 'escalated' ? 'Under Review' : associatedRefund.status}
                          </span>
                        )}
                      </div>

                      <button
                        onClick={() => onNewTicketForOrder(order.id)}
                        className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 px-3 py-1.5 rounded-lg hover:bg-brand-50 transition"
                      >
                        <span>Get Help</span>
                        <ChevronRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Right: Support Tickets (5 cols) */}
        <div className="space-y-4 lg:col-span-5">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-brand-500" />
              Support Conversations
            </h2>
            <p className="text-xs text-slate-500">Continue an active chat or review resolution status</p>
          </div>

          {tickets.length === 0 && loading ? (
            <div role="status" className="flex items-center justify-center gap-2 rounded-2xl border border-slate-200 bg-white p-8 text-sm text-slate-500">
              <RefreshCw className="h-4 w-4 animate-spin text-brand-600" />
              Loading conversations...
            </div>
          ) : tickets.length === 0 ? (
            <div className="bg-white border border-slate-200 rounded-2xl p-8 text-center text-slate-500">
              <MessageSquare className="w-10 h-10 mx-auto text-slate-300 mb-2" />
              <p className="font-medium text-sm">No support tickets yet.</p>
              <button
                onClick={onOpenNewTicket}
                className="mt-3 text-xs font-semibold text-brand-600 hover:underline inline-flex items-center gap-1"
              >
                <span>Start a conversation</span>
                <ArrowRight className="w-3 h-3" />
              </button>
            </div>
          ) : (
            <div className="space-y-3">
              {tickets.map((t) => {
                const isEscalated = t.status === 'escalated';
                const isResolved = t.status === 'resolved';

                return (
                  <div
                    key={t.id}
                    onClick={() => onOpenTicket(t)}
                    className="bg-white border border-slate-200/90 hover:border-brand-400 rounded-2xl p-4 transition cursor-pointer shadow-2xs hover:shadow-sm"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-xs text-slate-500">{t.id}</span>
                          {t.order_id && (
                            <span className="font-semibold text-[11px] text-brand-700 bg-brand-50 px-2 py-0.5 rounded-full">
                              {t.order_id}
                            </span>
                          )}
                        </div>
                        <h3 className="font-semibold text-sm text-slate-900 mt-1 line-clamp-1">{t.subject}</h3>
                      </div>

                      <span
                        className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full capitalize ${
                          isResolved
                            ? 'bg-emerald-100 text-emerald-800'
                            : isEscalated
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-brand-50 text-brand-700'
                        }`}
                      >
                        {isEscalated ? 'In Review' : t.status.replace('_', ' ')}
                      </span>
                    </div>

                    <p className="text-xs text-slate-500 mt-2 line-clamp-2">{t.description}</p>

                    <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-400">
                      <span>Updated {new Date(t.updated_at).toLocaleDateString()}</span>
                      <span className="text-brand-600 font-semibold flex items-center gap-1">
                        Open Chat <ArrowRight className="w-3 h-3" />
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {/* Customer Care Promise Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-5 text-xs text-slate-600 space-y-2.5 shadow-2xs">
            <div className="font-bold text-sm text-slate-900 flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-brand-500" />
              Kinetic Customer Promise
            </div>
            <ul className="space-y-1.5 text-slate-600 leading-relaxed">
              <li className="flex items-start gap-2">
                <span className="text-brand-500 font-bold">✓</span>
                <span>Instant eligibility checks based on your delivery date and product category.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-brand-500 font-bold">✓</span>
                <span>Approved refunds are credited back within 3–5 business days.</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-brand-500 font-bold">✓</span>
                <span>Dedicated support specialists review high-value orders with priority care.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};
