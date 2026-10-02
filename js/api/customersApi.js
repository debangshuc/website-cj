import { apiClient } from './apiClient.js';

/**
 * Customers API Client Module
 * Provides CRM customer operations backed by FastAPI / PostgreSQL.
 */
export const customersApi = {
  /**
   * Retrieve list of customers with optional search and filters
   * @param {Object} params - { search, status, sort_by, page, page_size }
   * @returns {Promise<Array>} List of CustomerResponse objects
   */
  getCustomers(params = {}) {
    return apiClient.get('/api/customers', params);
  },

  /**
   * Retrieve aggregated customer summary KPI metrics
   * @returns {Promise<Object>} CustomerMetricsResponse
   */
  getCustomerMetrics() {
    return apiClient.get('/api/customers/metrics');
  },

  /**
   * Retrieve detailed customer profile including associated recent orders
   * @param {string} customerId - Customer UUID
   * @returns {Promise<Object>} CustomerDetailResponse
   */
  getCustomer(customerId) {
    return apiClient.get(`/api/customers/${customerId}`);
  },

  /**
   * Register a new customer
   * @param {Object} data - { name, email, phone, address, notes }
   * @returns {Promise<Object>} Created CustomerResponse
   */
  createCustomer(data) {
    return apiClient.post('/api/customers', data);
  },

  /**
   * Update customer profile or active/inactive status (soft-delete)
   * @param {string} customerId - Customer UUID
   * @param {Object} data - { name, email, phone, address, notes, is_active }
   * @returns {Promise<Object>} Updated CustomerResponse
   */
  updateCustomer(customerId, data) {
    return apiClient.patch(`/api/customers/${customerId}`, data);
  },
};
