/**
 * Main Application Orchestrator for Accessory Inventory
 * Handles Authentication state, Authorization (403 Access Denied), View Routing (Dashboard <-> Products <-> Sales <-> Orders <-> Categories), Sidebar & Header coordination.
 */

import { authClient } from './auth/authClient.js';
import { store } from './data.js';
import { renderSidebar } from './components/sidebar.js';
import { renderHeader } from './components/header.js';
import { LoginView } from './views/loginView.js';
import { UnauthorizedView } from './views/unauthorizedView.js';
import { DashboardView } from './views/dashboardView.js';
import { ProductsView } from './views/productsView.js';
import { SalesView } from './views/salesView.js';
import { OrdersView } from './views/ordersView.js';
import { CategoriesView } from './views/categoriesView.js';

export const AUTH_STATE = {
  LOADING: 'AUTHENTICATION_LOADING',
  AUTHENTICATED: 'AUTHENTICATED',
  UNAUTHENTICATED: 'UNAUTHENTICATED',
  UNAUTHORIZED: 'UNAUTHORIZED',
};

class InventoryApp {
  constructor() {
    this.authState = AUTH_STATE.LOADING;
    this.currentRoute = 'dashboard';
    this.isSidebarOpen = false;
    this.isShellInitialized = false;
  }

  async init() {
    this.cacheDom();
    this.initViews();
    this.bindEvents();

    // 1. Enter Loading State
    this.setAuthState(AUTH_STATE.LOADING);

    // 2. Initialize and verify persistent auth session
    const session = await authClient.init();

    if (session && session.access_token) {
      this.setAuthState(AUTH_STATE.AUTHENTICATED);
    } else {
      this.setAuthState(AUTH_STATE.UNAUTHENTICATED);
    }

    // 3. Listen for Supabase Auth state transitions
    authClient.onAuthStateChange((event, newSession) => {
      if (event === 'SIGNED_IN' || (event === 'TOKEN_REFRESHED' && newSession)) {
        this.setAuthState(AUTH_STATE.AUTHENTICATED);
      } else if (event === 'SIGNED_OUT' || !newSession) {
        this.setAuthState(AUTH_STATE.UNAUTHENTICATED);
      }
    });
  }

  cacheDom() {
    this.authLoadingMountEl = document.getElementById('authLoadingMount');
    this.loginMountEl = document.getElementById('loginMount');
    this.unauthorizedMountEl = document.getElementById('unauthorizedMount');
    this.appContainerEl = document.getElementById('appContainer');

    this.sidebarEl = document.getElementById('sidebar');
    this.sidebarBackdropEl = document.getElementById('sidebarBackdrop');
    this.topHeaderEl = document.getElementById('topHeader');
    this.dashboardViewEl = document.getElementById('dashboardView');
    this.productsViewEl = document.getElementById('productsView');
    this.salesViewEl = document.getElementById('salesView');
    this.ordersViewEl = document.getElementById('ordersView');
    this.categoriesViewEl = document.getElementById('categoriesView');
    this.modalContainerEl = document.getElementById('modalContainer');
  }

  initViews() {
    // 1. Login View
    this.loginView = new LoginView(this.loginMountEl, (session) => {
      this.setAuthState(AUTH_STATE.AUTHENTICATED);
    });

    // 2. Unauthorized View (403 Access Denied)
    this.unauthorizedView = new UnauthorizedView(this.unauthorizedMountEl, () => {
      this.setAuthState(AUTH_STATE.UNAUTHENTICATED);
    });

    // 3. Authenticated Views
    this.dashboardView = new DashboardView(this.dashboardViewEl, store, (targetRoute) => {
      this.navigateTo(targetRoute);
    });

    this.productsView = new ProductsView(this.productsViewEl, this.modalContainerEl, store);
    this.salesView = new SalesView(this.salesViewEl, this.modalContainerEl, store);
    this.ordersView = new OrdersView(this.ordersViewEl, this.modalContainerEl);
    this.categoriesView = new CategoriesView(this.categoriesViewEl, this.modalContainerEl);
  }

  initShell() {
    if (this.isShellInitialized) return;

    const dashboardData = store.getDashboardData();
    const user = authClient.getUser() || dashboardData.user;
    const displayName = user?.email?.split('@')[0] || user?.name || 'Admin';

    // 1. Render Sidebar with Logout handler
    this.sidebarController = renderSidebar(
      this.sidebarEl,
      dashboardData.navigation,
      (navId) => this.navigateTo(navId),
      () => this.handleLogout()
    );

    // 2. Render Header with Logout handler
    this.headerController = renderHeader(
      this.topHeaderEl,
      { name: displayName, notificationsCount: dashboardData.user.notificationsCount },
      () => this.toggleSidebar(),
      () => this.handleLogout()
    );

    this.isShellInitialized = true;
  }

