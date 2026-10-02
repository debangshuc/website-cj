import { apiClient } from './apiClient.js';

/**
 * Dashboard API Module
 * Provides access to live overview summary metrics and time-series analytics aggregated by FastAPI & PostgreSQL.
 */
export const dashboardApi = {
  /**
   * Fetch dashboard summary containing KPIs, recent sales, best sellers, low-stock items, and revenue analytics.
   * @param {string} period - 'today', 'week', 'month'
   */
  async getDashboardSummary(period = 'week') {
    const summary = await apiClient.get('/api/dashboard/summary', { period });
    return {
      total_products: Number(summary.total_products || 0),
      total_stock: Number(summary.total_stock || 0),
      today_revenue: Number(summary.today_revenue || 0),
      today_sales: Number(summary.today_sales || 0),
      units_sold_today: Number(summary.units_sold_today || 0),
      best_selling_product: summary.best_selling_product || null,
      recent_sales: summary.recent_sales || [],
      low_stock_products: summary.low_stock_products || [],
      revenue_overview: summary.revenue_overview ? {
        period: summary.revenue_overview.period,
        total_revenue: Number(summary.revenue_overview.total_revenue || 0),
        previous_period_revenue: Number(summary.revenue_overview.previous_period_revenue || 0),
        points: (summary.revenue_overview.points || []).map(pt => ({
          date: pt.date,
          day: pt.day,
          value: Number(pt.revenue || 0),
          formatted: `₹${Number(pt.revenue || 0).toLocaleString('en-IN')}`,
          orderCount: Number(pt.order_count || 0),
        }))
      } : null,
    };
  },

  /**
   * Fetch historical daily revenue time-series analytics for a specified interval.
   * @param {string} period - 'today', 'week', 'month'
   */
  async getRevenueAnalytics(period = 'week') {
    const data = await apiClient.get('/api/dashboard/revenue', { period });
    return {
      period: data.period,
      total_revenue: Number(data.total_revenue || 0),
      previous_period_revenue: Number(data.previous_period_revenue || 0),
      points: (data.points || []).map(pt => ({
        date: pt.date,
        day: pt.day,
        value: Number(pt.revenue || 0),
        formatted: `₹${Number(pt.revenue || 0).toLocaleString('en-IN')}`,
        orderCount: Number(pt.order_count || 0),
      }))
    };
  }
};
