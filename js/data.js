/**
 * Unified In-Memory Reactive Store for Accessory Inventory
 * Manages Products, Sales Ledger, and Dashboard State.
 * Fully decoupled and ready for FastAPI / PostgreSQL replacement.
 */

// Helper to format ISO dates relative to current date
function getRelativeDate(daysAgo = 0) {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function getFormattedDate(daysAgo = 0) {
  const d = new Date();
  d.setDate(d.getDate() - daysAgo);
  return d.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });
}

export function getCategoryBadgeClass(category) {
  const cat = (category || '').toLowerCase();
  if (cat === 'poster') return 'badge-poster';
  if (cat === 'keychain') return 'badge-keychain';
  if (cat === 'sticker') return 'badge-sticker';
  if (cat === 'accessory') return 'badge-accessory';
  return 'badge-keychain';
}

export function getProductStatus(stock) {
  if (stock <= 0) {
    return { label: 'Out of Stock', type: 'out-of-stock', className: 'status-out' };
  }
  if (stock <= 10) {
    return { label: `${stock} left`, type: 'low-stock', className: 'status-low' };
  }
  return { label: 'In Stock', type: 'in-stock', className: 'status-in' };
}

export const initialNavigation = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', active: true },
  { id: 'products', label: 'Products', icon: 'products', active: false },
  { id: 'sales', label: 'Sales', icon: 'sales', active: false },
  { id: 'orders', label: 'Orders', icon: 'orders', active: false },
  { id: 'categories', label: 'Categories', icon: 'categories', active: false },
  { id: 'customers', label: 'Customers', icon: 'customers', active: false },
  { id: 'reports', label: 'Reports', icon: 'reports', active: false },
  { id: 'settings', label: 'Settings', icon: 'settings', active: false }
];

export const initialUser = {
  name: 'Admin',
  notificationsCount: 3,
  role: 'Store Manager'
};

