import React, { useState, useEffect } from 'react';
import { User, Order, Ticket, Refund } from './types';
import { api } from './services/api';
import { Header } from './components/Header';
import { CustomerDashboard } from './components/CustomerDashboard';
import { SupportDashboard } from './components/SupportDashboard';
import { ChatModal } from './components/ChatModal';
import { TicketCreationModal } from './components/TicketCreationModal';
import { PolicyModal } from './components/PolicyModal';
import { LoginModal } from './components/LoginModal';

export const App: React.FC = () => {
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [refunds, setRefunds] = useState<Refund[]>([]);
  const [loading, setLoading] = useState(true);
  const [initializing, setInitializing] = useState(true);
  const [dataError, setDataError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'customer' | 'support'>('customer');

  // Modals
  const [activeChatTicket, setActiveChatTicket] = useState<Ticket | null>(null);
  const [showNewTicketModal, setShowNewTicketModal] = useState(false);
  const [preselectedOrderId, setPreselectedOrderId] = useState<string | undefined>(undefined);
  const [showPoliciesModal, setShowPoliciesModal] = useState(false);

  // Load User Data
  const loadUserData = async () => {
    setLoading(true);
    try {
      const [fetchedOrders, fetchedTickets, fetchedRefunds] = await Promise.all([
        api.getOrders(),
        api.getTickets(),
        api.getRefunds(),
      ]);
      setOrders(fetchedOrders);
      setTickets(fetchedTickets);
      setRefunds(fetchedRefunds);
      setDataError(null);
    } catch (e) {
      console.error(e);
      setDataError("We couldn't load your account details. Check your connection and try again.");
    } finally {
      setLoading(false);
    }
  };

  // Quick Persona switcher
  const handleSelectRole = async (role: 'customer1' | 'customer2' | 'support') => {
    setLoading(true);
    try {
      if (role === 'customer1') {
        const res = await api.login('aarav@example.com', 'Password123!');
        setCurrentUser(res.user);
        setActiveTab('customer');
      } else if (role === 'customer2') {
        const res = await api.login('meera@example.com', 'Password123!');
        setCurrentUser(res.user);
        setActiveTab('customer');
      } else if (role === 'support') {
        const res = await api.login('support@kinetic.internal', 'AdminPassword123!');
        setCurrentUser(res.user);
        setActiveTab('support');
      }
      await loadUserData();
    } finally {
      setLoading(false);
    }
  };

  // Check login on startup, default to Customer 1 for effortless testing
  useEffect(() => {
    const init = async () => {
      try {
        if (api.getToken()) {
          const user = await api.getMe();
          setCurrentUser(user);
          if (user.role === 'support_agent' || user.role === 'admin') {
            setActiveTab('support');
          }
          await loadUserData();
        } else {
          setLoading(false);
        }
      } catch (e) {
        api.logout();
        setCurrentUser(null);
        setLoading(false);
      } finally {
        setInitializing(false);
      }
    };
    init();
  }, []);

  const handleLogout = () => {
    api.logout();
    setCurrentUser(null);
    setOrders([]);
    setTickets([]);
    setRefunds([]);
    setDataError(null);
    setActiveTab('customer');
  };

  const handleOpenTicket = (ticket: Ticket) => {
    setActiveChatTicket(ticket);
  };

  const handleNewTicketForOrder = (orderId: string) => {
    setPreselectedOrderId(orderId);
    setShowNewTicketModal(true);
  };

  const handleTicketCreated = async (ticketId: string) => {
    setShowNewTicketModal(false);
    setPreselectedOrderId(undefined);
    await loadUserData();
    try {
      const created = await api.getTicketDetails(ticketId);
      setActiveChatTicket(created);
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="min-h-screen bg-[#f4f8f6] flex flex-col font-sans">
      <Header
        currentUser={currentUser}
        onLogout={handleLogout}
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenPolicies={() => setShowPoliciesModal(true)}
        onOpenNewTicket={() => {
          setPreselectedOrderId(undefined);
          setShowNewTicketModal(true);
        }}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {currentUser && dataError && (
          <div role="alert" className="mb-5 flex flex-wrap items-center justify-between gap-3 rounded-2xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
            <span>{dataError}</span>
            <button
              type="button"
              onClick={loadUserData}
              className="rounded-lg px-3 py-1.5 font-semibold text-rose-800 transition hover:bg-rose-100"
            >
              Try again
            </button>
          </div>
        )}
        {initializing ? (
          <div className="min-h-[65vh] flex items-center justify-center">
            <div className="flex items-center gap-3 text-sm font-medium text-slate-500">
              <span className="h-5 w-5 rounded-full border-2 border-brand-200 border-t-brand-600 animate-spin" />
              Loading your account...
            </div>
          </div>
        ) : !currentUser ? (
          <LoginModal
            onSuccess={async (user) => {
              setCurrentUser(user);
              if (user.role === 'support_agent' || user.role === 'admin') {
                setActiveTab('support');
              }
              await loadUserData();
            }}
            onSelectRole={handleSelectRole}
          />
        ) : activeTab === 'customer' ? (
          <CustomerDashboard
            currentUser={currentUser}
            orders={orders}
            tickets={tickets}
            refunds={refunds}
            loading={loading}
            onRefresh={loadUserData}
            onOpenTicket={handleOpenTicket}
            onNewTicketForOrder={handleNewTicketForOrder}
            onOpenNewTicket={() => {
              setPreselectedOrderId(undefined);
              setShowNewTicketModal(true);
            }}
            onOpenPolicies={() => setShowPoliciesModal(true)}
          />
        ) : (
          <SupportDashboard
            currentUser={currentUser}
            tickets={tickets}
            loading={loading}
            onRefresh={loadUserData}
          />
        )}
      </main>

      {/* Modals */}
      {activeChatTicket && (
        <ChatModal
          ticket={activeChatTicket}
          onClose={() => setActiveChatTicket(null)}
          onTicketUpdated={loadUserData}
        />
      )}

      {showNewTicketModal && (
        <TicketCreationModal
          orders={orders}
          preselectedOrderId={preselectedOrderId}
          onClose={() => {
            setShowNewTicketModal(false);
            setPreselectedOrderId(undefined);
          }}
          onCreated={handleTicketCreated}
        />
      )}

      {showPoliciesModal && (
        <PolicyModal onClose={() => setShowPoliciesModal(false)} />
      )}
    </div>
  );
};
