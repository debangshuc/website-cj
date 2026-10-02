import { icons } from '../icons.js';
import { productsApi } from '../api/productsApi.js';

/**
 * Record Sale Modal Component
 * Loads live product inventory from backend and handles sale submissions.
 */
export class RecordSaleModal {
  constructor(container, onRecordSale) {
    this.container = container;
    this.onRecordSale = onRecordSale;
    this.availableProducts = [];
    this.renderModal();
    this.bindEvents();
  }

  renderModal() {
    this.container.innerHTML = `
      <div class="modal-backdrop" id="saleModalBackdrop">
        <div class="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="saleModalTitle">
          <div class="modal-header">
            <h2 class="modal-title" id="saleModalTitle">Record New Sale</h2>
            <button class="modal-close-btn" id="closeSaleModalBtn" type="button" aria-label="Close modal">
              ${icons.close}
            </button>
          </div>

          <form id="recordSaleForm">
            <div class="modal-body">
              <!-- Validation Alert Banner -->
              <div class="alert-danger" id="saleValidationAlert" role="alert"></div>

              <div class="form-grid">
                <!-- Product Selector -->
                <div class="form-group form-group-full">
                  <label class="form-label" for="saleProductSelect">
                    Product <span class="required-star">*</span>
                  </label>
                  <select id="saleProductSelect" class="form-select" required>
                    <option value="">Loading products...</option>
                  </select>
                  <div class="stock-helper-badge" id="selectedProductStockHelper"></div>
                </div>

                <!-- Quantity -->
                <div class="form-group">
                  <label class="form-label" for="saleQuantityInput">
                    Quantity <span class="required-star">*</span>
                  </label>
                  <input type="number" id="saleQuantityInput" class="form-input" min="1" step="1" value="1" required />
                </div>

                <!-- Unit Price (Editable) -->
                <div class="form-group">
                  <label class="form-label" for="saleUnitPriceInput">
                    Unit Price (₹) <span class="required-star">*</span>
                  </label>
                  <input type="number" id="saleUnitPriceInput" class="form-input" min="0" step="1" placeholder="0" required />
                </div>

                <!-- Date -->
                <div class="form-group">
                  <label class="form-label" for="saleDateInput">Date <span class="required-star">*</span></label>
                  <input type="date" id="saleDateInput" class="form-input" required />
                </div>

                <!-- Time -->
                <div class="form-group">
                  <label class="form-label" for="saleTimeInput">Time <span class="required-star">*</span></label>
                  <input type="time" id="saleTimeInput" class="form-input" required />
                </div>

                <!-- Live Calculated Summary -->
                <div class="form-group form-group-full">
                  <div class="sale-calc-summary">
                    <div class="calc-row">
                      <span class="calc-label">Product</span>
                      <span class="calc-val" id="summaryProductName">—</span>
                    </div>
                    <div class="calc-row">
                      <span class="calc-label">Quantity</span>
                      <span class="calc-val" id="summaryQuantity">0</span>
                    </div>
                    <div class="calc-row">
                      <span class="calc-label">Unit Price</span>
                      <span class="calc-val" id="summaryUnitPrice">₹0</span>
                    </div>
                    <div class="calc-row calc-row-total">
                      <span class="calc-label font-semibold">Total Revenue</span>
                      <span class="calc-val" id="summaryTotalAmount">₹0</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" id="cancelSaleBtn">Cancel</button>
              <button type="submit" class="btn-primary" id="submitSaleBtn">Record Sale</button>
            </div>
          </form>
        </div>
      </div>
    `;

    this.backdropEl = this.container.querySelector('#saleModalBackdrop');
    this.formEl = this.container.querySelector('#recordSaleForm');
    this.alertEl = this.container.querySelector('#saleValidationAlert');
    this.productSelect = this.container.querySelector('#saleProductSelect');
    this.stockHelper = this.container.querySelector('#selectedProductStockHelper');
    this.qtyInput = this.container.querySelector('#saleQuantityInput');
    this.priceInput = this.container.querySelector('#saleUnitPriceInput');
    this.dateInput = this.container.querySelector('#saleDateInput');
    this.timeInput = this.container.querySelector('#saleTimeInput');
    this.submitBtn = this.container.querySelector('#submitSaleBtn');

    this.summaryName = this.container.querySelector('#summaryProductName');
    this.summaryQty = this.container.querySelector('#summaryQuantity');
    this.summaryPrice = this.container.querySelector('#summaryUnitPrice');
    this.summaryTotal = this.container.querySelector('#summaryTotalAmount');
  }

