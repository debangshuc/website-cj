import { icons } from '../icons.js';

/**
 * Order Modal Component (Create Order & Order Details / Status Transition)
 */
export class OrderModal {
  constructor(container, onCreateOrder, onStatusChange) {
    this.container = container;
    this.onCreateOrder = onCreateOrder;
    this.onStatusChange = onStatusChange;
    this.currentOrder = null;
    this.products = [];
    this.customers = [];
    this.mode = 'create'; // 'create' or 'view'
    this.renderModal();
    this.bindEvents();
  }

  renderModal() {
    this.container.innerHTML = `
      <div class="modal-backdrop" id="orderModalBackdrop">
        <div class="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="orderModalTitle" style="max-width: 620px;">
          <div class="modal-header">
            <h2 class="modal-title" id="orderModalTitle">Create Customer Order</h2>
            <button class="modal-close-btn" id="closeOrderModalBtn" type="button" aria-label="Close modal">
              ${icons.close}
            </button>
          </div>

          <!-- Mode 1: Create Order Form -->
          <form id="createOrderForm">
            <div class="modal-body">
              <div id="orderModalError" style="display: none; margin-bottom: 16px; padding: 10px 14px; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 6px; color: #b91c1c; font-size: 13px;"></div>

              <div class="form-grid">
                <!-- Customer Selection -->
                <div class="form-group form-group-full">
                  <label class="form-label" for="formOrderCustomerSelect">Select Customer</label>
                  <select id="formOrderCustomerSelect" class="form-select">
                    <option value="">Guest / Walk-in Customer (Manual Entry)</option>
                  </select>
                </div>

                <!-- Customer Details -->
                <div class="form-group">
                  <label class="form-label" for="formOrderCustomerName">Customer Name</label>
                  <input type="text" id="formOrderCustomerName" class="form-input" placeholder="e.g. Aarav Sharma" maxlength="150" />
                </div>

                <div class="form-group">
                  <label class="form-label" for="formOrderCustomerEmail">Customer Email</label>
                  <input type="email" id="formOrderCustomerEmail" class="form-input" placeholder="e.g. aarav@example.com" maxlength="150" />
                </div>

                <!-- Product Selection -->
                <div class="form-group form-group-full">
                  <label class="form-label" for="formOrderProductSelect">Select Product <span class="required-star">*</span></label>
                  <select id="formOrderProductSelect" class="form-select" required>
                    <option value="" disabled selected>Choose active product...</option>
                  </select>
                </div>

                <!-- Price & Quantity -->
                <div class="form-group">
                  <label class="form-label" for="formOrderUnitPrice">Unit Price (₹)</label>
                  <input type="text" id="formOrderUnitPrice" class="form-input" value="₹0.00" readonly style="background: var(--color-slate-100, #f1f5f9);" />
                </div>

                <div class="form-group">
                  <label class="form-label" for="formOrderQuantity">Quantity <span class="required-star">*</span></label>
                  <input type="number" id="formOrderQuantity" class="form-input" min="1" max="999" value="1" required />
                  <span id="orderAvailableStockHint" class="form-hint" style="font-size: 12px; color: var(--color-slate-500); margin-top: 4px;">Available stock: —</span>
                </div>

                <!-- Line Total -->
                <div class="form-group form-group-full" style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; display: flex; justify-content: space-between; align-items: center;">
                  <span style="font-weight: 600; color: var(--color-slate-700);">Order Total Amount:</span>
                  <span id="formOrderCalculatedTotal" style="font-size: 18px; font-weight: 700; color: var(--color-primary, #2563eb);">₹0.00</span>
                </div>

                <!-- Order Notes -->
                <div class="form-group form-group-full">
                  <label class="form-label" for="formOrderNotes">Order Notes</label>
                  <textarea id="formOrderNotes" class="form-textarea" placeholder="Optional delivery instructions or notes..." maxlength="500"></textarea>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" id="cancelCreateOrderBtn">Cancel</button>
              <button type="submit" class="btn-primary" id="submitCreateOrderBtn">Create Order</button>
            </div>
          </form>

          <!-- Mode 2: View Order & Status Transition Container -->
          <div id="viewOrderContainer" style="display: none;">
            <div class="modal-body" id="viewOrderBody">
              <!-- Content rendered dynamically in openView -->
            </div>
            <div class="modal-footer" style="display: flex; justify-content: space-between; align-items: center;">
              <div id="orderStatusTransitionGroup" style="display: flex; gap: 8px; align-items: center;">
                <!-- Transition controls rendered dynamically -->
              </div>
              <button type="button" class="btn-secondary" id="closeViewOrderBtn">Close</button>
            </div>
          </div>
        </div>
      </div>
    `;

    this.backdropEl = this.container.querySelector('#orderModalBackdrop');
    this.titleEl = this.container.querySelector('#orderModalTitle');
    this.createFormEl = this.container.querySelector('#createOrderForm');
    this.viewContainerEl = this.container.querySelector('#viewOrderContainer');
    this.viewBodyEl = this.container.querySelector('#viewOrderBody');
    this.transitionGroupEl = this.container.querySelector('#orderStatusTransitionGroup');
    this.errorBanner = this.container.querySelector('#orderModalError');

    // Form inputs
    this.custSelect = this.container.querySelector('#formOrderCustomerSelect');
    this.custNameInput = this.container.querySelector('#formOrderCustomerName');
    this.custEmailInput = this.container.querySelector('#formOrderCustomerEmail');
    this.prodSelect = this.container.querySelector('#formOrderProductSelect');
    this.unitPriceInput = this.container.querySelector('#formOrderUnitPrice');
    this.qtyInput = this.container.querySelector('#formOrderQuantity');
    this.stockHint = this.container.querySelector('#orderAvailableStockHint');
    this.calcTotalEl = this.container.querySelector('#formOrderCalculatedTotal');
    this.notesInput = this.container.querySelector('#formOrderNotes');
  }

