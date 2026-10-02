import { icons } from '../icons.js';

/**
 * Render Customer KPI Summary Cards and Controls Bar
 * @param {HTMLElement} container - DOM mount container
 * @param {Object} metrics - { total_customers, active_customers, customers_with_orders, total_revenue }
 * @param {Object} state - Current filter and sort state
 * @param {Object} callbacks - onSearch, onStatusChange, onSortChange, onAddCustomer
 */
export function renderCustomerControls(container, metrics = {}, state = {}, callbacks = {}) {
  if (!container) return;

  const {
    searchTerm = '',
    selectedStatus = 'all',
    sortBy = 'newest',
  } = state || {};

  const {
    onSearch,
    onStatusChange,
    onSortChange,
    onAddCustomer,
  } = callbacks || {};

  const totalCust = metrics.total_customers || 0;
  const activeCust = metrics.active_customers || 0;
  const withOrders = metrics.customers_with_orders || 0;
  const totalRev = metrics.total_revenue ? parseFloat(metrics.total_revenue) : 0;

  container.innerHTML = `
    <!-- Top Customers Header -->
    <div class="products-header" style="margin-bottom: var(--space-4, 16px);">
      <div class="products-header-left">
        <h1 class="products-title">Customers</h1>
        <p class="products-subtitle">Manage customer CRM profiles, contact information, and lifetime order history</p>
      </div>
      <button class="btn-primary" id="addCustomerBtn" type="button">
        ${icons.plus}
        <span>Add Customer</span>
      </button>
    </div>

    <!-- Customer KPI Cards Grid -->
    <div class="kpi-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
      <!-- Total Customers -->
      <div class="kpi-card" style="background: #fff; border: 1px solid var(--color-slate-200, #e2e8f0); border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 13px; font-weight: 500; color: var(--color-slate-500, #64748b);">Total Customers</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--color-slate-900, #0f172a); margin-top: 4px;">${totalCust}</div>
      </div>

      <!-- Active Customers -->
      <div class="kpi-card" style="background: #fff; border: 1px solid #a7f3d0; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 13px; font-weight: 500; color: #047857;">Active Profiles</div>
        <div style="font-size: 24px; font-weight: 700; color: #059669; margin-top: 4px;">${activeCust}</div>
      </div>

      <!-- With Orders -->
      <div class="kpi-card" style="background: #fff; border: 1px solid #bae6fd; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 13px; font-weight: 500; color: #0369a1;">With Order History</div>
        <div style="font-size: 24px; font-weight: 700; color: #0284c7; margin-top: 4px;">${withOrders}</div>
      </div>

      <!-- Total Customer Revenue -->
      <div class="kpi-card" style="background: #fff; border: 1px solid #fed7aa; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 13px; font-weight: 500; color: #c2410c;">Customer Revenue</div>
        <div style="font-size: 24px; font-weight: 700; color: #ea580c; margin-top: 4px;">₹${totalRev.toFixed(2)}</div>
      </div>
    </div>

    <!-- Controls Bar -->
    <div class="products-controls-bar">
      <!-- Search Input -->
      <div class="search-input-wrapper">
        <span class="search-icon">${icons.search}</span>
        <input 
          type="text" 
          id="customersSearchInput" 
          class="search-input" 
          placeholder="Search by customer name, email, or phone..." 
          value="${searchTerm}" 
          autocomplete="off"
        />
      </div>

      <!-- Filters & Sort Group -->
      <div class="filters-group">
        <!-- Status Filter -->
        <select class="filter-select" id="customersStatusFilterSelect" aria-label="Filter by Status">
          <option value="all" ${selectedStatus === 'all' ? 'selected' : ''}>All Statuses</option>
          <option value="active" ${selectedStatus === 'active' ? 'selected' : ''}>Active Only</option>
          <option value="inactive" ${selectedStatus === 'inactive' ? 'selected' : ''}>Inactive Only</option>
        </select>

        <!-- Sorting -->
        <select class="filter-select" id="customersSortSelect" aria-label="Sort customers">
          <option value="newest" ${sortBy === 'newest' ? 'selected' : ''}>Newest Profiles</option>
          <option value="oldest" ${sortBy === 'oldest' ? 'selected' : ''}>Oldest Profiles</option>
          <option value="name_asc" ${sortBy === 'name_asc' ? 'selected' : ''}>Name (A-Z)</option>
          <option value="name_desc" ${sortBy === 'name_desc' ? 'selected' : ''}>Name (Z-A)</option>
          <option value="total_spent_desc" ${sortBy === 'total_spent_desc' ? 'selected' : ''}>Highest Total Spent</option>
          <option value="orders_desc" ${sortBy === 'orders_desc' ? 'selected' : ''}>Most Orders</option>
        </select>
      </div>
    </div>
  `;

  // Attach event listeners
  const searchInput = container.querySelector('#customersSearchInput');
  if (searchInput && typeof onSearch === 'function') {
    searchInput.addEventListener('input', (e) => {
      onSearch(e.target.value.trim());
    });
  }

  const statusSelect = container.querySelector('#customersStatusFilterSelect');
  if (statusSelect && typeof onStatusChange === 'function') {
    statusSelect.addEventListener('change', (e) => {
      onStatusChange(e.target.value);
    });
  }

  const sortSelect = container.querySelector('#customersSortSelect');
  if (sortSelect && typeof onSortChange === 'function') {
    sortSelect.addEventListener('change', (e) => {
      onSortChange(e.target.value);
    });
  }

  const addBtn = container.querySelector('#addCustomerBtn');
  if (addBtn && typeof onAddCustomer === 'function') {
    addBtn.addEventListener('click', onAddCustomer);
  }
}
