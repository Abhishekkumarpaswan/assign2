import React, { useState } from 'react';
import { api } from '../services/api';
import { User } from '../types';
import { Lock, Mail, UserCheck, AlertCircle, Sparkles } from 'lucide-react';

interface LoginModalProps {
  onSuccess: (user: User) => void;
  onSelectRole: (role: 'customer1' | 'customer2' | 'support') => Promise<void>;
}

export const LoginModal: React.FC<LoginModalProps> = ({ onSuccess, onSelectRole }) => {
  const [isRegister, setIsRegister] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      if (isRegister) {
        const res = await api.register(name, email, password);
        onSuccess(res.user);
      } else {
        const res = await api.login(email, password);
        onSuccess(res.user);
      }
    } catch (err: any) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = async (role: 'customer1' | 'customer2' | 'support') => {
    setLoading(true);
    setError(null);
    try {
      await onSelectRole(role);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in to this demo account.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-[80vh] flex items-center justify-center p-4">
      <div className="bg-white border border-slate-200 rounded-3xl p-6 sm:p-8 w-full max-w-md shadow-xl text-center">
        {/* Brand Logo */}
        <div className="w-12 h-12 rounded-2xl bg-brand-500 text-white font-black text-2xl flex items-center justify-center mx-auto mb-3 shadow-sm">
          <span className="transform -skew-x-6">K</span>
        </div>

        <h1 className="text-2xl font-black text-slate-900 tracking-tight">KINETIC SUPPORT</h1>
        <p className="text-xs text-slate-500 mt-1">
          {isRegister ? 'Create an account to track orders & support' : 'Sign in to access your orders and support dashboard'}
        </p>

        {/* 1-Click Evaluation Accounts */}
        <div className="mt-5 p-3 rounded-2xl bg-slate-50 border border-slate-200/80 text-left space-y-2">
          <span className="text-[11px] font-bold text-slate-700 flex items-center gap-1">
            <UserCheck className="w-3.5 h-3.5 text-brand-500" />
            1-Click Demo Evaluation Login:
          </span>
          <div className="grid grid-cols-1 gap-1.5 text-xs font-semibold">
            <button
              type="button"
              onClick={() => handleDemoLogin('customer1')}
              disabled={loading}
              className="px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:border-brand-500 disabled:opacity-50 text-slate-800 flex items-center justify-between text-xs transition"
            >
              <span>Aarav Sharma (Customer 1)</span>
              <span className="text-[10px] text-brand-600 font-bold">Orders & Refunds →</span>
            </button>
            <button
              type="button"
              onClick={() => handleDemoLogin('customer2')}
              disabled={loading}
              className="px-3 py-1.5 rounded-xl bg-white border border-slate-200 hover:border-brand-500 disabled:opacity-50 text-slate-800 flex items-center justify-between text-xs transition"
            >
              <span>Meera Patel (Customer 2)</span>
              <span className="text-[10px] text-brand-600 font-bold">Independent Orders →</span>
            </button>
            <button
              type="button"
              onClick={() => handleDemoLogin('support')}
              disabled={loading}
              className="px-3 py-1.5 rounded-xl bg-brand-50 border border-brand-200 hover:bg-brand-100 disabled:opacity-50 text-brand-900 flex items-center justify-between text-xs transition"
            >
              <span>Kavita Reddy (Support Agent)</span>
              <span className="text-[10px] text-brand-700 font-bold">Adjudication Queue →</span>
            </button>
          </div>
        </div>

        <div className="relative my-5">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-slate-200" />
          </div>
          <div className="relative flex justify-center text-xs uppercase">
            <span className="bg-white px-2 text-slate-400 font-bold text-[10px]">Or sign in with email</span>
          </div>
        </div>

        {error && (
          <div role="alert" className="mb-4 p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-center gap-2 text-left">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-3.5 text-left">
          {isRegister && (
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Full Name</label>
              <input
                type="text"
                required
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Aarav Sharma"
                className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs sm:text-sm text-slate-900 focus:outline-hidden focus:border-brand-500 focus:bg-white"
              />
            </div>
          )}

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Email Address</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="aarav@example.com"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs sm:text-sm text-slate-900 focus:outline-hidden focus:border-brand-500 focus:bg-white"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2 text-xs sm:text-sm text-slate-900 focus:outline-hidden focus:border-brand-500 focus:bg-white"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 bg-brand-500 hover:bg-brand-600 disabled:opacity-50 text-white font-bold py-2.5 rounded-xl shadow-xs transition text-xs sm:text-sm"
          >
            {loading ? 'Please wait...' : isRegister ? 'Create Account' : 'Sign In'}
          </button>
        </form>

        <div className="mt-4 text-xs text-slate-500">
          {isRegister ? 'Already have an account? ' : "Don't have an account? "}
          <button
            type="button"
            onClick={() => setIsRegister(!isRegister)}
            className="text-brand-600 font-bold hover:underline"
          >
            {isRegister ? 'Sign In' : 'Register'}
          </button>
        </div>
      </div>
    </div>
  );
};
