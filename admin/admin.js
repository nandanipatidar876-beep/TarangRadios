/**
 * Tarang Radios - Admin Panel Application Controller
 * Strict Separation: Normal Catalog vs "The Brands We Deal With"
 */

// Global State
const state = {
  token: localStorage.getItem('tarang_admin_token') || '',
  currentUser: null,
  currentTab: 'dashboard',
  
  // Normal Catalog (Uncoupled from brands)
  normalCategories: [],
  normalSubcategories: [],
  normalProducts: [],

  // "The Brands We Deal With"
  brands: [],
  activeBrandId: null,
  activeBrandHierarchy: null,

  // All Products for Price Management
  allProductsForPrice: [],

  // Offers & Promotions
  offers: [],

  // Bulk Uploads
  uploadedImagesMap: new Set(),
  parsedCsvProducts: [],
  selectedBulkImageFiles: []
};

// API Request Helper
async function apiRequest(endpoint, method = 'GET', data = null, isFormData = false) {
  const headers = {};
  if (state.token) {
    headers['Authorization'] = `Bearer ${state.token}`;
  }
  if (data && !isFormData) {
    headers['Content-Type'] = 'application/json';
  }

  const options = { method, headers };
  if (data) {
    options.body = isFormData ? data : JSON.stringify(data);
  }

  try {
    const res = await fetch(endpoint, options);
    const result = await res.json();
    if (!res.ok) {
      throw new Error(result.error || `HTTP Error ${res.status}`);
    }
    return result;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

// Image URL Formatter Helper
function formatImgUrl(url) {
  if (!url || typeof url !== 'string' || !url.trim()) return 'https://via.placeholder.com/60';
  const trimmed = url.trim();
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) return trimmed;
  if (trimmed.startsWith('/')) return trimmed;
  return `../${trimmed}`;
}

// Toast Notifications
function showToast(message, type = 'success') {
  const container = document.getElementById('toastContainer');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast-item ${type}`;
  toast.innerHTML = `
    <span>${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
    <div>${message}</div>
  `;
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// ---------------------------------------------------------------------------
// INITIALIZATION & AUTHENTICATION
// ---------------------------------------------------------------------------
document.addEventListener('DOMContentLoaded', async () => {
  if (window.lucide) window.lucide.createIcons();

  // Sidebar navigation
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
    btn.addEventListener('click', () => {
      const tab = btn.getAttribute('data-tab');
      switchTab(tab);
    });
  });

  // Mobile sidebar toggle
  const sidebarToggleBtn = document.getElementById('sidebarToggleBtn');
  const adminSidebar = document.getElementById('adminSidebar');
  if (sidebarToggleBtn && adminSidebar) {
    sidebarToggleBtn.addEventListener('click', () => {
      adminSidebar.classList.toggle('open');
    });
  }

  // Auth Forms
  const loginForm = document.getElementById('loginForm');
  if (loginForm) loginForm.addEventListener('submit', handleLoginSubmit);

  const logoutBtn = document.getElementById('logoutBtn');
  if (logoutBtn) logoutBtn.addEventListener('click', handleLogout);

  // Check existing session
  if (state.token) {
    try {
      const authCheck = await apiRequest('/api/auth/me');
      state.currentUser = authCheck.user;
      showAdminApp();
    } catch (e) {
      showLoginScreen();
    }
  } else {
    showLoginScreen();
  }
});

function showLoginScreen() {
  localStorage.removeItem('tarang_admin_token');
  state.token = '';
  state.currentUser = null;
  document.getElementById('loginOverlay').style.display = 'flex';
  document.getElementById('adminApp').style.display = 'none';
  if (window.lucide) window.lucide.createIcons();
}

function showAdminApp() {
  document.getElementById('loginOverlay').style.display = 'none';
  document.getElementById('adminApp').style.display = 'flex';

  const currentAdminName = document.getElementById('currentAdminName');
  const userAvatar = document.getElementById('userAvatar');
  if (state.currentUser) {
    if (currentAdminName) currentAdminName.textContent = state.currentUser.name || state.currentUser.username;
    if (userAvatar) userAvatar.textContent = (state.currentUser.username || 'A')[0].toUpperCase();
  }

  if (window.lucide) window.lucide.createIcons();
  loadAllAppData();
  loadNormalCategoriesTable();
  loadNormalSubcategoriesTable();
  loadNormalProductsTable();
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const usernameInput = document.getElementById('loginUsername');
  const passwordInput = document.getElementById('loginPassword');
  const errorBox = document.getElementById('loginError');
  const submitBtn = document.getElementById('loginSubmitBtn');

  errorBox.style.display = 'none';
  submitBtn.disabled = true;
  submitBtn.innerHTML = 'Signing in...';

  try {
    const res = await apiRequest('/api/auth/login', 'POST', {
      username: usernameInput.value.trim(),
      password: passwordInput.value.trim()
    });

    state.token = res.token;
    state.currentUser = res.user;
    localStorage.setItem('tarang_admin_token', res.token);

    showToast('Signed in successfully as Administrator!');
    showAdminApp();
  } catch (err) {
    errorBox.textContent = err.message || 'Invalid credentials.';
    errorBox.style.display = 'block';
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = '<i data-lucide="log-in"></i> Sign In to Dashboard';
    if (window.lucide) window.lucide.createIcons();
  }
}

async function handleLogout() {
  if (confirm('Are you sure you want to sign out?')) {
    try { await apiRequest('/api/auth/logout', 'POST'); } catch (e) { /* ignore */ }
    showLoginScreen();
    showToast('Signed out of admin panel.', 'info');
  }
}

// ---------------------------------------------------------------------------
// TAB SWITCHING
// ---------------------------------------------------------------------------
function switchTab(tabId) {
  state.currentTab = tabId;

  // Nav buttons
  document.querySelectorAll('.sidebar-nav .nav-item').forEach(btn => {
    if (btn.getAttribute('data-tab') === tabId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  // Tab views
  document.querySelectorAll('.tab-view').forEach(view => view.classList.remove('active'));
  const targetView = document.getElementById(`view-${tabId}`);
  if (targetView) targetView.classList.add('active');

  // Title bar
  const titles = {
    'dashboard': 'Dashboard Overview',
    'categories': 'Normal Categories Management',
    'subcategories': 'Normal Subcategories Management',
    'products': 'Normal Product Catalog',
    'offers': 'Offers & Promotions Management',
    'brands-management': 'The Brands We Deal With',
    'price-management': 'Instant Price Management',
    'bulk-import': 'Bulk Import (CSV / Excel)',
    'bulk-images': 'Media Library',
    'settings': 'Admin Settings'
  };
  const pageTitle = document.getElementById('pageTitle');
  if (pageTitle) pageTitle.textContent = titles[tabId] || 'Admin Portal';

  const adminSidebar = document.getElementById('adminSidebar');
  if (adminSidebar) adminSidebar.classList.remove('open');

  if (window.lucide) window.lucide.createIcons();

  // Tab refresh
  if (tabId === 'dashboard') loadDashboardStats();
  if (tabId === 'categories') loadNormalCategoriesTable();
  if (tabId === 'subcategories') loadNormalSubcategoriesTable();
  if (tabId === 'products') loadNormalProductsTable();
  if (tabId === 'offers') loadOffersTable();
  if (tabId === 'brands-management') loadTheBrandsWeDealWith();
  if (tabId === 'price-management') loadPriceManagementTable();
  if (tabId === 'bulk-images') loadMediaLibrary();
}

// ---------------------------------------------------------------------------
// LOAD ALL DATA
// ---------------------------------------------------------------------------
async function loadAllAppData() {
  try {
    await Promise.all([
      loadDashboardStats(),
      loadNormalCategoriesData(),
      loadNormalSubcategoriesData(),
      loadBrandsData()
    ]);
  } catch (err) {
    console.error('Error loading data:', err);
  }
}

// ---------------------------------------------------------------------------
// DASHBOARD STATS
// ---------------------------------------------------------------------------
async function loadDashboardStats() {
  try {
    const stats = await apiRequest('/api/admin/stats');
    
    document.getElementById('statTotalProducts').textContent = stats.totalProducts;
    document.getElementById('statInStockText').textContent = `${stats.inStockProducts} In Stock • ${stats.outOfStockProducts} Out`;
    document.getElementById('statTotalBrands').textContent = stats.totalBrands;
    document.getElementById('statNormalCategories').textContent = stats.totalNormalCategories;
    document.getElementById('statTotalSubcategories').textContent = stats.totalSubcategories;

    document.getElementById('badgeNormalCategoriesCount').textContent = stats.totalNormalCategories;
    document.getElementById('badgeNormalSubcategoriesCount').textContent = stats.totalSubcategories;
    
    if (document.getElementById('statTotalOffers')) {
      document.getElementById('statTotalOffers').textContent = stats.activeOffers || 0;
    }
    if (document.getElementById('badgeOffersCount')) {
      document.getElementById('badgeOffersCount').textContent = stats.totalOffers || 0;
    }

    const normalProds = await apiRequest('/api/products?type=normal');
    document.getElementById('badgeNormalProductsCount').textContent = normalProds.length;

    // Recent products preview
    const tbody = document.getElementById('dashboardRecentProductsList');
    if (tbody && stats.recentProducts) {
      if (stats.recentProducts.length === 0) {
        tbody.innerHTML = `<tr><td colspan="8" class="empty-state">No products in catalog.</td></tr>`;
        return;
      }
      tbody.innerHTML = stats.recentProducts.map(p => `
        <tr>
          <td><img src="${formatImgUrl(p.image)}" class="table-img-thumb" onerror="this.src='https://via.placeholder.com/60'" /></td>
          <td><strong>${p.name}</strong></td>
          <td><code>${p.sku || 'N/A'}</code></td>
          <td>
            ${p.brand_name 
              ? `<span style="background:#FFF0E6; color:var(--warm-orange); padding:2px 8px; border-radius:4px; font-weight:800; font-size:0.75rem;">🏷️ ${p.brand_name}</span>`
              : `<span style="background:#EBF5FB; color:#2980B9; padding:2px 8px; border-radius:4px; font-weight:700; font-size:0.75rem;">📁 Normal Catalog</span>`}
          </td>
          <td><span style="font-size:0.8rem; color:var(--text-muted); font-weight:600;">${p.subcategory || 'General'}</span></td>
          <td><strong style="color:var(--warm-orange);">₹${Number(p.price).toLocaleString('en-IN')}</strong></td>
          <td><span class="badge-stock ${p.in_stock ? 'in-stock' : 'out-of-stock'}">${p.in_stock ? 'In Stock' : 'Out of Stock'}</span></td>
          <td>
            <button class="action-btn edit" onclick="editProductFromDashboard('${p.id}', '${p.brand_name || ''}')">Edit</button>
          </td>
        </tr>
      `).join('');
    }
  } catch (err) {
    console.error('Failed to load stats:', err);
  }
}

function editProductFromDashboard(prodId, brandName) {
  if (brandName) {
    switchTab('brands-management');
  } else {
    switchTab('products');
    editNormalProduct(prodId);
  }
}

// ===========================================================================
// SECTION 1: NORMAL CATEGORIES MANAGEMENT (ZERO BRANDS)
// ===========================================================================
async function loadNormalCategoriesData() {
  try {
    state.normalCategories = await apiRequest('/api/categories?type=normal');
    populateNormalCategoryDropdowns();
  } catch (err) {
    console.error('Failed to fetch normal categories:', err);
  }
}

async function loadNormalCategoriesTable() {
  await loadNormalCategoriesData();
  const tbody = document.getElementById('normalCategoriesTableBody');
  if (!tbody) return;

  if (state.normalCategories.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No normal categories created yet. Click "Add Normal Category" to create one.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.normalCategories.map((c, idx) => `
    <tr>
      <td>
        <div style="display:flex; gap:0.2rem;">
          <button style="padding:2px 5px; font-weight:bold; cursor:pointer;" onclick="moveNormalCategoryOrder(${idx}, -1)" ${idx === 0 ? 'disabled' : ''}>▲</button>
          <button style="padding:2px 5px; font-weight:bold; cursor:pointer;" onclick="moveNormalCategoryOrder(${idx}, 1)" ${idx === state.normalCategories.length - 1 ? 'disabled' : ''}>▼</button>
        </div>
      </td>
      <td>
        <img src="${formatImgUrl(c.image)}" class="table-img-thumb" onerror="this.src='https://via.placeholder.com/60'" />
      </td>
      <td>
        <strong style="font-size:0.95rem;">${c.title}</strong>
        <div style="font-size:0.75rem; color:var(--text-muted); font-family:monospace;">ID: ${c.id}</div>
      </td>
      <td><span style="font-weight:600;">${c.short_title || c.title}</span></td>
      <td><span class="badge-stock in-stock">${c.subcategory_count || 0} Subcategories</span></td>
      <td><strong style="color:var(--warm-orange);">${c.product_count || 0} Products</strong></td>
      <td style="text-align: right; white-space: nowrap;">
        <button class="action-btn edit" onclick="editNormalCategory('${c.id}')">Edit</button>
        <button class="action-btn delete" onclick="deleteNormalCategory('${c.id}', '${c.title.replace(/'/g, "\\'")}')">Delete</button>
      </td>
    </tr>
  `).join('');
}

function openNormalCategoryModal(cat = null) {
  const modal = document.getElementById('normalCategoryModalOverlay');
  const title = document.getElementById('normalCatModalTitle');

  document.getElementById('normalCatFormId').value = cat ? cat.id : '';
  document.getElementById('normalCatFormTitle').value = cat ? cat.title : '';
  document.getElementById('normalCatFormShortTitle').value = cat ? (cat.short_title || cat.title) : '';
  document.getElementById('normalCatFormTagline').value = cat ? (cat.tagline || '') : '';
  document.getElementById('normalCatFormColor').value = cat ? (cat.color || '#D14B14') : '#D14B14';
  document.getElementById('normalCatFormImage').value = cat ? (cat.image || '') : '';

  title.textContent = cat ? 'Edit Normal Category' : 'Add Normal Category';
  modal.classList.add('open');
}

function closeNormalCategoryModal() {
  document.getElementById('normalCategoryModalOverlay').classList.remove('open');
}

function editNormalCategory(catId) {
  const cat = state.normalCategories.find(c => c.id === catId);
  if (cat) openNormalCategoryModal(cat);
}

async function saveNormalCategory(e) {
  e.preventDefault();
  const id = document.getElementById('normalCatFormId').value;
  const data = {
    brandId: null, // Normal category has NO brand
    title: document.getElementById('normalCatFormTitle').value.trim(),
    shortTitle: document.getElementById('normalCatFormShortTitle').value.trim(),
    tagline: document.getElementById('normalCatFormTagline').value.trim(),
    color: document.getElementById('normalCatFormColor').value,
    image: document.getElementById('normalCatFormImage').value.trim()
  };

  try {
    if (id) {
      await apiRequest(`/api/categories/${id}`, 'PUT', data);
      showToast(`Category "${data.title}" updated successfully.`);
    } else {
      await apiRequest('/api/categories', 'POST', data);
      showToast(`Category "${data.title}" created successfully.`);
    }
    closeNormalCategoryModal();
    loadNormalCategoriesTable();
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to save category.', 'error');
  }
}

async function deleteNormalCategory(id, name) {
  if (confirm(`WARNING: Delete category "${name}"?\nAll associated normal subcategories and products will also be deleted!`)) {
    try {
      await apiRequest(`/api/categories/${id}`, 'DELETE');
      showToast(`Category "${name}" deleted.`);
      loadNormalCategoriesTable();
      loadDashboardStats();
    } catch (err) {
      showToast(err.message || 'Failed to delete category.', 'error');
    }
  }
}

async function moveNormalCategoryOrder(index, direction) {
  const targetIndex = index + direction;
  if (targetIndex < 0 || targetIndex >= state.normalCategories.length) return;

  const orderList = state.normalCategories.map(c => c.id);
  const temp = orderList[index];
  orderList[index] = orderList[targetIndex];
  orderList[targetIndex] = temp;

  try {
    await apiRequest('/api/categories/reorder', 'POST', { order: orderList });
    showToast('Categories reordered.');
    loadNormalCategoriesTable();
  } catch (err) {
    showToast('Failed to update category order.', 'error');
  }
}

// ===========================================================================
// SECTION 2: NORMAL SUBCATEGORIES MANAGEMENT
// ===========================================================================
async function loadNormalSubcategoriesData() {
  try {
    state.normalSubcategories = await apiRequest('/api/subcategories?type=normal');
  } catch (err) {
    console.error('Failed to fetch normal subcategories:', err);
  }
}

async function loadNormalSubcategoriesTable() {
  await loadNormalSubcategoriesData();
  const filterCat = document.getElementById('normalSubcategoryParentFilter')?.value || 'all';
  const tbody = document.getElementById('normalSubcategoriesTableBody');
  if (!tbody) return;

  let list = state.normalSubcategories;
  if (filterCat && filterCat !== 'all') {
    list = list.filter(s => s.category_id === filterCat);
  }

  if (list.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">No subcategories found. Click "Add Subcategory" to create one.</td></tr>`;
    return;
  }

  tbody.innerHTML = list.map(s => `
    <tr>
      <td><strong>${s.name}</strong></td>
      <td>
        <span class="badge-stock in-stock" style="background:#FFF3E5; color:var(--warm-orange); border-color:#FFD4B2;">
          ${s.category_title || s.category_id}
        </span>
      </td>
      <td><strong>${s.product_count || 0} Products</strong></td>
      <td style="text-align: right; white-space: nowrap;">
        <button class="action-btn edit" onclick="editNormalSubcategory('${s.id}')">Edit</button>
        <button class="action-btn delete" onclick="deleteNormalSubcategory('${s.id}', '${s.name.replace(/'/g, "\\'")}')">Delete</button>
      </td>
    </tr>
  `).join('');
}

