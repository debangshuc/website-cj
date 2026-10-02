/**
 * Render Pagination Component
 * @param {HTMLElement} container - DOM container
 * @param {Object} paginationState - { currentPage, pageSize, totalItems, itemLabel }
 * @param {Function} onPageChange - Page change callback
 */
export function renderPagination(container, paginationState, onPageChange) {
  if (!container) return;

  const { currentPage = 1, pageSize = 8, totalItems = 0, itemLabel = 'products' } = paginationState || {};
  const totalPages = Math.ceil(totalItems / pageSize) || 1;

  if (totalItems === 0) {
    container.innerHTML = '';
    return;
  }

  const startItem = (currentPage - 1) * pageSize + 1;
  const endItem = Math.min(currentPage * pageSize, totalItems);

  let pageButtonsHtml = '';
  for (let i = 1; i <= totalPages; i++) {
    pageButtonsHtml += `
      <button class="page-btn ${i === currentPage ? 'active' : ''}" data-page="${i}" type="button">
        ${i}
      </button>
    `;
  }

  container.innerHTML = `
    <div class="pagination-container">
      <div class="pagination-info">
        Showing <strong>${startItem}–${endItem}</strong> of <strong>${totalItems}</strong> ${itemLabel}
      </div>
      <div class="pagination-controls">
        <button class="page-btn" id="prevPageBtn" ${currentPage <= 1 ? 'disabled' : ''} type="button">
          Previous
        </button>
        ${pageButtonsHtml}
        <button class="page-btn" id="nextPageBtn" ${currentPage >= totalPages ? 'disabled' : ''} type="button">
          Next
        </button>
      </div>
    </div>
  `;

  // Attach event listeners
  const pageBtns = container.querySelectorAll('.page-btn[data-page]');
  pageBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const page = parseInt(btn.getAttribute('data-page'), 10);
      if (page !== currentPage && typeof onPageChange === 'function') {
        onPageChange(page);
      }
    });
  });

  const prevBtn = container.querySelector('#prevPageBtn');
  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1 && typeof onPageChange === 'function') {
        onPageChange(currentPage - 1);
      }
    });
  }

  const nextBtn = container.querySelector('#nextPageBtn');
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (currentPage < totalPages && typeof onPageChange === 'function') {
        onPageChange(currentPage + 1);
      }
    });
  }
}
