import { apiClient } from './apiClient.js';

/**
 * Products API Module
 * Provides CRUD methods for communicating with FastAPI /api/products endpoints.
 */
export const productsApi = {
  /**
   * Fetch list of products with optional search, category, and stock_status filters.
   */
  async getProducts(params = {}) {
    const queryParams = {};
    if (params.search && params.search.trim()) {
      queryParams.search = params.search.trim();
    }
    if (params.category && params.category !== 'all') {
      queryParams.category = params.category;
    }
    if (params.stock_status && params.stock_status !== 'all') {
      queryParams.stock_status = params.stock_status;
    }
    if (params.include_inactive) {
      queryParams.include_inactive = true;
    }

    const rawList = await apiClient.get('/api/products', queryParams);
    
    // Normalize properties for UI component compatibility
    return (rawList || []).map(p => ({
      ...p,
      price: Number(p.price),
      unitsSold: p.units_sold ?? 0,
      imageUrl: p.image_path || 'assets/images/placeholder-poster-main.svg',
      createdAt: p.created_at || new Date().toISOString(),
    }));
  },

  /**
   * Retrieve a single product by ID.
   */
  async getProduct(id) {
    const p = await apiClient.get(`/api/products/${id}`);
    if (!p) return null;
    return {
      ...p,
      price: Number(p.price),
      unitsSold: p.units_sold ?? 0,
      imageUrl: p.image_path || 'assets/images/placeholder-poster-main.svg',
      createdAt: p.created_at || new Date().toISOString(),
    };
  },

  /**
   * Create a new product.
   */
  async createProduct(productData) {
    const payload = {
      name: productData.name,
      sku: productData.sku,
      category: productData.category,
      price: Number(productData.price),
      stock: Number(productData.stock),
      description: productData.description || null,
      image_path: productData.image_path || productData.imageUrl || null,
    };
    const created = await apiClient.post('/api/products', payload);
    return {
      ...created,
      price: Number(created.price),
      unitsSold: created.units_sold ?? 0,
      imageUrl: created.image_path || 'assets/images/placeholder-poster-main.svg',
      createdAt: created.created_at || new Date().toISOString(),
    };
  },

  /**
   * Update an existing product.
   */
  async updateProduct(id, updateData) {
    const payload = {};
    if (updateData.name !== undefined) payload.name = updateData.name;
    if (updateData.sku !== undefined) payload.sku = updateData.sku;
    if (updateData.category !== undefined) payload.category = updateData.category;
    if (updateData.price !== undefined) payload.price = Number(updateData.price);
    if (updateData.stock !== undefined) payload.stock = Number(updateData.stock);
    if (updateData.description !== undefined) payload.description = updateData.description;
    if (updateData.image_path !== undefined || updateData.imageUrl !== undefined) {
      payload.image_path = updateData.image_path || updateData.imageUrl;
    }

    const updated = await apiClient.patch(`/api/products/${id}`, payload);
    return {
      ...updated,
      price: Number(updated.price),
      unitsSold: updated.units_sold ?? 0,
      imageUrl: updated.image_path || 'assets/images/placeholder-poster-main.svg',
      createdAt: updated.created_at || new Date().toISOString(),
    };
  },

  /**
   * Upload an image file for a product.
   */
  async uploadProductImage(id, file) {
    const formData = new FormData();
    formData.append('file', file);
    const updated = await apiClient.post(`/api/products/${id}/image`, formData);
    return {
      ...updated,
      price: Number(updated.price),
      unitsSold: updated.units_sold ?? 0,
      imageUrl: updated.image_path || 'assets/images/placeholder-poster-main.svg',
      createdAt: updated.created_at || new Date().toISOString(),
    };
  },

  /**
   * Delete a product's image.
   */
  async deleteProductImage(id) {
    const updated = await apiClient.delete(`/api/products/${id}/image`);
    return {
      ...updated,
      price: Number(updated.price),
      unitsSold: updated.units_sold ?? 0,
      imageUrl: updated.image_path || 'assets/images/placeholder-poster-main.svg',
      createdAt: updated.created_at || new Date().toISOString(),
    };
  },

  /**
   * Soft-delete a product.
   */
  async deleteProduct(id) {
    return apiClient.delete(`/api/products/${id}`);
  },
};
