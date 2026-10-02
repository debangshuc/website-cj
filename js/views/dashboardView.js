import { renderKpiCards } from '../components/kpiCards.js';
import { renderRevenueOverview } from '../components/revenueChart.js';
import { renderBestSeller } from '../components/bestSeller.js';
import { renderRecentSalesTable } from '../components/recentSalesTable.js';
import { renderLowStock } from '../components/lowStock.js';
import { getCategoryBadgeClass } from '../data.js';
import { dashboardApi } from '../api/dashboardApi.js';
import { icons } from '../icons.js';

/**
 * Dashboard View Controller
 * Connected directly to FastAPI + Supabase PostgreSQL via dashboardApi.
 */
export class DashboardView {
  constructor(container, store, onNavigate) {
    this.container = container;
    this.store = store; // Preserved for compatibility
    this.onNavigate = onNavigate;
    this.selectedPeriod = 'week'; // 'today', 'week', 'month'
    this.isLoading = false;
    this.error = null;
    this.isInitialized = false;
  }

  init() {
    this.container.innerHTML = `
      <div class="dashboard-content-wrapper" id="dashboardContentWrapper" style="width: 100%; display: flex; flex-direction: column; gap: var(--space-6);">
        <!-- 4 Metric KPI Cards -->
        <section class="kpi-grid" id="kpiGrid" aria-label="Key Performance Indicators"></section>

        <!-- Middle Row: Revenue Overview + Best Selling Product -->
        <section class="dashboard-row" aria-label="Revenue and Best Selling Product">
          <div id="revenueOverviewContainer"></div>
          <div id="bestSellerContainer"></div>
        </section>

        <!-- Bottom Row: Recent Sales Table + Low Stock Products -->
        <section class="dashboard-row" aria-label="Recent Sales and Low Stock Products">
          <div id="recentSalesContainer"></div>
          <div id="lowStockContainer"></div>
        </section>
      </div>

      <!-- Loading / Error Overlay Container -->
      <div id="dashboardStatusContainer" style="display: none; width: 100%;"></div>
    `;

    this.contentWrapperEl = this.container.querySelector('#dashboardContentWrapper');
    this.statusContainerEl = this.container.querySelector('#dashboardStatusContainer');
    this.kpiGridEl = this.container.querySelector('#kpiGrid');
    this.revenueContainerEl = this.container.querySelector('#revenueOverviewContainer');
    this.bestSellerContainerEl = this.container.querySelector('#bestSellerContainer');
    this.recentSalesContainerEl = this.container.querySelector('#recentSalesContainer');
    this.lowStockContainerEl = this.container.querySelector('#lowStockContainer');

    this.isInitialized = true;
  }

  render() {
    if (!this.isInitialized) {
      this.init();
    }
    this.container.style.display = 'flex';
    this.loadDashboard();
  }

  hide() {
    this.container.style.display = 'none';
  }

  async loadDashboard() {
    this.isLoading = true;
    this.error = null;
    this.renderLoading();

    try {
      const summary = await dashboardApi.getDashboardSummary(this.selectedPeriod);
      this.isLoading = false;
      this.renderData(summary);
    } catch (err) {
      this.isLoading = false;
      if (err.status === 403 && window.__APP__) {
        window.__APP__.setAuthState('UNAUTHORIZED');
        return;
      }
      this.error = err.message || 'Unable to load dashboard summary.';
      this.renderError();
    }
  }

  renderLoading() {
    this.contentWrapperEl.style.display = 'none';
    this.statusContainerEl.style.display = 'block';
    this.statusContainerEl.innerHTML = `
      <div class="card" style="padding: 48px 24px; text-align: center; width: 100%;">
        <p class="empty-state-desc" style="font-size: 15px; color: var(--color-slate-600); font-weight: 500;">
          Loading dashboard...
        </p>
      </div>
    `;
  }

