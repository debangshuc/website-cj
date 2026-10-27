import { renderKpiCards } from '../components/kpiCards.js';
import { dashboardApi } from '../api/dashboardApi.js';
import { icons } from '../icons.js';

/**
 * Reports View Controller
 * Displays revenue analytics for a selectable period via dashboardApi.getRevenueAnalytics.
 */

const PERIOD_OPTIONS = [
  { id: 'today', label: 'Today', comparisonLabel: 'Yesterday Revenue' },
  { id: 'week', label: 'This Week', comparisonLabel: 'Last Week Revenue' },
  { id: 'month', label: 'This Month', comparisonLabel: 'Last Month Revenue' }
];

const DEFAULT_PERIOD = 'week';

function formatRevenue(value) {
  return `₹${Number(value || 0).toLocaleString('en-IN')}`;
}

function formatDateLabel(rawDate) {
  if (!rawDate) return '—';
  const parsed = new Date(`${rawDate}T00:00:00`);
  if (isNaN(parsed.getTime())) return rawDate;
  return parsed.toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
}

export class ReportsView {
  constructor(container) {
    this.container = container;
    this.selectedPeriod = DEFAULT_PERIOD;
    this.analytics = null;
    this.isLoading = false;
    this.error = null;
    this.isInitialized = false;
  }

  init() {
    this.container.innerHTML = `
      <div class="reports-content-wrapper" id="reportsContentWrapper" style="width: 100%; display: flex; flex-direction: column; gap: var(--space-6);">
        <!-- Period Revenue Summary -->
        <section class="reports-summary-grid" id="reportsSummaryGrid" aria-label="Period revenue summary"></section>

        <!-- Daily Breakdown Table -->
        <section class="card" id="reportsDailyCard" aria-label="Daily revenue breakdown">
          <div class="card-header">
            <h2 class="card-title" id="reportsDailyTitle">Daily Breakdown</h2>
            <div class="reports-period-toggle" id="reportsPeriodToggle" role="group" aria-label="Report period"></div>
          </div>
          <div class="card-body" id="reportsDailyBodyMount"></div>
        </section>
      </div>

      <!-- Loading / Empty / Error Overlay Container -->
      <div id="reportsStatusContainer" style="display: none; width: 100%;"></div>
    `;

    this.contentWrapperEl = this.container.querySelector('#reportsContentWrapper');
    this.statusContainerEl = this.container.querySelector('#reportsStatusContainer');
    this.summaryGridEl = this.container.querySelector('#reportsSummaryGrid');
    this.periodToggleEl = this.container.querySelector('#reportsPeriodToggle');
    this.dailyBodyMountEl = this.container.querySelector('#reportsDailyBodyMount');

    this.isInitialized = true;
  }

  render() {
    if (!this.isInitialized) {
      this.init();
    }
    this.container.style.display = 'block';
    this.loadAnalytics();
  }

  hide() {
    this.container.style.display = 'none';
  }

  async loadAnalytics() {
    this.isLoading = true;
    this.error = null;
    this.renderLoading();

    try {
      this.analytics = await dashboardApi.getRevenueAnalytics(this.selectedPeriod);
      this.isLoading = false;
      this.renderData();
    } catch (err) {
      this.isLoading = false;
      if (err.status === 403 && window.__APP__) {
        window.__APP__.setAuthState('UNAUTHORIZED');
        return;
      }
      this.error = err.message || 'Unable to load revenue analytics.';
      this.renderError();
    }
  }

