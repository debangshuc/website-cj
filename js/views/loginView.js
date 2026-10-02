import { authClient } from '../auth/authClient.js';
import { icons } from '../icons.js';

/**
 * Login View Controller
 * Administrative authentication screen integrated with Supabase Auth.
 */
export class LoginView {
  constructor(container, onLoginSuccess) {
    this.container = container;
    this.onLoginSuccess = onLoginSuccess;
    this.isLoading = false;
  }

  render() {
    this.container.innerHTML = `
      <div class="login-page-wrapper">
        <div class="login-card">
          <div class="login-header">
            <div class="login-brand-icon">
              ${icons.store}
            </div>
            <h1 class="login-title">Accessory Inventory</h1>
            <p class="login-subtitle">Admin Operations & Inventory Management</p>
          </div>

          <div class="login-error-banner" id="loginErrorBanner" role="alert">
            <span style="display:inline-flex; align-items:center;">${icons.alertCircle || icons.emptyBox}</span>
            <span id="loginErrorText" style="flex: 1;"></span>
          </div>

          <form class="login-form" id="loginForm">
            <div class="login-field">
              <label class="login-label" for="loginEmail">Admin Email</label>
              <div class="login-input-wrapper">
                <div class="login-input-icon">${icons.mail || icons.user}</div>
                <input 
                  type="email" 
                  id="loginEmail" 
                  class="login-input" 
                  placeholder="admin@accessoryinventory.com" 
                  required 
                  autocomplete="username" 
                />
              </div>
            </div>

            <div class="login-field">
              <label class="login-label" for="loginPassword">Password</label>
              <div class="login-input-wrapper">
                <div class="login-input-icon">${icons.lock || icons.settings}</div>
                <input 
                  type="password" 
                  id="loginPassword" 
                  class="login-input" 
                  placeholder="••••••••" 
                  required 
                  autocomplete="current-password" 
                />
              </div>
            </div>

            <button type="submit" class="login-submit-btn" id="loginSubmitBtn">
              <span>Sign In to Admin</span>
            </button>
          </form>
        </div>
      </div>
    `;

    this.formEl = this.container.querySelector('#loginForm');
    this.emailInputEl = this.container.querySelector('#loginEmail');
    this.passwordInputEl = this.container.querySelector('#loginPassword');
    this.submitBtnEl = this.container.querySelector('#loginSubmitBtn');
    this.errorBannerEl = this.container.querySelector('#loginErrorBanner');
    this.errorTextEl = this.container.querySelector('#loginErrorText');

    this.formEl.addEventListener('submit', async (e) => {
      e.preventDefault();
      await this.handleLogin();
    });
  }

  async handleLogin() {
    const email = this.emailInputEl.value.trim();
    const password = this.passwordInputEl.value;

    this.hideError();
    this.setLoading(true);

    const { data, error } = await authClient.signInWithPassword({ email, password });
    this.setLoading(false);

    if (error) {
      this.showError(error.message || 'Invalid email or password.');
      return;
    }

    if (typeof this.onLoginSuccess === 'function') {
      this.onLoginSuccess(data.session);
    }
  }

  setLoading(loading) {
    this.isLoading = loading;
    if (this.submitBtnEl) {
      this.submitBtnEl.disabled = loading;
      this.submitBtnEl.innerHTML = loading ? '<span>Signing In...</span>' : '<span>Sign In to Admin</span>';
    }
  }

  showError(msg) {
    if (this.errorTextEl && this.errorBannerEl) {
      this.errorTextEl.textContent = msg;
      this.errorBannerEl.classList.add('visible');
    }
  }

  hideError() {
    if (this.errorBannerEl && this.errorTextEl) {
      this.errorBannerEl.classList.remove('visible');
      this.errorTextEl.textContent = '';
    }
  }

  show() {
    this.container.style.display = 'block';
  }

  hide() {
    this.container.style.display = 'none';
  }
}
