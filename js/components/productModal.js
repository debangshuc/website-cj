import { icons } from '../icons.js';

/**
 * Product Modal (Add & Edit Product with Dynamic Categories & Supabase Storage Image Upload)
 */
export class ProductModal {
  constructor(container, onSave) {
    this.container = container;
    this.onSave = onSave;
    this.currentProduct = null;
    this.categories = [];
    this.isEditMode = false;
    this.selectedImageFile = null;
    this.removeImage = false;
    this.renderModal();
    this.bindEvents();
  }

  renderModal() {
    this.container.innerHTML = `
      <div class="modal-backdrop" id="productModalBackdrop">
        <div class="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="productModalTitle">
          <div class="modal-header">
            <h2 class="modal-title" id="productModalTitle">Add Product</h2>
            <button class="modal-close-btn" id="closeProductModalBtn" type="button" aria-label="Close modal">
              ${icons.close}
            </button>
          </div>

          <form id="productForm">
            <div class="modal-body">
              <div class="form-grid">
                <!-- Product Name -->
                <div class="form-group form-group-full">
                  <label class="form-label" for="formProductName">Product Name <span class="required-star">*</span></label>
                  <input type="text" id="formProductName" class="form-input" placeholder="e.g. Holographic Neon Poster" required />
                </div>

                <!-- SKU -->
                <div class="form-group">
                  <label class="form-label" for="formProductSku">SKU <span class="required-star">*</span></label>
                  <input type="text" id="formProductSku" class="form-input" placeholder="e.g. PST-NEO-005" required />
                </div>

                <!-- Category -->
                <div class="form-group">
                  <label class="form-label" for="formProductCategory">Category <span class="required-star">*</span></label>
                  <select id="formProductCategory" class="form-select" required>
                    <option value="" disabled selected>Select a category...</option>
                  </select>
                </div>

                <!-- Price -->
                <div class="form-group">
                  <label class="form-label" for="formProductPrice">Price (₹) <span class="required-star">*</span></label>
                  <input type="number" id="formProductPrice" class="form-input" placeholder="e.g. 250" min="0" step="1" required />
                </div>

                <!-- Stock Quantity -->
                <div class="form-group">
                  <label class="form-label" for="formProductStock">Stock Quantity <span class="required-star">*</span></label>
                  <input type="number" id="formProductStock" class="form-input" placeholder="e.g. 25" min="0" step="1" required />
                </div>

                <!-- Product Image Upload (Supabase Storage) -->
                <div class="form-group form-group-full">
                  <label class="form-label" for="formProductImageFile">Product Image</label>
                  <div class="image-upload-wrapper" style="display: flex; gap: 16px; align-items: center; background: var(--color-slate-50, #f8fafc); border: 1px dashed var(--color-slate-300, #cbd5e1); border-radius: 8px; padding: 12px 16px;">
                    <div class="image-preview-box" style="width: 60px; height: 60px; border-radius: 6px; overflow: hidden; background: #fff; border: 1px solid var(--color-slate-200, #e2e8f0); display: flex; align-items: center; justify-content: center; flex-shrink: 0;">
                      <img id="imagePreviewImg" src="assets/images/placeholder-poster-main.svg" alt="Preview" style="width: 100%; height: 100%; object-fit: cover;" />
                    </div>
                    <div style="flex: 1;">
                      <div style="display: flex; gap: 8px; margin-bottom: 4px;">
                        <input type="file" id="formProductImageFile" accept="image/jpeg,image/png,image/webp" style="display: none;" />
                        <button type="button" class="btn-secondary" id="browseImageBtn" style="padding: 6px 12px; font-size: 13px;">Choose Image</button>
                        <button type="button" class="btn-secondary" id="removeImageBtn" style="padding: 6px 12px; font-size: 13px; color: var(--color-danger, #ef4444); display: none;">Remove</button>
                      </div>
                      <span class="form-hint" style="font-size: 12px; color: var(--color-slate-500, #64748b);">Supported formats: JPEG, PNG, WebP (Max 5 MB)</span>
                    </div>
                  </div>
                </div>

                <!-- Description -->
                <div class="form-group form-group-full">
                  <label class="form-label" for="formProductDescription">Description</label>
                  <textarea id="formProductDescription" class="form-textarea" placeholder="Enter optional product description, material, dimensions..."></textarea>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" id="cancelProductBtn">Cancel</button>
              <button type="submit" class="btn-primary" id="saveProductSubmitBtn">Save Product</button>
            </div>
          </form>
        </div>
      </div>
    `;

    this.backdropEl = this.container.querySelector('#productModalBackdrop');
    this.titleEl = this.container.querySelector('#productModalTitle');
    this.formEl = this.container.querySelector('#productForm');
    this.nameInput = this.container.querySelector('#formProductName');
    this.skuInput = this.container.querySelector('#formProductSku');
    this.categorySelect = this.container.querySelector('#formProductCategory');
    this.priceInput = this.container.querySelector('#formProductPrice');
    this.stockInput = this.container.querySelector('#formProductStock');
    this.descInput = this.container.querySelector('#formProductDescription');
    this.fileInput = this.container.querySelector('#formProductImageFile');
    this.previewImg = this.container.querySelector('#imagePreviewImg');
    this.browseBtn = this.container.querySelector('#browseImageBtn');
    this.removeBtn = this.container.querySelector('#removeImageBtn');
  }