  bindEvents() {
    const closeBtn = this.container.querySelector('#closeOrderModalBtn');
    const cancelBtn = this.container.querySelector('#cancelCreateOrderBtn');
    const closeViewBtn = this.container.querySelector('#closeViewOrderBtn');

    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (cancelBtn) cancelBtn.addEventListener('click', () => this.close());
    if (closeViewBtn) closeViewBtn.addEventListener('click', () => this.close());

    if (this.backdropEl) {
      this.backdropEl.addEventListener('click', (e) => {
        if (e.target === this.backdropEl) this.close();
      });
    }

    if (this.custSelect) {
      this.custSelect.addEventListener('change', () => {
        const custId = this.custSelect.value;
        if (custId) {
          const selected = this.customers.find((c) => c.id === custId);
          if (selected) {
            this.custNameInput.value = selected.name || '';
            this.custEmailInput.value = selected.email || '';
          }
        }
      });
    }

    if (this.prodSelect) {
      this.prodSelect.addEventListener('change', () => this.recalculateCreateTotal());
    }

    if (this.qtyInput) {
      this.qtyInput.addEventListener('input', () => this.recalculateCreateTotal());
    }

    if (this.createFormEl) {
      this.createFormEl.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleCreateSubmit();
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

  recalculateCreateTotal() {
    const prodId = this.prodSelect.value;
    const selectedProd = this.products.find((p) => p.id === prodId);
    const qty = parseInt(this.qtyInput.value, 10) || 0;

    if (selectedProd) {
      const price = parseFloat(selectedProd.price) || 0;
      this.unitPriceInput.value = `₹${price.toFixed(2)}`;
      this.stockHint.textContent = `Available stock: ${selectedProd.stock} units`;
      const lineTotal = price * qty;
      this.calcTotalEl.textContent = `₹${lineTotal.toFixed(2)}`;
    } else {
      this.unitPriceInput.value = '₹0.00';
      this.stockHint.textContent = 'Available stock: —';
      this.calcTotalEl.textContent = '₹0.00';
    }
  }

  openCreate(products = [], customers = []) {
    this.mode = 'create';
    this.currentOrder = null;
    this.products = products.filter((p) => p.is_active !== false && p.stock > 0);
    this.customers = (customers || []).filter((c) => c.is_active !== false);
    this.titleEl.textContent = 'Create Customer Order';
    this.clearError();

    this.createFormEl.style.display = 'block';
    this.viewContainerEl.style.display = 'none';

    // Populate customers dropdown
    this.custSelect.innerHTML = [
      `<option value="">Guest / Walk-in Customer (Manual Entry)</option>`,
      ...this.customers.map((c) => `<option value="${c.id}">${c.name}${c.email ? ` (${c.email})` : ''}</option>`),
    ].join('');

    // Populate products dropdown
    if (this.products.length === 0) {
      this.prodSelect.innerHTML = `<option value="" disabled selected>No in-stock active products available</option>`;
    } else {
      this.prodSelect.innerHTML = [
        `<option value="" disabled selected>Choose active product...</option>`,
        ...this.products.map(
          (p) => `<option value="${p.id}">${p.name} (${p.sku}) — ₹${parseFloat(p.price).toFixed(2)} [Stock: ${p.stock}]</option>`
        ),
      ].join('');
    }

    this.createFormEl.reset();
    this.recalculateCreateTotal();
    this.backdropEl.classList.add('active');
  }

  openView(order) {
    if (!order) return;
    this.mode = 'view';
    this.currentOrder = order;
    this.titleEl.textContent = `Order Details — ${order.order_number}`;
    this.clearError();

    this.createFormEl.style.display = 'none';
    this.viewContainerEl.style.display = 'block';

    const statusBadge = this.getStatusBadge(order.status);
    const createdDate = order.created_at
      ? new Date(order.created_at).toLocaleString('en-IN', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: '2-digit',
          minute: '2-digit',
        })
      : '—';

    const itemsRows = (order.items || []).map((item) => `
      <tr style="border-bottom: 1px solid #e2e8f0;">
        <td style="padding: 10px 12px; font-weight: 600; color: #1e293b;">${item.product_name}</td>
        <td style="padding: 10px 12px; color: #64748b; font-size: 13px;">${item.sku}</td>
        <td style="padding: 10px 12px; color: #64748b; font-size: 13px;">${item.category}</td>
        <td style="padding: 10px 12px; text-align: right; color: #334155;">₹${parseFloat(item.unit_price).toFixed(2)}</td>
        <td style="padding: 10px 12px; text-align: center; font-weight: 600;">${item.quantity}</td>
        <td style="padding: 10px 12px; text-align: right; font-weight: 700; color: #0f172a;">₹${parseFloat(item.line_total).toFixed(2)}</td>
      </tr>
    `).join('');

    this.viewBodyEl.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; padding-bottom: 12px; border-bottom: 1px solid #e2e8f0;">
        <div>
          <div style="font-size: 13px; color: #64748b;">Customer</div>
          <div style="font-weight: 600; color: #0f172a;">${order.customer_name || 'Guest Customer'}</div>
          ${order.customer_email ? `<div style="font-size: 13px; color: #3b82f6;">${order.customer_email}</div>` : ''}
          ${order.customer_id ? `<div style="font-size: 11px; color: #059669; font-weight: 600; margin-top: 2px;">Linked CRM Customer</div>` : ''}
        </div>
        <div style="text-align: right;">
          <div style="font-size: 13px; color: #64748b;">Order Date: ${createdDate}</div>
          <div style="margin-top: 4px;">${statusBadge}</div>
        </div>
      </div>

      <div style="margin-bottom: 16px;">
        <h4 style="font-size: 14px; font-weight: 600; color: #334155; margin-bottom: 8px;">Order Line Items</h4>
        <div style="border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;">
          <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <thead>
              <tr style="background: #f8fafc; border-bottom: 1px solid #e2e8f0; color: #64748b; text-align: left;">
                <th style="padding: 8px 12px;">Product</th>
                <th style="padding: 8px 12px;">SKU</th>
                <th style="padding: 8px 12px;">Category</th>
                <th style="padding: 8px 12px; text-align: right;">Unit Price</th>
                <th style="padding: 8px 12px; text-align: center;">Qty</th>
                <th style="padding: 8px 12px; text-align: right;">Line Total</th>
              </tr>
            </thead>
            <tbody>
              ${itemsRows}
            </tbody>
            <tfoot>
              <tr style="background: #f8fafc; font-weight: 700;">
                <td colspan="5" style="padding: 10px 12px; text-align: right; color: #334155;">Total Amount:</td>
                <td style="padding: 10px 12px; text-align: right; color: #2563eb; font-size: 15px;">₹${parseFloat(order.total).toFixed(2)}</td>
              </tr>
            </tfoot>
          </table>
        </div>
      </div>

      ${order.notes ? `
        <div style="background: #f8fafc; border-radius: 6px; padding: 10px 14px; font-size: 13px; color: #475569;">
          <strong>Notes:</strong> ${order.notes}
        </div>
      ` : ''}
    `;

    // Render valid transition actions
    this.renderTransitions(order);
    this.backdropEl.classList.add('active');
  }

  renderTransitions(order) {
    const status = order.status.toLowerCase();
    this.transitionGroupEl.innerHTML = '';

    if (status === 'pending') {
      this.transitionGroupEl.innerHTML = `
        <button type="button" class="btn-primary" id="confirmOrderActionBtn" style="background: #0284c7;">
          Confirm Order
        </button>
        <button type="button" class="btn-secondary" id="cancelOrderActionBtn" style="color: #ef4444;">
          Cancel Order
        </button>
      `;

      const confirmBtn = this.transitionGroupEl.querySelector('#confirmOrderActionBtn');
      const cancelBtn = this.transitionGroupEl.querySelector('#cancelOrderActionBtn');

      if (confirmBtn) {
        confirmBtn.addEventListener('click', () => this.handleStatusTransition(order.id, 'confirmed'));
      }
      if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
          if (confirm('Are you sure you want to cancel this order? Reserved stock will be restored.')) {
            this.handleStatusTransition(order.id, 'cancelled');
          }
        });
      }
    } else if (status === 'confirmed') {
      this.transitionGroupEl.innerHTML = `
        <button type="button" class="btn-primary" id="completeOrderActionBtn" style="background: #10b981;">
          Complete Order
        </button>
        <button type="button" class="btn-secondary" id="cancelOrderActionBtn" style="color: #ef4444;">
          Cancel Order
        </button>
      `;

      const completeBtn = this.transitionGroupEl.querySelector('#completeOrderActionBtn');
      const cancelBtn = this.transitionGroupEl.querySelector('#cancelOrderActionBtn');

      if (completeBtn) {
        completeBtn.addEventListener('click', () => this.handleStatusTransition(order.id, 'completed'));
      }
      if (cancelBtn) {
        cancelBtn.addEventListener('click', () => {
          if (confirm('Are you sure you want to cancel this order? Reserved stock will be restored.')) {
            this.handleStatusTransition(order.id, 'cancelled');
          }
        });
      }
    } else {
      // Completed or Cancelled (Terminal)
      this.transitionGroupEl.innerHTML = `
        <span style="font-size: 13px; font-weight: 500; color: #64748b;">
          ${status === 'completed' ? 'Order fulfilled and recorded in sales ledger.' : 'Order cancelled and stock restored.'}
        </span>
      `;
    }
  }

  getStatusBadge(statusStr) {
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
  }

  async handleStatusTransition(orderId, targetStatus) {
    if (typeof this.onStatusChange === 'function') {
      try {
        const updated = await this.onStatusChange(orderId, targetStatus);
        if (updated) {
          this.openView(updated);
        }
      } catch (err) {
        alert(`Error updating order status: ${err.message}`);
      }
    }
  }

  close() {
    this.backdropEl.classList.remove('active');
  }

  async handleCreateSubmit() {
    const custId = this.custSelect.value || undefined;
    const prodId = this.prodSelect.value;
    const qty = parseInt(this.qtyInput.value, 10) || 0;
    const customer_name = this.custNameInput.value.trim();
    const customer_email = this.custEmailInput.value.trim();
    const notes = this.notesInput.value.trim();

    if (!prodId) {
      this.showError('Please select a product.');
      return;
    }

    if (qty <= 0) {
      this.showError('Quantity must be greater than 0.');
      return;
    }

    const payload = {
      customer_id: custId,
      customer_name: customer_name || undefined,
      customer_email: customer_email || undefined,
      notes: notes || undefined,
      items: [
        {
          product_id: prodId,
          quantity: qty,
        },
      ],
    };

    if (typeof this.onCreateOrder === 'function') {
      try {
        await this.onCreateOrder(payload);
        this.close();
      } catch (err) {
        this.showError(err.message || 'Failed to create order.');
      }
    }
  }
}
