import { icons } from '../icons.js';
import { renderProductControls } from '../components/productControls.js';
import { renderProductTable } from '../components/productTable.js';
import { renderPagination } from '../components/pagination.js';
import { ProductModal } from '../components/productModal.js';
import { DeleteProductModal } from '../components/deleteProductModal.js';
import { productsApi } from '../api/productsApi.js';
import { categoriesApi } from '../api/categoriesApi.js';

/**
 * Products View Controller
 * Connected directly to the FastAPI / Supabase backend via productsApi and categoriesApi.
 */
export class ProductsView {
  constructor(container, modalMountContainer, store) {
    this.container = container;
    this.modalMountContainer = modalMountContainer;
    this.store = store; // Preserved for shared compatibility during migration

    // Product & Category state
    this.products = [];
    this.categories = [];
    this.isLoading = false;
    this.error = null;

    // Filter, sort, and pagination state
    this.state = {
      searchTerm: '',
      selectedCategory: 'all',
      selectedStock: 'all',
      sortBy: 'recent',
      currentPage: 1,
      pageSize: 8,
      categories: []
    };

    this.isInitialized = false;
  }

  init() {
    this.container.innerHTML = `
      <div class="products-view">
        <!-- Controls Bar Mount -->
        <div id="productControlsMount"></div>

        <!-- Table / Empty State Card -->
        <div class="card products-table-card" id="productsTableCard">
          <div id="productTableMount"></div>
          <div id="paginationMount"></div>
        </div>
      </div>
    `;

    this.controlsMountEl = this.container.querySelector('#productControlsMount');
    this.tableCardEl = this.container.querySelector('#productsTableCard');
    this.tableMountEl = this.container.querySelector('#productTableMount');
    this.paginationMountEl = this.container.querySelector('#paginationMount');

    // Initialize Add/Edit & Delete Modals
    this.productModal = new ProductModal(
      this.modalMountContainer.querySelector('#productModalMount'),
      (savedProduct, isEdit, selectedImageFile, removeImage) => 
        this.handleSaveProduct(savedProduct, isEdit, selectedImageFile, removeImage)
    );

    this.deleteModal = new DeleteProductModal(
      this.modalMountContainer.querySelector('#deleteModalMount'),
      (productId) => this.handleDeleteProduct(productId)
    );

    this.isInitialized = true;
  }

  render() {
    if (!this.isInitialized) {
      this.init();
    }

    this.container.style.display = 'block';
    this.loadData();

    // Check if modal parameter is in URL for testing / direct link
    if (window.location.hash.includes('modal=add')) {
      this.productModal.openAdd(this.categories);
    }
  }

  hide() {
    this.container.style.display = 'none';
  }

  renderControls() {
    renderProductControls(this.controlsMountEl, { ...this.state, categories: this.categories }, {
      onSearch: (term) => {
        this.state.searchTerm = term;
        this.state.currentPage = 1;
        this.loadProducts();
      },
      onCategoryChange: (category) => {
        this.state.selectedCategory = category;
        this.state.currentPage = 1;
        this.loadProducts();
      },
      onStockChange: (stock) => {
        this.state.selectedStock = stock;
        this.state.currentPage = 1;
        this.loadProducts();
      },
      onSortChange: (sortBy) => {
        this.state.sortBy = sortBy;
        this.renderContent();
      },
      onAddProduct: () => {
        this.productModal.openAdd(this.categories);
      }
    });
  }

  async loadData() {
    try {
      const cats = await categoriesApi.getCategories();
      this.categories = cats;
    } catch (err) {
      console.warn('Unable to load categories list:', err);
    }
    this.renderControls();
    this.loadProducts();
  }

  async loadProducts() {
    this.isLoading = true;
    this.error = null;
    this.renderLoading();

    try {
      const data = await productsApi.getProducts({
        search: this.state.searchTerm,
        category: this.state.selectedCategory,
        stock_status: this.state.selectedStock,
      });
      this.products = data;
      this.isLoading = false;
      this.renderContent();
    } catch (err) {
      this.isLoading = false;
      if (err.status === 403 && window.__APP__) {
        window.__APP__.setAuthState('UNAUTHORIZED');
        return;
      }
      this.error = err.message || 'Unable to load products from server.';
      this.renderError();
    }
  }