function openNormalSubcategoryModal(sub = null) {
  const modal = document.getElementById('normalSubcategoryModalOverlay');
  const title = document.getElementById('normalSubModalTitle');
  const catSelect = document.getElementById('normalSubFormParentCat');

  catSelect.innerHTML = state.normalCategories.map(c => `
    <option value="${c.id}">${c.title}</option>
  `).join('');

  document.getElementById('normalSubFormId').value = sub ? sub.id : '';
  document.getElementById('normalSubFormName').value = sub ? sub.name : '';
  if (sub) catSelect.value = sub.category_id;

  title.textContent = sub ? 'Edit Normal Subcategory' : 'Add Normal Subcategory';
  modal.classList.add('open');
}

function closeNormalSubcategoryModal() {
  document.getElementById('normalSubcategoryModalOverlay').classList.remove('open');
}

function editNormalSubcategory(subId) {
  const sub = state.normalSubcategories.find(s => s.id === subId);
  if (sub) openNormalSubcategoryModal(sub);
}

async function saveNormalSubcategory(e) {
  e.preventDefault();
  const id = document.getElementById('normalSubFormId').value;
  const data = {
    name: document.getElementById('normalSubFormName').value.trim(),
    categoryId: document.getElementById('normalSubFormParentCat').value
  };

  try {
    if (id) {
      await apiRequest(`/api/subcategories/${id}`, 'PUT', data);
      showToast(`Subcategory "${data.name}" updated.`);
    } else {
      await apiRequest('/api/subcategories', 'POST', data);
      showToast(`Subcategory "${data.name}" created.`);
    }
    closeNormalSubcategoryModal();
    loadNormalSubcategoriesTable();
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to save subcategory.', 'error');
  }
}

