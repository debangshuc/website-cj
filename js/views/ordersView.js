import { icons } from '../icons.js';
import { ordersApi } from '../api/ordersApi.js';
import { productsApi } from '../api/productsApi.js';
import { customersApi } from '../api/customersApi.js';
import { renderOrderControls } from '../components/orderControls.js';
import { renderOrderTable } from '../components/orderTable.js';
import { OrderModal } from '../components/orderModal.js';

/**
 * Orders View Controller
 * Connected directly to FastAPI / PostgreSQL via ordersApi.
 */
export class OrdersView {
  constructor(container, modalMountContainer) {
    this.container = container;
    this.modalMountContainer = modalMountContainer;

    this.orders = [];
    this.metrics = {};
    this.products = [];
    this.customers = [];
    this.isLoading = false;
    this.error = null;

    this.state = {
      searchTerm: '',
      selectedStatus: 'all',
      sortBy: 'newest',
    };

    this.isInitialized = false;
  }

  init() {
    this.container.innerHTML = `
      <div class="products-content-wrapper" id="ordersContentWrapper" style="width: 100%; display: flex; flex-direction: column; gap: var(--space-4, 16px);">
        <!-- Orders Controls & KPI Cards Mount -->
        <div id="ordersControlsMount"></div>

        <!-- Orders Table Card -->
        <div class="card" id="ordersTableCard">
          <div id="ordersTableMount"></div>
        </div>
      </div>
    `;

    this.controlsMountEl = this.container.querySelector('#ordersControlsMount');
    this.tableMountEl = this.container.querySelector('#ordersTableMount');

    // Initialize Order Modal
    let modalMount = this.modalMountContainer.querySelector('#orderModalMount');
    if (!modalMount) {
      modalMount = document.createElement('div');
      modalMount.id = 'orderModalMount';
      this.modalMountContainer.appendChild(modalMount);
    }

    this.orderModal = new OrderModal(
      modalMount,
      (orderData) => this.handleCreateOrder(orderData),
      (orderId, status) => this.handleStatusChange(orderId, status)
    );

    this.isInitialized = true;
  }

  render() {
    if (!this.isInitialized) {
      this.init();
    }
    this.container.style.display = 'block';
    this.loadData();
  }

  hide() {
    this.container.style.display = 'none';
  }

  async loadData() {
    this.isLoading = true;
    this.error = null;
    this.renderLoading();

    try {
      const [ordersData, metricsData, productsData, customersData] = await Promise.all([
        ordersApi.getOrders({
          search: this.state.searchTerm,
          status: this.state.selectedStatus,
          sort_by: this.state.sortBy,
        }),
        ordersApi.getOrderMetrics().catch(() => ({})),
        productsApi.getProducts().catch(() => []),
        customersApi.getCustomers({ status: 'active' }).catch(() => []),
      ]);

      this.orders = ordersData;
      this.metrics = metricsData;
      this.products = productsData;
      this.customers = customersData;
      this.isLoading = false;

      this.renderControls();
      this.renderContent();
    } catch (err) {
      this.isLoading = false;
      if (err.status === 403 && window.__APP__) {
        window.__APP__.setAuthState('UNAUTHORIZED');
        return;
      }
      this.error = err.message || 'Unable to load orders data.';
      this.renderError();
    }
  }

  renderControls() {
    renderOrderControls(this.controlsMountEl, this.metrics, this.state, {
      onSearch: (term) => {
        this.state.searchTerm = term;
        this.loadData();
      },
      onStatusChange: (status) => {
        this.state.selectedStatus = status;
        this.loadData();
      },
      onSortChange: (sort) => {
        this.state.sortBy = sort;
        this.loadData();
      },
      onCreateOrder: () => {
        this.orderModal.openCreate(this.products, this.customers);
      },
    });
  }

  renderLoading() {
    this.tableMountEl.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <p class="empty-state-desc" style="font-size: 15px; color: var(--color-slate-600); font-weight: 500;">
          Loading orders...
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
        <h2 class="empty-state-title">Unable to load orders</h2>
        <p class="empty-state-desc">${this.error}</p>
        <button class="btn-primary" id="retryOrdersBtn" type="button" style="margin-top: 8px;">Retry</button>
      </div>
    `;

    const retryBtn = this.tableMountEl.querySelector('#retryOrdersBtn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.loadData();
      });
    }
  }

  renderContent() {
    if (this.isLoading || this.error) return;

    renderOrderTable(this.tableMountEl, this.orders, {
      onViewOrder: (order) => {
        this.orderModal.openView(order);
      },
      onCreateOrder: () => {
        this.orderModal.openCreate(this.products, this.customers);
      },
    });
  }

  async handleCreateOrder(orderData) {
    const created = await ordersApi.createOrder(orderData);
    await this.loadData();
    return created;
  }

  async handleStatusChange(orderId, targetStatus) {
    const updated = await ordersApi.updateOrderStatus(orderId, targetStatus);
    await this.loadData();
    return updated;
  }
}
