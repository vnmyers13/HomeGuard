/**
 * API client layer - axios instance with auth interceptors.
 * 
 * JWT tokens are kept in memory only (CP-10 compliance).
 * Tokens are NOT stored in localStorage or sessionStorage.
 */

import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// In-memory token storage - never persisted to localStorage
let accessToken = null;
let refreshToken = null;

/**
 * Set tokens in memory after login/register.
 */
export function setTokens(access, refresh) {
  accessToken = access;
  refreshToken = refresh;
}

/**
 * Clear tokens on logout.
 */
export function clearTokens() {
  accessToken = null;
  refreshToken = null;
}

/**
 * Get current access token (for external use).
 */
export function getAccessToken() {
  return accessToken;
}

// Request interceptor - attach Authorization header
api.interceptors.request.use(
  (config) => {
    if (accessToken) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle 401 with token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // Only retry once on 401, and only if we haven't already retried
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      refreshToken
    ) {
      originalRequest._retry = true;

      try {
        // Try to refresh the token
        const response = await axios.post(`${API_BASE}/auth/refresh`, {
          refresh_token: refreshToken,
        });

        const newAccess = response.data?.data?.access_token;
        const newRefresh = response.data?.data?.refresh_token;

        if (newAccess) {
          accessToken = newAccess;
        }
        if (newRefresh) {
          refreshToken = newRefresh;
        }

        // Retry original request with new token
        originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed - clear tokens and let the app handle logout
        clearTokens();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// --- Auth endpoints (no auth header needed) ---

export const authApi = {
  register: (data) => api.post('/auth/register', data),
  login: (data) => api.post('/auth/login', data),
  verify: () => api.get('/auth/verify'),
  logout: () => api.post('/auth/logout'),
  changePassword: (data) => api.post('/auth/change-password', data),
};

// --- Profile endpoints ---

export const profilesApi = {
  list: (params) => api.get('/profiles', { params }),
  get: (id) => api.get(`/profiles/${id}`),
  create: (data) => api.post('/profiles', data),
  update: (id, data) => api.patch(`/profiles/${id}`, data),
  delete: (id) => api.delete(`/profiles/${id}`),
  addField: (profileId, data) => api.post(`/profiles/${profileId}/fields`, data),
  removeField: (profileId, fieldId) => api.delete(`/profiles/${profileId}/fields/${fieldId}`),
};

// --- Broker endpoints ---

export const brokersApi = {
  list: (params) => api.get('/brokers', { params }),
  get: (id) => api.get(`/brokers/${id}`),
  create: (data) => api.post('/brokers', data),
  update: (id, data) => api.patch(`/brokers/${id}`, data),
  delete: (id) => api.delete(`/brokers/${id}`),
  healthCheck: (domain) => api.get(`/brokers/health`, { params: { domain } }),
  triggerScan: (data) => api.post('/brokers/scan', data),
};

// --- Scan endpoints ---

export const scansApi = {
  list: (params) => api.get('/scans', { params }),
  get: (id) => api.get(`/scans/${id}`),
  trigger: (data) => api.post('/scans', data),
  cancel: (id) => api.post(`/scans/${id}/cancel`),
};

// --- Webhook endpoints ---

export const webhooksApi = {
  list: () => api.get('/webhooks'),
  create: (data) => api.post('/webhooks', data),
  update: (id, data) => api.patch(`/webhooks/${id}`, data),
  delete: (id) => api.delete(`/webhooks/${id}`),
  test: (id) => api.post(`/webhooks/${id}/test`),
};

// --- System endpoints ---

export const systemApi = {
  health: () => api.get('/system/health'),
};

// --- Alert endpoints ---

export const alertsApi = {
  list: (params) => api.get('/alerts', { params }),
  get: (id) => api.get(`/alerts/${id}`),
  acknowledge: (id) => api.post(`/alerts/${id}/acknowledge`),
};

// --- Request endpoints ---

export const getRequests = (params) => api.get('/requests', { params });
export const getRequest = (id) => api.get(`/requests/${id}`);
export const createRequest = (data) => api.post('/requests', data);
export const updateRequest = (id, data) => api.patch(`/requests/${id}`, data);
export const deleteRequest = (id) => api.delete(`/requests/${id}`);
export const getRequestLogs = (id) => api.get(`/requests/${id}/logs`);
export const getFollowups = (id) => api.get(`/requests/${id}/followups`);
export const createFollowup = (id, data) => api.post(`/requests/${id}/followups`, data);
export const getVerificationScans = (id) => api.get(`/requests/${id}/verification-scans`);
export const createVerificationScan = (id, data) => api.post(`/requests/${id}/verification-scans`, data);
export const downloadLegalLetter = (id, letterType) =>
  api.get(`/requests/${id}/pdf`, { params: { letter_type: letterType }, responseType: 'blob' });

// --- Report endpoints ---

export const getExposureTrends = (params) => api.get('/reports/exposure-trends', { params });
export const getBrokerSummary = () => api.get('/reports/broker-summary');
export const getRemovalStats = () => api.get('/reports/removal-stats');

// --- System endpoints ---

export const getDiskUsage = () => api.get('/system/disk-usage');

// --- Notification preferences (client-side only, no backend endpoint yet) ---

const PREFS_KEY = 'homeguard_prefs';

export const getPreferences = () => {
  const stored = localStorage.getItem(PREFS_KEY);
  if (stored) return Promise.resolve({ data: JSON.parse(stored) });
  return Promise.resolve({
    data: {
      email_enabled: true,
      in_app_enabled: true,
      digest_frequency: 'realtime',
      alert_types: { new_listing: true, removal: true, scan_complete: true, opt_out: true },
    },
  });
};

export const updatePreferences = (prefs) => {
  localStorage.setItem(PREFS_KEY, JSON.stringify(prefs));
  return Promise.resolve({ data: prefs });
};

export const getAlerts = (params) => alertsApi.list(params);

// --- Removal request endpoints ---

export const requestsApi = {
  list: (params) => api.get('/requests', { params }),
  get: (id) => api.get(`/requests/${id}`),
  create: (data) => api.post('/requests', data),
  update: (id, data) => api.patch(`/requests/${id}`, data),
  delete: (id) => api.delete(`/requests/${id}`),
  getLogs: (id) => api.get(`/requests/${id}/logs`),
  getFollowups: (id) => api.get(`/requests/${id}/followups`),
  createFollowup: (id, data) => api.post(`/requests/${id}/followups`, data),
  getVerificationScans: (id) => api.get(`/requests/${id}/verification-scans`),
  createVerificationScan: (id, data) => api.post(`/requests/${id}/verification-scans`, data),
  downloadPdf: (id, type = 'ccpa') => api.get(`/requests/${id}/pdf`, { params: { letter_type: type }, responseType: 'blob' }),
};

export const getRequests = requestsApi.list;
export const createRequest = requestsApi.create;
export const updateRequest = requestsApi.update;
export const deleteRequest = requestsApi.delete;
export const getRequest = requestsApi.get;
export const downloadLegalLetter = requestsApi.downloadPdf;
export const getFollowups = requestsApi.getFollowups;
export const createFollowup = requestsApi.createFollowup;
export const getVerificationScans = requestsApi.getVerificationScans;
export const createVerificationScan = requestsApi.createVerificationScan;

// --- WebSocket scan progress ---

export function connectScanProgress(scanId, onMessage) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/ws/scans/${scanId}`;
  const ws = new WebSocket(wsUrl);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (e) {
      console.error('WebSocket message parse error:', e);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };

  ws.onclose = () => {
    console.log('WebSocket closed');
  };

  return ws;
}

// --- Convenience exports (shorthand) ---

export const getProfiles = profilesApi.list;
export const createProfile = profilesApi.create;
export const updateProfile = (id, data) => profilesApi.update(id, data);
export const deleteProfile = profilesApi.delete;
export const getProfile = profilesApi.get;

export const getBrokers = brokersApi.list;
export const triggerScan = brokersApi.triggerScan;

export const getScans = scansApi.list;
export const triggerScanJob = scansApi.trigger;

export default api;