async function deleteNormalSubcategory(id, name) {
  if (confirm(`Delete subcategory "${name}"?`)) {
    try {
      await apiRequest(`/api/subcategories/${id}`, 'DELETE');
      showToast(`Subcategory "${name}" deleted.`);
      loadNormalSubcategoriesTable();
      loadDashboardStats();
    } catch (err) {
      showToast(err.message || 'Failed to delete subcategory.', 'error');
    }
  }
}

// ===========================================================================
// SECTION 3: NORMAL PRODUCTS CATALOG (ZERO BRANDS)
// ===========================================================================
let normalSearchTimeout = null;
function debouncedSearchNormalProducts() {
  clearTimeout(normalSearchTimeout);
  normalSearchTimeout = setTimeout(() => loadNormalProductsTable(), 300);
}

async function loadNormalProductsTable() {
  const search = (document.getElementById('normalProductSearchInput')?.value || '').trim();
  const catId = document.getElementById('normalProductCategoryFilter')?.value || 'all';
  const subcat = document.getElementById('normalProductSubcategoryFilter')?.value || 'all';
  const sort = document.getElementById('normalProductSortFilter')?.value || 'date_desc';

  let url = `/api/products?type=normal&sort=${sort}`;
  if (catId && catId !== 'all') url += `&category_id=${encodeURIComponent(catId)}`;
  if (subcat && subcat !== 'all') url += `&subcategory=${encodeURIComponent(subcat)}`;
  if (search) url += `&q=${encodeURIComponent(search)}`;

  try {
    state.normalProducts = await apiRequest(url);
    renderNormalProductsTable();
  } catch (err) {
    console.error('Failed to load normal products:', err);
  }
}

