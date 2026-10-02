import { getCategoryBadgeClass } from '../data.js';

/**
 * Render Sales Transactions Table
 * @param {HTMLElement} container - DOM mount container
 * @param {Array} sales - Array of transaction objects
 */
export function renderSalesTable(container, sales = []) {
  if (!container) return;

  const rowsHtml = sales.map(sale => {
    const badgeClass = getCategoryBadgeClass(sale.category);
    const totalAmount = sale.total !== undefined ? sale.total : (sale.quantity * sale.unitPrice);

    return `
      <tr>
        <td class="sale-id-col">${sale.id}</td>
        <td class="sale-product-col">${sale.productName}</td>
        <td>
          <span class="badge ${badgeClass}">${sale.category}</span>
        </td>
        <td class="sale-qty-col">${sale.quantity}</td>
        <td class="sale-price-col">₹${Number(sale.unitPrice).toLocaleString('en-IN')}</td>
        <td class="sale-total-col">₹${Number(totalAmount).toLocaleString('en-IN')}</td>
        <td class="sale-date-col">${sale.date}</td>
        <td class="sale-time-col">${sale.time}</td>
      </tr>
    `;
  }).join('');

  container.innerHTML = `
    <div class="sales-table-wrapper">
      <table class="transactions-table">
        <thead>
          <tr>
            <th>Sale ID</th>
            <th>Product</th>
            <th>Category</th>
            <th>Quantity</th>
            <th>Unit Price</th>
            <th>Total</th>
            <th>Date</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          ${rowsHtml}
        </tbody>
      </table>
    </div>
  `;
}
