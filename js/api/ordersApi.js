import { apiClient } from './apiClient.js';

/**
 * Orders API Client Module
 * Provides unified customer order endpoints backed by FastAPI / PostgreSQL.
 */
export const ordersApi = {
  /**
   * Retrieve all orders with optional search and filters
   * @param {Object} params - Query parameters (search, status, date_filter, sort_by)
   * @returns {Promise<Array>} List of OrderResponse objects
   */
  getOrders(params = {}) {
    return apiClient.get('/api/orders', params);
  },

  /**
   * Retrieve aggregated order summary KPI metrics
   * @returns {Promise<Object>} OrderMetricsResponse
   */
  getOrderMetrics() {
    return apiClient.get('/api/orders/metrics');
  },

  /**
   * Retrieve a single order by ID or order_number
   * @param {string} orderId - Unique Order UUID or Order Number
   * @returns {Promise<Object>} OrderResponse object
   */
  getOrder(orderId) {
    return apiClient.get(`/api/orders/${orderId}`);
  },

  /**
   * Create a new customer order (in pending status)
   * @param {Object} data - { customer_name, customer_email, notes, items: [{ product_id, quantity }] }
   * @returns {Promise<Object>} Created OrderResponse object
   */
  createOrder(data) {
    return apiClient.post('/api/orders', data);
  },

  /**
   * Transition order lifecycle status
   * @param {string} orderId - Unique Order UUID or Order Number
   * @param {string} status - Target status (confirmed, completed, cancelled)
   * @returns {Promise<Object>} Updated OrderResponse object
   */
  updateOrderStatus(orderId, status) {
    return apiClient.patch(`/api/orders/${orderId}/status`, { status });
  },
};