  renderLoading() {
    this.tableMountEl.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <p class="empty-state-desc" style="font-size: 15px; color: var(--color-slate-600); font-weight: 500;">
          Loading products...
        </p>
      </div>
    `;
    this.paginationMountEl.innerHTML = '';
  }

  renderError() {
    this.tableMountEl.innerHTML = `
      <div class="empty-state-card" style="padding: 48px 24px;">
        <div class="empty-state-icon" style="color: var(--color-danger, #ef4444);">
          ${icons.alertCircle || icons.emptyBox}
        </div>
        <h2 class="empty-state-title">Unable to load products</h2>
        <p class="empty-state-desc">${this.error}</p>
        <button class="btn-primary" id="retryProductsBtn" type="button" style="margin-top: 8px;">Retry</button>
      </div>
    `;
    this.paginationMountEl.innerHTML = '';

    const retryBtn = this.tableMountEl.querySelector('#retryProductsBtn');
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        this.loadProducts();
      });
    }
  }

  getSortedProducts() {
    const result = [...this.products];

    // Client-side sort on filtered results
    switch (this.state.sortBy) {
      case 'name_asc':
        result.sort((a, b) => a.name.localeCompare(b.name));
        break;
      case 'price_asc':
        result.sort((a, b) => a.price - b.price);
        break;
      case 'price_desc':
        result.sort((a, b) => b.price - a.price);
        break;
      case 'stock_asc':
        result.sort((a, b) => a.stock - b.stock);
        break;
      case 'stock_desc':
        result.sort((a, b) => b.stock - a.stock);
        break;
      case 'bestseller':
        result.sort((a, b) => (b.unitsSold || 0) - (a.unitsSold || 0));
        break;
      case 'recent':
      default:
        result.sort((a, b) => new Date(b.createdAt || b.created_at || 0) - new Date(a.createdAt || a.created_at || 0));
        break;
    }

    return result;
  }

  renderContent() {
    if (this.isLoading || this.error) return;

    const sortedProducts = this.getSortedProducts();
    const totalItems = sortedProducts.length;

    // Handle Empty State
    if (totalItems === 0) {
      this.tableMountEl.innerHTML = `
        <div class="empty-state-card">
          <div class="empty-state-icon">
            ${icons.emptyBox}
          </div>
          <h2 class="empty-state-title">No products found</h2>
          <p class="empty-state-desc">Try changing or resetting your search term and filter criteria.</p>
          <button class="btn-secondary" id="resetFiltersBtn" type="button">Reset Filters</button>
        </div>
      `;
      this.paginationMountEl.innerHTML = '';

      const resetBtn = this.tableMountEl.querySelector('#resetFiltersBtn');
      if (resetBtn) {
        resetBtn.addEventListener('click', () => {
          this.state.searchTerm = '';
          this.state.selectedCategory = 'all';
          this.state.selectedStock = 'all';
          this.state.sortBy = 'recent';
          this.state.currentPage = 1;
          this.renderControls();
          this.loadProducts();
        });
      }
      return;
    }

    // Pagination slice
    const totalPages = Math.ceil(totalItems / this.state.pageSize) || 1;
    if (this.state.currentPage > totalPages) {
      this.state.currentPage = totalPages;
    }

    const startIndex = (this.state.currentPage - 1) * this.state.pageSize;
    const paginatedProducts = sortedProducts.slice(startIndex, startIndex + this.state.pageSize);

    // Render Table
    renderProductTable(this.tableMountEl, paginatedProducts, {
      onEdit: (productId) => {
        const product = this.products.find(p => p.id === productId);
        if (product) this.productModal.openEdit(product, this.categories);
      },
      onDelete: (productId) => {
        const product = this.products.find(p => p.id === productId);
        if (product) this.deleteModal.open(product);
      }
    });

    // Render Pagination
    renderPagination(this.paginationMountEl, {
      currentPage: this.state.currentPage,
      pageSize: this.state.pageSize,
      totalItems
    }, (newPage) => {
      this.state.currentPage = newPage;
      this.renderContent();
    });
  }

  async handleSaveProduct(product, isEdit, selectedImageFile, removeImage) {
    try {
      let savedResult;
      const payload = {
        name: product.name,
        sku: product.sku,
        category_id: product.category_id,
        category: product.category,
        price: product.price,
        stock: product.stock,
        description: product.description,
      };

      if (isEdit) {
        savedResult = await productsApi.updateProduct(product.id, payload);
      } else {
        savedResult = await productsApi.createProduct(payload);
      }

      // Handle image upload if a file was selected
      if (selectedImageFile && savedResult && savedResult.id) {
        await productsApi.uploadProductImage(savedResult.id, selectedImageFile);
      } else if (removeImage && isEdit && product.id) {
        await productsApi.deleteProductImage(product.id);
      }

      await this.loadProducts();
    } catch (err) {
      alert(`Error saving product: ${err.message}`);
      await this.loadProducts();
    }
  }

  async handleDeleteProduct(productId) {
    try {
      await productsApi.deleteProduct(productId);
      await this.loadProducts();
    } catch (err) {
      alert(`Error deleting product: ${err.message}`);
    }
  }
}
