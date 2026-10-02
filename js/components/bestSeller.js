import { icons } from '../icons.js';

/**
 * Render Best Selling Product Component
 * @param {HTMLElement} container - DOM container element
 * @param {Object} bestSellerData - Data for the top selling product
 * @param {Function} onViewAll - Callback for "View all products"
 */
export function renderBestSeller(container, bestSellerData, onViewAll) {
  if (!container) return;

  const {
    title = 'Best Selling Product',
    name = 'Anime Poster Collection',
    category = 'Poster',
    unitsSold = 0,
    revenue = '₹0',
    imageUrl = 'assets/images/placeholder-poster-main.svg',
    imageAlt = 'Product Poster'
  } = bestSellerData || {};

  container.innerHTML = `
    <div class="card best-seller-card">
      <div class="card-header">
        <h2 class="card-title">${title}</h2>
      </div>

      <div class="card-body">
        <div class="best-seller-content">
          <div class="best-seller-image-wrapper">
            <img src="${imageUrl}" alt="${imageAlt}" loading="lazy" />
          </div>

          <div class="best-seller-details">
            <h3 class="best-seller-title">${name}</h3>
            <div>
              <span class="badge badge-poster">${category}</span>
            </div>
            
            <div class="best-seller-stat-label">Units Sold</div>
            <div class="best-seller-stat-value">${unitsSold}</div>

            <div class="best-seller-stat-label">Revenue</div>
            <div class="best-seller-revenue-value">${revenue}</div>
          </div>
        </div>

        <a href="#products" class="card-footer-link" id="viewAllProductsBtn">
          <span>View all products</span>
          ${icons.chevronRight}
        </a>
      </div>
    </div>
  `;

  const viewAllBtn = container.querySelector('#viewAllProductsBtn');
  if (viewAllBtn && typeof onViewAll === 'function') {
    viewAllBtn.addEventListener('click', (e) => {
      e.preventDefault();
      onViewAll();
    });
  }
}
