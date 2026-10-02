import { icons } from '../icons.js';
import { renderSalesSummary } from '../components/salesSummary.js';
import { renderSalesControls } from '../components/salesControls.js';
import { renderSalesTable } from '../components/salesTable.js';
import { renderPagination } from '../components/pagination.js';
import { RecordSaleModal } from '../components/saleModal.js';
import { salesApi } from '../api/salesApi.js';
import { categoriesApi } from '../api/categoriesApi.js';

/**
 * Sales View Controller
 * Connected directly to the FastAPI / Supabase backend via salesApi and categoriesApi.
 */
export class SalesView {
  constructor(container, modalMountContainer, store) {
    this.container = container;
    this.modalMountContainer = modalMountContainer;
    this.store = store; // Preserved for shared compatibility during migration

    this.sales = [];
    this.categories = [];
    this.summaryMetrics = {
      todayRevenue: '₹0',
      todaySales: 0,
      unitsSoldToday: 0,
      avgTransactionValue: '₹0',
    };
    this.isLoading = false;
    this.error = null;

    this.state = {
      searchTerm: '',
      dateFilter: 'all',
      categoryFilter: 'all',
      sortBy: 'newest',
      currentPage: 1,
      pageSize: 8,
      categories: []
    };

    this.isInitialized = false;
  }

  init() {
    this.container.innerHTML = `
      <div class="sales-view">
        <!-- Sales KPI Summary Cards -->
        <div id="salesSummaryMount"></div>

        <!-- Controls Bar -->
        <div id="salesControlsMount"></div>

        <!-- Sales Table Card -->
        <div class="card sales-table-card" id="salesTableCard">
          <div id="salesTableMount"></div>
          <div id="salesPaginationMount"></div>
        </div>
      </div>
    `;

    this.summaryMountEl = this.container.querySelector('#salesSummaryMount');
    this.controlsMountEl = this.container.querySelector('#salesControlsMount');
    this.tableCardEl = this.container.querySelector('#salesTableCard');
    this.tableMountEl = this.container.querySelector('#salesTableMount');
    this.paginationMountEl = this.container.querySelector('#salesPaginationMount');

    // Initialize Record Sale Modal with API submission handler
    this.saleModal = new RecordSaleModal(
      this.modalMountContainer.querySelector('#saleModalMount'),
      (saleData) => this.handleRecordSale(saleData)
    );

    this.isInitialized = true;
  }

  render() {
    if (!this.isInitialized) {
      this.init();
    }

    this.container.style.display = 'block';
    this.loadData();

    // Direct hash query support for modal testing
    if (window.location.hash.includes('modal=sale')) {
      this.saleModal.open();
    }
  }

  hide() {
    this.container.style.display = 'none';
  }

  async loadData() {
    this.isLoading = true;
    this.error = null;
    this.renderLoading();

    try {
      const [salesData, summaryData, categoriesData] = await Promise.all([
        salesApi.getSales({
          search: this.state.searchTerm,
          category: this.state.categoryFilter,
          date_filter: this.state.dateFilter,
          sort_by: this.state.sortBy,
        }),
        salesApi.getSummaryMetrics(),
        categoriesApi.getCategories().catch(() => []),
      ]);

      this.sales = salesData;
      this.summaryMetrics = summaryData;
      this.categories = categoriesData;
      this.isLoading = false;

      this.renderSummary();
      this.renderControls();
      this.renderContent();
    } catch (err) {
      this.isLoading = false;
      if (err.status === 403 && window.__APP__) {
        window.__APP__.setAuthState('UNAUTHORIZED');
        return;
      }
      this.error = err.message || 'Unable to load sales data.';
      this.renderError();
    }
  }

  renderSummary() {
    renderSalesSummary(this.summaryMountEl, this.summaryMetrics);
  }

  renderControls() {
    renderSalesControls(this.controlsMountEl, { ...this.state, categories: this.categories }, {
      onSearch: (term) => {
        this.state.searchTerm = term;
        this.state.currentPage = 1;
        this.loadData();
      },
      onDateChange: (dateRange) => {
        this.state.dateFilter = dateRange;
        this.state.currentPage = 1;
        this.loadData();
      },
      onCategoryChange: (category) => {
        this.state.categoryFilter = category;
        this.state.currentPage = 1;
        this.loadData();
      },
      onSortChange: (sortBy) => {
        this.state.sortBy = sortBy;
        this.loadData();
      },
      onRecordSale: () => {
        this.saleModal.open();
      }
    });
  }

  renderLoading() {
    this.tableMountEl.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <p class="empty-state-desc" style="font-size: 15px; color: var(--color-slate-600); font-weight: 500;">
          Loading sales...
        </p>
      </div>
    `;
    this.paginationMountEl.innerHTML = '';
  }

  renderError() {
    this.tableMountEl.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <div class="empty-state-icon" style="color: var(--color-danger, #ef4444);">
          ${icons.alertCircle || icons.emptyBox}
        </div>
        <h2 class="empty-state-title">Unable to load sales</h2>
        <p class="empty-state-desc">${this.error}</p>
        <button class="btn-primary" id="retrySalesBtn" type="button" style="margin-top: 8px;">Retry</button>
      </div>
    `;
    this.paginationMountEl.innerHTML = '';

    const retryBtn = this.tableMountEl.querySelector('#retrySalesBtn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.loadData();
      });
    }
  }

  renderContent() {
    if (this.isLoading || this.error) return;

    const totalItems = this.sales.length;

    // Handle Empty State
    if (totalItems === 0) {
      this.tableMountEl.innerHTML = `
        <div class="empty-state-card">
          <div class="empty-state-icon">
            ${icons.emptyBox}
          </div>
          <h2 class="empty-state-title">No sales found</h2>
          <p class="empty-state-desc">Try changing or resetting your search term and date/category filters.</p>
          <button class="btn-secondary" id="resetSalesFiltersBtn" type="button">Reset Filters</button>
        </div>
      `;
      this.paginationMountEl.innerHTML = '';

      const resetBtn = this.tableMountEl.querySelector('#resetSalesFiltersBtn');
      if (resetBtn) {
        resetBtn.addEventListener('click', () => {
          this.state.searchTerm = '';
          this.state.dateFilter = 'all';
          this.state.categoryFilter = 'all';
          this.state.sortBy = 'newest';
          this.state.currentPage = 1;
          this.renderControls();
          this.loadData();
        });
      }
      return;
    }

    // Pagination
    const totalPages = Math.ceil(totalItems / this.state.pageSize) || 1;
    if (this.state.currentPage > totalPages) {
      this.state.currentPage = totalPages;
    }

    const startIndex = (this.state.currentPage - 1) * this.state.pageSize;
    const paginatedSales = this.sales.slice(startIndex, startIndex + this.state.pageSize);

    renderSalesTable(this.tableMountEl, paginatedSales);

    renderPagination(this.paginationMountEl, {
      currentPage: this.state.currentPage,
      pageSize: this.state.pageSize,
      totalItems,
      itemLabel: 'transactions'
    }, (newPage) => {
      this.state.currentPage = newPage;
      this.renderContent();
    });
  }

  async handleRecordSale(saleData) {
    // Submit transaction directly to backend API
    await salesApi.recordSale(saleData);
    // Reload live sales & KPI metrics
    await this.loadData();
  }
}
