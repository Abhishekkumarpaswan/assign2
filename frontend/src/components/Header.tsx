import React from 'react';
import { User } from '../types';
import {
  ShieldCheck,
  Sparkles,
  ShoppingBag,
  Lock,
  LogOut,
  BookOpen,
} from 'lucide-react';

interface HeaderProps {
  currentUser: User | null;
  onLogout: () => void;
  activeTab: 'customer' | 'support';
  setActiveTab: (tab: 'customer' | 'support') => void;
  onOpenPolicies: () => void;
  onOpenNewTicket: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentUser,
  onLogout,
  activeTab,
  setActiveTab,
  onOpenPolicies,
  onOpenNewTicket,
}) => {
  const canAccessSupport = currentUser?.role === 'support_agent' || currentUser?.role === 'admin';

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/95 shadow-sm backdrop-blur">
      <div className="border-b border-brand-100 bg-brand-50/70">
        <div className="mx-auto flex max-w-7xl items-center justify-center gap-2 px-4 py-2 text-[11px] font-medium tracking-wide text-brand-900 sm:text-xs">
          <ShieldCheck className="h-3.5 w-3.5 text-brand-600" />
          <span>Thoughtful care for every order</span>
        </div>
      </div>

      <div className="mx-auto flex h-[4.5rem] max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-8">
          <button
            type="button"
            aria-label="KINETIC home"
            onClick={() => setActiveTab('customer')}
            className="flex items-center gap-2.5 rounded-lg text-left"
          >
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br from-brand-400 to-brand-700 text-base font-black tracking-wider text-white shadow-sm">
              <span className="transform -skew-x-6">K</span>
            </span>
            <span className="text-xl font-extrabold tracking-tight text-slate-900">KINETIC</span>
          </button>

          <nav className="hidden md:flex items-center gap-1.5">
            <button
              onClick={() => setActiveTab('customer')}
              className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-semibold transition ${
                activeTab === 'customer'
                  ? 'bg-brand-50 text-brand-800'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-50'
              }`}
            >
              <ShoppingBag className="h-4 w-4 text-brand-600" />
              Orders & Support
            </button>
            {canAccessSupport && (
              <button
                onClick={() => setActiveTab('support')}
                className={`flex items-center gap-2 rounded-xl px-3.5 py-2 text-sm font-semibold transition ${
                  activeTab === 'support'
                    ? 'bg-brand-50 text-brand-800'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                }`}
              >
                <Lock className="h-4 w-4 text-brand-600" />
                Staff Portal
              </button>
            )}
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={onOpenPolicies}
            className="hidden items-center gap-1.5 rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold text-slate-700 transition hover:border-brand-200 hover:bg-brand-50/50 sm:flex"
          >
            <BookOpen className="h-3.5 w-3.5 text-brand-600" />
            Return Policy
          </button>

          {currentUser && activeTab === 'customer' && (
            <button
              onClick={onOpenNewTicket}
              className="flex items-center gap-1.5 rounded-xl bg-brand-600 px-4 py-2 text-xs font-semibold text-white shadow-sm transition hover:bg-brand-700 sm:text-sm"
            >
              <Sparkles className="h-4 w-4" />
              <span>Ask Support</span>
            </button>
          )}

          {currentUser && (
            <div className="flex items-center gap-2.5 border-l border-slate-200 pl-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-full border border-brand-200 bg-brand-50 text-xs font-bold text-brand-800">
                {currentUser.name.charAt(0)}
              </div>
              <div className="hidden text-left text-xs lg:block">
                <div className="font-semibold text-slate-900">{currentUser.name}</div>
                <div className="text-[11px] text-slate-500">
                  {canAccessSupport ? 'Support team' : 'Customer account'}
                </div>
              </div>
              <button
                onClick={onLogout}
                title="Sign out"
                aria-label="Sign out"
                className="rounded-lg p-2 text-slate-400 transition hover:bg-slate-100 hover:text-slate-700"
              >
                <LogOut className="h-4 w-4" />
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
};
