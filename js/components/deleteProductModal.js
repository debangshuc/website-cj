import { icons } from '../icons.js';

/**
 * Delete Product Confirmation Modal
 */
export class DeleteProductModal {
  constructor(container, onConfirm) {
    this.container = container;
    this.onConfirm = onConfirm;
    this.productToDelete = null;
    this.renderModal();
    this.bindEvents();
  }

  renderModal() {
    this.container.innerHTML = `
      <div class="modal-backdrop" id="deleteModalBackdrop">
        <div class="modal-dialog modal-sm" role="dialog" aria-modal="true" aria-labelledby="deleteModalTitle">
          <div class="modal-header">
            <h2 class="modal-title" id="deleteModalTitle">Delete Product?</h2>
            <button class="modal-close-btn" id="closeDeleteModalBtn" type="button" aria-label="Close modal">
              ${icons.close}
            </button>
          </div>

          <div class="modal-body">
            <p class="delete-modal-text">
              Are you sure you want to delete <span class="delete-product-name" id="deleteProductNameText">this product</span> from your inventory? This action cannot be undone.
            </p>
          </div>

          <div class="modal-footer">
            <button type="button" class="btn-secondary" id="cancelDeleteBtn">Cancel</button>
            <button type="button" class="btn-danger" id="confirmDeleteBtn">Delete</button>
          </div>
        </div>
      </div>
    `;

    this.backdropEl = this.container.querySelector('#deleteModalBackdrop');
    this.productNameEl = this.container.querySelector('#deleteProductNameText');
  }

  bindEvents() {
    const closeBtn = this.container.querySelector('#closeDeleteModalBtn');
    const cancelBtn = this.container.querySelector('#cancelDeleteBtn');
    const confirmBtn = this.container.querySelector('#confirmDeleteBtn');

    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (cancelBtn) cancelBtn.addEventListener('click', () => this.close());

    if (confirmBtn) {
      confirmBtn.addEventListener('click', () => {
        if (this.productToDelete && typeof this.onConfirm === 'function') {
          this.onConfirm(this.productToDelete.id);
        }
        this.close();
      });
    }

    if (this.backdropEl) {
      this.backdropEl.addEventListener('click', (e) => {
        if (e.target === this.backdropEl) this.close();
      });
    }
  }

  open(product) {
    if (!product) return;
    this.productToDelete = product;
    this.productNameEl.textContent = `"${product.name}"`;
    this.backdropEl.classList.add('active');
  }

  close() {
    this.backdropEl.classList.remove('active');
    this.productToDelete = null;
  }
}