const initialProducts = [
  {
    id: 'PRD-101',
    name: 'Anime Poster Collection',
    sku: 'PST-ANM-001',
    category: 'Poster',
    price: 250,
    stock: 45,
    unitsSold: 126,
    imageUrl: 'assets/images/placeholder-poster-main.svg',
    description: 'Set of 6 high-definition aesthetic anime wall art posters with matte lamination.',
    createdAt: getRelativeDate(14)
  },
  {
    id: 'PRD-102',
    name: 'Sunset Landscape Poster',
    sku: 'PST-SNT-002',
    category: 'Poster',
    price: 250,
    stock: 18,
    unitsSold: 42,
    imageUrl: 'assets/images/placeholder-wave.svg',
    description: 'Vibrant sunset landscape artwork printed on 300 GSM thick premium art paper.',
    createdAt: getRelativeDate(12)
  },
  {
    id: 'PRD-103',
    name: 'Vintage Car Poster',
    sku: 'PST-VTC-003',
    category: 'Poster',
    price: 220,
    stock: 5,
    unitsSold: 89,
    imageUrl: 'assets/images/placeholder-car.svg',
    description: 'Classic vintage retro automobile illustration poster with distressed grunge border.',
    createdAt: getRelativeDate(16)
  },
  {
    id: 'PRD-104',
    name: 'Minimal Wave Poster',
    sku: 'PST-MWV-004',
    category: 'Poster',
    price: 200,
    stock: 8,
    unitsSold: 64,
    imageUrl: 'assets/images/placeholder-wave.svg',
    description: 'Japanese inspired minimalist ocean wave decorative wall print.',
    createdAt: getRelativeDate(10)
  },
  {
    id: 'PRD-105',
    name: 'Black Dragon Keychain',
    sku: 'KCH-BDG-001',
    category: 'Keychain',
    price: 150,
    stock: 3,
    unitsSold: 95,
    imageUrl: 'assets/images/placeholder-keychain.svg',
    description: 'Solid zinc alloy black matte dragon charm keychain with reinforced ring.',
    createdAt: getRelativeDate(20)
  },
  {
    id: 'PRD-106',
    name: 'Aesthetic Keychain',
    sku: 'KCH-AST-002',
    category: 'Keychain',
    price: 180,
    stock: 24,
    unitsSold: 110,
    imageUrl: 'assets/images/placeholder-keychain.svg',
    description: 'Double-sided acrylic aesthetic pastel keychain for bags, keys, and backpacks.',
    createdAt: getRelativeDate(8)
  },
  {
    id: 'PRD-107',
    name: 'Minimalist Keychain',
    sku: 'KCH-MNM-003',
    category: 'Keychain',
    price: 160,
    stock: 0,
    unitsSold: 78,
    imageUrl: 'assets/images/placeholder-keychain.svg',
    description: 'Ultra-light aerospace titanium finish minimalist carabiner keychain.',
    createdAt: getRelativeDate(22)
  },
  {
    id: 'PRD-108',
    name: 'Space Explorer Stickers',
    sku: 'STK-SPC-001',
    category: 'Sticker',
    price: 120,
    stock: 7,
    unitsSold: 154,
    imageUrl: 'assets/images/placeholder-space.svg',
    description: 'Pack of 15 waterproof vinyl stickers featuring planets, astronauts, and rockets.',
    createdAt: getRelativeDate(6)
  },
  {
    id: 'PRD-109',
    name: 'Cute Stickers Pack',
    sku: 'STK-CTE-002',
    category: 'Sticker',
    price: 120,
    stock: 32,
    unitsSold: 180,
    imageUrl: 'assets/images/placeholder-space.svg',
    description: '25 assorted cute kawaii animal die-cut stickers for laptops and phone cases.',
    createdAt: getRelativeDate(4)
  },
  {
    id: 'PRD-110',
    name: 'BTS Photo Card Set',
    sku: 'ACC-BTS-001',
    category: 'Accessory',
    price: 200,
    stock: 15,
    unitsSold: 98,
    imageUrl: 'assets/images/placeholder-poster-main.svg',
    description: '55-piece glossy LOMO collectible photo cards set in a protective presentation box.',
    createdAt: getRelativeDate(9)
  },
  {
    id: 'PRD-111',
    name: 'Retro Game Sticker Pack',
    sku: 'STK-RGM-003',
    category: 'Sticker',
    price: 140,
    stock: 0,
    unitsSold: 67,
    imageUrl: 'assets/images/placeholder-space.svg',
    description: '8-bit retro arcade gaming pixel vinyl decals with UV resistance.',
    createdAt: getRelativeDate(25)
  },
  {
    id: 'PRD-112',
    name: 'Custom Name Keychain',
    sku: 'KCH-CST-004',
    category: 'Keychain',
    price: 220,
    stock: 12,
    unitsSold: 53,
    imageUrl: 'assets/images/placeholder-keychain.svg',
    description: 'Personalized laser-engraved acrylic block keychain with metallic lobster clasp.',
    createdAt: getRelativeDate(3)
  }
];

