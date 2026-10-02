import { icons } from '../icons.js';

/**
 * Render Product Controls Bar & Page Header
 * @param {HTMLElement} container - Container for the controls
 * @param {Object} state - Current filter & sort state (includes categories array)
 * @param {Object} callbacks - Handler callbacks
 */
export function renderProductControls(container, state, callbacks) {
  if (!container) return;

  const {
    searchTerm = '',
    selectedCategory = 'all',
    selectedStock = 'all',
    sortBy = 'recent',
    categories = [],
  } = state || {};

  const {
    onSearch,
    onCategoryChange,
    onStockChange,
    onSortChange,
    onAddProduct,
  } = callbacks || {};

  // Build category filter options dynamically
  const activeCategories = (categories || []).filter((c) => c.is_active !== false);
  const categoryOptionsHtml = [
    `<option value="all" ${selectedCategory === 'all' ? 'selected' : ''}>All Categories</option>`,
    ...activeCategories.map(
      (c) => `<option value="${c.name}" ${selectedCategory === c.name ? 'selected' : ''}>${c.name}</option>`
    ),
  ].join('');

  container.innerHTML = `
    <!-- Top Products Header -->
    <div class="products-header">
      <div class="products-header-left">
        <h1 class="products-title">Products</h1>
        <p class="products-subtitle">Manage your products and inventory</p>
      </div>
      <button class="btn-primary" id="addProductBtn" type="button">
        ${icons.plus}
        <span>Add Product</span>
      </button>
    </div>

    <!-- Controls / Filters Bar -->
    <div class="products-controls-bar">
      <!-- Search Input -->
      <div class="search-input-wrapper">
        <span class="search-icon">${icons.search}</span>
        <input 
          type="text" 
          id="productSearchInput" 
          class="search-input" 
          placeholder="Search products by name, SKU, or category..." 
          value="${searchTerm}" 
          autocomplete="off"
        />
      </div>

      <!-- Filters & Sort Group -->
      <div class="filters-group">
        <!-- Category Filter -->
        <select class="filter-select" id="categoryFilterSelect" aria-label="Filter by Category">
          ${categoryOptionsHtml}
        </select>

        <!-- Stock Status Filter -->
        <select class="filter-select" id="stockFilterSelect" aria-label="Filter by Stock Status">
          <option value="all" ${selectedStock === 'all' ? 'selected' : ''}>All Stock</option>
          <option value="in_stock" ${selectedStock === 'in_stock' ? 'selected' : ''}>In Stock</option>
          <option value="low_stock" ${selectedStock === 'low_stock' ? 'selected' : ''}>Low Stock</option>
          <option value="out_of_stock" ${selectedStock === 'out_of_stock' ? 'selected' : ''}>Out of Stock</option>
        </select>

        <!-- Sorting -->
        <select class="filter-select" id="sortSelect" aria-label="Sort products">
          <option value="recent" ${sortBy === 'recent' ? 'selected' : ''}>Recently Added</option>
          <option value="name_asc" ${sortBy === 'name_asc' ? 'selected' : ''}>Name (A–Z)</option>
          <option value="price_asc" ${sortBy === 'price_asc' ? 'selected' : ''}>Price: Low to High</option>
          <option value="price_desc" ${sortBy === 'price_desc' ? 'selected' : ''}>Price: High to Low</option>
          <option value="stock_asc" ${sortBy === 'stock_asc' ? 'selected' : ''}>Stock: Low to High</option>
          <option value="stock_desc" ${sortBy === 'stock_desc' ? 'selected' : ''}>Stock: High to Low</option>
          <option value="bestseller" ${sortBy === 'bestseller' ? 'selected' : ''}>Best Selling</option>
        </select>
      </div>
    </div>
  `;

  // Attach event listeners
  const searchInput = container.querySelector('#productSearchInput');
  if (searchInput && typeof onSearch === 'function') {
    searchInput.addEventListener('input', (e) => {
      onSearch(e.target.value.trim());
    });
  }

  const categorySelect = container.querySelector('#categoryFilterSelect');
  if (categorySelect && typeof onCategoryChange === 'function') {
    categorySelect.addEventListener('change', (e) => {
      onCategoryChange(e.target.value);
    });
  }

  const stockSelect = container.querySelector('#stockFilterSelect');
  if (stockSelect && typeof onStockChange === 'function') {
    stockSelect.addEventListener('change', (e) => {
      onStockChange(e.target.value);
    });
  }

  const sortSelect = container.querySelector('#sortSelect');
  if (sortSelect && typeof onSortChange === 'function') {
    sortSelect.addEventListener('change', (e) => {
      onSortChange(e.target.value);
    });
  }

  const addBtn = container.querySelector('#addProductBtn');
  if (addBtn && typeof onAddProduct === 'function') {
    addBtn.addEventListener('click', onAddProduct);
  }
}
