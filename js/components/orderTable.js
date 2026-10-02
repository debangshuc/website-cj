import { icons } from '../icons.js';

/**
 * Render Orders Data Table
 * @param {HTMLElement} container - DOM mount container
 * @param {Array} orders - List of OrderResponse objects
 * @param {Object} callbacks - { onViewOrder }
 */
export function renderOrderTable(container, orders = [], callbacks = {}) {
  if (!container) return;

  const { onViewOrder } = callbacks || {};

  if (!orders || orders.length === 0) {
    container.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <div class="empty-state-icon">
          ${icons.emptyBox}
        </div>
        <h2 class="empty-state-title">No orders found</h2>
        <p class="empty-state-desc">Orders created through the customer order workflow will appear here.</p>
        <button class="btn-primary" id="emptyCreateOrderBtn" type="button" style="margin-top: 8px;">
          ${icons.plus}
          <span>Create Order</span>
        </button>
      </div>
    `;

    const emptyBtn = container.querySelector('#emptyCreateOrderBtn');
    if (emptyBtn && typeof callbacks.onCreateOrder === 'function') {
      emptyBtn.addEventListener('click', callbacks.onCreateOrder);
    }
    return;
  }

  const getStatusBadge = (statusStr) => {
    const s = (statusStr || 'pending').toLowerCase();
    switch (s) {
      case 'completed':
        return `<span class="badge" style="background: #ecfdf5; color: #059669; font-weight: 600;">Completed</span>`;
      case 'confirmed':
        return `<span class="badge" style="background: #e0f2fe; color: #0284c7; font-weight: 600;">Confirmed</span>`;
      case 'cancelled':
        return `<span class="badge" style="background: #fef2f2; color: #dc2626; font-weight: 600;">Cancelled</span>`;
      case 'pending':
      default:
        return `<span class="badge" style="background: #fef3c7; color: #d97706; font-weight: 600;">Pending</span>`;
    }
  };

  const rowsHtml = orders.map((order) => {
    const itemsCount = (order.items || []).reduce((acc, item) => acc + (item.quantity || 0), 0);
    const primaryItem = order.items && order.items[0] ? order.items[0].product_name : 'No items';
    const itemsSummary = order.items && order.items.length > 1
      ? `${primaryItem} + ${order.items.length - 1} more`
      : primaryItem;

    const createdDate = order.created_at
      ? new Date(order.created_at).toLocaleDateString('en-IN', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })
      : '—';

    const customerDisplay = order.customer_name || 'Guest Customer';

    return `
      <tr class="table-row">
        <td class="table-cell" style="font-weight: 700; color: var(--color-primary, #2563eb);">
          ${order.order_number}
        </td>
        <td class="table-cell">
          <div style="font-weight: 600; color: #1e293b;">${customerDisplay}</div>
          ${order.customer_email ? `<div style="font-size: 12px; color: #64748b;">${order.customer_email}</div>` : ''}
        </td>
        <td class="table-cell">
          <div style="font-size: 13px; color: #334155; font-weight: 500;">${itemsSummary}</div>
          <div style="font-size: 12px; color: #64748b;">${itemsCount} physical units</div>
        </td>
        <td class="table-cell" style="font-weight: 700; color: #0f172a;">
          ₹${parseFloat(order.total).toFixed(2)}
        </td>
        <td class="table-cell">
          ${getStatusBadge(order.status)}
        </td>
        <td class="table-cell" style="color: var(--color-slate-500); font-size: 13px;">
          ${createdDate}
        </td>
        <td class="table-cell table-actions">
          <button type="button" class="btn-action view-order-btn" data-order-id="${order.id}" title="View Order Details" aria-label="View Order Details">
            ${icons.edit}
          </button>
        </td>
      </tr>
    `;
  }).join('');

  container.innerHTML = `
    <div class="table-responsive">
      <table class="data-table" aria-label="Customer Orders Table">
        <thead>
          <tr>
            <th class="table-th">Order #</th>
            <th class="table-th">Customer</th>
            <th class="table-th">Items</th>
            <th class="table-th">Total</th>
            <th class="table-th">Status</th>
            <th class="table-th">Date</th>
            <th class="table-th table-th-actions">Actions</th>
          </tr>
        </thead>
        <tbody>
          ${rowsHtml}
        </tbody>
      </table>
    </div>
  `;

  // Attach event handlers
  container.querySelectorAll('.view-order-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const orderId = btn.getAttribute('data-order-id');
      const order = orders.find((o) => o.id === orderId);
      if (order && typeof onViewOrder === 'function') {
        onViewOrder(order);
      }
    });
  });
}
