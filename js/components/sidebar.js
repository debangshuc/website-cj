import { icons } from '../icons.js';

/**
 * Render Sidebar Component
 * @param {HTMLElement} container - DOM container element
 * @param {Array} navItems - Array of navigation item objects
 * @param {Function} onNavigate - Navigation callback handler
 * @param {Function} onLogout - Logout callback handler
 * @returns {Object} Sidebar controller with setActive method
 */
export function renderSidebar(container, navItems, onNavigate, onLogout) {
  if (!container) return null;

  const navHtml = navItems.map(item => {
    const iconSvg = icons[item.icon] || icons.dashboard;
    const activeClass = item.active ? 'active' : '';
    return `
      <a href="#${item.id}" class="nav-item ${activeClass}" data-nav-id="${item.id}">
        ${iconSvg}
        <span>${item.label}</span>
      </a>
    `;
  }).join('');

  container.innerHTML = `
    <div class="sidebar-header">
      <div class="brand-icon">
        ${icons.store}
      </div>
      <div class="brand-title">
        <span class="brand-title-top">Accessory</span>
        <span class="brand-title-bottom">Inventory</span>
      </div>
    </div>

    <nav class="sidebar-nav">
      ${navHtml}
    </nav>

    <div class="sidebar-footer">
      <button class="logout-btn" id="logoutBtn" type="button">
        ${icons.logout}
        <span>Logout</span>
      </button>
    </div>
  `;

  const navLinks = container.querySelectorAll('.nav-item');
  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const navId = link.getAttribute('data-nav-id');
      if (typeof onNavigate === 'function') {
        onNavigate(navId);
      }
    });
  });

  const logoutBtn = container.querySelector('#logoutBtn');
  if (logoutBtn && typeof onLogout === 'function') {
    logoutBtn.addEventListener('click', onLogout);
  }

  return {
    setActive: (activeId) => {
      navLinks.forEach(link => {
        const id = link.getAttribute('data-nav-id');
        link.classList.toggle('active', id === activeId);
      });
    }
  };
}