  setCategories(categories = []) {
    this.categories = categories;
    const activeCategories = categories.filter((c) => c.is_active !== false);

    if (activeCategories.length === 0) {
      this.categorySelect.innerHTML = `<option value="" disabled selected>No categories available</option>`;
      return;
    }

    const optionsHtml = activeCategories
      .map((c) => `<option value="${c.id}" data-name="${c.name}">${c.name}</option>`)
      .join('');
    this.categorySelect.innerHTML = optionsHtml;
  }

  bindEvents() {
    const closeBtn = this.container.querySelector('#closeProductModalBtn');
    const cancelBtn = this.container.querySelector('#cancelProductBtn');

    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (cancelBtn) cancelBtn.addEventListener('click', () => this.close());

    // Backdrop click
    if (this.backdropEl) {
      this.backdropEl.addEventListener('click', (e) => {
        if (e.target === this.backdropEl) this.close();
      });
    }

    // Image browse button
    if (this.browseBtn && this.fileInput) {
      this.browseBtn.addEventListener('click', () => {
        this.fileInput.click();
      });
    }

    // File input change
    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
          if (file.size > 5 * 1024 * 1024) {
            alert('Image file size exceeds the 5 MB limit.');
            this.fileInput.value = '';
            return;
          }
          this.selectedImageFile = file;
          this.removeImage = false;
          this.previewImg.src = URL.createObjectURL(file);
          if (this.removeBtn) this.removeBtn.style.display = 'inline-block';
        }
      });
    }

    // Remove image button
    if (this.removeBtn) {
      this.removeBtn.addEventListener('click', () => {
        this.selectedImageFile = null;
        this.removeImage = true;
        if (this.fileInput) this.fileInput.value = '';
        this.previewImg.src = 'assets/images/placeholder-poster-main.svg';
        this.removeBtn.style.display = 'none';
      });
    }

    // Form submit
    if (this.formEl) {
      this.formEl.addEventListener('submit', (e) => {
        e.preventDefault();
        this.handleSubmit();
      });
    }
  }

  openAdd(categories = []) {
    this.isEditMode = false;
    this.currentProduct = null;
    this.selectedImageFile = null;
    this.removeImage = false;
    this.titleEl.textContent = 'Add New Product';
    this.formEl.reset();

    if (categories && categories.length > 0) {
      this.setCategories(categories);
    }

    if (this.fileInput) this.fileInput.value = '';
    this.previewImg.src = 'assets/images/placeholder-poster-main.svg';
    if (this.removeBtn) this.removeBtn.style.display = 'none';
    this.backdropEl.classList.add('active');
    setTimeout(() => this.nameInput.focus(), 50);
  }

  openEdit(product, categories = []) {
    if (!product) return;
    this.isEditMode = true;
    this.currentProduct = product;
    this.selectedImageFile = null;
    this.removeImage = false;
    this.titleEl.textContent = 'Edit Product';

    if (categories && categories.length > 0) {
      this.setCategories(categories);
    }

    this.nameInput.value = product.name || '';
    this.skuInput.value = product.sku || '';

    // Select category by category_id or fallback by name
    if (product.category_id && this.categorySelect.querySelector(`option[value="${product.category_id}"]`)) {
      this.categorySelect.value = product.category_id;
    } else if (product.category) {
      const matchOpt = Array.from(this.categorySelect.options).find(
        (opt) => opt.getAttribute('data-name')?.toLowerCase() === product.category.toLowerCase()
      );
      if (matchOpt) {
        this.categorySelect.value = matchOpt.value;
      }
    }

    this.priceInput.value = product.price ?? 0;
    this.stockInput.value = product.stock ?? 0;
    this.descInput.value = product.description || '';
    if (this.fileInput) this.fileInput.value = '';

    const currentImg = product.imageUrl || product.image_path || 'assets/images/placeholder-poster-main.svg';
    this.previewImg.src = currentImg;

    if (this.removeBtn) {
      this.removeBtn.style.display = product.image_path ? 'inline-block' : 'none';
    }

    this.backdropEl.classList.add('active');
    setTimeout(() => this.nameInput.focus(), 50);
  }

  close() {
    this.backdropEl.classList.remove('active');
  }

  handleSubmit() {
    const name = this.nameInput.value.trim();
    const sku = this.skuInput.value.trim();
    const category_id = this.categorySelect.value;
    const selectedOption = this.categorySelect.selectedOptions[0];
    const category = selectedOption ? selectedOption.getAttribute('data-name') || selectedOption.textContent : undefined;
    const price = parseFloat(this.priceInput.value) || 0;
    const stock = parseInt(this.stockInput.value, 10) || 0;
    const description = this.descInput.value.trim();

    if (!name || !sku || !category_id) {
      alert('Please fill in all required fields including category.');
      return;
    }

    const productPayload = {
      id: this.isEditMode ? this.currentProduct.id : undefined,
      name,
      sku,
      category_id,
      category,
      price,
      stock,
      description,
    };

    if (typeof this.onSave === 'function') {
      this.onSave(productPayload, this.isEditMode, this.selectedImageFile, this.removeImage);
    }

    this.close();
  }
}
