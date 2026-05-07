/**
 * SheEarn API Client
 * Central module for all backend communication.
 */

const API_BASE = `${window.location.origin}/api`;

/* ── Token Management ────────────────────────────────────────────────────────── */
const Auth = {
  setTokens(access, refresh) {
    localStorage.setItem('she_token', access);
    localStorage.setItem('she_refresh', refresh);
  },
  getToken() { return localStorage.getItem('she_token'); },
  getRefresh() { return localStorage.getItem('she_refresh'); },
  clearTokens() {
    localStorage.removeItem('she_token');
    localStorage.removeItem('she_refresh');
    localStorage.removeItem('she_user');
  },
  setUser(u) { localStorage.setItem('she_user', JSON.stringify(u)); },
  getUser() { try { return JSON.parse(localStorage.getItem('she_user')); } catch { return null; } },
  isLoggedIn() { return !!this.getToken(); },
  requireAuth() {
    if (!this.isLoggedIn()) { window.location.href = 'auth.html'; return false; }
    return true;
  },
  requireRole(...roles) {
    const u = this.getUser();
    if (!u || !roles.includes(u.role)) { window.location.href = 'index.html'; return false; }
    return true;
  },
};

/* ── Core Fetch ──────────────────────────────────────────────────────────────── */
async function apiFetch(path, options = {}) {
  const token = Auth.getToken();
  const headers = { ...options.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  if (!(options.body instanceof FormData)) headers['Content-Type'] = 'application/json';

  const fetchOptions = { ...options, headers };
  // Disable caching for GET requests to prevent stale UI
  if (!options.method || options.method.toUpperCase() === 'GET') {
    fetchOptions.cache = 'no-store';
  }

  let res = await fetch(`${API_BASE}${path}`, fetchOptions);

  // Auto-refresh
  if (res.status === 401 && Auth.getRefresh()) {
    const rRes = await fetch(`${API_BASE}/auth/refresh`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${Auth.getRefresh()}`, 'Content-Type': 'application/json' },
    });
    if (rRes.ok) {
      const rData = await rRes.json();
      Auth.setTokens(rData.data.access_token, Auth.getRefresh());
      headers['Authorization'] = `Bearer ${rData.data.access_token}`;
      res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    } else {
      Auth.clearTokens();
      window.location.href = 'auth.html';
      return null;
    }
  }

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new APIError(data.error || 'Request failed', res.status, data);
  return data;
}

class APIError extends Error {
  constructor(message, status, data) {
    super(message); this.status = status; this.data = data;
  }
}

/* ── API Methods ─────────────────────────────────────────────────────────────── */
const api = {
  // Auth
  register: (d) => apiFetch('/auth/register', { method: 'POST', body: d instanceof FormData ? d : JSON.stringify(d) }),
  login: (d) => apiFetch('/auth/login', { method: 'POST', body: JSON.stringify(d) }),
  requestOtp: (phone) => apiFetch('/auth/request-otp', { method: 'POST', body: JSON.stringify({ phone }) }),
  loginOtp: (d) => apiFetch('/auth/login-otp', { method: 'POST', body: JSON.stringify(d) }),
  me: () => apiFetch('/auth/me'),
  changePassword: (d) => apiFetch('/auth/change-password', { method: 'POST', body: JSON.stringify(d) }),
  forgotPassword: (identifier) => apiFetch('/auth/forgot-password', { method: 'POST', body: JSON.stringify({ identifier }) }),
  resetPassword: (d) => apiFetch('/auth/reset-password', { method: 'POST', body: JSON.stringify(d) }),

  // Profile
  getProfile: () => apiFetch('/profile/'),
  updateProfile: (d) => apiFetch('/profile/', { method: 'PUT', body: JSON.stringify(d) }),
  getPublicProfile: (id) => apiFetch(`/profile/${id}`),
  uploadProfileImage: (f) => {
    const fd = new FormData(); fd.append('image', f);
    return apiFetch('/profile/upload-image', { method: 'POST', body: fd });
  },
  removeProfileImage: () => apiFetch('/profile/remove-image', { method: 'DELETE' }),

  // Services
  listServices: (params = {}) => apiFetch('/services/?' + new URLSearchParams(params)),
  getService: (id) => apiFetch(`/services/${id}`),
  createService: (d) => apiFetch('/services/', { method: 'POST', body: d instanceof FormData ? d : JSON.stringify(d) }),
  updateService: (id, d) => apiFetch(`/services/${id}`, { method: 'PUT', body: JSON.stringify(d) }),
  deleteService: (id) => apiFetch(`/services/${id}`, { method: 'DELETE' }),
  myServices: () => apiFetch('/services/my'),
  categories: () => apiFetch('/services/categories'),
  uploadServiceImages: (id, files) => {
    const fd = new FormData();
    files.forEach(f => fd.append('images', f));
    return apiFetch(`/services/${id}/images`, { method: 'POST', body: fd });
  },

  // Bookings
  createBooking: (d) => apiFetch('/bookings/', { method: 'POST', body: JSON.stringify(d) }),
  listBookings: (params = {}) => apiFetch('/bookings/?' + new URLSearchParams(params)),
  getBooking: (id) => apiFetch(`/bookings/${id}`),
  acceptBooking: (id) => apiFetch(`/bookings/${id}/accept`, { method: 'POST' }),
  rejectBooking: (id) => apiFetch(`/bookings/${id}/reject`, { method: 'POST' }),
  completeBooking: (id) => apiFetch(`/bookings/${id}/complete`, { method: 'POST' }),
  cancelBooking: (id) => apiFetch(`/bookings/${id}/cancel`, { method: 'POST' }),
  updateBookingStatus: (id, status) => apiFetch(`/bookings/${id}/status`, { method: 'PUT', body: JSON.stringify({ status }) }),

  // Payments (Real UPI)
  initiatePayment: (d) => apiFetch('/payments/initiate', { method: 'POST', body: JSON.stringify(d) }),
  confirmPayment: (id, d = {}) => apiFetch(`/payments/confirm/${id}`, { method: 'POST', body: JSON.stringify(d) }),
  getWallet: () => apiFetch('/payments/wallet'),
  addMoney: (amount) => apiFetch('/payments/wallet/add', { method: 'POST', body: JSON.stringify({ amount }) }),
  paymentHistory: () => apiFetch('/payments/history'),

  // Ratings
  submitRating: (d) => apiFetch('/ratings/', { method: 'POST', body: JSON.stringify(d) }),
  serviceRatings: (id) => apiFetch(`/ratings/service/${id}`),

  // Chat
  conversations: () => apiFetch('/chat/conversations'),
  getMessages: (uid, page = 1) => apiFetch(`/chat/messages/${uid}?page=${page}`),
  sendMessage: (d) => apiFetch('/chat/send', { method: 'POST', body: JSON.stringify(d) }),
  deleteMessage: (id) => apiFetch(`/chat/messages/${id}`, { method: 'DELETE' }),
  searchUsers: (q) => apiFetch(`/chat/search-users?q=${encodeURIComponent(q)}`),
  unreadCount: () => apiFetch('/chat/unread-count'),

  // Schemes
  listSchemes: (params = {}) => apiFetch('/schemes/?' + new URLSearchParams(params)),
  getScheme: (id) => apiFetch(`/schemes/${id}`),
  schemeCategories: () => apiFetch('/schemes/categories'),

  // Admin
  adminStats: () => apiFetch('/admin/stats'),
  adminUsers: (p = {}) => apiFetch('/admin/users?' + new URLSearchParams(p)),
  adminToggleUser: (id) => apiFetch(`/admin/users/${id}/toggle-active`, { method: 'POST' }),
  adminMakeAdmin: (id) => apiFetch(`/admin/users/${id}/make-admin`, { method: 'POST' }),
  adminPendingServices: () => apiFetch('/admin/services/pending'),
  adminApproveService: (id) => apiFetch(`/admin/services/${id}/approve`, { method: 'POST' }),
  adminRejectService: (id) => apiFetch(`/admin/services/${id}/reject`, { method: 'POST' }),
  adminAllBookings: (p = {}) => apiFetch('/admin/bookings?' + new URLSearchParams(p)),
  adminAllPayments: (p = {}) => apiFetch('/admin/payments?' + new URLSearchParams(p)),
  adminCreditWallet: (d) => apiFetch('/admin/wallet/credit', { method: 'POST', body: JSON.stringify(d) }),
};

/* ── Category Emoji Map ──────────────────────────────────────────────────────── */
const CATEGORY_EMOJI = {
  cooking: '🍳', stitching: '🧵', tutoring: '📚',
  handmade_crafts: '🎨', beauty: '💄', cleaning: '🧹', other: '✨',
};
const CATEGORY_LABEL = {
  cooking: 'Cooking', stitching: 'Stitching', tutoring: 'Tutoring',
  handmade_crafts: 'Handmade Crafts', beauty: 'Beauty', cleaning: 'Cleaning', other: 'Other',
};
const STATUS_BADGE = {
  pending: 'badge-warning', accepted: 'badge-info',
  confirmed: 'badge-info', packed: 'badge-info', out_for_delivery: 'badge-primary',
  completed: 'badge-success', rejected: 'badge-danger', cancelled: 'badge-danger',
};
