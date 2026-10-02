import { apiClient } from './apiClient.js';
import { dashboardApi } from './dashboardApi.js';

/**
 * Sales API Module
 * Provides methods for interacting with FastAPI /api/sales endpoints.
 */
export const salesApi = {
  /**
   * Fetch sales transactions with filters and sorting.
   */
  async getSales(params = {}) {
    const queryParams = {};
    if (params.search && params.search.trim()) {
      queryParams.search = params.search.trim();
    }
    if (params.category && params.category !== 'all') {
      queryParams.category = params.category;
    }
    if (params.date_filter && params.date_filter !== 'all') {
      queryParams.date_filter = params.date_filter;
    }
    if (params.sort_by && params.sort_by !== 'newest') {
      queryParams.sort_by = params.sort_by;
    }

    const rawSales = await apiClient.get('/api/sales', queryParams);

    // Normalize properties for UI table rendering
    return (rawSales || []).map(s => {
      const soldAtDate = s.sold_at ? new Date(s.sold_at) : new Date();
      const dateStr = soldAtDate.toLocaleDateString('en-IN', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
      });
      const timeStr = soldAtDate.toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      });

      return {
        ...s,
        productName: s.product_name,
        unitPrice: Number(s.unit_price),
        total: Number(s.total),
        date: dateStr,
        time: timeStr,
        rawDate: soldAtDate.toISOString().split('T')[0],
      };
    });
  },

  /**
   * Fetch single sale transaction by ID.
   */
  async getSale(id) {
    const s = await apiClient.get(`/api/sales/${id}`);
    if (!s) return null;
    const soldAtDate = s.sold_at ? new Date(s.sold_at) : new Date();
    return {
      ...s,
      productName: s.product_name,
      unitPrice: Number(s.unit_price),
      total: Number(s.total),
      date: soldAtDate.toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' }),
      time: soldAtDate.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', hour12: true }),
      rawDate: soldAtDate.toISOString().split('T')[0],
    };
  },

  /**
   * Record a new sale transaction.
   * Total is calculated and verified server-side by PostgreSQL.
   */
  async recordSale(data) {
    let soldAt = undefined;
    if (data.date && data.time) {
      soldAt = new Date(`${data.date}T${data.time}:00`).toISOString();
    } else if (data.sold_at) {
      soldAt = data.sold_at;
    }

    const payload = {
      product_id: data.productId || data.product_id,
      quantity: Number(data.quantity),
      unit_price: Number(data.unitPrice ?? data.unit_price),
    };
    if (soldAt) {
      payload.sold_at = soldAt;
    }

    return apiClient.post('/api/sales', payload);
  },

  /**
   * Fetch summary KPI metrics from canonical dashboardApi.
   */
  async getSummaryMetrics() {
    const summary = await dashboardApi.getDashboardSummary();
    const todayRevenue = summary.today_revenue;
    const todaySales = summary.today_sales;
    const unitsSoldToday = summary.units_sold_today;
    const avgVal = todaySales > 0 ? Math.round(todayRevenue / todaySales) : 0;

    return {
      todayRevenue: `₹${todayRevenue.toLocaleString('en-IN')}`,
      todaySales,
      unitsSoldToday,
      avgTransactionValue: `₹${avgVal.toLocaleString('en-IN')}`,
    };
  },
};
