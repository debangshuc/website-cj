import { icons } from '../icons.js';

/**
 * Render Revenue Overview & Line Chart Component
 * Data-driven, responsive SVG rendering with tooltips and Y-axis scaling.
 * 
 * @param {HTMLElement} container - DOM container element
 * @param {Object} revenueData - Dataset containing title, points, summary, timeRange
 * @param {Function} onTimeRangeChange - Optional callback for time-range dropdown
 */
export function renderRevenueOverview(container, revenueData, onTimeRangeChange) {
  if (!container) return;

  const {
    title = 'Revenue Overview',
    timeRange = 'This Week',
    thisWeekRevenue = '₹0',
    lastWeekRevenue = '₹0',
    points = []
  } = revenueData || {};

  container.innerHTML = `
    <div class="card revenue-card">
      <div class="card-header">
        <h2 class="card-title">${title}</h2>
        <button class="time-dropdown" id="timeRangeBtn" type="button">
          <span>${timeRange}</span>
          ${icons.chevronDown}
        </button>
      </div>

      <div class="card-body">
        <div class="chart-container" id="chartSvgWrapper">
          <div class="chart-tooltip" id="chartTooltip"></div>
        </div>

        <div class="revenue-summary-row">
          <div class="summary-col">
            <div class="summary-label">This Week Revenue</div>
            <div class="summary-value">${thisWeekRevenue}</div>
          </div>
          <div class="summary-col">
            <div class="summary-label">Last Week Revenue</div>
            <div class="summary-value">${lastWeekRevenue}</div>
          </div>
        </div>
      </div>
    </div>
  `;

  const chartWrapper = container.querySelector('#chartSvgWrapper');
  const tooltip = container.querySelector('#chartTooltip');

  function drawChart() {
    if (!chartWrapper || points.length === 0) return;

    const width = 720;
    const height = 200;
    const padding = { top: 16, right: 24, bottom: 28, left: 65 };

    const chartWidth = width - padding.left - padding.right;
    const chartHeight = height - padding.top - padding.bottom;

    // Calculate dynamic Y domain
    const values = points.map(p => p.value);
    const maxVal = Math.max(...values, 20000);
    const minVal = 0;
    const yMaxCeil = Math.ceil(maxVal / 5000) * 5000;

    // Y Axis step ticks
    const tickCount = 4;
    const tickStep = yMaxCeil / tickCount;
    const yTicks = [];
    for (let i = 0; i <= tickCount; i++) {
      yTicks.push(i * tickStep);
    }

    // Y coordinate mapping
    const getY = (val) => {
      const ratio = (val - minVal) / (yMaxCeil - minVal);
      return padding.top + chartHeight - (ratio * chartHeight);
    };

    // X coordinate mapping
    const getX = (index) => {
      if (points.length === 1) return padding.left + chartWidth / 2;
      return padding.left + (index / (points.length - 1)) * chartWidth;
    };

    // Generate grid lines and Y-axis text
    let gridLinesSvg = '';
    yTicks.forEach(tick => {
      const y = getY(tick);
      const formattedLabel = `₹${tick.toLocaleString('en-IN')}`;
      gridLinesSvg += `
        <line x1="${padding.left}" y1="${y}" x2="${width - padding.right}" y2="${y}" class="chart-grid-line" stroke="#f1f5f9" stroke-width="1" />
        <text x="${padding.left - 12}" y="${y + 4}" text-anchor="end" class="chart-axis-text">${formattedLabel}</text>
      `;
    });

    // Generate X-axis labels & points
    let xAxisSvg = '';
    const pointsCoords = [];

    points.forEach((pt, index) => {
      const x = getX(index);
      const y = getY(pt.value);
      pointsCoords.push({ x, y, pt });

      xAxisSvg += `
        <text x="${x}" y="${height - 4}" text-anchor="middle" class="chart-axis-text">${pt.day}</text>
      `;
    });

    // Generate Polyline path
    const pathString = pointsCoords.map((coord, i) => `${i === 0 ? 'M' : 'L'} ${coord.x} ${coord.y}`).join(' ');

    // Generate Data dots
    let dotsSvg = '';
    pointsCoords.forEach((coord) => {
      dotsSvg += `
        <circle 
          cx="${coord.x}" 
          cy="${coord.y}" 
          r="4" 
          class="chart-dot" 
          data-day="${coord.pt.day}" 
          data-value="${coord.pt.formatted || ('₹' + coord.pt.value.toLocaleString('en-IN'))}"
          data-cx="${coord.x}"
          data-cy="${coord.y}"
        />
      `;
    });

    const svgHtml = `
      <svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" class="chart-svg">
        <g class="chart-grid">
          ${gridLinesSvg}
        </g>
        <path d="${pathString}" class="chart-line" />
        <g class="chart-dots">
          ${dotsSvg}
        </g>
        <g class="chart-x-axis">
          ${xAxisSvg}
        </g>
      </svg>
    `;

    const existingSvg = chartWrapper.querySelector('svg');
    if (existingSvg) existingSvg.remove();
    
    chartWrapper.insertAdjacentHTML('afterbegin', svgHtml);

    // Interactive tooltip
    const dots = chartWrapper.querySelectorAll('.chart-dot');
    dots.forEach(dot => {
      dot.addEventListener('mouseenter', () => {
        const day = dot.getAttribute('data-day');
        const val = dot.getAttribute('data-value');
        const cx = parseFloat(dot.getAttribute('data-cx'));
        const cy = parseFloat(dot.getAttribute('data-cy'));

        const leftPercent = (cx / width) * 100;
        const topPercent = (cy / height) * 100;

        tooltip.textContent = `${day}: ${val}`;
        tooltip.style.left = `${leftPercent}%`;
        tooltip.style.top = `${topPercent}%`;
        tooltip.classList.add('visible');
      });

      dot.addEventListener('mouseleave', () => {
        tooltip.classList.remove('visible');
      });
    });
  }

  drawChart();

  const timeBtn = container.querySelector('#timeRangeBtn');
  if (timeBtn && typeof onTimeRangeChange === 'function') {
    timeBtn.addEventListener('click', onTimeRangeChange);
  }
}
