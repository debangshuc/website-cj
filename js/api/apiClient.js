import { authClient } from '../auth/authClient.js';

/**
 * Centralized API Client Module
 * Handles HTTP communication with the FastAPI backend and automatically attaches Bearer tokens.
 */
export const API_BASE_URL = window.API_BASE_URL || 'http://localhost:8000';

export class ApiError extends Error {
  constructor(message, status, data = null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function request(endpoint, options = {}, isRetry = false) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  
  // 1. Build headers with Bearer token
  const headers = {
    'Accept': 'application/json',
    ...(options.body && !(options.body instanceof FormData) ? { 'Content-Type': 'application/json' } : {}),
    ...options.headers,
  };

  const token = authClient.getAccessToken();
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const config = {
    ...options,
    headers,
  };

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    config.body = JSON.stringify(options.body);
  }

  let response;
  try {
    response = await fetch(url, config);
  } catch (netErr) {
    throw new ApiError(
      'Unable to connect to the backend server. Please verify FastAPI is running.',
      0,
      netErr
    );
  }

  // 2. Handle 401 Unauthorized (Session Expired / Token Refresh)
  if (response.status === 401 && !isRetry) {
    const refreshed = await authClient.refreshSession();
    if (refreshed && refreshed.access_token) {
      // Retry once with new token
      return request(endpoint, options, true);
    } else {
      // Refresh failed or no refresh token -> sign out
      authClient.signOut();
      throw new ApiError('Session expired. Please sign in again.', 401);
    }
  }

  if (response.status === 204) {
    return null;
  }

  let data;
  try {
    data = await response.json();
  } catch (jsonErr) {
    data = null;
  }

  if (!response.ok) {
    let errorMsg = 'API request failed';
    if (data && data.detail) {
      if (typeof data.detail === 'string') {
        errorMsg = data.detail;
      } else if (Array.isArray(data.detail)) {
        errorMsg = data.detail.map(err => err.msg || JSON.stringify(err)).join(', ');
      }
    } else {
      errorMsg = `API request failed with status ${response.status}`;
    }
    throw new ApiError(errorMsg, response.status, data);
  }

  return data;
}

export const apiClient = {
  get(endpoint, params = {}) {
    const searchParams = new URLSearchParams();
    Object.entries(params).forEach(([key, val]) => {
      if (val !== undefined && val !== null && val !== '') {
        searchParams.append(key, val);
      }
    });
    const query = searchParams.toString();
    const url = query ? `${endpoint}?${query}` : endpoint;
    return request(url, { method: 'GET' });
  },

  post(endpoint, body = {}) {
    return request(endpoint, { method: 'POST', body });
  },

  patch(endpoint, body = {}) {
    return request(endpoint, { method: 'PATCH', body });
  },

  delete(endpoint) {
    return request(endpoint, { method: 'DELETE' });
  },
};