function renderNormalProductsTable() {
  const tbody = document.getElementById('normalProductsTableBody');
  if (!tbody) return;

  if (state.normalProducts.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No products found in normal catalog.</td></tr>`;
    return;
  }

  tbody.innerHTML = state.normalProducts.map(p => `
    <tr>
      <td>
        <img src="${formatImgUrl(p.image)}" class="table-img-thumb" onerror="this.src='https://via.placeholder.com/60'" />
      </td>
      <td>
        <strong>${p.name}</strong>
        <div style="font-size:0.75rem; color:var(--text-muted);">SKU: <code>${p.sku || 'N/A'}</code></div>
      </td>
      <td>
        <div style="font-weight:600;">${p.category_title || p.category_id}</div>
        <small style="color:var(--warm-orange); font-weight:700;">${p.subcategory || 'General'}</small>
      </td>
      <td>
        <strong style="color:var(--warm-orange); font-size:1rem;">₹${Number(p.price).toLocaleString('en-IN')}</strong>
      </td>
      <td>
        <span class="badge-stock ${p.in_stock ? 'in-stock' : 'out-of-stock'}">
          ${p.in_stock ? 'In Stock' : 'Out of Stock'}
        </span>
      </td>
      <td style="text-align: right; white-space: nowrap;">
        <button class="action-btn edit" onclick="editNormalProduct('${p.id}')">Edit</button>
        <button class="action-btn copy" onclick="duplicateNormalProduct('${p.id}')" title="Duplicate product">Copy</button>
        <button class="action-btn delete" onclick="deleteNormalProduct('${p.id}', '${p.name.replace(/'/g, "\\'")}')">Delete</button>
      </td>
    </tr>
  `).join('');
}

function populateNormalCategoryDropdowns() {
  const catSelectProduct = document.getElementById('normalProdFormCat');
  const catSelectFilter = document.getElementById('normalProductCategoryFilter');
  const subcatParentFilter = document.getElementById('normalSubcategoryParentFilter');

  const options = state.normalCategories.map(c => `<option value="${c.id}">${c.title}</option>`).join('');

  if (catSelectProduct) catSelectProduct.innerHTML = `<option value="">Select Category</option>` + options;
  if (catSelectFilter) catSelectFilter.innerHTML = `<option value="all">All Categories</option>` + options;
  if (subcatParentFilter) subcatParentFilter.innerHTML = `<option value="all">All Normal Categories</option>` + options;
}

function onNormalCategoryFilterChange() {
  const catId = document.getElementById('normalProductCategoryFilter').value;
  const subcatSelect = document.getElementById('normalProductSubcategoryFilter');
  
  if (catId === 'all') {
    subcatSelect.innerHTML = `<option value="all">All Subcategories</option>`;
  } else {
    const subs = state.normalSubcategories.filter(s => s.category_id === catId);
    subcatSelect.innerHTML = `<option value="all">All Subcategories</option>` + subs.map(s => `
      <option value="${s.name}">${s.name}</option>
    `).join('');
  }
  loadNormalProductsTable();
}

function populateNormalSubcategoriesForProduct(catId, selectedSubcat = '') {
  const subcatSelect = document.getElementById('normalProdFormSubcat');
  if (!subcatSelect) return;

  const filtered = state.normalSubcategories.filter(s => s.category_id === catId);
  subcatSelect.innerHTML = `<option value="">Select Subcategory</option>` + filtered.map(s => `
    <option value="${s.name}" ${s.name === selectedSubcat ? 'selected' : ''}>${s.name}</option>
  `).join('');
}

function openNormalProductModal(prod = null) {
  const modal = document.getElementById('normalProductModalOverlay');
  const title = document.getElementById('normalProdModalTitle');

  populateNormalCategoryDropdowns();

  document.getElementById('normalProdFormId').value = prod ? prod.id : '';
  document.getElementById('normalProdFormName').value = prod ? prod.name : '';
  document.getElementById('normalProdFormSku').value = prod ? (prod.sku || '') : '';
  document.getElementById('normalProdFormCat').value = prod ? prod.category_id : '';
  document.getElementById('normalProdFormPrice').value = prod ? prod.price : '';
  document.getElementById('normalProdFormStock').value = prod ? (prod.in_stock ? '1' : '0') : '1';
  document.getElementById('normalProdFormImage').value = prod ? (prod.image || '') : '';
  document.getElementById('normalProdFormBadge').value = prod ? (prod.badge || '') : '';
  document.getElementById('normalProdFormDesc').value = prod ? (prod.description || '') : '';

  if (prod) {
    populateNormalSubcategoriesForProduct(prod.category_id, prod.subcategory);
    updateNormalProdImagePreview(prod.image);
  } else {
    document.getElementById('normalProdFormSubcat').innerHTML = '<option value="">Select Subcategory</option>';
    updateNormalProdImagePreview('');
  }

  title.textContent = prod ? 'Edit Normal Product' : 'Add Normal Product';
  modal.classList.add('open');
}

function closeNormalProductModal() {
  document.getElementById('normalProductModalOverlay').classList.remove('open');
}

function editNormalProduct(prodId) {
  const prod = state.normalProducts.find(p => p.id === prodId);
  if (prod) openNormalProductModal(prod);
}

function updateNormalProdImagePreview(url) {
  const box = document.getElementById('normalProdImagePreviewBox');
  const img = document.getElementById('normalProdImagePreviewImg');
  if (url && url.trim()) {
    img.src = url.startsWith('http') ? url : `../${url}`;
    box.style.display = 'block';
  } else {
    box.style.display = 'none';
  }
}

async function saveNormalProduct(e) {
  e.preventDefault();
  const id = document.getElementById('normalProdFormId').value;
  const data = {
    name: document.getElementById('normalProdFormName').value.trim(),
    sku: document.getElementById('normalProdFormSku').value.trim(),
    brandId: null, // Normal product has NO brand
    categoryId: document.getElementById('normalProdFormCat').value,
    subcategory: document.getElementById('normalProdFormSubcat').value,
    price: parseFloat(document.getElementById('normalProdFormPrice').value) || 0,
    inStock: document.getElementById('normalProdFormStock').value === '1',
    image: document.getElementById('normalProdFormImage').value.trim(),
    badge: document.getElementById('normalProdFormBadge').value.trim(),
    description: document.getElementById('normalProdFormDesc').value.trim()
  };

  try {
    if (id) {
      await apiRequest(`/api/products/${id}`, 'PUT', data);
      showToast(`Product "${data.name}" updated successfully.`);
    } else {
      await apiRequest('/api/products', 'POST', data);
      showToast(`Product "${data.name}" created successfully.`);
    }
    closeNormalProductModal();
    loadNormalProductsTable();
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to save product.', 'error');
  }
}

async function duplicateNormalProduct(prodId) {
  try {
    await apiRequest(`/api/products/${prodId}/duplicate`, 'POST');
    showToast('Product duplicated successfully.');
    loadNormalProductsTable();
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to duplicate product.', 'error');
  }
}

async function deleteNormalProduct(prodId, name) {
  if (confirm(`Delete product "${name}"?`)) {
    try {
      await apiRequest(`/api/products/${prodId}`, 'DELETE');
      showToast(`Product "${name}" deleted.`);
      loadNormalProductsTable();
      loadDashboardStats();
    } catch (err) {
      showToast(err.message || 'Failed to delete product.', 'error');
    }
  }
}

// ===========================================================================
// SECTION 4: THE BRANDS WE DEAL WITH (DEDICATED 7 BRANDS MANAGEMENT)
// ===========================================================================
async function loadBrandsData() {
  try {
    state.brands = await apiRequest('/api/brands?all=1');
  } catch (err) {
    console.error('Failed to load brands:', err);
  }
}

async function loadTheBrandsWeDealWith() {
  await loadBrandsData();
  renderBrandTabs();
  
  if (state.brands.length > 0) {
    if (!state.activeBrandId || !state.brands.some(b => b.id === state.activeBrandId)) {
      state.activeBrandId = state.brands[0].id;
    }
    selectActiveBrand(state.activeBrandId);
  } else {
    document.getElementById('brandDetailContainer').style.display = 'none';
  }
}

function renderBrandTabs() {
  const tabsBar = document.getElementById('brandTabsBar');
  if (!tabsBar) return;

  if (state.brands.length === 0) {
    tabsBar.innerHTML = `<div class="empty-state" style="padding:1rem;">No brands configured yet. Click "Add New Brand" above.</div>`;
    return;
  }

  tabsBar.innerHTML = state.brands.map((b, idx) => `
    <button class="brand-tab-btn ${b.id === state.activeBrandId ? 'active' : ''}" onclick="selectActiveBrand('${b.id}')">
      <span>${b.name}</span>
      <small style="opacity:0.8; font-size:0.75rem;">(${b.is_enabled ? 'Active' : 'Disabled'})</small>
    </button>
  `).join('');
}

async function selectActiveBrand(brandId) {
  state.activeBrandId = brandId;
  renderBrandTabs();

  const brand = state.brands.find(b => b.id === brandId);
  if (!brand) return;

  const detailContainer = document.getElementById('brandDetailContainer');
  detailContainer.style.display = 'block';

  document.getElementById('activeBrandNameDisplay').textContent = brand.name;
  document.getElementById('activeBrandHierarchyTitle').textContent = brand.name;

  const statusBadge = document.getElementById('activeBrandStatusBadge');
  statusBadge.className = `status-pill ${brand.is_enabled ? 'enabled' : 'disabled'}`;
  statusBadge.textContent = brand.is_enabled ? '● Active' : '○ Disabled';

  loadActiveBrandHierarchy(brandId);
}

async function loadActiveBrandHierarchy(brandId) {
  const treeContainer = document.getElementById('brandHierarchyTree');
  if (!treeContainer) return;

  try {
    const hierarchies = await apiRequest(`/api/brands/hierarchy?brand_id=${brandId}`);
    const brandTree = hierarchies[0];
    state.activeBrandHierarchy = brandTree;

    if (!brandTree || brandTree.categories.length === 0) {
      treeContainer.innerHTML = `
        <div style="text-align:center; padding:3rem 1rem; color:var(--text-muted);">
          <i data-lucide="layers" style="width:40px; height:40px; color:var(--warm-orange); margin-bottom:0.5rem;"></i>
          <h4>No categories created under ${brandTree ? brandTree.name : 'this brand'}.</h4>
          <p style="font-size:0.88rem; margin-bottom:1rem;">Add categories (e.g. Wires, Cables, Hand Tools) to organize products for this brand.</p>
          <button class="btn-primary" onclick="openBrandCategoryModal()">
            <i data-lucide="plus"></i> Add First Category to ${brandTree ? brandTree.name : 'Brand'}
          </button>
        </div>
      `;
      if (window.lucide) window.lucide.createIcons();
      return;
    }

    treeContainer.innerHTML = brandTree.categories.map(cat => {
      const subcatsHtml = cat.subcategories.map(sub => {
        const prodsHtml = sub.products.map(prod => `
          <div class="tree-product-pill">
            <img src="${formatImgUrl(prod.image)}" class="table-img-thumb" style="width:42px; height:42px; object-fit:contain; border-radius:6px; background:#FFF;" onerror="this.src='https://via.placeholder.com/60'" />
            <div style="flex:1; min-width:0;">
              <strong style="font-size:0.84rem; display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="${prod.name}">${prod.name}</strong>
              <div style="font-size:0.75rem; color:var(--warm-orange); font-weight:800;">₹${Number(prod.price).toLocaleString('en-IN')}</div>
            </div>
            <div style="display:flex; gap:0.2rem;">
              <button class="action-btn edit" style="padding:2px 5px;" onclick="editBrandProduct('${prod.id}', '${cat.id}')">Edit</button>
              <button class="action-btn delete" style="padding:2px 5px;" onclick="deleteBrandProduct('${prod.id}', '${prod.name.replace(/'/g, "\\'")}')">×</button>
            </div>
          </div>
        `).join('');

        return `
          <div class="tree-sub-node">
            <div class="tree-sub-header">
              <div class="tree-sub-name">
                <i data-lucide="corner-down-right" style="width:16px; height:16px; color:var(--warm-orange);"></i>
                <span>${sub.name}</span>
                <span class="badge-stock in-stock" style="font-size:0.72rem;">${sub.productsCount} Products</span>
              </div>
              <div class="tree-actions-group">
                <button class="btn-primary" style="padding:3px 8px; font-size:0.75rem;" onclick="openBrandProductModal('${cat.id}', '${sub.name}')">
                  <i data-lucide="plus"></i> Add Product
                </button>
                <button class="action-btn edit" onclick="editBrandSubcategory('${sub.id}', '${cat.id}', '${sub.name.replace(/'/g, "\\'")}')">Rename</button>
                <button class="action-btn delete" onclick="deleteBrandSubcategory('${sub.id}', '${sub.name.replace(/'/g, "\\'")}')">Delete</button>
              </div>
            </div>
            
            ${prodsHtml 
              ? `<div class="tree-products-subgrid">${prodsHtml}</div>`
              : `<div style="font-size:0.8rem; color:var(--text-muted); padding:4px;">No products under this subcategory yet. Click "+ Add Product".</div>`}
          </div>
        `;
      }).join('');

      return `
        <div class="tree-cat-node">
          <div class="tree-cat-header">
            <div class="tree-cat-title">
              <i data-lucide="layers" style="width:18px; height:18px; color:var(--warm-orange);"></i>
              <span>${cat.title}</span>
              <small style="color:var(--text-muted); font-weight:600;">(${cat.shortTitle || ''})</small>
            </div>
            <div class="tree-actions-group">
              <button class="btn-primary" style="padding:3px 9px; font-size:0.78rem;" onclick="openBrandSubcategoryModal('${cat.id}', '${cat.title.replace(/'/g, "\\'")}')">
                <i data-lucide="plus"></i> Add Subcategory
              </button>
              <button class="action-btn edit" onclick="editBrandCategory('${cat.id}')">Edit</button>
              <button class="action-btn delete" onclick="deleteBrandCategory('${cat.id}', '${cat.title.replace(/'/g, "\\'")}')">Delete</button>
            </div>
          </div>

          <div class="tree-subcats-list">
            ${subcatsHtml || `<div style="font-size:0.85rem; color:var(--text-muted); padding:8px;">No subcategories. Click "+ Add Subcategory" to add one.</div>`}
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    console.error('Failed to load brand hierarchy:', err);
  }
}

// Brand CRUD
function openBrandModal() {
  document.getElementById('brandFormId').value = '';
  document.getElementById('brandFormName').value = '';
  document.getElementById('brandFormEnabled').checked = true;
  document.getElementById('brandModalTitle').textContent = 'Add Brand Partner';
  document.getElementById('brandModalOverlay').classList.add('open');
}

function openEditActiveBrandModal() {
  const brand = state.brands.find(b => b.id === state.activeBrandId);
  if (!brand) return;

  document.getElementById('brandFormId').value = brand.id;
  document.getElementById('brandFormName').value = brand.name;
  document.getElementById('brandFormEnabled').checked = Boolean(brand.is_enabled);
  document.getElementById('brandModalTitle').textContent = `Edit Brand "${brand.name}"`;
  document.getElementById('brandModalOverlay').classList.add('open');
}

function closeBrandModal() {
  document.getElementById('brandModalOverlay').classList.remove('open');
}