const initialSales = [
  {
    id: 'SALE-1048',
    productId: 'PRD-106',
    productName: 'Aesthetic Keychain',
    category: 'Keychain',
    quantity: 2,
    unitPrice: 180,
    total: 360,
    date: getFormattedDate(0),
    rawDate: getRelativeDate(0),
    time: '18:42'
  },
  {
    id: 'SALE-1047',
    productId: 'PRD-102',
    productName: 'Sunset Landscape Poster',
    category: 'Poster',
    quantity: 1,
    unitPrice: 250,
    total: 250,
    date: getFormattedDate(0),
    rawDate: getRelativeDate(0),
    time: '17:15'
  },
  {
    id: 'SALE-1046',
    productId: 'PRD-109',
    productName: 'Cute Stickers Pack',
    category: 'Sticker',
    quantity: 3,
    unitPrice: 120,
    total: 360,
    date: getFormattedDate(0),
    rawDate: getRelativeDate(0),
    time: '15:30'
  },
  {
    id: 'SALE-1045',
    productId: 'PRD-110',
    productName: 'BTS Photo Card Set',
    category: 'Accessory',
    quantity: 1,
    unitPrice: 200,
    total: 200,
    date: getFormattedDate(0),
    rawDate: getRelativeDate(0),
    time: '14:05'
  },
  {
    id: 'SALE-1044',
    productId: 'PRD-101',
    productName: 'Anime Poster Collection',
    category: 'Poster',
    quantity: 2,
    unitPrice: 250,
    total: 500,
    date: getFormattedDate(0),
    rawDate: getRelativeDate(0),
    time: '11:20'
  },
  {
    id: 'SALE-1043',
    productId: 'PRD-107',
    productName: 'Minimalist Keychain',
    category: 'Keychain',
    quantity: 2,
    unitPrice: 160,
    total: 320,
    date: getFormattedDate(1),
    rawDate: getRelativeDate(1),
    time: '19:10'
  },
  {
    id: 'SALE-1042',
    productId: 'PRD-108',
    productName: 'Space Explorer Stickers',
    category: 'Sticker',
    quantity: 4,
    unitPrice: 120,
    total: 480,
    date: getFormattedDate(1),
    rawDate: getRelativeDate(1),
    time: '16:45'
  },
  {
    id: 'SALE-1041',
    productId: 'PRD-103',
    productName: 'Vintage Car Poster',
    category: 'Poster',
    quantity: 1,
    unitPrice: 220,
    total: 220,
    date: getFormattedDate(1),
    rawDate: getRelativeDate(1),
    time: '13:10'
  },
  {
    id: 'SALE-1040',
    productId: 'PRD-101',
    productName: 'Anime Poster Collection',
    category: 'Poster',
    quantity: 3,
    unitPrice: 250,
    total: 750,
    date: getFormattedDate(3),
    rawDate: getRelativeDate(3),
    time: '18:00'
  },
  {
    id: 'SALE-1039',
    productId: 'PRD-112',
    productName: 'Custom Name Keychain',
    category: 'Keychain',
    quantity: 2,
    unitPrice: 220,
    total: 440,
    date: getFormattedDate(4),
    rawDate: getRelativeDate(4),
    time: '15:25'
  },
  {
    id: 'SALE-1038',
    productId: 'PRD-104',
    productName: 'Minimal Wave Poster',
    category: 'Poster',
    quantity: 2,
    unitPrice: 200,
    total: 400,
    date: getFormattedDate(5),
    rawDate: getRelativeDate(5),
    time: '12:40'
  },
  {
    id: 'SALE-1037',
    productId: 'PRD-111',
    productName: 'Retro Game Sticker Pack',
    category: 'Sticker',
    quantity: 5,
    unitPrice: 140,
    total: 700,
    date: getFormattedDate(12),
    rawDate: getRelativeDate(12),
    time: '17:50'
  },
  {
    id: 'SALE-1036',
    productId: 'PRD-105',
    productName: 'Black Dragon Keychain',
    category: 'Keychain',
    quantity: 2,
    unitPrice: 150,
    total: 300,
    date: getFormattedDate(18),
    rawDate: getRelativeDate(18),
    time: '14:15'
  },
  {
    id: 'SALE-1035',
    productId: 'PRD-102',
    productName: 'Sunset Landscape Poster',
    category: 'Poster',
    quantity: 2,
    unitPrice: 250,
    total: 500,
    date: getFormattedDate(24),
    rawDate: getRelativeDate(24),
    time: '11:05'
  }
];

/**
 * Observable In-Memory Application Store
 */
class InventoryStore {
  constructor() {
    this.products = [...initialProducts];
    this.sales = [...initialSales];
    this.listeners = new Set();
  }

