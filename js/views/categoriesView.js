import { categoriesApi } from '../api/categoriesApi.js';
import { CategoryModal } from '../components/categoryModal.js';
import { icons } from '../icons.js';

/**
 * Categories View Controller
 * Connected directly to FastAPI + PostgreSQL via categoriesApi.
 */
export class CategoriesView {
  constructor(container, modalContainer) {
    this.container = container;
    this.modalContainer = modalContainer;
    this.categories = [];
    this.isLoading = false;
    this.error = null;
    this.searchTerm = '';
    this.statusFilter = 'all'; // 'all', 'active', 'inactive'
    this.isInitialized = false;
  }

  init() {
    this.container.innerHTML = `
      <div class="products-content-wrapper" id="categoriesContentWrapper" style="width: 100%; display: flex; flex-direction: column; gap: var(--space-6, 24px);">
        <!-- Top Categories Header -->
        <div class="products-header">
          <div class="products-header-left">
            <h1 class="products-title">Categories</h1>
            <p class="products-subtitle">Manage product categories and catalog organization</p>
          </div>
          <button class="btn-primary" id="addCategoryBtn" type="button">
            ${icons.plus}
            <span>Add Category</span>
          </button>
        </div>

        <!-- Controls / Search Bar -->
        <div class="products-controls-bar">
          <div class="search-input-wrapper">
            <span class="search-icon">${icons.search}</span>
            <input 
              type="text" 
              id="categorySearchInput" 
              class="search-input" 
              placeholder="Search categories by name or description..." 
              autocomplete="off"
            />
          </div>

          <div class="filters-group">
            <select class="filter-select" id="categoryStatusFilter" aria-label="Filter by Status">
              <option value="all">All Categories</option>
              <option value="active" selected>Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
          </div>
        </div>

        <!-- Table / List Mount -->
        <div class="table-card" id="categoriesTableCard">
          <div id="categoriesTableMount"></div>
        </div>
      </div>

      <!-- Loading / Error Overlay Container -->
      <div id="categoriesStatusContainer" style="display: none; width: 100%;"></div>
    `;

    this.contentWrapperEl = this.container.querySelector('#categoriesContentWrapper');
    this.statusContainerEl = this.container.querySelector('#categoriesStatusContainer');
    this.tableMountEl = this.container.querySelector('#categoriesTableMount');
    this.searchInput = this.container.querySelector('#categorySearchInput');
    this.statusFilterSelect = this.container.querySelector('#categoryStatusFilter');
    this.addBtn = this.container.querySelector('#addCategoryBtn');

    // Initialize Category Modal
    let modalMount = this.modalContainer.querySelector('#categoryModalMount');
    if (!modalMount) {
      modalMount = document.createElement('div');
      modalMount.id = 'categoryModalMount';
      this.modalContainer.appendChild(modalMount);
    }
    this.categoryModal = new CategoryModal(modalMount, (data, isEdit) => this.handleSaveCategory(data, isEdit));

    this.bindEvents();
    this.isInitialized = true;
  }

  bindEvents() {
    if (this.addBtn) {
      this.addBtn.addEventListener('click', () => {
        this.categoryModal.openAdd();
      });
    }

    if (this.searchInput) {
      this.searchInput.addEventListener('input', (e) => {
        this.searchTerm = e.target.value.trim().toLowerCase();
        this.renderContent();
      });
    }

    if (this.statusFilterSelect) {
      this.statusFilterSelect.addEventListener('change', (e) => {
        this.statusFilter = e.target.value;
        this.loadCategories();
      });
    }
  }

  render() {
    if (!this.isInitialized) {
      this.init();
    }
    this.container.style.display = 'block';
    this.loadCategories();
  }

  hide() {
    this.container.style.display = 'none';
  }

  async loadCategories() {
    this.isLoading = true;
    this.error = null;
    this.renderLoading();

    try {
      // If user selected 'inactive' or 'all', fetch include_inactive=true
      const includeInactive = this.statusFilter !== 'active';
      const data = await categoriesApi.getCategories({ include_inactive: includeInactive });
      this.categories = data;
      this.isLoading = false;
      this.renderContent();
    } catch (err) {
      this.isLoading = false;
      if (err.status === 403 && window.__APP__) {
        window.__APP__.setAuthState('UNAUTHORIZED');
        return;
      }
      this.error = err.message || 'Unable to load categories.';
      this.renderError();
    }
  }

