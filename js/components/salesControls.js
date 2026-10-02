import { icons } from '../icons.js';

/**
 * Render Sales Controls Bar & Header
 * @param {HTMLElement} container - DOM mount container
 * @param {Object} state - Current filter and sort state (includes categories array)
 * @param {Object} callbacks - onSearch, onDateChange, onCategoryChange, onSortChange, onRecordSale
 */
export function renderSalesControls(container, state, callbacks) {
  if (!container) return;

  const {
    searchTerm = '',
    dateFilter = 'all',
    categoryFilter = 'all',
    sortBy = 'newest',
    categories = [],
  } = state || {};

  const {
    onSearch,
    onDateChange,
    onCategoryChange,
    onSortChange,
    onRecordSale,
  } = callbacks || {};

  // Build category filter options dynamically
  const activeCategories = (categories || []).filter((c) => c.is_active !== false);
  const categoryOptionsHtml = [
    `<option value="all" ${categoryFilter === 'all' ? 'selected' : ''}>All Categories</option>`,
    ...activeCategories.map(
      (c) => `<option value="${c.name}" ${categoryFilter === c.name ? 'selected' : ''}>${c.name}</option>`
    ),
  ].join('');

  container.innerHTML = `
    <!-- Top Sales Header -->
    <div class="sales-header">
      <div class="sales-header-left">
        <h1 class="sales-title">Sales</h1>
        <p class="sales-subtitle">Track sales and inventory movements</p>
      </div>
      <button class="btn-primary" id="recordSaleBtn" type="button">
        ${icons.plus}
        <span>Record Sale</span>
      </button>
    </div>

    <!-- Sales Controls Bar -->
    <div class="products-controls-bar">
      <!-- Search Input -->
      <div class="search-input-wrapper">
        <span class="search-icon">${icons.search}</span>
        <input 
          type="text" 
          id="salesSearchInput" 
          class="search-input" 
          placeholder="Search sales by ID, product, or category..." 
          value="${searchTerm}" 
          autocomplete="off"
        />
      </div>

      <!-- Filters Group -->
      <div class="filters-group">
        <!-- Date Filter -->
        <select class="filter-select" id="salesDateFilterSelect" aria-label="Filter by Date Range">
          <option value="all" ${dateFilter === 'all' ? 'selected' : ''}>All Time</option>
          <option value="today" ${dateFilter === 'today' ? 'selected' : ''}>Today</option>
          <option value="yesterday" ${dateFilter === 'yesterday' ? 'selected' : ''}>Yesterday</option>
          <option value="this_week" ${dateFilter === 'this_week' ? 'selected' : ''}>This Week</option>
          <option value="this_month" ${dateFilter === 'this_month' ? 'selected' : ''}>This Month</option>
        </select>

        <!-- Category Filter -->
        <select class="filter-select" id="salesCategoryFilterSelect" aria-label="Filter by Category">
          ${categoryOptionsHtml}
        </select>

        <!-- Sort Filter -->
        <select class="filter-select" id="salesSortSelect" aria-label="Sort Sales">
          <option value="newest" ${sortBy === 'newest' ? 'selected' : ''}>Newest</option>
          <option value="oldest" ${sortBy === 'oldest' ? 'selected' : ''}>Oldest</option>
          <option value="amount_desc" ${sortBy === 'amount_desc' ? 'selected' : ''}>Highest Amount</option>
          <option value="amount_asc" ${sortBy === 'amount_asc' ? 'selected' : ''}>Lowest Amount</option>
        </select>
      </div>
    </div>
  `;

  // Attach event listeners
  const searchInput = container.querySelector('#salesSearchInput');
  if (searchInput && typeof onSearch === 'function') {
    searchInput.addEventListener('input', (e) => {
      onSearch(e.target.value.trim());
    });
  }

  const dateSelect = container.querySelector('#salesDateFilterSelect');
  if (dateSelect && typeof onDateChange === 'function') {
    dateSelect.addEventListener('change', (e) => {
      onDateChange(e.target.value);
    });
  }

  const catSelect = container.querySelector('#salesCategoryFilterSelect');
  if (catSelect && typeof onCategoryChange === 'function') {
    catSelect.addEventListener('change', (e) => {
      onCategoryChange(e.target.value);
    });
  }

  const sortSelect = container.querySelector('#salesSortSelect');
  if (sortSelect && typeof onSortChange === 'function') {
    sortSelect.addEventListener('change', (e) => {
      onSortChange(e.target.value);
    });
  }

  const recordBtn = container.querySelector('#recordSaleBtn');
  if (recordBtn && typeof onRecordSale === 'function') {
    recordBtn.addEventListener('click', onRecordSale);
  }
}
