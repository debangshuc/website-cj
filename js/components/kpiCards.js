import { icons } from '../icons.js';

/**
 * Render KPI Cards Component
 * @param {HTMLElement} container - DOM container element
 * @param {Array} kpiMetrics - Array of metric card data objects
 */
export function renderKpiCards(container, kpiMetrics = []) {
  if (!container) return;

  const iconMap = {
    products: icons.kpiProducts,
    stock: icons.kpiStock,
    revenue: icons.kpiRevenue,
    orders: icons.kpiOrders
  };

  const cardsHtml = kpiMetrics.map(item => {
    const iconSvg = iconMap[item.iconType] || icons.dashboard;
    
    let subtextHtml = '';
    if (item.trendType === 'up') {
      subtextHtml = `
        <span class="trend-indicator trend-up">
          ${icons.arrowUp}
          <span class="kpi-trend">${item.trend.split(' ')[0]}</span>
        </span>
        <span class="kpi-label">${item.trend.substring(item.trend.indexOf(' ') + 1)}</span>
      `;
    } else if (item.trendType === 'down') {
      subtextHtml = `
        <span class="trend-indicator trend-down">
          <span class="kpi-trend">${item.trend.split(' ')[0]}</span>
        </span>
        <span class="kpi-label">${item.trend.substring(item.trend.indexOf(' ') + 1)}</span>
      `;
    } else {
      subtextHtml = `
        <span class="kpi-label">${item.trend}</span>
      `;
    }

    return `
      <div class="card kpi-card">
        <div class="kpi-top">
          <span class="kpi-title">${item.title}</span>
          <div class="kpi-icon-badge ${item.iconBg}">
            ${iconSvg}
          </div>
        </div>
        <div class="kpi-value">${item.value}</div>
        <div class="kpi-subtext">
          ${subtextHtml}
        </div>
      </div>
    `;
  }).join('');

  container.innerHTML = cardsHtml;
}
