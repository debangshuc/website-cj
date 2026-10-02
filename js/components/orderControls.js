import { icons } from '../icons.js';

/**
 * Render Order KPI Summary Cards and Controls Bar
 * @param {HTMLElement} container - DOM mount container
 * @param {Object} metrics - { total_orders, pending_orders, confirmed_orders, completed_orders, cancelled_orders, total_revenue }
 * @param {Object} state - Current filter and sort state
 * @param {Object} callbacks - onSearch, onStatusChange, onSortChange, onCreateOrder
 */
export function renderOrderControls(container, metrics = {}, state = {}, callbacks = {}) {
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
    onCreateOrder,
  } = callbacks || {};

  const totalOrders = metrics.total_orders || 0;
  const pendingOrders = metrics.pending_orders || 0;
  const confirmedOrders = metrics.confirmed_orders || 0;
  const completedOrders = metrics.completed_orders || 0;
  const cancelledOrders = metrics.cancelled_orders || 0;

  container.innerHTML = `
    <!-- Top Orders Header -->
    <div class="products-header" style="margin-bottom: var(--space-4, 16px);">
      <div class="products-header-left">
        <h1 class="products-title">Orders</h1>
        <p class="products-subtitle">Manage customer orders and order status lifecycles</p>
      </div>
      <button class="btn-primary" id="createOrderBtn" type="button">
        ${icons.plus}
        <span>Create Order</span>
      </button>
    </div>

    <!-- Order KPI Cards Grid -->
    <div class="kpi-grid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 16px; margin-bottom: 24px;">
      <!-- Total Orders -->
      <div class="kpi-card" style="background: #fff; border: 1px solid var(--color-slate-200, #e2e8f0); border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 13px; font-weight: 500; color: var(--color-slate-500, #64748b);">Total Orders</div>
        <div style="font-size: 24px; font-weight: 700; color: var(--color-slate-900, #0f172a); margin-top: 4px;">${totalOrders}</div>
      </div>

      <!-- Pending Orders -->
      <div class="kpi-card" style="background: #fff; border: 1px solid #fde68a; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 13px; font-weight: 500; color: #b45309;">Pending</div>
        <div style="font-size: 24px; font-weight: 700; color: #d97706; margin-top: 4px;">${pendingOrders}</div>
      </div>

      <!-- Confirmed Orders -->
      <div class="kpi-card" style="background: #fff; border: 1px solid #bae6fd; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 13px; font-weight: 500; color: #0369a1;">Confirmed</div>
        <div style="font-size: 24px; font-weight: 700; color: #0284c7; margin-top: 4px;">${confirmedOrders}</div>
      </div>

      <!-- Completed Orders -->
      <div class="kpi-card" style="background: #fff; border: 1px solid #a7f3d0; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 13px; font-weight: 500; color: #047857;">Completed</div>
        <div style="font-size: 24px; font-weight: 700; color: #059669; margin-top: 4px;">${completedOrders}</div>
      </div>

      <!-- Cancelled Orders -->
      <div class="kpi-card" style="background: #fff; border: 1px solid #fecaca; border-radius: 12px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <div style="font-size: 13px; font-weight: 500; color: #b91c1c;">Cancelled</div>
        <div style="font-size: 24px; font-weight: 700; color: #dc2626; margin-top: 4px;">${cancelledOrders}</div>
      </div>
    </div>

    <!-- Controls Bar -->
    <div class="products-controls-bar">
      <!-- Search Input -->
      <div class="search-input-wrapper">
        <span class="search-icon">${icons.search}</span>
        <input 
          type="text" 
          id="ordersSearchInput" 
          class="search-input" 
          placeholder="Search by order #, customer, or product..." 
          value="${searchTerm}" 
          autocomplete="off"
        />
      </div>

      <!-- Filters & Sort Group -->
      <div class="filters-group">
        <!-- Status Filter -->
        <select class="filter-select" id="ordersStatusFilterSelect" aria-label="Filter by Status">
          <option value="all" ${selectedStatus === 'all' ? 'selected' : ''}>All Statuses</option>
          <option value="pending" ${selectedStatus === 'pending' ? 'selected' : ''}>Pending Only</option>
          <option value="confirmed" ${selectedStatus === 'confirmed' ? 'selected' : ''}>Confirmed Only</option>
          <option value="completed" ${selectedStatus === 'completed' ? 'selected' : ''}>Completed Only</option>
          <option value="cancelled" ${selectedStatus === 'cancelled' ? 'selected' : ''}>Cancelled Only</option>
        </select>

        <!-- Sorting -->
        <select class="filter-select" id="ordersSortSelect" aria-label="Sort orders">
          <option value="newest" ${sortBy === 'newest' ? 'selected' : ''}>Newest Orders</option>
          <option value="oldest" ${sortBy === 'oldest' ? 'selected' : ''}>Oldest Orders</option>
          <option value="total_desc" ${sortBy === 'total_desc' ? 'selected' : ''}>Highest Total</option>
          <option value="total_asc" ${sortBy === 'total_asc' ? 'selected' : ''}>Lowest Total</option>
        </select>
      </div>
    </div>
  `;

  // Attach event listeners
  const searchInput = container.querySelector('#ordersSearchInput');
  if (searchInput && typeof onSearch === 'function') {
    searchInput.addEventListener('input', (e) => {
      onSearch(e.target.value.trim());
    });
  }

  const statusSelect = container.querySelector('#ordersStatusFilterSelect');
  if (statusSelect && typeof onStatusChange === 'function') {
    statusSelect.addEventListener('change', (e) => {
      onStatusChange(e.target.value);
    });
  }

  const sortSelect = container.querySelector('#ordersSortSelect');
  if (sortSelect && typeof onSortChange === 'function') {
    sortSelect.addEventListener('change', (e) => {
      onSortChange(e.target.value);
    });
  }

  const createBtn = container.querySelector('#createOrderBtn');
  if (createBtn && typeof onCreateOrder === 'function') {
    createBtn.addEventListener('click', onCreateOrder);
  }
}
