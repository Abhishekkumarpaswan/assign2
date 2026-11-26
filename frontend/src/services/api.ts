import { User, Order, Ticket, Message, Refund, Escalation, ReturnPolicy } from '../types';

const API_BASE = '/api/v1';

class ApiClient {
  private token: string | null = null;

  constructor() {
    this.token = localStorage.getItem('kinetic_auth_token');
  }

  setToken(token: string | null) {
    this.token = token;
    if (token) {
      localStorage.setItem('kinetic_auth_token', token);
    } else {
      localStorage.removeItem('kinetic_auth_token');
    }
  }

  getToken(): string | null {
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string>),
    };

    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      this.setToken(null);
    }

    if (!response.ok) {
      if (response.status >= 500) {
        throw new Error('Support is temporarily unavailable. Please try again in a moment.');
      }

      let errorDetail = 'Request failed';
      try {
        const errorData = await response.json();
        if (Array.isArray(errorData.detail)) {
          errorDetail = errorData.detail.map((d: any) => d.msg || JSON.stringify(d)).join(', ');
        } else {
          errorDetail = errorData.detail || errorData.message || JSON.stringify(errorData);
        }
      } catch (e) {
        errorDetail = response.statusText;
      }
      throw new Error(errorDetail);
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await this.request<{ access_token: string; user: User }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async register(name: string, email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await this.request<{ access_token: string; user: User }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  logout() {
    this.setToken(null);
  }

  // Orders
  async getOrders(): Promise<Order[]> {
    return this.request<Order[]>('/orders');
  }

  async getOrder(orderId: string): Promise<Order> {
    return this.request<Order>(`/orders/${orderId}`);
  }

  // Tickets
  async getTickets(params?: { status?: string; priority?: string; category?: string; search?: string }): Promise<Ticket[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.priority) query.append('priority', params.priority);
    if (params?.category) query.append('category', params.category);
    if (params?.search) query.append('search', params.search);

    const qs = query.toString();
    return this.request<Ticket[]>(`/tickets${qs ? `?${qs}` : ''}`);
  }

  async getTicketDetails(ticketId: string): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${ticketId}`);
  }

  async getSupportTicketDetails(ticketId: string): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${ticketId}/support-view`);
  }

  async createTicket(payload: { subject: string; description: string; category?: string; order_id?: string; priority?: string }): Promise<Ticket> {
    return this.request<Ticket>('/tickets', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  }

  async updateTicket(ticketId: string, payload: { status?: string; priority?: string; internal_note?: string }): Promise<Ticket> {
    return this.request<Ticket>(`/tickets/${ticketId}`, {
      method: 'PATCH',
      body: JSON.stringify(payload),
    });
  }

  async addMessage(ticketId: string, content: string): Promise<Message> {
    return this.request<Message>(`/tickets/${ticketId}/messages`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    });
  }

  // AI Chat
  async sendChatMessage(ticketId: string, message: string): Promise<{
    response: string;
    ticket_status: string;
    refund_status?: string;
    escalated: boolean;
  }> {
    return this.request(`/tickets/${ticketId}/chat`, {
      method: 'POST',
      body: JSON.stringify({ ticket_id: ticketId, message }),
    });
  }

  // Refunds
  async getRefunds(params?: { status?: string; order_id?: string }): Promise<Refund[]> {
    const query = new URLSearchParams();
    if (params?.status) query.append('status', params.status);
    if (params?.order_id) query.append('order_id', params.order_id);
    const qs = query.toString();
    return this.request<Refund[]>(`/refunds${qs ? `?${qs}` : ''}`);
  }

  async reviewRefund(refundId: string, decision: 'approved' | 'rejected' | 'info_requested', decision_reason?: string): Promise<Refund> {
    return this.request<Refund>(`/refunds/${refundId}/review`, {
      method: 'POST',
      body: JSON.stringify({ decision, decision_reason }),
    });
  }

  // Escalations
  async getEscalations(params?: { decision?: string; priority?: string }): Promise<Escalation[]> {
    const query = new URLSearchParams();
    if (params?.decision) query.append('decision', params.decision);
    if (params?.priority) query.append('priority', params.priority);
    const qs = query.toString();
    return this.request<Escalation[]>(`/escalations${qs ? `?${qs}` : ''}`);
  }

  async decideEscalation(escalationId: string, decision: 'approved' | 'rejected' | 'info_requested', internal_note?: string): Promise<Escalation> {
    return this.request<Escalation>(`/escalations/${escalationId}/decision`, {
      method: 'POST',
      body: JSON.stringify({ decision, internal_note }),
    });
  }

  // Policies
  async getPolicies(): Promise<ReturnPolicy[]> {
    return this.request<ReturnPolicy[]>('/policies');
  }

  async searchPolicy(query: string): Promise<ReturnPolicy> {
    return this.request<ReturnPolicy>(`/policies/search?q=${encodeURIComponent(query)}`);
  }
}

export const api = new ApiClient();
