import { icons } from '../icons.js';

/**
 * Render Header Component
 * @param {HTMLElement} container - DOM container element
 * @param {Object} userData - User info (name, notificationsCount)
 * @param {Function} onToggleSidebar - Sidebar toggle callback
 * @param {Function} onLogout - Logout callback
 * @returns {Object} Header controller with setTitle and setUser methods
 */
export function renderHeader(container, userData, onToggleSidebar, onLogout) {
  if (!container) return null;

  const { name = 'Admin', notificationsCount = 0 } = userData || {};

  container.innerHTML = `
    <div class="header-left">
      <button class="sidebar-toggle-btn" id="sidebarToggleBtn" aria-label="Toggle Sidebar" type="button">
        ${icons.menu}
      </button>
      <h1 class="page-title" id="headerPageTitle">Dashboard</h1>
    </div>

    <div class="header-right">
      <button class="notification-btn" aria-label="Notifications" type="button">
        ${icons.bell}
        ${notificationsCount > 0 ? `<span class="notification-badge">${notificationsCount}</span>` : ''}
      </button>

      <div class="admin-profile" id="adminProfileBtn" style="cursor: pointer;" title="Click to Sign Out">
        <div class="avatar-circle">
          ${icons.user}
        </div>
        <span class="admin-name" id="headerAdminName">${name}</span>
        <span class="chevron-down">${icons.chevronDown}</span>
      </div>
    </div>
  `;

  const titleEl = container.querySelector('#headerPageTitle');
  const nameEl = container.querySelector('#headerAdminName');
  const toggleBtn = container.querySelector('#sidebarToggleBtn');
  const profileBtn = container.querySelector('#adminProfileBtn');

  if (toggleBtn && typeof onToggleSidebar === 'function') {
    toggleBtn.addEventListener('click', onToggleSidebar);
  }

  if (profileBtn && typeof onLogout === 'function') {
    profileBtn.addEventListener('click', onLogout);
  }

  return {
    setTitle: (title) => {
      if (titleEl) titleEl.textContent = title;
    },
    setUser: (newName) => {
      if (nameEl) nameEl.textContent = newName || 'Admin';
    }
  };
}
