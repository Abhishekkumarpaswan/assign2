import React, { useState, useEffect, useRef } from 'react';
import { Ticket, Message } from '../types';
import { api } from '../services/api';
import {
  X,
  Send,
  Sparkles,
  User as UserIcon,
  RefreshCw,
  Headphones
} from 'lucide-react';

interface ChatModalProps {
  ticket: Ticket;
  onClose: () => void;
  onTicketUpdated: () => void;
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

export const ChatModal: React.FC<ChatModalProps> = ({
  ticket,
  onClose,
  onTicketUpdated,
}) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentStatus, setCurrentStatus] = useState(ticket.status);
  const [inputMessage, setInputMessage] = useState('');
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const loadTicketDetails = async () => {
    setHistoryError(null);
    setLoadingHistory(true);
    try {
      const fullTicket = await api.getTicketDetails(ticket.id);
      setMessages(fullTicket.messages || []);
      setCurrentStatus(fullTicket.status);
    } catch (e) {
      console.error(e);
      setHistoryError(e instanceof Error ? e.message : 'Unable to load this conversation.');
    } finally {
      setLoadingHistory(false);
    }
  };

  useEffect(() => {
    loadTicketDetails();
  }, [ticket.id]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, sending]);

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || sending) return;

    setInputMessage('');
    setSending(true);

    const tempId = `temp-${Date.now()}`;
    const optimisticMsg: Message = {
      id: tempId,
      ticket_id: ticket.id,
      sender_type: 'customer',
      content: text,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, optimisticMsg]);

    try {
      await api.sendChatMessage(ticket.id, text);
      await loadTicketDetails();
      onTicketUpdated();
    } catch (e: any) {
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          ticket_id: ticket.id,
          sender_type: 'ai',
          content: e.message || 'Unable to send message right now. Please try again.',
          created_at: new Date().toISOString(),
        },
      ]);
    } finally {
      setSending(false);
    }
  };

  const statusBadge = () => {
    if (currentStatus === 'resolved') {
      return { label: 'Resolved', cls: 'bg-emerald-50 text-emerald-700 border-emerald-200' };
    }
    if (currentStatus === 'escalated') {
      return { label: 'Specialist Review', cls: 'bg-amber-50 text-amber-700 border-amber-200' };
    }
    if (currentStatus === 'closed') {
      return { label: 'Closed', cls: 'bg-slate-100 text-slate-600 border-slate-200' };
    }
    return { label: 'Active', cls: 'bg-brand-50 text-brand-700 border-brand-200' };
  };

  const badge = statusBadge();

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-slate-900/50 backdrop-blur-xs">
      <div className="bg-white border border-slate-200 rounded-2xl w-full max-w-2xl h-[86vh] flex flex-col shadow-2xl overflow-hidden">
        {/* Clean Support Header */}
        <div className="bg-white border-b border-slate-200 px-5 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-full bg-brand-500 flex items-center justify-center text-white shadow-xs">
              <Headphones className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h2 className="font-bold text-slate-900 text-sm sm:text-base">Kinetic Support</h2>
                {ticket.order_id && (
                  <span className="text-[11px] font-semibold px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                    {ticket.order_id}
                  </span>
                )}
                <span className={`text-[11px] font-semibold px-2.5 py-0.5 rounded-full border ${badge.cls}`}>
                  {badge.label}
                </span>
              </div>
              <p className="text-xs text-slate-500 truncate max-w-xs sm:max-w-md mt-0.5">
                {ticket.subject} · <span className="text-slate-400">{ticket.id}</span>
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1">
            <button
              onClick={loadTicketDetails}
              title="Refresh conversation"
              className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition"
            >
              <RefreshCw className={`w-4 h-4 ${loadingHistory ? 'animate-spin' : ''}`} />
            </button>
            <button
              onClick={onClose}
              className="p-2 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-full transition"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 bg-slate-50/70">
          {loadingHistory && messages.length === 0 ? (
            <div className="flex items-center justify-center h-full text-slate-400 text-xs">
              <RefreshCw className="w-4 h-4 animate-spin mr-2" />
              Loading conversation...
            </div>
          ) : historyError && messages.length === 0 ? (
            <div role="alert" className="m-auto max-w-sm rounded-2xl border border-rose-200 bg-white p-5 text-center text-sm text-rose-700">
              <p>{historyError}</p>
              <button
                type="button"
                onClick={loadTicketDetails}
                className="mt-3 rounded-lg bg-rose-50 px-3 py-2 text-xs font-semibold text-rose-800 hover:bg-rose-100"
              >
                Try again
              </button>
            </div>
          ) : (
            messages.map((msg) => {
              const isCustomer = msg.sender_type === 'customer';
              const isAI = msg.sender_type === 'ai';

              return (
                <div
                  key={msg.id}
                  className={`flex flex-col ${isCustomer ? 'items-end' : 'items-start'}`}
                >
                  <div
                    className={`flex items-end gap-2 max-w-[85%] sm:max-w-[78%] ${
                      isCustomer ? 'flex-row-reverse' : 'flex-row'
                    }`}
                  >
                    <div
                      className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
                        isCustomer
                          ? 'bg-slate-200 text-slate-700'
                          : isAI
                          ? 'bg-brand-500 text-white'
                          : 'bg-slate-800 text-white'
                      }`}
                    >
                      {isCustomer ? (
                        <UserIcon className="w-3.5 h-3.5" />
                      ) : isAI ? (
                        <Sparkles className="w-3.5 h-3.5" />
                      ) : (
                        'K'
                      )}
                    </div>

                    <div
                      className={`rounded-2xl px-4 py-3 text-xs sm:text-sm leading-relaxed ${
                        isCustomer
                          ? 'bg-brand-500 text-white rounded-br-xs shadow-xs'
                          : isAI
                          ? 'bg-white text-slate-800 border border-slate-200/80 rounded-bl-xs shadow-2xs'
                          : 'bg-slate-900 text-white rounded-bl-xs shadow-xs'
                      }`}
                    >
                      <div className="whitespace-pre-line">{formatMessageText(msg.content)}</div>
                      <div
                        className={`text-[10px] mt-1.5 flex items-center gap-1.5 ${
                          isCustomer ? 'text-white/75 justify-end' : 'text-slate-400'
                        }`}
                      >
                        <span>{isCustomer ? 'You' : isAI ? 'Kinetic Assistant' : 'Support Specialist'}</span>
                        <span>·</span>
                        <span>
                          {new Date(msg.created_at).toLocaleTimeString([], {
                            hour: '2-digit',
                            minute: '2-digit',
                          })}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {sending && (
            <div className="flex items-end gap-2">
              <div className="w-7 h-7 rounded-full bg-brand-500 text-white flex items-center justify-center shrink-0">
                <Sparkles className="w-3.5 h-3.5" />
              </div>
              <div className="bg-white border border-slate-200/80 rounded-2xl rounded-bl-xs px-4 py-3 shadow-2xs flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '0ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '150ms' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Helpful Quick Prompts */}
        <div className="bg-white border-t border-slate-100 px-4 py-2.5 flex items-center gap-2 overflow-x-auto text-xs">
          {ticket.order_id && (
            <>
              <button
                onClick={() => handleSend(`Where is my order ${ticket.order_id}?`)}
                className="px-3 py-1 bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-700 rounded-full font-medium whitespace-nowrap transition"
              >
                Track {ticket.order_id}
              </button>
              <button
                onClick={() => handleSend(`I would like to request a refund for order ${ticket.order_id}`)}
                className="px-3 py-1 bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-700 rounded-full font-medium whitespace-nowrap transition"
              >
                Request refund
              </button>
            </>
          )}
          <button
            onClick={() => handleSend('What is the return policy?')}
            className="px-3 py-1 bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-700 rounded-full font-medium whitespace-nowrap transition"
          >
            Return policy
          </button>
          <button
            onClick={() => handleSend('Please connect me to a human support specialist.')}
            className="px-3 py-1 bg-slate-100 hover:bg-brand-50 hover:text-brand-700 text-slate-700 rounded-full font-medium whitespace-nowrap transition"
          >
            Talk to a specialist
          </button>
        </div>

        {/* Input Bar */}
        <div className="p-3.5 sm:p-4 bg-white border-t border-slate-200 flex items-center gap-2.5">
          <input
            type="text"
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter') handleSend();
            }}
            placeholder="Write a message..."
            disabled={sending}
            className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-slate-900 focus:outline-hidden focus:border-brand-500 focus:bg-white transition"
          />
          <button
            onClick={() => handleSend()}
            disabled={!inputMessage.trim() || sending}
            className="bg-brand-500 hover:bg-brand-600 disabled:opacity-40 text-white font-semibold p-2.5 sm:px-5 sm:py-2.5 rounded-xl shadow-xs transition flex items-center gap-1.5"
          >
            <Send className="w-4 h-4" />
            <span className="hidden sm:inline text-xs font-semibold">Send</span>
          </button>
        </div>
      </div>
    </div>
  );
};
