import { icons } from '../icons.js';
import { getCategoryBadgeClass, getProductStatus } from '../data.js';

/**
 * Render Product Table Component
 * @param {HTMLElement} container - DOM container
 * @param {Array} products - Paginated products list
 * @param {Object} callbacks - onEdit and onDelete handlers
 */
export function renderProductTable(container, products = [], callbacks = {}) {
  if (!container) return;

  const { onEdit, onDelete } = callbacks;

  const rowsHtml = products.map(product => {
    const status = getProductStatus(product.stock);
    const badgeClass = getCategoryBadgeClass(product.category);

    return `
      <tr data-product-id="${product.id}">
        <!-- Product (Thumb + Name + SKU) -->
        <td>
          <div class="product-cell">
            <div class="product-cell-thumb">
              <img src="${product.imageUrl || 'assets/images/placeholder-poster-main.svg'}" alt="${product.name}" onerror="this.onerror=null; this.src='assets/images/placeholder-poster-main.svg';" loading="lazy" />
            </div>
            <div class="product-cell-info">
              <span class="product-cell-name">${product.name}</span>
              <span class="product-cell-sku">${product.sku}</span>
            </div>
          </div>
        </td>

        <!-- Category Badge -->
        <td>
          <span class="badge ${badgeClass}">${product.category}</span>
        </td>

        <!-- Price -->
        <td class="product-price">
          ₹${Number(product.price).toLocaleString('en-IN')}
        </td>

        <!-- Stock -->
        <td class="product-stock-count">
          ${product.stock}
        </td>

        <!-- Units Sold -->
        <td class="product-units-sold">
          ${product.unitsSold || 0}
        </td>

        <!-- Status -->
        <td>
          <span class="status-pill ${status.className}">
            <span class="status-dot"></span>
            <span>${status.label}</span>
          </span>
        </td>

        <!-- Actions -->
        <td>
          <div class="action-buttons-group">
            <button class="action-btn action-btn-edit" data-id="${product.id}" title="Edit Product" type="button">
              ${icons.edit}
              <span>Edit</span>
            </button>
            <button class="action-btn action-btn-delete" data-id="${product.id}" title="Delete Product" type="button">
              ${icons.trash}
              <span>Delete</span>
            </button>
          </div>
        </td>
      </tr>
    `;
  }).join('');

  container.innerHTML = `
    <div class="products-table-wrapper">
      <table class="products-table">
        <thead>
          <tr>
            <th>Product</th>
            <th>Category</th>
            <th>Price</th>
            <th>Stock</th>
            <th>Units Sold</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${rowsHtml}
        </tbody>
      </table>
    </div>
  `;

  // Attach action button event listeners
  const editBtns = container.querySelectorAll('.action-btn-edit');
  editBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      if (typeof onEdit === 'function') onEdit(id);
    });
  });

  const deleteBtns = container.querySelectorAll('.action-btn-delete');
  deleteBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      if (typeof onDelete === 'function') onDelete(id);
    });
  });
}
