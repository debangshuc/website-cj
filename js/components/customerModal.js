import { icons } from '../icons.js';

/**
 * Escape HTML-unsafe characters in customer/product controlled text before rendering.
 */
function escapeHtml(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Render the "Lifetime Items Ordered" section: per-product totals across the
 * customer's non-cancelled orders.
 */
function renderLifetimeItemsSection(items = []) {
  if (!items || items.length === 0) {
    return `
      <div style="margin-bottom: 20px;">
        <h4 style="font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px;">Lifetime Items Ordered</h4>
        <div style="border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; text-align: center; color: #64748b; font-size: 13px;">
          No lifetime items ordered yet.
        </div>
      </div>
    `;
  }

  return `
    <div style="margin-bottom: 20px;">
      <h4 style="font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px;">Lifetime Items Ordered</h4>
      <div style="border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
          <thead>
            <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0; color: #64748b; text-align: left;">
              <th style="padding: 8px 12px;">Product</th>
              <th style="padding: 8px 12px; text-align: right;">Total Quantity</th>
            </tr>
          </thead>
          <tbody>
            ${items.map((item) => `
              <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 8px 12px; font-weight: 600; color: #0f172a;">${escapeHtml(item.product_name)}</td>
                <td style="padding: 8px 12px; text-align: right; color: #334155;">${Number(item.total_quantity || 0)}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

/**
 * Compact per-order item summary, e.g. "2 × Anime Poster · 1 × Keychain".
 */
function renderOrderItemsSummary(items = []) {
  if (!items || items.length === 0) return '—';
  return items
    .map((item) => `${Number(item.quantity || 0)} × ${escapeHtml(item.product_name)}`)
    .join('<br/>');
}

/**
 * Customer Modal Component (Add / Edit / View Customer Details & Order History)
 */
export class CustomerModal {
  constructor(container, onSaveCustomer, onStatusToggle) {
    this.container = container;
    this.onSaveCustomer = onSaveCustomer;
    this.onStatusToggle = onStatusToggle;
    this.currentCustomer = null;
    this.mode = 'add'; // 'add', 'edit', 'view'
    this.renderModal();
    this.bindEvents();
  }

  renderModal() {
    this.container.innerHTML = `
      <div class="modal-backdrop" id="customerModalBackdrop">
        <div class="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="customerModalTitle" style="max-width: 640px;">
          <div class="modal-header">
            <h2 class="modal-title" id="customerModalTitle">Add Customer</h2>
            <button class="modal-close-btn" id="closeCustomerModalBtn" type="button" aria-label="Close modal">
              ${icons.close}
            </button>
          </div>

          <!-- Form Mode (Add / Edit) -->
          <form id="customerForm">
            <div class="modal-body">
              <div id="customerModalError" style="display: none; margin-bottom: 16px; padding: 10px 14px; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 6px; color: #b91c1c; font-size: 13px;"></div>

              <div class="form-grid">
                <div class="form-group form-group-full">
                  <label class="form-label" for="formCustomerName">Full Name <span class="required-star">*</span></label>
                  <input type="text" id="formCustomerName" class="form-input" placeholder="e.g. Aarav Sharma" required maxlength="150" />
                </div>

                <div class="form-group">
                  <label class="form-label" for="formCustomerEmail">Email Address</label>
                  <input type="email" id="formCustomerEmail" class="form-input" placeholder="e.g. aarav@example.com" maxlength="150" />
                </div>

                <div class="form-group">
                  <label class="form-label" for="formCustomerPhone">Phone Number</label>
                  <input type="tel" id="formCustomerPhone" class="form-input" placeholder="e.g. +91 98765 43210" maxlength="50" />
                </div>

                <div class="form-group form-group-full">
                  <label class="form-label" for="formCustomerAddress">Address</label>
                  <input type="text" id="formCustomerAddress" class="form-input" placeholder="e.g. 42 Connaught Place, New Delhi" maxlength="300" />
                </div>

                <div class="form-group form-group-full">
                  <label class="form-label" for="formCustomerNotes">Notes / Preferences</label>
                  <textarea id="formCustomerNotes" class="form-textarea" placeholder="Customer notes or delivery preferences..." maxlength="500"></textarea>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" id="cancelCustomerFormBtn">Cancel</button>
              <button type="submit" class="btn-primary" id="submitCustomerFormBtn">Save Customer</button>
            </div>
          </form>

          <!-- View Mode (Details & Order History) -->
          <div id="viewCustomerContainer" style="display: none;">
            <div class="modal-body" id="viewCustomerBody">
              <!-- Rendered dynamically -->
            </div>
            <div class="modal-footer" style="display: flex; justify-content: space-between; align-items: center;">
              <div id="viewCustomerActions" style="display: flex; gap: 8px;">
                <!-- Edit & Deactivate buttons -->
              </div>
              <button type="button" class="btn-secondary" id="closeViewCustomerBtn">Close</button>
            </div>
          </div>
        </div>
      </div>
    `;

    this.backdropEl = this.container.querySelector('#customerModalBackdrop');
    this.titleEl = this.container.querySelector('#customerModalTitle');
    this.formEl = this.container.querySelector('#customerForm');
    this.viewContainerEl = this.container.querySelector('#viewCustomerContainer');
    this.viewBodyEl = this.container.querySelector('#viewCustomerBody');
    this.viewActionsEl = this.container.querySelector('#viewCustomerActions');
    this.errorBanner = this.container.querySelector('#customerModalError');

    this.nameInput = this.container.querySelector('#formCustomerName');
    this.emailInput = this.container.querySelector('#formCustomerEmail');
    this.phoneInput = this.container.querySelector('#formCustomerPhone');
    this.addressInput = this.container.querySelector('#formCustomerAddress');
    this.notesInput = this.container.querySelector('#formCustomerNotes');
    this.submitBtn = this.container.querySelector('#submitCustomerFormBtn');
  }

  bindEvents() {
    const closeBtn = this.container.querySelector('#closeCustomerModalBtn');
    const cancelBtn = this.container.querySelector('#cancelCustomerFormBtn');
    const closeViewBtn = this.container.querySelector('#closeViewCustomerBtn');

    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (cancelBtn) cancelBtn.addEventListener('click', () => this.close());
    if (closeViewBtn) closeViewBtn.addEventListener('click', () => this.close());

    if (this.backdropEl) {
      this.backdropEl.addEventListener('click', (e) => {
        if (e.target === this.backdropEl) this.close();
      });
    }

    if (this.formEl) {
      this.formEl.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleSubmit();
      });
    }
  }

  showError(msg) {
    if (this.errorBanner) {
      this.errorBanner.textContent = msg;
      this.errorBanner.style.display = 'block';
    }
  }

  clearError() {
    if (this.errorBanner) {
      this.errorBanner.textContent = '';
      this.errorBanner.style.display = 'none';
    }
  }

  openAdd() {
    this.mode = 'add';
    this.currentCustomer = null;
    this.titleEl.textContent = 'Add Customer';
    this.submitBtn.textContent = 'Create Customer';
    this.clearError();

    this.formEl.style.display = 'block';
    this.viewContainerEl.style.display = 'none';
    this.formEl.reset();

    this.backdropEl.classList.add('active');
  }

  openEdit(customer) {
    if (!customer) return;
    this.mode = 'edit';
    this.currentCustomer = customer;
    this.titleEl.textContent = `Edit Customer — ${customer.name}`;
    this.submitBtn.textContent = 'Save Changes';
    this.clearError();

    this.formEl.style.display = 'block';
    this.viewContainerEl.style.display = 'none';

    this.nameInput.value = customer.name || '';
    this.emailInput.value = customer.email || '';
    this.phoneInput.value = customer.phone || '';
    this.addressInput.value = customer.address || '';
    this.notesInput.value = customer.notes || '';

    this.backdropEl.classList.add('active');
  }

  openView(customer) {
    if (!customer) return;
    this.mode = 'view';
    this.currentCustomer = customer;
    this.titleEl.textContent = `Customer Profile — ${customer.name}`;
    this.clearError();

    this.formEl.style.display = 'none';
    this.viewContainerEl.style.display = 'block';

    const statusBadge = customer.is_active
      ? `<span class="badge" style="background: #ecfdf5; color: #059669; font-weight: 600;">Active</span>`
      : `<span class="badge" style="background: #fef2f2; color: #dc2626; font-weight: 600;">Inactive</span>`;

    const recentOrders = customer.recent_orders || [];
    const ordersTableHtml = recentOrders.length === 0
      ? `<div style="padding: 16px; text-align: center; color: #64748b; font-size: 13px;">No order history found for this customer.</div>`
      : `
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
          <thead>
            <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0; color: #64748b; text-align: left;">
              <th style="padding: 8px 12px;">Order #</th>
              <th style="padding: 8px 12px;">Items</th>
              <th style="padding: 8px 12px;">Status</th>
              <th style="padding: 8px 12px; text-align: right;">Total Amount</th>
              <th style="padding: 8px 12px; text-align: right;">Date</th>
            </tr>
          </thead>
          <tbody>
            ${recentOrders.map((o) => `
              <tr style="border-bottom: 1px solid #e2e8f0;">
                <td style="padding: 8px 12px; font-weight: 600; color: #2563eb;">${escapeHtml(o.order_number)}</td>
                <td style="padding: 8px 12px; color: #475569; font-size: 12px; max-width: 180px;">${renderOrderItemsSummary(o.items)}</td>
                <td style="padding: 8px 12px;"><span style="text-transform: capitalize; font-size: 12px; font-weight: 600;">${escapeHtml(o.status)}</span></td>
                <td style="padding: 8px 12px; text-align: right; font-weight: 700; color: #0f172a;">₹${parseFloat(o.total).toFixed(2)}</td>
                <td style="padding: 8px 12px; text-align: right; color: #64748b;">${new Date(o.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;

    this.viewBodyEl.innerHTML = `
      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 20px; padding-bottom: 16px; border-bottom: 1px solid #e2e8f0;">
        <div>
          <div style="font-size: 12px; color: #64748b; font-weight: 500;">Email</div>
          <div style="font-weight: 600; color: #0f172a; margin-top: 2px;">${customer.email ? escapeHtml(customer.email) : '—'}</div>
        </div>
        <div>
          <div style="font-size: 12px; color: #64748b; font-weight: 500;">Phone</div>
          <div style="font-weight: 600; color: #0f172a; margin-top: 2px;">${customer.phone ? escapeHtml(customer.phone) : '—'}</div>
        </div>
        <div style="grid-column: 1 / -1;">
          <div style="font-size: 12px; color: #64748b; font-weight: 500;">Address</div>
          <div style="color: #334155; margin-top: 2px; font-size: 13px;">${customer.address ? escapeHtml(customer.address) : '—'}</div>
        </div>
        ${customer.notes ? `
          <div style="grid-column: 1 / -1; background: #f8fafc; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #475569;">
            <strong>Notes:</strong> ${escapeHtml(customer.notes)}
          </div>
        ` : ''}
      </div>

      <!-- Lifetime Summary Cards -->
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin-bottom: 20px;">
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px; text-align: center;">
          <div style="font-size: 12px; color: #64748b;">Total Orders</div>
          <div style="font-size: 18px; font-weight: 700; color: #0f172a; margin-top: 2px;">${customer.order_count || 0}</div>
        </div>
        <div style="background: #ecfdf5; border: 1px solid #a7f3d0; border-radius: 8px; padding: 12px; text-align: center;">
          <div style="font-size: 12px; color: #047857;">Completed</div>
          <div style="font-size: 18px; font-weight: 700; color: #059669; margin-top: 2px;">${customer.completed_order_count || 0}</div>
        </div>
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 12px; text-align: center;">
          <div style="font-size: 12px; color: #1d4ed8;">Total Spent</div>
          <div style="font-size: 18px; font-weight: 700; color: #2563eb; margin-top: 2px;">₹${parseFloat(customer.total_spent || 0).toFixed(2)}</div>
        </div>
      </div>

      ${renderLifetimeItemsSection(customer.lifetime_items)}

      <div>
        <h4 style="font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px;">Recent Customer Orders</h4>
        <div style="border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">
          ${ordersTableHtml}
        </div>
      </div>
    `;

    this.viewActionsEl.innerHTML = `
      <button type="button" class="btn-primary" id="editCustomerFromViewBtn" style="padding: 8px 14px; font-size: 13px;">
        Edit Profile
      </button>
      <button type="button" class="btn-secondary" id="toggleCustomerActiveBtn" style="padding: 8px 14px; font-size: 13px; color: ${customer.is_active ? '#ef4444' : '#059669'};">
        ${customer.is_active ? 'Deactivate' : 'Reactivate'}
      </button>
    `;

    const editBtn = this.viewActionsEl.querySelector('#editCustomerFromViewBtn');
    const toggleBtn = this.viewActionsEl.querySelector('#toggleCustomerActiveBtn');

    if (editBtn) {
      editBtn.addEventListener('click', () => {
        this.openEdit(customer);
      });
    }

    if (toggleBtn) {
      toggleBtn.addEventListener('click', async () => {
        const actionText = customer.is_active ? 'deactivate' : 'reactivate';
        if (confirm(`Are you sure you want to ${actionText} customer "${customer.name}"?`)) {
          if (typeof this.onStatusToggle === 'function') {
            await this.onStatusToggle(customer.id, !customer.is_active);
            this.close();
          }
        }
      });
    }

    this.backdropEl.classList.add('active');
  }

  close() {
    this.backdropEl.classList.remove('active');
  }

  async handleSubmit() {
    const name = this.nameInput.value.trim();
    const email = this.emailInput.value.trim();
    const phone = this.phoneInput.value.trim();
    const address = this.addressInput.value.trim();
    const notes = this.notesInput.value.trim();

    if (!name) {
      this.showError('Customer name is required.');
      return;
    }

    const payload = {
      name,
      email: email || undefined,
      phone: phone || undefined,
      address: address || undefined,
      notes: notes || undefined,
    };

    if (typeof this.onSaveCustomer === 'function') {
      try {
        await this.onSaveCustomer(this.mode, this.currentCustomer ? this.currentCustomer.id : null, payload);
        this.close();
      } catch (err) {
        this.showError(err.message || 'Failed to save customer.');
      }
    }
  }
}