  renderPeriodToggle() {
    this.periodToggleEl.innerHTML = PERIOD_OPTIONS.map(option => `
      <button
        class="reports-period-btn${option.id === this.selectedPeriod ? ' active' : ''}"
        type="button"
        data-period="${option.id}"
      >${option.label}</button>
    `).join('');

    this.periodToggleEl.querySelectorAll('.reports-period-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const nextPeriod = btn.getAttribute('data-period');
        if (!nextPeriod || nextPeriod === this.selectedPeriod) return;
        this.selectedPeriod = nextPeriod;
        this.loadAnalytics();
      });
    });
  }

  renderLoading() {
    this.contentWrapperEl.style.display = 'none';
    this.statusContainerEl.style.display = 'block';
    this.statusContainerEl.innerHTML = `
      <div class="card" style="padding: 48px 24px; text-align: center; width: 100%;">
        <p class="empty-state-desc" style="font-size: 15px; color: var(--color-slate-600); font-weight: 500;">
          Loading reports...
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
        <h2 class="empty-state-title">Unable to load reports</h2>
        <p class="empty-state-desc">${this.error}</p>
        <button class="btn-primary" id="retryReportsBtn" type="button" style="margin-top: 8px;">Retry</button>
      </div>
    `;

    const retryBtn = this.statusContainerEl.querySelector('#retryReportsBtn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.loadAnalytics();
      });
    }
  }

  renderData() {
    this.statusContainerEl.style.display = 'none';
    this.contentWrapperEl.style.display = 'flex';

    this.renderPeriodToggle();
    this.renderSummary();
    this.renderDailyBreakdown();
  }

  renderSummary() {
    const analytics = this.analytics || {};
    const totalRevenue = Number(analytics.total_revenue || 0);
    const previousRevenue = Number(analytics.previous_period_revenue || 0);
    const points = analytics.points || [];
    const ordersInPeriod = points.reduce((sum, pt) => sum + Number(pt.orderCount || 0), 0);

    const currentOption = PERIOD_OPTIONS.find(o => o.id === this.selectedPeriod) || PERIOD_OPTIONS[DEFAULT_PERIOD];
    const comparisonLabel = currentOption.comparisonLabel;

    let comparisonTrend = 'No change vs previous period';
    let comparisonTrendType = 'neutral';
    if (previousRevenue > 0) {
      const deltaPercent = Math.round(((totalRevenue - previousRevenue) / previousRevenue) * 100);
      if (deltaPercent > 0) {
        comparisonTrend = `${deltaPercent}% vs previous period`;
        comparisonTrendType = 'up';
      } else if (deltaPercent < 0) {
        comparisonTrend = `${Math.abs(deltaPercent)}% vs previous period`;
        comparisonTrendType = 'down';
      } else {
        comparisonTrend = 'Same as previous period';
      }
    }

    renderKpiCards(this.summaryGridEl, [
      {
        id: 'period-revenue',
        title: `${currentOption.label} Revenue`,
        value: formatRevenue(totalRevenue),
        trend: `${ordersInPeriod} orders in period`,
        trendType: totalRevenue > 0 ? 'up' : 'neutral',
        iconType: 'revenue',
        iconBg: 'kpi-icon-green'
      },
      {
        id: 'previous-period-revenue',
        title: comparisonLabel,
        value: formatRevenue(previousRevenue),
        trend: comparisonTrend,
        trendType: comparisonTrendType,
        iconType: 'revenue',
        iconBg: 'kpi-icon-gray'
      },
      {
        id: 'period-orders',
        title: 'Orders',
        value: ordersInPeriod.toLocaleString('en-IN'),
        trend: 'Completed transactions',
        trendType: ordersInPeriod > 0 ? 'up' : 'neutral',
        iconType: 'orders',
        iconBg: 'kpi-icon-blue'
      }
    ]);
  }

  renderDailyBreakdown() {
    const points = (this.analytics && this.analytics.points) || [];

    if (points.length === 0) {
      this.dailyBodyMountEl.innerHTML = `
        <div class="empty-state-card" style="padding: 36px 24px; text-align: center;">
          <div class="empty-state-icon">${icons.emptyBox}</div>
          <h2 class="empty-state-title">No revenue data</h2>
          <p class="empty-state-desc">No revenue has been recorded for this period yet. Choose a different period to compare.</p>
        </div>
      `;
      return;
    }

    this.dailyBodyMountEl.innerHTML = `
      <div class="table-responsive">
        <table class="sales-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Day</th>
              <th>Revenue</th>
              <th>Orders</th>
            </tr>
          </thead>
          <tbody>
            ${points.map(pt => `
              <tr>
                <td class="sales-date">${formatDateLabel(pt.date)}</td>
                <td class="product-name">${pt.day || '—'}</td>
                <td class="sales-amount">${pt.formatted || formatRevenue(pt.value)}</td>
                <td>${Number(pt.orderCount || 0).toLocaleString('en-IN')}</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>
    `;
  }
}