async function saveBrand(e) {
  e.preventDefault();
  const id = document.getElementById('brandFormId').value;
  const name = document.getElementById('brandFormName').value.trim();
  const isEnabled = document.getElementById('brandFormEnabled').checked;

  try {
    if (id) {
      await apiRequest(`/api/brands/${id}`, 'PUT', { name, isEnabled });
      showToast(`Brand updated to "${name}".`);
    } else {
      const res = await apiRequest('/api/brands', 'POST', { name, isEnabled });
      showToast(`Brand "${name}" added successfully.`);
      state.activeBrandId = res.id;
    }
    closeBrandModal();
    loadTheBrandsWeDealWith();
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to save brand.', 'error');
  }
}

async function toggleActiveBrandStatus() {
  if (!state.activeBrandId) return;
  try {
    const res = await apiRequest(`/api/brands/${state.activeBrandId}/toggle`, 'POST');
    showToast(res.message);
    loadTheBrandsWeDealWith();
    loadDashboardStats();
  } catch (err) {
    showToast('Failed to toggle brand status.', 'error');
  }
}

async function deleteActiveBrand() {
  const brand = state.brands.find(b => b.id === state.activeBrandId);
  if (!brand) return;

  if (confirm(`WARNING: Delete brand "${brand.name}" and ALL its categories, subcategories, and products?`)) {
    try {
      await apiRequest(`/api/brands/${brand.id}`, 'DELETE');
      showToast(`Brand "${brand.name}" deleted.`);
      state.activeBrandId = null;
      loadTheBrandsWeDealWith();
      loadDashboardStats();
    } catch (err) {
      showToast(err.message || 'Failed to delete brand.', 'error');
    }
  }
}

// Brand-Category CRUD
function openBrandCategoryModal(cat = null) {
  const brand = state.brands.find(b => b.id === state.activeBrandId);
  if (!brand) return;

  document.getElementById('brandCatFormId').value = cat ? cat.id : '';
  document.getElementById('brandCatFormBrandId').value = brand.id;
  document.getElementById('brandCatFormBrandNameDisplay').value = brand.name;
  document.getElementById('brandCatFormTitle').value = cat ? cat.title : '';
  document.getElementById('brandCatFormShortTitle').value = cat ? (cat.short_title || cat.title) : '';
  document.getElementById('brandCatFormTagline').value = cat ? (cat.tagline || '') : '';
  document.getElementById('brandCatFormColor').value = cat ? (cat.color || '#D14B14') : '#D14B14';

  document.getElementById('brandCatModalTitle').textContent = cat ? `Edit Category under ${brand.name}` : `Add Category to ${brand.name}`;
  document.getElementById('brandCategoryModalOverlay').classList.add('open');
}

function closeBrandCategoryModal() {
  document.getElementById('brandCategoryModalOverlay').classList.remove('open');
}

function editBrandCategory(catId) {
  const cat = state.activeBrandHierarchy?.categories.find(c => c.id === catId);
  if (cat) openBrandCategoryModal(cat);
}

async function saveBrandCategory(e) {
  e.preventDefault();
  const id = document.getElementById('brandCatFormId').value;
  const brandId = document.getElementById('brandCatFormBrandId').value;
  const data = {
    brandId: brandId,
    title: document.getElementById('brandCatFormTitle').value.trim(),
    shortTitle: document.getElementById('brandCatFormShortTitle').value.trim(),
    tagline: document.getElementById('brandCatFormTagline').value.trim(),
    color: document.getElementById('brandCatFormColor').value
  };

  try {
    if (id) {
      await apiRequest(`/api/categories/${id}`, 'PUT', data);
      showToast(`Category "${data.title}" updated.`);
    } else {
      await apiRequest('/api/categories', 'POST', data);
      showToast(`Category "${data.title}" added to brand.`);
    }
    closeBrandCategoryModal();
    loadActiveBrandHierarchy(brandId);
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to save brand category.', 'error');
  }
}

async function deleteBrandCategory(catId, title) {
  if (confirm(`Delete category "${title}" under this brand?\nAll nested subcategories and products will also be deleted!`)) {
    try {
      await apiRequest(`/api/categories/${catId}`, 'DELETE');
      showToast(`Category "${title}" deleted.`);
      loadActiveBrandHierarchy(state.activeBrandId);
      loadDashboardStats();
    } catch (err) {
      showToast(err.message || 'Failed to delete category.', 'error');
    }
  }
}

// Brand-Subcategory CRUD
function openBrandSubcategoryModal(catId, catTitle) {
  document.getElementById('brandSubFormId').value = '';
  document.getElementById('brandSubFormCatId').value = catId;
  document.getElementById('brandSubFormCatTitleDisplay').value = catTitle;
  document.getElementById('brandSubFormName').value = '';
  document.getElementById('brandSubModalTitle').textContent = `Add Subcategory to "${catTitle}"`;
  document.getElementById('brandSubcategoryModalOverlay').classList.add('open');
}

function editBrandSubcategory(subId, catId, subName) {
  const cat = state.activeBrandHierarchy?.categories.find(c => c.id === catId);
  document.getElementById('brandSubFormId').value = subId;
  document.getElementById('brandSubFormCatId').value = catId;
  document.getElementById('brandSubFormCatTitleDisplay').value = cat ? cat.title : 'Category';
  document.getElementById('brandSubFormName').value = subName;
  document.getElementById('brandSubModalTitle').textContent = `Edit Subcategory "${subName}"`;
  document.getElementById('brandSubcategoryModalOverlay').classList.add('open');
}

function closeBrandSubcategoryModal() {
  document.getElementById('brandSubcategoryModalOverlay').classList.remove('open');
}

async function saveBrandSubcategory(e) {
  e.preventDefault();
  const id = document.getElementById('brandSubFormId').value;
  const catId = document.getElementById('brandSubFormCatId').value;
  const data = {
    name: document.getElementById('brandSubFormName').value.trim(),
    categoryId: catId
  };

  try {
    if (id) {
      await apiRequest(`/api/subcategories/${id}`, 'PUT', data);
      showToast(`Subcategory "${data.name}" updated.`);
    } else {
      await apiRequest('/api/subcategories', 'POST', data);
      showToast(`Subcategory "${data.name}" added.`);
    }
    closeBrandSubcategoryModal();
    loadActiveBrandHierarchy(state.activeBrandId);
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to save subcategory.', 'error');
  }
}

async function deleteBrandSubcategory(subId, name) {
  if (confirm(`Delete subcategory "${name}"?`)) {
    try {
      await apiRequest(`/api/subcategories/${subId}`, 'DELETE');
      showToast(`Subcategory "${name}" deleted.`);
      loadActiveBrandHierarchy(state.activeBrandId);
      loadDashboardStats();
    } catch (err) {
      showToast(err.message || 'Failed to delete subcategory.', 'error');
    }
  }
}

// Brand-Product CRUD
function openBrandProductModal(catId, subcatName = '') {
  const brand = state.brands.find(b => b.id === state.activeBrandId);
  const cat = state.activeBrandHierarchy?.categories.find(c => c.id === catId);

  document.getElementById('brandProdFormId').value = '';
  document.getElementById('brandProdFormBrandId').value = brand.id;
  document.getElementById('brandProdFormCatId').value = catId;
  document.getElementById('brandProdFormMetaDisplay').value = `${brand.name} → ${cat ? cat.title : 'Category'}`;
  
  document.getElementById('brandProdFormName').value = '';
  document.getElementById('brandProdFormSku').value = '';
  document.getElementById('brandProdFormPrice').value = '';
  document.getElementById('brandProdFormStock').value = '1';
  document.getElementById('brandProdFormImage').value = '';
  document.getElementById('brandProdFormBadge').value = '';
  document.getElementById('brandProdFormDesc').value = '';

  const subSelect = document.getElementById('brandProdFormSubcat');
  if (cat && cat.subcategories) {
    subSelect.innerHTML = cat.subcategories.map(s => `
      <option value="${s.name}" ${s.name === subcatName ? 'selected' : ''}>${s.name}</option>
    `).join('');
  }

  updateBrandProdImagePreview('');
  document.getElementById('brandProdModalTitle').textContent = `Add Product to ${brand.name}`;
  document.getElementById('brandProductModalOverlay').classList.add('open');
}

function editBrandProduct(prodId, catId) {
  const cat = state.activeBrandHierarchy?.categories.find(c => c.id === catId);
  let targetProd = null;
  if (cat) {
    for (const sub of cat.subcategories) {
      const p = sub.products.find(x => x.id === prodId);
      if (p) { targetProd = p; break; }
    }
  }
  if (!targetProd) return;

  const brand = state.brands.find(b => b.id === state.activeBrandId);

  document.getElementById('brandProdFormId').value = targetProd.id;
  document.getElementById('brandProdFormBrandId').value = brand.id;
  document.getElementById('brandProdFormCatId').value = catId;
  document.getElementById('brandProdFormMetaDisplay').value = `${brand.name} → ${cat.title}`;

  document.getElementById('brandProdFormName').value = targetProd.name;
  document.getElementById('brandProdFormSku').value = targetProd.sku || '';
  document.getElementById('brandProdFormPrice').value = targetProd.price;
  document.getElementById('brandProdFormStock').value = targetProd.in_stock ? '1' : '0';
  document.getElementById('brandProdFormImage').value = targetProd.image || '';
  document.getElementById('brandProdFormBadge').value = targetProd.badge || '';
  document.getElementById('brandProdFormDesc').value = targetProd.description || '';

  const subSelect = document.getElementById('brandProdFormSubcat');
  if (cat && cat.subcategories) {
    subSelect.innerHTML = cat.subcategories.map(s => `
      <option value="${s.name}" ${s.name === targetProd.subcategory ? 'selected' : ''}>${s.name}</option>
    `).join('');
  }

  updateBrandProdImagePreview(targetProd.image);
  document.getElementById('brandProdModalTitle').textContent = `Edit Product "${targetProd.name}"`;
  document.getElementById('brandProductModalOverlay').classList.add('open');
}