  subscribe(listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  notify(event = { type: 'CHANGE' }) {
    for (const listener of this.listeners) {
      try {
        listener(event, this);
      } catch (err) {
        console.error('Error in store listener:', err);
      }
    }
  }

  // --- Products API ---
  getProducts() {
    return [...this.products];
  }

  getProductById(id) {
    return this.products.find(p => p.id === id);
  }

  addProduct(product) {
    const newProduct = {
      ...product,
      id: product.id || `PRD-${Date.now().toString().slice(-4)}`,
      createdAt: product.createdAt || getRelativeDate(0),
      unitsSold: product.unitsSold || 0
    };
    this.products.unshift(newProduct);
    this.notify({ type: 'PRODUCT_ADDED', product: newProduct });
    return newProduct;
  }

  updateProduct(updatedProduct) {
    const idx = this.products.findIndex(p => p.id === updatedProduct.id);
    if (idx !== -1) {
      this.products[idx] = { ...this.products[idx], ...updatedProduct };
      this.notify({ type: 'PRODUCT_UPDATED', product: this.products[idx] });
      return this.products[idx];
    }
    return null;
  }

  deleteProduct(productId) {
    const idx = this.products.findIndex(p => p.id === productId);
    if (idx !== -1) {
      const deleted = this.products.splice(idx, 1)[0];
      this.notify({ type: 'PRODUCT_DELETED', productId });
      return deleted;
    }
    return null;
  }

  // --- Sales API ---
  getSales() {
    return [...this.sales];
  }

  recordSale({ productId, quantity, unitPrice, date, time }) {
    const product = this.getProductById(productId);
    if (!product) {
      return { success: false, error: 'Product not found.' };
    }

    const qty = parseInt(quantity, 10);
    if (isNaN(qty) || qty <= 0) {
      return { success: false, error: 'Please enter a valid quantity greater than 0.' };
    }

    if (qty > product.stock) {
      return { 
        success: false, 
        error: `Only ${product.stock} units are currently available in stock.` 
      };
    }

    const price = parseFloat(unitPrice);
    if (isNaN(price) || price < 0) {
      return { success: false, error: 'Please enter a valid unit price.' };
    }

    const total = qty * price;
    const rawDate = date || getRelativeDate(0);
    
    // Parse formatted display date
    const dObj = new Date(rawDate + 'T00:00:00');
    const formattedDate = isNaN(dObj.getTime()) 
      ? getFormattedDate(0) 
      : dObj.toLocaleDateString('en-GB', { day: 'numeric', month: 'short', year: 'numeric' });

    const formattedTime = time || new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false });

    // Deduct stock and increment unitsSold on authoritative product record
    product.stock -= qty;
    product.unitsSold = (product.unitsSold || 0) + qty;

    const newSale = {
      id: `SALE-${1000 + this.sales.length + 1}`,
      productId: product.id,
      productName: product.name,
      category: product.category,
      quantity: qty,
      unitPrice: price,
      total: total,
      date: formattedDate,
      rawDate: rawDate,
      time: formattedTime
    };

