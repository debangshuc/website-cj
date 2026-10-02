import { icons } from '../icons.js';

/**
 * Render Sales Summary KPI Cards
 * @param {HTMLElement} container - DOM mount container
 * @param {Object} summaryMetrics - { todayRevenue, todaySales, unitsSoldToday, avgTransactionValue }
 */
export function renderSalesSummary(container, summaryMetrics) {
  if (!container) return;

  const {
    todayRevenue = '₹0',
    todaySales = 0,
    unitsSoldToday = 0,
    avgTransactionValue = '₹0'
  } = summaryMetrics || {};

  const cards = [
    {
      title: "Today's Revenue",
      value: todayRevenue,
      subtext: "Gross revenue today",
      iconSvg: icons.kpiRevenue,
      iconBg: "kpi-icon-green"
    },
    {
      title: "Today's Sales",
      value: todaySales.toString(),
      subtext: "Completed transactions",
      iconSvg: icons.kpiOrders,
      iconBg: "kpi-icon-blue"
    },
    {
      title: "Units Sold Today",
      value: unitsSoldToday.toString(),
      subtext: "Physical items sold",
      iconSvg: icons.kpiProducts,
      iconBg: "kpi-icon-blue"
    },
    {
      title: "Average Transaction Value",
      value: avgTransactionValue,
      subtext: "Revenue / transactions",
      iconSvg: icons.kpiStock,
      iconBg: "kpi-icon-gray"
    }
  ];

  container.innerHTML = `
    <div class="sales-summary-grid">
      ${cards.map(card => `
        <div class="card kpi-card">
          <div class="kpi-top">
            <span class="kpi-title">${card.title}</span>
            <div class="kpi-icon-badge ${card.iconBg}">
              ${card.iconSvg}
            </div>
          </div>
          <div class="kpi-value">${card.value}</div>
          <div class="kpi-subtext">
            <span class="kpi-label">${card.subtext}</span>
          </div>
        </div>
      `).join('')}
    </div>
  `;
}
