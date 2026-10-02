import { icons } from '../icons.js';

/**
 * Category Modal Component (Add & Edit Category)
 */
export class CategoryModal {
  constructor(container, onSave) {
    this.container = container;
    this.onSave = onSave;
    this.currentCategory = null;
    this.isEditMode = false;
    this.renderModal();
    this.bindEvents();
  }

  renderModal() {
    this.container.innerHTML = `
      <div class="modal-backdrop" id="categoryModalBackdrop">
        <div class="modal-dialog" role="dialog" aria-modal="true" aria-labelledby="categoryModalTitle">
          <div class="modal-header">
            <h2 class="modal-title" id="categoryModalTitle">Add Category</h2>
            <button class="modal-close-btn" id="closeCategoryModalBtn" type="button" aria-label="Close modal">
              ${icons.close}
            </button>
          </div>

          <form id="categoryForm">
            <div class="modal-body">
              <!-- Error Banner -->
              <div id="categoryModalError" style="display: none; margin-bottom: 16px; padding: 10px 14px; background: #fee2e2; border: 1px solid #fca5a5; border-radius: 6px; color: #b91c1c; font-size: 13px;"></div>

              <div class="form-grid">
                <!-- Category Name -->
                <div class="form-group form-group-full">
                  <label class="form-label" for="formCategoryName">Category Name <span class="required-star">*</span></label>
                  <input type="text" id="formCategoryName" class="form-input" placeholder="e.g. Enamel Pins" maxlength="100" required />
                </div>

                <!-- Description -->
                <div class="form-group form-group-full">
                  <label class="form-label" for="formCategoryDescription">Description</label>
                  <textarea id="formCategoryDescription" class="form-textarea" placeholder="Optional category description..." maxlength="500"></textarea>
                </div>

                <!-- Active Status (Edit Mode only) -->
                <div class="form-group form-group-full" id="categoryStatusGroup" style="display: none;">
                  <label class="form-label" style="display: flex; align-items: center; gap: 8px; cursor: pointer;">
                    <input type="checkbox" id="formCategoryIsActive" style="width: 16px; height: 16px; accent-color: var(--color-primary, #2563eb);" />
                    <span style="font-size: 14px; font-weight: 500; color: var(--color-slate-700, #334155);">Active category (available for product assignment)</span>
                  </label>
                </div>
              </div>
            </div>

            <div class="modal-footer">
              <button type="button" class="btn-secondary" id="cancelCategoryBtn">Cancel</button>
              <button type="submit" class="btn-primary" id="saveCategorySubmitBtn">Save Category</button>
            </div>
          </form>
        </div>
      </div>
    `;

    this.backdropEl = this.container.querySelector('#categoryModalBackdrop');
    this.titleEl = this.container.querySelector('#categoryModalTitle');
    this.formEl = this.container.querySelector('#categoryForm');
    this.nameInput = this.container.querySelector('#formCategoryName');
    this.descInput = this.container.querySelector('#formCategoryDescription');
    this.statusGroup = this.container.querySelector('#categoryStatusGroup');
    this.isActiveCheckbox = this.container.querySelector('#formCategoryIsActive');
    this.errorBanner = this.container.querySelector('#categoryModalError');
  }

  bindEvents() {
    const closeBtn = this.container.querySelector('#closeCategoryModalBtn');
    const cancelBtn = this.container.querySelector('#cancelCategoryBtn');

    if (closeBtn) closeBtn.addEventListener('click', () => this.close());
    if (cancelBtn) cancelBtn.addEventListener('click', () => this.close());

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
    this.isEditMode = false;
    this.currentCategory = null;
    this.titleEl.textContent = 'Add Category';
    this.formEl.reset();
    this.statusGroup.style.display = 'none';
    this.clearError();
    this.backdropEl.classList.add('active');
    setTimeout(() => this.nameInput.focus(), 50);
  }

  openEdit(category) {
    if (!category) return;
    this.isEditMode = true;
    this.currentCategory = category;
    this.titleEl.textContent = 'Edit Category';
    this.clearError();

    this.nameInput.value = category.name || '';
    this.descInput.value = category.description || '';
    this.isActiveCheckbox.checked = category.is_active !== false;
    this.statusGroup.style.display = 'block';

    this.backdropEl.classList.add('active');
    setTimeout(() => this.nameInput.focus(), 50);
  }

  close() {
    this.backdropEl.classList.remove('active');
  }

  async handleSubmit() {
    const name = this.nameInput.value.trim();
    const description = this.descInput.value.trim();
    const is_active = this.isActiveCheckbox.checked;

    if (!name) {
      this.showError('Please enter a category name.');
      return;
    }

    const payload = {
      id: this.isEditMode ? this.currentCategory.id : undefined,
      name,
      description: description || null,
      is_active: this.isEditMode ? is_active : true,
    };

    if (typeof this.onSave === 'function') {
      try {
        await this.onSave(payload, this.isEditMode);
        this.close();
      } catch (err) {
        this.showError(err.message || 'Failed to save category.');
      }
    }
  }
}
