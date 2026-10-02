import { authClient } from '../auth/authClient.js';
import { icons } from '../icons.js';

/**
 * Unauthorized (403 Access Denied) View Controller
 * Displayed when an authenticated user does not possess administrative privileges.
 */
export class UnauthorizedView {
  constructor(container, onSignOut) {
    this.container = container;
    this.onSignOut = onSignOut;
  }

  render() {
    const user = authClient.getUser();
    const userEmail = user?.email || 'Unknown User';

    this.container.innerHTML = `
      <div class="login-page-wrapper">
        <div class="login-card" style="text-align: center;">
          <div class="login-header">
            <div class="login-brand-icon" style="background: var(--color-rose-50); color: var(--color-rose-600);">
              ${icons.alertCircle || icons.emptyBox}
            </div>
            <h1 class="login-title" style="color: var(--color-rose-600);">Access Denied</h1>
            <p class="login-subtitle">Administrator Privileges Required</p>
          </div>

          <div style="margin: 20px 0; padding: 14px; background: var(--color-slate-50); border: 1px solid var(--color-slate-200); border-radius: 8px; font-size: 13px; color: var(--color-slate-600); line-height: 1.5;">
            Your account <strong style="color: var(--color-slate-900);">${userEmail}</strong> is authenticated, but does not have permission to access the administrative inventory operations.
          </div>

          <button type="button" class="login-submit-btn" id="unauthorizedLogoutBtn" style="background: var(--color-slate-800);">
            <span>Sign Out / Switch Account</span>
          </button>
        </div>
      </div>
    `;

    const logoutBtn = this.container.querySelector('#unauthorizedLogoutBtn');
    if (logoutBtn) {
      logoutBtn.addEventListener('click', async () => {
        await authClient.signOut();
        if (typeof this.onSignOut === 'function') {
          this.onSignOut();
        }
      });
    }
  }

  show() {
    if (this.container) this.container.style.display = 'block';
  }

  hide() {
    if (this.container) this.container.style.display = 'none';
  }
}
