import { icons } from '../icons.js';

/**
 * Render Dashboard Recent Sales Table Component
 * @param {HTMLElement} container - DOM container element
 * @param {Array} sales - Array of recent sale records
 * @param {Function} onViewAll - Callback for "View all sales"
 */
export function renderRecentSalesTable(container, sales = [], onViewAll) {
  if (!container) return;

  const rowsHtml = sales.length > 0 
    ? sales.map(sale => `
        <tr>
          <td class="order-id">${sale.id}</td>
          <td class="product-name">${sale.product}</td>
          <td>
            <span class="badge ${sale.categoryClass || 'badge-keychain'}">${sale.category}</span>
          </td>
          <td>${sale.qty}</td>
          <td class="sales-amount">${sale.amount}</td>
          <td class="sales-date">${sale.date}</td>
        </tr>
      `).join('')
    : `
        <tr>
          <td colspan="6" style="text-align: center; color: var(--color-slate-400); padding: 36px 16px; font-size: 14px;">
            No recent transactions recorded
          </td>
        </tr>
      `;

  container.innerHTML = `
    <div class="card sales-card">
      <div class="card-header">
        <h2 class="card-title">Recent Sales</h2>
      </div>

      <div class="card-body">
        <div class="table-responsive">
          <table class="sales-table">
            <thead>
              <tr>
                <th>Order ID</th>
                <th>Product</th>
                <th>Category</th>
                <th>Qty</th>
                <th>Amount</th>
                <th>Date</th>
              </tr>
            </thead>
            <tbody>
              ${rowsHtml}
            </tbody>
          </table>
        </div>

        <a href="#sales" class="card-footer-link" id="viewAllSalesBtn">
          <span>View all sales</span>
          ${icons.chevronRight}
        </a>
      </div>
    </div>
  `;

  const viewAllBtn = container.querySelector('#viewAllSalesBtn');
  if (viewAllBtn && typeof onViewAll === 'function') {
    viewAllBtn.addEventListener('click', (e) => {
      e.preventDefault();
      onViewAll();
    });
  }
}