    this.sales.unshift(newSale);
    this.notify({ type: 'SALE_RECORDED', sale: newSale, product });
    return { success: true, sale: newSale };
  }

  // --- Sales Metrics Calculation ---
  getSalesSummaryMetrics() {
    const todayRaw = getRelativeDate(0);
    const todaySales = this.sales.filter(s => s.rawDate === todayRaw);

    const todayRevenue = todaySales.reduce((sum, s) => sum + s.total, 0);
    const todaySalesCount = todaySales.length;
    const unitsSoldToday = todaySales.reduce((sum, s) => sum + s.quantity, 0);
    const avgTransactionValue = todaySalesCount > 0 ? Math.round(todayRevenue / todaySalesCount) : 0;

    return {
      todayRevenue: `₹${todayRevenue.toLocaleString('en-IN')}`,
      todaySales: todaySalesCount,
      unitsSoldToday: unitsSoldToday,
      avgTransactionValue: `₹${avgTransactionValue.toLocaleString('en-IN')}`
    };
  }

  // --- Dashboard Data Provider ---
  getDashboardData() {
    return {
      user: initialUser,
      navigation: initialNavigation,
      kpiMetrics: [
        {
          id: 'total-products',
          title: 'Total Products',
          value: '245',
          trend: '12 new this week',
          trendType: 'up',
          iconType: 'products',
          iconBg: 'kpi-icon-blue'
        },
        {
          id: 'total-stock',
          title: 'Total Stock',
          value: '1,432',
          trend: 'Updated just now',
          trendType: 'neutral',
          iconType: 'stock',
          iconBg: 'kpi-icon-gray'
        },
        {
          id: 'today-revenue',
          title: "Today's Revenue",
          value: '₹12,450',
          trend: '18.6% vs yesterday',
          trendType: 'up',
          iconType: 'revenue',
          iconBg: 'kpi-icon-green'
        },
        {
          id: 'today-orders',
          title: "Today's Orders",
          value: '38',
          trend: '11.1% vs yesterday',
          trendType: 'up',
          iconType: 'orders',
          iconBg: 'kpi-icon-blue'
        }
      ],
      revenueOverview: {
        title: 'Revenue Overview',
        timeRange: 'This Week',
        thisWeekRevenue: '₹76,840',
        lastWeekRevenue: '₹64,210',
        yAxisMax: 20000,
        yAxisMin: 0,
        yAxisStep: 5000,
        points: [
          { day: 'Mon', value: 5500, formatted: '₹5,500' },
          { day: 'Tue', value: 8000, formatted: '₹8,000' },
          { day: 'Wed', value: 13500, formatted: '₹13,500' },
          { day: 'Thu', value: 11000, formatted: '₹11,000' },
          { day: 'Fri', value: 16000, formatted: '₹16,000' },
          { day: 'Sat', value: 10000, formatted: '₹10,000' },
          { day: 'Sun', value: 12000, formatted: '₹12,000' }
        ]
      },
      bestSeller: {
        title: 'Best Selling Product',
        name: 'Anime Poster Collection',
        category: 'Poster',
        unitsSold: 126,
        revenue: '₹6,300',
        imageUrl: 'assets/images/placeholder-poster-main.svg',
        imageAlt: 'Anime Poster Collection'
      },
      recentSales: [
        {
          id: '#ORD-1048',
          product: 'Aesthetic Keychain',
          category: 'Keychain',
          categoryClass: 'badge-keychain',
          qty: 2,
          amount: '₹180',
          date: '24 May, 2025'
        },
        {
          id: '#ORD-1047',
          product: 'Sunset Landscape Poster',
          category: 'Poster',
          categoryClass: 'badge-poster',
          qty: 1,
          amount: '₹250',
          date: '24 May, 2025'
        },
        {
          id: '#ORD-1046',
          product: 'Cute Stickers Pack',
          category: 'Sticker',
          categoryClass: 'badge-sticker',
          qty: 3,
          amount: '₹120',
          date: '24 May, 2025'
        },
        {
          id: '#ORD-1045',
          product: 'BTS Photo Card Set',
          category: 'Accessory',
          categoryClass: 'badge-accessory',
          qty: 1,
          amount: '₹200',
          date: '24 May, 2025'
        },
        {
          id: '#ORD-1044',
          product: 'Minimalist Keychain',
          category: 'Keychain',
          categoryClass: 'badge-keychain',
          qty: 2,
          amount: '₹160',
          date: '23 May, 2025'
        }
      ],
      lowStockProducts: [
        {
          id: 'ls-1',
          name: 'Black Dragon Keychain',
          category: 'Keychain',
          remaining: 3,
          imageUrl: 'assets/images/placeholder-keychain.svg',
          imageAlt: 'Black Dragon Keychain'
        },
        {
          id: 'ls-2',
          name: 'Vintage Car Poster',
          category: 'Poster',
          remaining: 5,
          imageUrl: 'assets/images/placeholder-car.svg',
          imageAlt: 'Vintage Car Poster'
        },
        {
          id: 'ls-3',
          name: 'Space Explorer Stickers',
          category: 'Sticker',
          remaining: 7,
          imageUrl: 'assets/images/placeholder-space.svg',
          imageAlt: 'Space Explorer Stickers'
        },
        {
          id: 'ls-4',
          name: 'Minimal Wave Poster',
          category: 'Poster',
          remaining: 8,
          imageUrl: 'assets/images/placeholder-wave.svg',
          imageAlt: 'Minimal Wave Poster'
        }
      ]
    };
  }
}

// Export singleton instance
export const store = new InventoryStore();
export const mockDashboardData = store.getDashboardData();
export const initialProductsData = store.getProducts();