function closeBrandProductModal() {
  document.getElementById('brandProductModalOverlay').classList.remove('open');
}

function updateBrandProdImagePreview(url) {
  const box = document.getElementById('brandProdImagePreviewBox');
  const img = document.getElementById('brandProdImagePreviewImg');
  if (url && url.trim()) {
    img.src = url.startsWith('http') ? url : `../${url}`;
    box.style.display = 'block';
  } else {
    box.style.display = 'none';
  }
}

async function saveBrandProduct(e) {
  e.preventDefault();
  const id = document.getElementById('brandProdFormId').value;
  const brandId = document.getElementById('brandProdFormBrandId').value;
  const catId = document.getElementById('brandProdFormCatId').value;

  const data = {
    brandId: brandId,
    categoryId: catId,
    name: document.getElementById('brandProdFormName').value.trim(),
    sku: document.getElementById('brandProdFormSku').value.trim(),
    subcategory: document.getElementById('brandProdFormSubcat').value,
    price: parseFloat(document.getElementById('brandProdFormPrice').value) || 0,
    inStock: document.getElementById('brandProdFormStock').value === '1',
    badge: document.getElementById('brandProdFormBadge').value.trim(),
    image: document.getElementById('brandProdFormImage').value.trim(),
    description: document.getElementById('brandProdFormDesc').value.trim()
  };

  try {
    if (id) {
      await apiRequest(`/api/products/${id}`, 'PUT', data);
      showToast(`Product "${data.name}" updated successfully.`);
    } else {
      await apiRequest('/api/products', 'POST', data);
      showToast(`Product "${data.name}" added to ${state.brands.find(b => b.id === brandId)?.name || 'Brand'}.`);
    }
    closeBrandProductModal();
    loadActiveBrandHierarchy(brandId);
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to save brand product.', 'error');
  }
}

async function deleteBrandProduct(prodId, name) {
  if (confirm(`Delete product "${name}"?`)) {
    try {
      await apiRequest(`/api/products/${prodId}`, 'DELETE');
      showToast(`Product "${name}" deleted.`);
      loadActiveBrandHierarchy(state.activeBrandId);
      loadDashboardStats();
    } catch (err) {
      showToast(err.message || 'Failed to delete product.', 'error');
    }
  }
}

// ===========================================================================
// SECTION 5: INSTANT PRICE MANAGEMENT (CENTRALIZED)
// ===========================================================================
let priceSearchTimeout = null;
function debouncedSearchPriceTable() {
  clearTimeout(priceSearchTimeout);
  priceSearchTimeout = setTimeout(() => loadPriceManagementTable(), 300);
}