  renderError() {
    this.contentWrapperEl.style.display = 'none';
    this.statusContainerEl.style.display = 'block';
    this.statusContainerEl.innerHTML = `
      <div class="card empty-state-card" style="padding: 48px 24px; text-align: center; width: 100%;">
        <div class="empty-state-icon" style="color: var(--color-danger, #ef4444);">
          ${icons.alertCircle || icons.emptyBox}
        </div>
        <h2 class="empty-state-title">Unable to load dashboard</h2>
        <p class="empty-state-desc">${this.error}</p>
        <button class="btn-primary" id="retryDashboardBtn" type="button" style="margin-top: 8px;">Retry</button>
      </div>
    `;

    const retryBtn = this.statusContainerEl.querySelector('#retryDashboardBtn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.loadDashboard();
      });
    }
  }

  renderData(summary) {
    this.statusContainerEl.style.display = 'none';
    this.contentWrapperEl.style.display = 'flex';

    // 1. KPI Cards data mapping from backend summary
    const kpiMetrics = [
      {
        id: 'total-products',
        title: 'Total Products',
        value: Number(summary.total_products).toLocaleString('en-IN'),
        trend: 'Live active inventory',
        trendType: 'neutral',
        iconType: 'products',
        iconBg: 'kpi-icon-blue'
      },
      {
        id: 'total-stock',
        title: 'Total Stock',
        value: Number(summary.total_stock).toLocaleString('en-IN'),
        trend: 'Available physical units',
        trendType: 'neutral',
        iconType: 'stock',
        iconBg: 'kpi-icon-gray'
      },
      {
        id: 'today-revenue',
        title: "Today's Revenue",
        value: `₹${Number(summary.today_revenue).toLocaleString('en-IN')}`,
        trend: 'Gross sales today',
        trendType: summary.today_revenue > 0 ? 'up' : 'neutral',
        iconType: 'revenue',
        iconBg: 'kpi-icon-green'
      },
      {
        id: 'today-orders',
        title: "Today's Orders",
        value: Number(summary.today_sales).toLocaleString('en-IN'),
        trend: 'Completed transactions',
        trendType: summary.today_sales > 0 ? 'up' : 'neutral',
        iconType: 'orders',
        iconBg: 'kpi-icon-blue'
      }
    ];

    // 2. Revenue Overview mapping from PostgreSQL time-series analytics
    const revOverview = summary.revenue_overview || {
      period: this.selectedPeriod,
      total_revenue: summary.today_revenue,
      previous_period_revenue: 0,
      points: [{ day: 'Today', value: summary.today_revenue, formatted: `₹${summary.today_revenue.toLocaleString('en-IN')}` }]
    };

    let periodLabel = 'This Week';
    let compLabel = 'Last Week Revenue';
    if (this.selectedPeriod === 'today') {
      periodLabel = 'Today';
      compLabel = 'Yesterday Revenue';
    } else if (this.selectedPeriod === 'month') {
      periodLabel = 'This Month';
      compLabel = 'Last Month Revenue';
    }

    const revenueOverview = {
      title: 'Revenue Overview',
      timeRange: periodLabel,
      thisWeekRevenue: `₹${Number(revOverview.total_revenue).toLocaleString('en-IN')}`,
      lastWeekRevenue: `₹${Number(revOverview.previous_period_revenue).toLocaleString('en-IN')}`,
      points: revOverview.points && revOverview.points.length > 0 ? revOverview.points : [
        { day: 'Today', value: Number(summary.today_revenue), formatted: `₹${Number(summary.today_revenue).toLocaleString('en-IN')}` }
      ]
    };

    // 3. Best Selling Product mapping
    let bestSellerData;
    if (summary.best_selling_product && (summary.best_selling_product.units_sold > 0 || summary.total_products > 0)) {
      const p = summary.best_selling_product;
      const unitsSold = p.units_sold ?? 0;
      const revenue = Number(p.revenue || 0);
      bestSellerData = {
        title: 'Best Selling Product',
        name: p.name,
        category: p.category,
        unitsSold: unitsSold,
        revenue: `₹${revenue.toLocaleString('en-IN')}`,
        imageUrl: p.image_path || 'assets/images/placeholder-poster-main.svg',
        imageAlt: p.name
      };
    } else {
      bestSellerData = {
        title: 'Best Selling Product',
        name: 'No sales recorded yet',
        category: '—',
        unitsSold: 0,
        revenue: '₹0',
        imageUrl: 'assets/images/placeholder-poster-main.svg',
        imageAlt: 'No sales recorded yet'
      };
    }

    // 4. Recent Sales mapping
    const recentSalesData = (summary.recent_sales || []).map(s => {
      const soldAtDate = s.sold_at ? new Date(s.sold_at) : new Date();
      const dateStr = soldAtDate.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        year: 'numeric'
      });
      return {
        id: `#${s.id.slice(0, 8)}`,
        product: s.product_name,
        category: s.category,
        categoryClass: getCategoryBadgeClass(s.category),
        qty: s.quantity,
        amount: `₹${Number(s.total).toLocaleString('en-IN')}`,
        date: dateStr
      };
    });

    // 5. Low Stock Products mapping
    const lowStockData = (summary.low_stock_products || []).map(p => ({
      name: p.name,
      category: p.category,
      remaining: p.stock,
      imageUrl: p.image_path || 'assets/images/placeholder-poster-main.svg',
      imageAlt: p.name
    }));

    // Render components
    renderKpiCards(this.kpiGridEl, kpiMetrics);
    renderRevenueOverview(this.revenueContainerEl, revenueOverview, () => {
      // Cycle through periods: week -> month -> today -> week
      const nextPeriod = this.selectedPeriod === 'week' ? 'month' : (this.selectedPeriod === 'month' ? 'today' : 'week');
      this.selectedPeriod = nextPeriod;
      this.loadDashboard();
    });
    renderBestSeller(this.bestSellerContainerEl, bestSellerData, () => {
      if (typeof this.onNavigate === 'function') {
        this.onNavigate('products');
      }
    });
    renderRecentSalesTable(this.recentSalesContainerEl, recentSalesData, () => {
      if (typeof this.onNavigate === 'function') {
        this.onNavigate('sales');
      }
    });
    renderLowStock(this.lowStockContainerEl, lowStockData, () => {
      if (typeof this.onNavigate === 'function') {
        this.onNavigate('products');
      }
    });
  }
}
