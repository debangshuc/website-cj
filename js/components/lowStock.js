/**
 * Render Low Stock Products Component
 * @param {HTMLElement} container - DOM container element
 * @param {Array} products - Array of low stock product items
 * @param {Function} onViewAll - Callback for "View all" link
 */
export function renderLowStock(container, products = [], onViewAll) {
  if (!container) return;

  const itemsHtml = products.length > 0 
    ? products.map(item => `
        <div class="low-stock-item">
          <div class="low-stock-item-left">
            <div class="low-stock-thumbnail">
              <img src="${item.imageUrl || 'assets/images/placeholder-poster-main.svg'}" alt="${item.imageAlt || item.name}" loading="lazy" />
            </div>
            <div class="low-stock-info">
              <div class="low-stock-name">${item.name}</div>
              <div class="low-stock-category">${item.category}</div>
            </div>
          </div>
          <div class="low-stock-badge">
            ${item.remaining} left
          </div>
        </div>
      `).join('')
    : `
        <div style="text-align: center; color: var(--color-slate-400); padding: 36px 16px; font-size: 14px;">
          No low stock products
        </div>
      `;

  container.innerHTML = `
    <div class="card low-stock-card">
      <div class="card-header">
        <h2 class="card-title">Low Stock Products</h2>
        <a href="#products" class="view-all-header-link" id="viewAllLowStockBtn">View all</a>
      </div>

      <div class="card-body">
        <div class="low-stock-list">
          ${itemsHtml}
        </div>
      </div>
    </div>
  `;

  const viewAllBtn = container.querySelector('#viewAllLowStockBtn');
  if (viewAllBtn && typeof onViewAll === 'function') {
    viewAllBtn.addEventListener('click', (e) => {
      e.preventDefault();
      onViewAll();
    });
  }
}
