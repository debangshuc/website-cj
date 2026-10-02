import { SUPABASE_CONFIG } from './config.js';

/**
 * Centralized Supabase Auth Client
 * Manages administrative sessions, login, logout, token persistence, and auth state listeners.
 */
class AuthClient {
  constructor() {
    this.session = null;
    this.listeners = new Set();
    this.isInitialized = false;
  }

  /**
   * Initialize session from persistent storage.
   */
  async init() {
    if (this.isInitialized) return this.session;

    try {
      const stored = localStorage.getItem(SUPABASE_CONFIG.storageKey);
      if (stored) {
        const parsed = JSON.parse(stored);
        const now = Math.floor(Date.now() / 1000);
        
        // If token expired but refresh token exists, refresh it
        if (parsed.expires_at && parsed.expires_at < now && parsed.refresh_token) {
          await this.refreshSession(parsed.refresh_token);
        } else if (parsed.access_token) {
          this.session = parsed;
        }
      }
    } catch (err) {
      console.warn('Failed to parse saved auth session:', err);
      localStorage.removeItem(SUPABASE_CONFIG.storageKey);
      this.session = null;
    }

    this.isInitialized = true;
    return this.session;
  }

  /**
   * Sign in with Email and Password
   * @param {Object} credentials - { email, password }
   */
  async signInWithPassword({ email, password }) {
    if (!email || !password) {
      return { data: null, error: { message: 'Email and password are required.' } };
    }

    try {
      const res = await fetch(`${SUPABASE_CONFIG.url}/auth/v1/token?grant_type=password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'apikey': SUPABASE_CONFIG.anonKey,
        },
        body: JSON.stringify({ email: email.trim(), password })
      });

      const data = await res.json();

      if (!res.ok) {
        return {
          data: null,
          error: {
            message: data.error_description || data.msg || data.message || 'Invalid login credentials.',
            status: res.status,
          }
        };
      }

      const now = Math.floor(Date.now() / 1000);
      const session = {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        expires_in: data.expires_in,
        expires_at: now + (data.expires_in || 3600),
        user: data.user,
      };

      this._saveSession(session);
      this._notifyListeners('SIGNED_IN', session);

      return { data: { session, user: session.user }, error: null };
    } catch (err) {
      return {
        data: null,
        error: { message: err.message || 'Network error during authentication.' }
      };
    }
  }

  /**
   * Sign out current administrative session
   */
  async signOut() {
    const token = this.getAccessToken();
    if (token) {
      try {
        await fetch(`${SUPABASE_CONFIG.url}/auth/v1/logout`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'apikey': SUPABASE_CONFIG.anonKey,
            'Authorization': `Bearer ${token}`,
          }
        });
      } catch (err) {
        console.warn('Remote logout notification failed:', err);
      }
    }

    this._clearSession();
    this._notifyListeners('SIGNED_OUT', null);
    return { error: null };
  }

  /**
   * Attempt token refresh with Supabase refresh token
   */
  async refreshSession(refreshTokenParam) {
    const refreshToken = refreshTokenParam || this.session?.refresh_token;
    if (!refreshToken) {
      this._clearSession();
      this._notifyListeners('SIGNED_OUT', null);
      return null;
    }

    try {
      const res = await fetch(`${SUPABASE_CONFIG.url}/auth/v1/token?grant_type=refresh_token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'apikey': SUPABASE_CONFIG.anonKey,
        },
        body: JSON.stringify({ refresh_token: refreshToken })
      });

      const data = await res.json();
      if (!res.ok) {
        this._clearSession();
        this._notifyListeners('SIGNED_OUT', null);
        return null;
      }

      const now = Math.floor(Date.now() / 1000);
      const session = {
        access_token: data.access_token,
        refresh_token: data.refresh_token,
        expires_in: data.expires_in,
        expires_at: now + (data.expires_in || 3600),
        user: data.user,
      };

      this._saveSession(session);
      this._notifyListeners('TOKEN_REFRESHED', session);
      return session;
    } catch (err) {
      console.warn('Token refresh failed:', err);
      this._clearSession();
      this._notifyListeners('SIGNED_OUT', null);
      return null;
    }
  }

  /**
   * Get current session
   */
  getSession() {
    return this.session;
  }

  /**
   * Get current authenticated user
   */
  getUser() {
    return this.session?.user || null;
  }

  /**
   * Get current Bearer access token string
   */
  getAccessToken() {
    return this.session?.access_token || null;
  }

  /**
   * Register auth state change listener
   * @param {Function} callback - (event, session) => void
   */
  onAuthStateChange(callback) {
    if (typeof callback === 'function') {
      this.listeners.add(callback);
    }
    return {
      data: {
        subscription: {
          unsubscribe: () => {
            this.listeners.delete(callback);
          }
        }
      }
    };
  }

  /**
   * Manual session setter (e.g. for mock / testing)
   */
  setSession(session) {
    if (session && session.access_token) {
      this._saveSession(session);
      this._notifyListeners('SIGNED_IN', session);
    } else {
      this._clearSession();
      this._notifyListeners('SIGNED_OUT', null);
    }
  }

  _saveSession(session) {
    this.session = session;
    try {
      localStorage.setItem(SUPABASE_CONFIG.storageKey, JSON.stringify(session));
    } catch (err) {
      console.warn('Failed to persist session to localStorage:', err);
    }
  }

  _clearSession() {
    this.session = null;
    try {
      localStorage.removeItem(SUPABASE_CONFIG.storageKey);
    } catch (err) {
      console.warn('Failed to clear session from localStorage:', err);
    }
  }

  _notifyListeners(event, session) {
    this.listeners.forEach((callback) => {
      try {
        callback(event, session);
      } catch (err) {
        console.error('Auth listener error:', err);
      }
    });
  }
}

export const authClient = new AuthClient();