  setAuthState(newState) {
    this.authState = newState;

    if (newState === AUTH_STATE.LOADING) {
      if (this.authLoadingMountEl) this.authLoadingMountEl.style.display = 'flex';
      if (this.loginMountEl) this.loginMountEl.style.display = 'none';
      if (this.unauthorizedMountEl) this.unauthorizedMountEl.style.display = 'none';
      if (this.appContainerEl) this.appContainerEl.style.display = 'none';
    } else if (newState === AUTH_STATE.UNAUTHENTICATED) {
      if (this.authLoadingMountEl) this.authLoadingMountEl.style.display = 'none';
      if (this.unauthorizedMountEl) this.unauthorizedMountEl.style.display = 'none';
      if (this.appContainerEl) this.appContainerEl.style.display = 'none';
      if (this.loginMountEl) {
        this.loginMountEl.style.display = 'block';
        this.loginView.render();
      }
    } else if (newState === AUTH_STATE.UNAUTHORIZED) {
      if (this.authLoadingMountEl) this.authLoadingMountEl.style.display = 'none';
      if (this.loginMountEl) this.loginMountEl.style.display = 'none';
      if (this.appContainerEl) this.appContainerEl.style.display = 'none';
      if (this.unauthorizedMountEl) {
        this.unauthorizedMountEl.style.display = 'block';
        this.unauthorizedView.render();
      }
    } else if (newState === AUTH_STATE.AUTHENTICATED) {
      if (this.authLoadingMountEl) this.authLoadingMountEl.style.display = 'none';
      if (this.loginMountEl) this.loginMountEl.style.display = 'none';
      if (this.unauthorizedMountEl) this.unauthorizedMountEl.style.display = 'none';
      if (this.appContainerEl) this.appContainerEl.style.display = 'flex';

      this.initShell();

      const user = authClient.getUser();
      if (user && this.headerController) {
        const displayName = user.email ? user.email.split('@')[0] : 'Admin';
        this.headerController.setUser(displayName);
      }

      this.handleInitialRoute();
    }
  }

  async handleLogout() {
    await authClient.signOut();
  }

  bindEvents() {
    // Backdrop click
    if (this.sidebarBackdropEl) {
      this.sidebarBackdropEl.addEventListener('click', () => {
        this.toggleSidebar(false);
      });
    }

    // Auto-close mobile drawer on desktop resize
    window.addEventListener('resize', () => {
      if (window.innerWidth > 768 && this.isSidebarOpen) {
        this.toggleSidebar(false);
      }
    });

    // Hashchange listener for direct URL navigation & browser history
    window.addEventListener('hashchange', () => {
      if (this.authState !== AUTH_STATE.AUTHENTICATED) return;
      const rawHash = window.location.hash.replace('#', '') || 'dashboard';
      const routeName = rawHash.split('?')[0];
      this.routeTo(routeName);
    });
  }

  handleInitialRoute() {
    const rawHash = window.location.hash.replace('#', '') || 'dashboard';
    const routeName = rawHash.split('?')[0];
    this.routeTo(routeName);
  }

  navigateTo(routeId) {
    window.location.hash = routeId;
  }

  routeTo(routeId) {
    if (this.authState !== AUTH_STATE.AUTHENTICATED) return;

    const cleanRoute = (routeId || 'dashboard').split('?')[0];
    this.currentRoute = cleanRoute;
    this.toggleSidebar(false);

    if (cleanRoute === 'categories') {
      if (this.sidebarController) this.sidebarController.setActive('categories');
      if (this.headerController) this.headerController.setTitle('Categories');
      this.dashboardView.hide();
      this.productsView.hide();
      this.salesView.hide();
      this.ordersView.hide();
      this.categoriesView.render();
    } else if (cleanRoute === 'orders') {
      if (this.sidebarController) this.sidebarController.setActive('orders');
      if (this.headerController) this.headerController.setTitle('Orders');
      this.dashboardView.hide();
      this.productsView.hide();
      this.salesView.hide();
      this.categoriesView.hide();
      this.ordersView.render();
    } else if (cleanRoute === 'sales') {
      if (this.sidebarController) this.sidebarController.setActive('sales');
      if (this.headerController) this.headerController.setTitle('Sales');
      this.dashboardView.hide();
      this.productsView.hide();
      this.ordersView.hide();
      this.categoriesView.hide();
      this.salesView.render();
    } else if (cleanRoute === 'products') {
      if (this.sidebarController) this.sidebarController.setActive('products');
      if (this.headerController) this.headerController.setTitle('Products');
      this.dashboardView.hide();
      this.salesView.hide();
      this.ordersView.hide();
      this.categoriesView.hide();
      this.productsView.render();
    } else {
      // Default to Dashboard
      if (this.sidebarController) this.sidebarController.setActive('dashboard');
      if (this.headerController) this.headerController.setTitle('Dashboard');
      this.productsView.hide();
      this.salesView.hide();
      this.ordersView.hide();
      this.categoriesView.hide();
      this.dashboardView.render();
    }
  }

  toggleSidebar(forceState) {
    this.isSidebarOpen = typeof forceState === 'boolean' ? forceState : !this.isSidebarOpen;
    if (this.sidebarEl) {
      this.sidebarEl.classList.toggle('open', this.isSidebarOpen);
    }
    if (this.sidebarBackdropEl) {
      this.sidebarBackdropEl.classList.toggle('open', this.isSidebarOpen);
    }
  }
}

// Bootstrap Application
document.addEventListener('DOMContentLoaded', () => {
  const app = new InventoryApp();
  app.init();
  window.__APP__ = app;
});
