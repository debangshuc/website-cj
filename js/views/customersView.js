import { icons } from '../icons.js';
import { customersApi } from '../api/customersApi.js';
import { renderCustomerControls } from '../components/customerControls.js';
import { renderCustomerTable } from '../components/customerTable.js';
import { CustomerModal } from '../components/customerModal.js';

/**
 * Customers View Controller
 * Connected directly to FastAPI / PostgreSQL via customersApi.
 */
export class CustomersView {
  constructor(container, modalMountContainer) {
    this.container = container;
    this.modalMountContainer = modalMountContainer;

    this.customers = [];
    this.metrics = {};
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
      <div class="products-content-wrapper" id="customersContentWrapper" style="width: 100%; display: flex; flex-direction: column; gap: var(--space-4, 16px);">
        <!-- Customers Controls Mount -->
        <div id="customersControlsMount"></div>

        <!-- Customers Table Card -->
        <div class="card" id="customersTableCard">
          <div id="customersTableMount"></div>
        </div>
      </div>
    `;

    this.controlsMountEl = this.container.querySelector('#customersControlsMount');
    this.tableMountEl = this.container.querySelector('#customersTableMount');

    // Initialize Customer Modal
    let modalMount = this.modalMountContainer.querySelector('#customerModalMount');
    if (!modalMount) {
      modalMount = document.createElement('div');
      modalMount.id = 'customerModalMount';
      this.modalMountContainer.appendChild(modalMount);
    }

    this.customerModal = new CustomerModal(
      modalMount,
      (mode, customerId, data) => this.handleSaveCustomer(mode, customerId, data),
      (customerId, isActive) => this.handleStatusToggle(customerId, isActive)
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
      const [customersData, metricsData] = await Promise.all([
        customersApi.getCustomers({
          search: this.state.searchTerm,
          status: this.state.selectedStatus,
          sort_by: this.state.sortBy,
        }),
        customersApi.getCustomerMetrics().catch(() => ({})),
      ]);

      this.customers = customersData;
      this.metrics = metricsData;
      this.isLoading = false;

      this.renderControls();
      this.renderContent();
    } catch (err) {
      this.isLoading = false;
      if (err.status === 403 && window.__APP__) {
        window.__APP__.setAuthState('UNAUTHORIZED');
        return;
      }
      this.error = err.message || 'Unable to load customer records.';
      this.renderError();
    }
  }

  renderControls() {
    renderCustomerControls(this.controlsMountEl, this.metrics, this.state, {
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
      onAddCustomer: () => {
        this.customerModal.openAdd();
      },
    });
  }

  renderLoading() {
    this.tableMountEl.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <p class="empty-state-desc" style="font-size: 15px; color: var(--color-slate-600); font-weight: 500;">
          Loading customers...
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
        <h2 class="empty-state-title">Unable to load customers</h2>
        <p class="empty-state-desc">${this.error}</p>
        <button class="btn-primary" id="retryCustomersBtn" type="button" style="margin-top: 8px;">Retry</button>
      </div>
    `;

    const retryBtn = this.tableMountEl.querySelector('#retryCustomersBtn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.loadData();
      });
    }
  }

  renderContent() {
    if (this.isLoading || this.error) return;

    renderCustomerTable(this.tableMountEl, this.customers, {
      onViewCustomer: async (customerId) => {
        try {
          const detail = await customersApi.getCustomer(customerId);
          this.customerModal.openView(detail);
        } catch (err) {
          alert(`Failed to load customer profile: ${err.message}`);
        }
      },
      onEditCustomer: (customer) => {
        this.customerModal.openEdit(customer);
      },
      onAddCustomer: () => {
        this.customerModal.openAdd();
      },
    });
  }

  async handleSaveCustomer(mode, customerId, data) {
    if (mode === 'add') {
      await customersApi.createCustomer(data);
    } else {
      await customersApi.updateCustomer(customerId, data);
    }
    await this.loadData();
  }

  async handleStatusToggle(customerId, isActive) {
    await customersApi.updateCustomer(customerId, { is_active: isActive });
    await this.loadData();
  }
}