  renderLoading() {
    this.tableMountEl.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <p class="empty-state-desc" style="font-size: 15px; color: var(--color-slate-600); font-weight: 500;">
          Loading categories...
        </p>
      </div>
    `;
  }

  renderError() {
    this.tableMountEl.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <div class="empty-state-icon" style="color: var(--color-danger, #ef4444);">
          ${icons.alertCircle || icons.emptyBox}
        </div>
        <h2 class="empty-state-title">Unable to load categories</h2>
        <p class="empty-state-desc">${this.error}</p>
        <button class="btn-primary" id="retryCategoriesBtn" type="button" style="margin-top: 8px;">Retry</button>
      </div>
    `;

    const retryBtn = this.tableMountEl.querySelector('#retryCategoriesBtn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.loadCategories();
      });
    }
  }

  getFilteredCategories() {
    return this.categories.filter((cat) => {
      // Status filter
      if (this.statusFilter === 'active' && !cat.is_active) return false;
      if (this.statusFilter === 'inactive' && cat.is_active) return false;

      // Search term
      if (this.searchTerm) {
        const nameMatch = cat.name.toLowerCase().includes(this.searchTerm);
        const descMatch = cat.description && cat.description.toLowerCase().includes(this.searchTerm);
        return nameMatch || descMatch;
      }

      return true;
    });
  }

  renderContent() {
    if (this.isLoading || this.error) return;

    const filtered = this.getFilteredCategories();

    if (filtered.length === 0) {
      this.tableMountEl.innerHTML = `
        <div class="empty-state-card" style="padding: 48px 24px;">
          <div class="empty-state-icon">
            ${icons.emptyBox}
          </div>
          <h2 class="empty-state-title">No categories found</h2>
          <p class="empty-state-desc">
            ${this.categories.length === 0 ? 'Create your first category to organize your inventory.' : 'Try changing your search term or status filter.'}
          </p>
          <button class="btn-primary" id="emptyAddCategoryBtn" type="button" style="margin-top: 8px;">
            ${icons.plus}
            <span>Add Category</span>
          </button>
        </div>
      `;

      const emptyAddBtn = this.tableMountEl.querySelector('#emptyAddCategoryBtn');
      if (emptyAddBtn) {
        emptyAddBtn.addEventListener('click', () => {
          this.categoryModal.openAdd();
        });
      }
      return;
    }

    const rowsHtml = filtered.map((cat) => {
      const isInactive = !cat.is_active;
      const statusBadge = isInactive
        ? `<span class="badge" style="background: #f1f5f9; color: #64748b; font-weight: 600;">Inactive</span>`
        : `<span class="badge" style="background: #ecfdf5; color: #059669; font-weight: 600;">Active</span>`;

      const createdDate = cat.created_at
        ? new Date(cat.created_at).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })
        : '—';

      const prodCount = cat.product_count !== undefined ? cat.product_count : 0;

      return `
        <tr class="table-row">
          <td class="table-cell" style="font-weight: 600; color: var(--color-slate-900);">
            ${cat.name}
          </td>
          <td class="table-cell" style="color: var(--color-slate-600); max-width: 320px; font-size: 13px;">
            ${cat.description || '<span style="color: var(--color-slate-400);">No description</span>'}
          </td>
          <td class="table-cell">
            ${statusBadge}
          </td>
          <td class="table-cell">
            <span style="font-size: 13px; font-weight: 600; color: var(--color-slate-700);">${prodCount} products</span>
          </td>
          <td class="table-cell" style="color: var(--color-slate-500); font-size: 13px;">
            ${createdDate}
          </td>
          <td class="table-cell table-actions">
            <button type="button" class="btn-action edit-category-btn" data-cat-id="${cat.id}" title="Edit Category" aria-label="Edit Category">
              ${icons.edit}
            </button>
            ${
              isInactive
                ? `<button type="button" class="btn-action reactivate-category-btn" data-cat-id="${cat.id}" title="Reactivate Category" aria-label="Reactivate Category" style="color: var(--color-success, #10b981);">
                    ${icons.plus}
                  </button>`
                : `<button type="button" class="btn-action deactivate-category-btn" data-cat-id="${cat.id}" title="Deactivate Category" aria-label="Deactivate Category" style="color: var(--color-danger, #ef4444);">
                    ${icons.trash}
                  </button>`
            }
          </td>
        </tr>
      `;
    }).join('');

    this.tableMountEl.innerHTML = `
      <div class="table-responsive">
        <table class="data-table" aria-label="Categories table">
          <thead>
            <tr>
              <th class="table-th">Category Name</th>
              <th class="table-th">Description</th>
              <th class="table-th">Status</th>
              <th class="table-th">Assigned Products</th>
              <th class="table-th">Created Date</th>
              <th class="table-th table-th-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            ${rowsHtml}
          </tbody>
        </table>
      </div>
    `;

    // Attach row action listeners
    this.tableMountEl.querySelectorAll('.edit-category-btn').forEach((btn) => {
      btn.addEventListener('click', () => {
        const catId = btn.getAttribute('data-cat-id');
        const cat = this.categories.find((c) => c.id === catId);
        if (cat) this.categoryModal.openEdit(cat);
      });
    });

    this.tableMountEl.querySelectorAll('.deactivate-category-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const catId = btn.getAttribute('data-cat-id');
        const cat = this.categories.find((c) => c.id === catId);
        if (cat && confirm(`Are you sure you want to deactivate "${cat.name}"?`)) {
          try {
            await categoriesApi.deleteCategory(catId);
            await this.loadCategories();
          } catch (err) {
            alert(`Error deactivating category: ${err.message}`);
          }
        }
      });
    });

    this.tableMountEl.querySelectorAll('.reactivate-category-btn').forEach((btn) => {
      btn.addEventListener('click', async () => {
        const catId = btn.getAttribute('data-cat-id');
        try {
          await categoriesApi.updateCategory(catId, { is_active: true });
          await this.loadCategories();
        } catch (err) {
          alert(`Error reactivating category: ${err.message}`);
        }
      });
    });
  }

  async handleSaveCategory(categoryData, isEdit) {
    if (isEdit) {
      await categoriesApi.updateCategory(categoryData.id, {
        name: categoryData.name,
        description: categoryData.description,
        is_active: categoryData.is_active,
      });
    } else {
      await categoriesApi.createCategory({
        name: categoryData.name,
        description: categoryData.description,
      });
    }
    await this.loadCategories();
  }
}