async function loadPriceManagementTable() {
  const search = (document.getElementById('priceSearchInput')?.value || '').trim();
  const scope = document.getElementById('priceScopeFilter')?.value || 'all';

  let url = '/api/products?sort=date_desc';
  if (scope === 'normal') url += '&type=normal';
  if (search) url += `&q=${encodeURIComponent(search)}`;

  try {
    let products = await apiRequest(url);
    if (scope === 'brands') {
      products = products.filter(p => p.brand_id);
    }

    const tbody = document.getElementById('priceTableBody');
    if (!tbody) return;

    if (products.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-state">No products found for price editing.</td></tr>`;
      return;
    }

    tbody.innerHTML = products.map(p => `
      <tr id="price-row-${p.id}">
        <td>
          <img src="${formatImgUrl(p.image)}" class="table-img-thumb" onerror="this.src='https://via.placeholder.com/60'" />
        </td>
        <td>
          <strong>${p.name}</strong>
          <div style="font-size:0.75rem; color:var(--text-muted);">SKU: <code>${p.sku || 'N/A'}</code></div>
        </td>
        <td>
          ${p.brand_name || p.brand
            ? `<span style="background:#FFF0E6; color:var(--warm-orange); padding:2px 8px; border-radius:4px; font-weight:800; font-size:0.75rem;">🏷️ ${p.brand_name || p.brand}</span>`
            : `<span style="background:#EBF5FB; color:#2980B9; padding:2px 8px; border-radius:4px; font-weight:700; font-size:0.75rem;">📁 Normal Catalog</span>`}
        </td>
        <td><span style="font-weight:600;">${p.category_title || p.category_id}</span></td>
        <td>
          <span id="current-price-badge-${p.id}" style="font-weight:800; color:var(--warm-orange); font-size:1.05rem;">
            ₹${Number(p.price).toLocaleString('en-IN')}
          </span>
        </td>
        <td>
          <div style="display:flex; align-items:center; gap:0.3rem;">
            <span style="font-weight:700;">₹</span>
            <input type="number" step="0.01" min="0" class="quick-price-input" id="quick-input-${p.id}" value="${p.price}" />
          </div>
        </td>
        <td style="text-align: right;">
          <button class="btn-primary" style="padding:0.4rem 0.8rem; font-size:0.8rem;" onclick="saveQuickPrice('${p.id}')">
            Save Price
          </button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load price table:', err);
  }
}

async function saveQuickPrice(prodId) {
  const input = document.getElementById(`quick-input-${prodId}`);
  if (!input) return;

  const newPrice = parseFloat(input.value);
  if (isNaN(newPrice) || newPrice < 0) {
    showToast('Please enter a valid price (>= 0).', 'error');
    return;
  }

  try {
    const res = await apiRequest('/api/products/quick-price', 'POST', {
      id: prodId,
      price: newPrice
    });

    const badge = document.getElementById(`current-price-badge-${prodId}`);
    if (badge) badge.textContent = `₹${newPrice.toLocaleString('en-IN')}`;

    const row = document.getElementById(`price-row-${prodId}`);
    if (row) {
      row.style.backgroundColor = '#EAFAF1';
      setTimeout(() => {
        row.style.backgroundColor = '';
        row.style.transition = 'background-color 1s ease';
      }, 1500);
    }

    showToast(`Price updated for "${res.name}" to ₹${newPrice.toLocaleString('en-IN')}!`);
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to update price.', 'error');
  }
}

// ===========================================================================
// SECTION 6: BULK IMAGE & CSV PRODUCT IMPORT
// ===========================================================================
async function uploadSingleImage(event, targetInputId, callback = null) {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await apiRequest('/api/upload/images', 'POST', formData, true);
    if (res.files && res.files.length > 0) {
      const imgUrl = res.files[0].url;
      document.getElementById(targetInputId).value = imgUrl;
      showToast(`Image "${res.files[0].filename}" uploaded!`);
      if (callback) callback(imgUrl);
    }
  } catch (err) {
    showToast(err.message || 'Image upload failed.', 'error');
  }
}

function handleBulkImagesSelected(event) {
  state.selectedBulkImageFiles = Array.from(event.target.files);
  const display = document.getElementById('imagesCountDisplay');
  const btn = document.getElementById('btnUploadBulkImages');

  if (state.selectedBulkImageFiles.length > 0) {
    display.textContent = `${state.selectedBulkImageFiles.length} images selected ready to upload.`;
    btn.disabled = false;
  } else {
    display.textContent = '';
    btn.disabled = true;
  }
}

async function uploadBulkImagesToServer() {
  if (state.selectedBulkImageFiles.length === 0) return;

  const btn = document.getElementById('btnUploadBulkImages');
  btn.disabled = true;
  btn.innerHTML = 'Uploading images...';

  const formData = new FormData();
  state.selectedBulkImageFiles.forEach(file => {
    formData.append('images', file);
  });

  try {
    const res = await apiRequest('/api/upload/images', 'POST', formData, true);
    res.files.forEach(f => state.uploadedImagesMap.add(f.filename));
    showToast(`Successfully uploaded ${res.count} images to server!`);
    btn.innerHTML = `✓ ${res.count} Images Uploaded`;
    
    if (state.parsedCsvProducts.length > 0) {
      renderImportPreview();
    }
  } catch (err) {
    showToast(err.message || 'Bulk image upload failed.', 'error');
    btn.disabled = false;
    btn.innerHTML = '<i data-lucide="upload"></i> Upload & Process Images';
    if (window.lucide) window.lucide.createIcons();
  }
}

function handleCsvFileSelected(event) {
  const file = event.target.files[0];
  if (!file) return;

  document.getElementById('csvFileNameDisplay').textContent = `Loaded: ${file.name}`;
  
  const reader = new FileReader();
  reader.onload = function(e) {
    parseCsvContent(e.target.result);
  };
  reader.readAsText(file);
}

function parseCsvContent(text) {
  const lines = text.split(/\r?\n/).filter(line => line.trim() !== '');
  if (lines.length < 2) {
    showToast('CSV file is empty or missing data rows.', 'error');
    return;
  }

  const headers = parseCsvLine(lines[0]).map(h => h.trim());
  const autoNameFromImage = document.getElementById('autoNameFromImageFilename')?.checked;

  const products = [];
  for (let i = 1; i < lines.length; i++) {
    const row = parseCsvLine(lines[i]);
    if (row.length === 0 || (row.length === 1 && !row[0])) continue;

    const item = {};
    headers.forEach((h, idx) => {
      item[h] = row[idx] ? row[idx].trim() : '';
    });

    let prodName = item['Product Name'] || item['name'] || '';
    let imageFilename = item['Image Filename'] || item['image'] || '';

    if (!prodName && imageFilename && autoNameFromImage) {
      const base = imageFilename.split('/').pop().split('\\').pop();
      const dotIdx = base.lastIndexOf('.');
      const cleanBase = dotIdx > -1 ? base.substring(0, dotIdx) : base;
      prodName = cleanBase.replace(/[_-]/g, ' ');
    }

    item['name'] = prodName;
    item['price'] = parseFloat(item['Price'] || item['price'] || 0);
    item['brand'] = item['Brand'] || item['brand'] || '';
    item['category'] = item['Category'] || item['category'] || '';
    item['subcategory'] = item['Subcategory'] || item['subcategory'] || '';
    item['sku'] = item['SKU'] || item['sku'] || '';
    item['image'] = imageFilename;
    item['availability'] = item['Availability'] || item['availability'] || 'In Stock';
    item['description'] = item['Description'] || item['description'] || '';

    products.push(item);
  }

  state.parsedCsvProducts = products;
  renderImportPreview();
}

function parseCsvLine(text) {
  const result = [];
  let cur = '';
  let inQuotes = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') {
      inQuotes = !inQuotes;
    } else if (c === ',' && !inQuotes) {
      result.push(cur);
      cur = '';
    } else {
      cur += c;
    }
  }
  result.push(cur);
  return result;
}

function renderImportPreview() {
  const card = document.getElementById('importPreviewCard');
  const tbody = document.getElementById('importPreviewTableBody');
  const summaryBar = document.getElementById('validationSummaryBar');
  const countSpan = document.getElementById('importValidCount');
  
  if (!card || !tbody) return;
  card.style.display = 'block';

  let validCount = 0;
  let missingNameCount = 0;
  let invalidPriceCount = 0;

  const rowsHtml = state.parsedCsvProducts.map((p, idx) => {
    const errors = [];
    const warnings = [];

    if (!p.name) errors.push('Missing Name');
    if (isNaN(p.price) || p.price < 0) errors.push('Invalid Price');
    
    let imgSrc = 'https://via.placeholder.com/60';
    if (p.image) {
      if (p.image.startsWith('http')) {
        imgSrc = p.image;
      } else {
        const cleanName = p.image.replace(/^uploads\//, '');
        imgSrc = `../uploads/${cleanName}`;
      }
    } else {
      warnings.push('No Image');
    }

    const isValid = errors.length === 0;
    if (isValid) validCount++;
    if (!p.name) missingNameCount++;
    if (isNaN(p.price) || p.price < 0) invalidPriceCount++;

    return `
      <tr>
        <td>
          ${isValid 
            ? '<span class="badge-valid">✓ Ready</span>' 
            : `<span class="badge-error">✕ ${errors.join(', ')}</span>`}
          ${warnings.length > 0 ? `<br><small class="badge-warn">⚠ ${warnings.join(', ')}</small>` : ''}
        </td>
        <td><img src="${imgSrc}" class="table-img-thumb" onerror="this.src='https://via.placeholder.com/60'" /></td>
        <td>
          <input type="text" class="form-control" value="${p.name}" style="padding:4px 8px; font-size:0.85rem;" onchange="state.parsedCsvProducts[${idx}].name = this.value; renderImportPreview();" />
        </td>
        <td>
          <input type="text" class="form-control" value="${p.brand}" placeholder="Optional" style="width:90px; padding:4px 8px; font-size:0.85rem;" onchange="state.parsedCsvProducts[${idx}].brand = this.value;" />
        </td>
        <td>
          <input type="number" step="0.01" class="form-control" value="${p.price}" style="width:90px; padding:4px 8px; font-size:0.85rem;" onchange="state.parsedCsvProducts[${idx}].price = parseFloat(this.value); renderImportPreview();" />
        </td>
        <td>
          <input type="text" class="form-control" value="${p.category}" style="padding:4px 8px; font-size:0.85rem;" onchange="state.parsedCsvProducts[${idx}].category = this.value;" />
        </td>
        <td>
          <input type="text" class="form-control" value="${p.subcategory}" style="padding:4px 8px; font-size:0.85rem;" onchange="state.parsedCsvProducts[${idx}].subcategory = this.value;" />
        </td>
        <td><input type="text" class="form-control" value="${p.sku}" style="width:90px; padding:4px 8px; font-size:0.85rem;" onchange="state.parsedCsvProducts[${idx}].sku = this.value;" /></td>
        <td>
          <select class="form-control" style="padding:4px; font-size:0.85rem;" onchange="state.parsedCsvProducts[${idx}].availability = this.value;">
            <option value="In Stock" ${p.availability.toLowerCase().includes('in') ? 'selected' : ''}>In Stock</option>
            <option value="Out of Stock" ${p.availability.toLowerCase().includes('out') ? 'selected' : ''}>Out of Stock</option>
          </select>
        </td>
      </tr>
    `;
  }).join('');

  tbody.innerHTML = rowsHtml;
  countSpan.textContent = validCount;

  summaryBar.innerHTML = `
    <span>Total Rows: <strong>${state.parsedCsvProducts.length}</strong></span>
    <span class="badge-valid">Valid: <strong>${validCount}</strong></span>
    ${missingNameCount > 0 ? `<span class="badge-error">Missing Names: <strong>${missingNameCount}</strong></span>` : ''}
    ${invalidPriceCount > 0 ? `<span class="badge-error">Invalid Prices: <strong>${invalidPriceCount}</strong></span>` : ''}
  `;

  document.getElementById('btnConfirmImport').disabled = validCount === 0;
}

function clearImportPreview() {
  state.parsedCsvProducts = [];
  document.getElementById('importPreviewCard').style.display = 'none';
  document.getElementById('csvFileInput').value = '';
  document.getElementById('csvFileNameDisplay').textContent = '';
}

async function confirmBulkImport() {
  const validProducts = state.parsedCsvProducts.filter(p => p.name && !isNaN(p.price) && p.price >= 0);
  if (validProducts.length === 0) {
    showToast('No valid products to import.', 'error');
    return;
  }

  const btn = document.getElementById('btnConfirmImport');
  btn.disabled = true;
  btn.innerHTML = 'Importing Products...';

  try {
    const res = await apiRequest('/api/import/bulk-products', 'POST', { products: validProducts });
    showToast(`Success! Imported ${res.count} products into catalog.`);
    clearImportPreview();
    loadDashboardStats();
    loadNormalCategoriesData();
    loadNormalSubcategoriesData();
    loadBrandsData();
    switchTab('products');
  } catch (err) {
    showToast(err.message || 'Import failed.', 'error');
    btn.disabled = false;
    btn.innerHTML = `<i data-lucide="check-circle"></i> Confirm Import`;
    if (window.lucide) window.lucide.createIcons();
  }
}

// Media Library
async function loadMediaLibrary() {
  const grid = document.getElementById('mediaLibraryGrid');
  if (!grid) return;

  const images = new Set();
  state.normalProducts.forEach(p => { if (p.image) images.add(p.image); });
  state.normalCategories.forEach(c => { if (c.image) images.add(c.image); });

  if (images.size === 0) {
    grid.innerHTML = `<div class="empty-state" style="grid-column: 1/-1;">No images found in catalog. Use the upload button to add images.</div>`;
    return;
  }

  grid.innerHTML = Array.from(images).map(imgUrl => {
    const fullUrl = imgUrl.startsWith('http') ? imgUrl : `../${imgUrl}`;
    const name = imgUrl.split('/').pop();
    return `
      <div class="media-item-card">
        <img src="${fullUrl}" onerror="this.src='https://via.placeholder.com/120'" />
        <div class="media-item-name" title="${name}">${name}</div>
        <button class="btn-link" style="font-size:0.75rem; padding:0.2rem;" onclick="navigator.clipboard.writeText('${imgUrl}'); showToast('Copied path to clipboard!');">Copy Path</button>
      </div>
    `;
  }).join('');
}

async function handleMediaLibraryUpload(event) {
  const files = Array.from(event.target.files);
  if (files.length === 0) return;

  const formData = new FormData();
  files.forEach(f => formData.append('images', f));

  try {
    const res = await apiRequest('/api/upload/images', 'POST', formData, true);
    showToast(`Uploaded ${res.count} images to media library.`);
    loadMediaLibrary();
  } catch (err) {
    showToast(err.message || 'Upload failed.', 'error');
  }
}

// Settings
async function handleChangePassword(e) {
  e.preventDefault();
  const oldPassword = document.getElementById('oldPassword').value;
  const newPassword = document.getElementById('newPassword').value;
  const confirmNewPassword = document.getElementById('confirmNewPassword').value;

  if (newPassword !== confirmNewPassword) {
    showToast('New passwords do not match.', 'error');
    return;
  }

  try {
    await apiRequest('/api/auth/change-password', 'POST', { oldPassword, newPassword });
    showToast('Password changed successfully!');
    document.getElementById('changePasswordForm').reset();
  } catch (err) {
    showToast(err.message || 'Failed to update password.', 'error');
  }
}

async function exportDataBackupJson() {
  try {
    const data = await apiRequest('/api/public-data');
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `tarang_catalog_backup_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
    showToast('Backup JSON downloaded.');
  } catch (err) {
    showToast('Failed to export backup.', 'error');
  }
}

// ---------------------------------------------------------------------------
// OFFERS & PROMOTIONS MANAGEMENT CONTROLLER
// ---------------------------------------------------------------------------
async function loadOffersTable() {
  const tbody = document.getElementById('offersTableBody');
  if (!tbody) return;

  try {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-state">Loading offers...</td></tr>`;
    const offers = await apiRequest('/api/admin/offers');
    state.offers = offers;

    const badge = document.getElementById('badgeOffersCount');
    if (badge) badge.textContent = offers.length;

    if (!offers || offers.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" class="empty-state">No promotional offers found. Click "+ Add New Offer" to create your first promotion!</td></tr>`;
      return;
    }

    tbody.innerHTML = offers.map(o => {
      const themeColors = {
        orange: 'background:#FFF3E0; color:#D84315; border:1px solid #FFCCBC;',
        gold: 'background:#FFFDE7; color:#B78103; border:1px solid #FFE082;',
        emerald: 'background:#E8F8F5; color:#117A65; border:1px solid #A3E4D7;',
        royal: 'background:#EBF5FB; color:#1A5276; border:1px solid #AED6F1;'
      };
      const themeStyle = themeColors[o.bgGradient] || themeColors.orange;
      const themeName = (o.bgGradient || 'orange').toUpperCase();

      const statusBadge = o.isActive
        ? `<span class="badge badge-success" style="cursor:pointer;" onclick="toggleOfferStatus('${o.id}')" title="Click to Deactivate">✓ Live Active</span>`
        : `<span class="badge badge-secondary" style="cursor:pointer; background:#E0E0E0; color:#666;" onclick="toggleOfferStatus('${o.id}')" title="Click to Activate">✕ Inactive</span>`;

      return `
        <tr>
          <td><strong style="color:var(--warm-orange); font-size:1.1rem;">#${o.displayOrder}</strong></td>
          <td>
            <div style="display:flex; flex-direction:column; gap:4px;">
              <span style="font-size:0.75rem; font-weight:800; padding:2px 8px; border-radius:4px; display:inline-block; width:max-content; ${themeStyle}">${o.badgeText || 'OFFER'}</span>
              <small style="color:var(--text-muted); font-size:0.72rem; text-transform:uppercase;">Theme: ${themeName}</small>
            </div>
          </td>
          <td>
            <strong style="font-size:0.95rem; color:var(--text-main);">${escapeHtml(o.title)}</strong>
            ${o.subtitle ? `<div style="font-size:0.8rem; color:var(--warm-orange);">${escapeHtml(o.subtitle)}</div>` : ''}
          </td>
          <td>
            <span style="font-family:'Cinzel', serif; font-weight:900; color:#D82300; font-size:1rem;">${escapeHtml(o.discountText || '—')}</span>
          </td>
          <td>
            ${o.couponCode 
              ? `<code style="background:#FFF0E6; color:#D14B14; font-weight:800; padding:2px 6px; border-radius:4px; font-size:0.85rem;">${escapeHtml(o.couponCode)}</code>` 
              : '<span style="color:#999; font-size:0.8rem;">None</span>'}
          </td>
          <td>
            <span style="font-size:0.8rem; font-weight:600; color:var(--text-main);">${escapeHtml(o.ctaText || 'Explore')}</span>
            <div style="font-size:0.7rem; color:var(--text-muted); font-family:monospace;">${escapeHtml(o.ctaLink || '#')}</div>
          </td>
          <td>${statusBadge}</td>
          <td style="text-align: right;">
            <div style="display:inline-flex; gap:0.4rem;">
              <button class="btn-icon" title="Edit Offer" onclick="openOfferModal('${o.id}')">
                <i data-lucide="edit-2"></i>
              </button>
              <button class="btn-icon danger" title="Delete Offer" onclick="deleteOffer('${o.id}')">
                <i data-lucide="trash-2"></i>
              </button>
            </div>
          </td>
        </tr>
      `;
    }).join('');

    if (window.lucide) window.lucide.createIcons();
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" class="empty-state error">Failed to load offers: ${err.message}</td></tr>`;
  }
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function openOfferModal(offerId = null) {
  const modal = document.getElementById('offerModalOverlay');
  const titleElem = document.getElementById('offerModalTitle');
  const form = document.getElementById('offerForm');
  if (!modal || !form) return;

  form.reset();
  document.getElementById('offerFormId').value = '';
  document.getElementById('offerFormIsActive').checked = true;
  document.getElementById('offerFormCtaText').value = 'Explore Deals';
  document.getElementById('offerFormCtaLink').value = '#categorySection';
  document.getElementById('offerFormTheme').value = 'orange';

  if (offerId && state.offers) {
    const offer = state.offers.find(o => o.id === offerId);
    if (offer) {
      titleElem.textContent = 'Edit Offer & Scheme';
      document.getElementById('offerFormId').value = offer.id;
      document.getElementById('offerFormTitle').value = offer.title || '';
      document.getElementById('offerFormSubtitle').value = offer.subtitle || '';
      document.getElementById('offerFormBadge').value = offer.badgeText || '';
      document.getElementById('offerFormDiscount').value = offer.discountText || '';
      document.getElementById('offerFormDesc').value = offer.description || '';
      document.getElementById('offerFormCoupon').value = offer.couponCode || '';
      document.getElementById('offerFormCtaText').value = offer.ctaText || 'Explore Deals';
      document.getElementById('offerFormCtaLink').value = offer.ctaLink || '#categorySection';
      document.getElementById('offerFormTheme').value = offer.bgGradient || 'orange';
      document.getElementById('offerFormOrder').value = offer.displayOrder || 1;
      document.getElementById('offerFormIsActive').checked = Boolean(offer.isActive);
    }
  } else {
    titleElem.textContent = 'Add New Offer & Promotion';
    const nextOrder = (state.offers && state.offers.length > 0) ? (state.offers.length + 1) : 1;
    document.getElementById('offerFormOrder').value = nextOrder;
  }

  modal.classList.add('open');
  if (window.lucide) window.lucide.createIcons();
}

function closeOfferModal() {
  const modal = document.getElementById('offerModalOverlay');
  if (modal) modal.classList.remove('open');
}

async function saveOffer(e) {
  e.preventDefault();
  const offerId = document.getElementById('offerFormId').value.trim();
  const title = document.getElementById('offerFormTitle').value.trim();
  const subtitle = document.getElementById('offerFormSubtitle').value.trim();
  const badgeText = document.getElementById('offerFormBadge').value.trim();
  const discountText = document.getElementById('offerFormDiscount').value.trim();
  const description = document.getElementById('offerFormDesc').value.trim();
  const couponCode = document.getElementById('offerFormCoupon').value.trim().toUpperCase();
  const ctaText = document.getElementById('offerFormCtaText').value.trim();
  const ctaLink = document.getElementById('offerFormCtaLink').value.trim();
  const bgGradient = document.getElementById('offerFormTheme').value;
  const displayOrder = parseInt(document.getElementById('offerFormOrder').value) || 0;
  const isActive = document.getElementById('offerFormIsActive').checked;

  if (!title) {
    showToast('Please enter an offer title.', 'error');
    return;
  }

  const payload = {
    title, subtitle, badgeText, discountText, description,
    couponCode, ctaText, ctaLink, bgGradient, displayOrder, isActive
  };

  try {
    if (offerId) {
      await apiRequest(`/api/admin/offers/${offerId}`, 'PUT', payload);
      showToast('Offer updated successfully!');
    } else {
      await apiRequest('/api/admin/offers', 'POST', payload);
      showToast('New offer created and live on storefront!');
    }
    closeOfferModal();
    loadOffersTable();
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to save offer.', 'error');
  }
}

async function toggleOfferStatus(offerId) {
  try {
    const res = await apiRequest(`/api/admin/offers/${offerId}/toggle`, 'POST');
    showToast(res.message || 'Offer status updated.');
    loadOffersTable();
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to toggle offer status.', 'error');
  }
}

async function deleteOffer(offerId) {
  const offer = state.offers ? state.offers.find(o => o.id === offerId) : null;
  const name = offer ? offer.title : 'this offer';
  if (!confirm(`Are you sure you want to delete "${name}"?`)) return;

  try {
    await apiRequest(`/api/admin/offers/${offerId}`, 'DELETE');
    showToast('Offer deleted successfully.');
    loadOffersTable();
    loadDashboardStats();
  } catch (err) {
    showToast(err.message || 'Failed to delete offer.', 'error');
  }
}

window.openOfferModal = openOfferModal;
window.closeOfferModal = closeOfferModal;
window.saveOffer = saveOffer;
window.toggleOfferStatus = toggleOfferStatus;
window.deleteOffer = deleteOffer;

