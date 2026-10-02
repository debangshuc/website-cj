import { icons } from '../icons.js';

/**
 * Render Customers Data Table
 * @param {HTMLElement} container - DOM mount container
 * @param {Array} customers - List of CustomerResponse objects
 * @param {Object} callbacks - { onViewCustomer, onEditCustomer, onAddCustomer }
 */
export function renderCustomerTable(container, customers = [], callbacks = {}) {
  if (!container) return;

  const { onViewCustomer, onEditCustomer, onAddCustomer } = callbacks || {};

  if (!customers || customers.length === 0) {
    container.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <div class="empty-state-icon">
          ${icons.emptyBox}
        </div>
        <h2 class="empty-state-title">No customers yet</h2>
        <p class="empty-state-desc">Customers associated with orders and direct registrations will appear here.</p>
        <button class="btn-primary" id="emptyAddCustomerBtn" type="button" style="margin-top: 8px;">
          ${icons.plus}
          <span>Add Customer</span>
        </button>
      </div>
    `;

    const emptyBtn = container.querySelector('#emptyAddCustomerBtn');
    if (emptyBtn && typeof onAddCustomer === 'function') {
      emptyBtn.addEventListener('click', onAddCustomer);
    }
    return;
  }

  const rowsHtml = customers.map((cust) => {
    const statusBadge = cust.is_active
      ? `<span class="badge" style="background: #ecfdf5; color: #059669; font-weight: 600;">Active</span>`
      : `<span class="badge" style="background: #fef2f2; color: #dc2626; font-weight: 600;">Inactive</span>`;

    const lastOrderDisplay = cust.last_order_at
      ? new Date(cust.last_order_at).toLocaleDateString('en-IN', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })
      : 'Never';

    return `
      <tr class="table-row">
        <td class="table-cell" style="font-weight: 700; color: #0f172a;">
          <a href="javascript:void(0)" class="view-customer-link" data-customer-id="${cust.id}" style="color: var(--color-primary, #2563eb); text-decoration: none;">
            ${cust.name}
          </a>
        </td>
        <td class="table-cell" style="color: #475569; font-size: 13px;">
          ${cust.email || '—'}
        </td>
        <td class="table-cell" style="color: #475569; font-size: 13px;">
          ${cust.phone || '—'}
        </td>
        <td class="table-cell" style="font-weight: 600; color: #334155;">
          ${cust.order_count || 0} orders
        </td>
        <td class="table-cell" style="font-weight: 700; color: #0f172a;">
          ₹${parseFloat(cust.total_spent || 0).toFixed(2)}
        </td>
        <td class="table-cell" style="color: #64748b; font-size: 13px;">
          ${lastOrderDisplay}
        </td>
        <td class="table-cell">
          ${statusBadge}
        </td>
        <td class="table-cell table-actions">
          <button type="button" class="btn-action view-customer-btn" data-customer-id="${cust.id}" title="View Customer Profile" aria-label="View Customer Profile">
            ${icons.search}
          </button>
          <button type="button" class="btn-action edit-customer-btn" data-customer-id="${cust.id}" title="Edit Customer Profile" aria-label="Edit Customer Profile">
            ${icons.edit}
          </button>
        </td>
      </tr>
    `;
  }).join('');

  container.innerHTML = `
    <div class="table-responsive">
      <table class="data-table" aria-label="Customers Table">
        <thead>
          <tr>
            <th class="table-th">Customer</th>
            <th class="table-th">Email</th>
            <th class="table-th">Phone</th>
            <th class="table-th">Orders</th>
            <th class="table-th">Total Spent</th>
            <th class="table-th">Last Order</th>
            <th class="table-th">Status</th>
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
  container.querySelectorAll('.view-customer-link, .view-customer-btn').forEach((el) => {
    el.addEventListener('click', () => {
      const custId = el.getAttribute('data-customer-id');
      if (typeof onViewCustomer === 'function') {
        onViewCustomer(custId);
      }
    });
  });

  container.querySelectorAll('.edit-customer-btn').forEach((btn) => {
    btn.addEventListener('click', () => {
      const custId = btn.getAttribute('data-customer-id');
      const cust = customers.find((c) => c.id === custId);
      if (cust && typeof onEditCustomer === 'function') {
        onEditCustomer(cust);
      }
    });
  });
}