  bindEvents() {
    const closeBtn = this.container.querySelector('#closeSaleModalBtn');
    const cancelBtn = this.container.querySelector('#cancelSaleBtn');

    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (cancelBtn) cancelBtn.addEventListener('click', () => this.close());

    if (this.backdropEl) {
      this.backdropEl.addEventListener('click', (e) => {
        if (e.target === this.backdropEl) this.close();
      });
    }

    // On Product Change -> populate price & stock helper
    this.productSelect.addEventListener('change', () => {
      const selectedId = this.productSelect.value;
      const product = this.availableProducts.find(p => p.id === selectedId);
      if (product) {
        this.priceInput.value = product.price;
        this.updateStockHelper(product);
      } else {
        this.priceInput.value = '';
        this.stockHelper.textContent = '';
      }
      this.updateLiveSummary();
    });

    // Realtime live calculation
    this.qtyInput.addEventListener('input', () => this.updateLiveSummary());
    this.priceInput.addEventListener('input', () => this.updateLiveSummary());

    // Form submit
    this.formEl.addEventListener('submit', (e) => {
      e.preventDefault();
      this.handleSubmit();
    });
  }

  updateStockHelper(product) {
    if (!product) {
      this.stockHelper.textContent = '';
      return;
    }
    if (product.stock <= 0) {
      this.stockHelper.className = 'stock-helper-badge out-of-stock';
      this.stockHelper.textContent = 'Out of Stock (0 units available)';
    } else if (product.stock <= 10) {
      this.stockHelper.className = 'stock-helper-badge low-stock';
      this.stockHelper.textContent = `Low Stock (${product.stock} units available)`;
    } else {
      this.stockHelper.className = 'stock-helper-badge in-stock';
      this.stockHelper.textContent = `In Stock (${product.stock} units available)`;
    }
  }

  updateLiveSummary() {
    const selectedId = this.productSelect.value;
    const product = this.availableProducts.find(p => p.id === selectedId);
    const qty = parseInt(this.qtyInput.value, 10) || 0;
    const unitPrice = parseFloat(this.priceInput.value) || 0;
    const total = qty * unitPrice;

    this.summaryName.textContent = product ? product.name : '—';
    this.summaryQty.textContent = qty.toString();
    this.summaryPrice.textContent = `₹${unitPrice.toLocaleString('en-IN')}`;
    this.summaryTotal.textContent = `₹${total.toLocaleString('en-IN')}`;
  }

  async open() {
    this.alertEl.classList.remove('visible');
    this.alertEl.textContent = '';
    this.formEl.reset();
    this.submitBtn.disabled = false;
    this.submitBtn.textContent = 'Record Sale';

    // Set default date to today YYYY-MM-DD
    const now = new Date();
    const yyyy = now.getFullYear();
    const mm = String(now.getMonth() + 1).padStart(2, '0');
    const dd = String(now.getDate()).padStart(2, '0');
    this.dateInput.value = `${yyyy}-${mm}-${dd}`;

    // Set default time to HH:MM
    const hh = String(now.getHours()).padStart(2, '0');
    const min = String(now.getMinutes()).padStart(2, '0');
    this.timeInput.value = `${hh}:${min}`;

    this.qtyInput.value = 1;
    this.stockHelper.textContent = '';
    this.updateLiveSummary();

    this.backdropEl.classList.add('active');

    // Fetch fresh live products from backend
    try {
      this.productSelect.innerHTML = `<option value="">Loading products...</option>`;
      this.availableProducts = await productsApi.getProducts();
      
      if (this.availableProducts.length === 0) {
        this.productSelect.innerHTML = `<option value="">No active products available</option>`;
      } else {
        this.productSelect.innerHTML = `
          <option value="">-- Select a product --</option>
          ${this.availableProducts.map(p => `
            <option value="${p.id}" ${p.stock <= 0 ? 'disabled' : ''}>
              ${p.name} (${p.category}) — ₹${p.price} [${p.stock} in stock]
            </option>
          `).join('')}
        `;
      }
    } catch (err) {
      this.productSelect.innerHTML = `<option value="">Failed to load products</option>`;
      this.alertEl.textContent = 'Unable to fetch current products. Please check connection.';
      this.alertEl.classList.add('visible');
    }

    setTimeout(() => this.productSelect.focus(), 50);
  }

  close() {
    this.backdropEl.classList.remove('active');
  }

  async handleSubmit() {
    const productId = this.productSelect.value;
    const quantity = parseInt(this.qtyInput.value, 10);
    const unitPrice = parseFloat(this.priceInput.value);
    const date = this.dateInput.value;
    const time = this.timeInput.value;

    this.alertEl.classList.remove('visible');
    this.alertEl.textContent = '';

    if (!productId) {
      this.alertEl.textContent = 'Please select a product.';
      this.alertEl.classList.add('visible');
      return;
    }

    if (isNaN(quantity) || quantity <= 0) {
      this.alertEl.textContent = 'Quantity must be at least 1.';
      this.alertEl.classList.add('visible');
      return;
    }

    // Disable submit button while recording
    this.submitBtn.disabled = true;
    this.submitBtn.textContent = 'Recording sale...';

    try {
      if (typeof this.onRecordSale === 'function') {
        await this.onRecordSale({
          productId,
          quantity,
          unitPrice,
          date,
          time,
        });
      }
      this.close();
    } catch (err) {
      this.alertEl.textContent = err.message || 'Failed to record sale.';
      this.alertEl.classList.add('visible');
    } finally {
      this.submitBtn.disabled = false;
      this.submitBtn.textContent = 'Record Sale';
    }
  }
}
