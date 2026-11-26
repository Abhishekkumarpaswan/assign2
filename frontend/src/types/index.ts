export interface User {
  id: string;
  name: string;
  email: string;
  role: 'customer' | 'support_agent' | 'admin';
  created_at: string;
}

export interface OrderItem {
  name: string;
  qty: number;
  price: number;
  category: string;
}

export interface Order {
  id: string;
  customer_id: string;
  status: 'delivered' | 'in_transit' | 'processing' | 'cancelled' | 'returned';
  delivery_date: string | null;
  total_amount: number;
  category: string;
  item_details: OrderItem[];
  created_at: string;
  is_return_window_open?: boolean;
  days_since_delivery?: number | null;
}

export interface Message {
  id: string;
  ticket_id: string;
  sender_type: 'customer' | 'ai' | 'agent' | 'system';
  content: string;
  created_at: string;
}

export interface Refund {
  id: string;
  order_id: string;
  ticket_id: string;
  amount: number;
  reason: string;
  status: 'pending_review' | 'escalated' | 'approved' | 'rejected';
  idempotency_key?: string;
  requested_by: string;
  reviewed_by?: string;
  decision_reason?: string;
  created_at: string;
  updated_at: string;
}

export interface Escalation {
  id: string;
  ticket_id: string;
  summary: string;
  priority: 'low' | 'medium' | 'high' | 'urgent';
  assigned_to?: string;
  decision: 'pending' | 'approved' | 'rejected' | 'info_requested';
  internal_note?: string;
  created_at: string;
  updated_at: string;
}

export interface Ticket {
  id: string;
  customer_id: string;
  order_id?: string;
  subject: string;
  description: string;
  category: string;
  status: 'open' | 'in_progress' | 'escalated' | 'resolved' | 'closed';
  priority: 'low' | 'medium' | 'high' | 'urgent';
  created_at: string;
  updated_at: string;
  customer?: User;
  order?: Order;
  messages?: Message[];
  refunds?: Refund[];
  escalations?: Escalation[];
}

export interface ReturnPolicy {
  category: string;
  window_days: number;
  allowed_reasons: string[];
  non_refundable_items: string[];
  condition_required: string;
  notes: string;
}
