import { apiClient } from './apiClient.js';

/**
 * Categories API Client Module
 * Provides unified category management endpoints backed by FastAPI / PostgreSQL.
 */
export const categoriesApi = {
  /**
   * Retrieve all categories
   * @param {Object} params - Query parameters (e.g. { include_inactive: true/false })
   * @returns {Promise<Array>} List of CategoryResponse objects
   */
  getCategories(params = {}) {
    return apiClient.get('/api/categories', params);
  },

  /**
   * Retrieve a single category by ID
   * @param {string} categoryId - Unique Category UUID
   * @returns {Promise<Object>} CategoryResponse object
   */
  getCategory(categoryId) {
    return apiClient.get(`/api/categories/${categoryId}`);
  },

  /**
   * Create a new category
   * @param {Object} data - { name: string, description?: string }
   * @returns {Promise<Object>} Created CategoryResponse object
   */
  createCategory(data) {
    return apiClient.post('/api/categories', data);
  },

  /**
   * Partially update an existing category
   * @param {string} categoryId - Unique Category UUID
   * @param {Object} data - { name?: string, description?: string, is_active?: boolean }
   * @returns {Promise<Object>} Updated CategoryResponse object
   */
  updateCategory(categoryId, data) {
    return apiClient.patch(`/api/categories/${categoryId}`, data);
  },

  /**
   * Deactivate or delete a category
   * @param {string} categoryId - Unique Category UUID
   * @returns {Promise<null>}
   */
  deleteCategory(categoryId) {
    return apiClient.delete(`/api/categories/${categoryId}`);
  },
};
