/**
 * Tarang Radios - Main Application Logic
 * Structure: Product Categories -> Category -> Subcategory -> Products (Image, Actual Name, Price)
 * Real-time dynamic CMS connection to central SQLite database.
 */

// Global state container
window.TARANG_DATA = window.TARANG_DATA || { brands: [], categories: [], brandCategories: [], products: [] };

document.addEventListener('DOMContentLoaded', async () => {
  // Initialize Lucide Icons
  if (window.lucide) {
    window.lucide.createIcons();
  }

  // --- STATE MANAGEMENT ---
  let state = {
    priceHidden: localStorage.getItem('tarang_price_hidden') === 'true',
    wishlist: JSON.parse(localStorage.getItem('tarang_wishlist') || '[]'),
    activeSubcategoryFilter: null,
    searchQuery: '',
    categoryFilterQuery: '',
    selectedCategoryForModal: null,
    selectedBrandForModal: null
  };

  // DOM Elements
  const priceToggleInput = document.getElementById('priceToggleInput');
  const priceToggleStatusText = document.getElementById('priceToggleStatusText');
  const profileMenuBtn = document.getElementById('profileMenuBtn');
  const profileMenuPanel = document.getElementById('profileMenuPanel');
  const wishlistToggleBtn = document.getElementById('wishlistToggleBtn');
  const wishlistBadge = document.getElementById('wishlistBadge');
  const wishlistDrawer = document.getElementById('wishlistDrawer');
  const drawerOverlay = document.getElementById('drawerOverlay');
  const closeWishlistBtn = document.getElementById('closeWishlistBtn');
  const wishlistItemsContainer = document.getElementById('wishlistItemsContainer');
  
  const searchInput = document.getElementById('searchInput');
  const searchResultsDropdown = document.getElementById('searchResultsDropdown');
  
  const categoriesGrid = document.getElementById('categoriesGrid');
  const categorySearchInput = document.getElementById('categorySearchInput');
  const clearCategorySearchBtn = document.getElementById('clearCategorySearchBtn');
  const categoryCountDisplay = document.getElementById('categoryCountDisplay');
  const brandsGrid = document.getElementById('brandsGrid');

  const subcategoryModal = document.getElementById('subcategoryModal');
  const modalCloseBtn = document.getElementById('modalCloseBtn');
  const modalCategoryTitle = document.getElementById('modalCategoryTitle');
  const modalCategorySubtitle = document.getElementById('modalCategorySubtitle');
  const modalSubcategoryPills = document.getElementById('modalSubcategoryPills');
  const modalProductsGrid = document.getElementById('modalProductsGrid');

  // --- DYNAMIC DATA FETCHING FROM REST API / SQLITE ---
  async function loadDynamicStoreData() {
    try {
      const res = await fetch('/api/public-data');
      if (res.ok) {
        const liveData = await res.json();
        if (liveData && liveData.categories && liveData.products) {
          window.TARANG_DATA = liveData;
        }
      }
    } catch (err) {
      console.log('Using offline dataset fallback.');
    }
  }

  // Image URL Formatter Helper
  function formatImageUrl(img) {
    if (!img) return 'https://via.placeholder.com/600';
    return img;
  }

  // Price Display Helper (Respects Price Hide Switch)
  function formatPriceHtml(priceNum) {
    if (state.priceHidden) {
      return '';
    }
    const val = Number(priceNum) || 0;
    return `<div class="subcat-product-price">₹${val.toLocaleString('en-IN')}</div>`;
  }

  // --- PRICE HIDE TOGGLE INITIALIZATION ---
  if (priceToggleInput) {
    priceToggleInput.checked = state.priceHidden;
    updatePriceToggleUI();

    priceToggleInput.addEventListener('change', (e) => {
      state.priceHidden = e.target.checked;
      localStorage.setItem('tarang_price_hidden', state.priceHidden);
      updatePriceToggleUI();
      renderWishlist();
      if (state.selectedCategoryForModal || state.selectedBrandForModal) {
        renderModalProducts();
      }
    });
  }

  function updatePriceToggleUI() {
    if (priceToggleStatusText) {
      priceToggleStatusText.textContent = state.priceHidden ? 'Prices Hidden Across Site' : 'Prices Visible Across Site';
    }
  }

  // --- PROFILE MENU TOGGLE ---
  if (profileMenuBtn && profileMenuPanel) {
    profileMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      profileMenuPanel.classList.toggle('open');
    });

    document.addEventListener('click', (e) => {
      if (!profileMenuPanel.contains(e.target) && !profileMenuBtn.contains(e.target)) {
        profileMenuPanel.classList.remove('open');
      }
    });
  }

  // --- WISHLIST DRAWER ---
  function updateWishlistBadge() {
    if (wishlistBadge) {
      wishlistBadge.textContent = state.wishlist.length;
    }
  }

  function toggleWishlist(productId) {
    const idx = state.wishlist.indexOf(productId);
    if (idx > -1) {
      state.wishlist.splice(idx, 1);
    } else {
      state.wishlist.push(productId);
    }
    localStorage.setItem('tarang_wishlist', JSON.stringify(state.wishlist));
    updateWishlistBadge();
    renderWishlist();
    if (state.selectedCategoryForModal || state.selectedBrandForModal) {
      renderModalProducts();
    }
  }

  if (wishlistToggleBtn) {
    wishlistToggleBtn.addEventListener('click', () => {
      wishlistDrawer.classList.add('open');
      drawerOverlay.classList.add('open');
      renderWishlist();
    });
  }

  if (closeWishlistBtn) closeWishlistBtn.addEventListener('click', closeDrawers);
  if (drawerOverlay) drawerOverlay.addEventListener('click', closeDrawers);

  function closeDrawers() {
    if (wishlistDrawer) wishlistDrawer.classList.remove('open');
    if (drawerOverlay) drawerOverlay.classList.remove('open');
    if (subcategoryModal) subcategoryModal.classList.remove('open');
  }

  function renderWishlist() {
    if (!wishlistItemsContainer) return;

    if (state.wishlist.length === 0) {
      wishlistItemsContainer.innerHTML = `
        <div style="text-align: center; padding: 3rem 1rem; color: var(--text-muted);">
          <div style="font-size: 3rem; margin-bottom: 1rem;">📻</div>
          <p style="font-weight: 600;">Your Tarang Wishlist is empty.</p>
          <small>Click the heart icon on any product card to save it here.</small>
        </div>
      `;
      return;
    }

    const items = window.TARANG_DATA.products.filter(p => state.wishlist.includes(p.id));
    wishlistItemsContainer.innerHTML = items.map(p => `
      <div style="display: flex; gap: 1rem; padding: 1rem; background: #FFF8EA; border: 2px solid var(--honey-yellow); border-radius: var(--radius-sm); margin-bottom: 0.85rem; align-items: center;">
        <img src="${formatImageUrl(p.image)}" style="width: 60px; height: 60px; object-fit: cover; border-radius: var(--radius-sm);" onerror="this.src='https://via.placeholder.com/60'" />
        <div style="flex: 1;">
          <h5 style="font-size: 0.95rem; color: var(--text-main); line-height: 1.2; font-weight: 700;">${p.name}</h5>
          ${!state.priceHidden ? `<div style="color:var(--warm-orange); font-weight:800; font-size:0.95rem;">₹${Number(p.price).toLocaleString('en-IN')}</div>` : ''}
        </div>
        <button onclick="window.removeWishlistItem('${p.id}')" style="color: var(--warm-orange); font-size: 1.4rem; font-weight: 800;">&times;</button>
      </div>
    `).join('');
  }

  window.removeWishlistItem = (id) => {
    toggleWishlist(id);
  };

  // --- LIVE SEARCH BAR ---
  if (searchInput && searchResultsDropdown) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.toLowerCase().trim();
      state.searchQuery = q;

      if (!q) {
        searchResultsDropdown.classList.remove('active');
        return;
      }

      const matches = window.TARANG_DATA.products.filter(p => 
        (p.name && p.name.toLowerCase().includes(q)) ||
        (p.sku && p.sku.toLowerCase().includes(q)) ||
        (p.brand && p.brand.toLowerCase().includes(q)) ||
        (p.subcategory && p.subcategory.toLowerCase().includes(q)) ||
        (p.categoryId && p.categoryId.toLowerCase().includes(q))
      );

      if (matches.length === 0) {
        searchResultsDropdown.innerHTML = `<div style="padding: 1rem; color: var(--text-muted); text-align: center; font-weight: 600;">No matching products found for "${q}"</div>`;
      } else {
        searchResultsDropdown.innerHTML = matches.map(p => `
          <div class="search-item" onclick="window.selectSearchProduct('${p.id}')">
            <img src="${formatImageUrl(p.image)}" alt="${p.name}" onerror="this.src='https://via.placeholder.com/60'" />
            <div style="flex:1;">
              <div style="font-weight: 800; font-size: 0.9rem; color: var(--text-main);">${p.name}</div>
              <div style="font-size: 0.75rem; color: var(--warm-orange); font-weight: 700;">${p.subcategory || 'General'}</div>
              ${!state.priceHidden ? `<div style="color:var(--warm-orange); font-weight:800; font-size:0.85rem;">₹${Number(p.price).toLocaleString('en-IN')}</div>` : ''}
            </div>
          </div>
        `).join('');
      }

      searchResultsDropdown.classList.add('active');
    });

    document.addEventListener('click', (e) => {
      if (!searchInput.contains(e.target) && !searchResultsDropdown.contains(e.target)) {
        searchResultsDropdown.classList.remove('active');
      }
    });
  }

  window.selectSearchProduct = (id) => {
    searchResultsDropdown.classList.remove('active');
    const p = window.TARANG_DATA.products.find(item => item.id === id);
    if (!p) return;

    // Find category for this product
    const cat = window.TARANG_DATA.categories.find(c => c.id === p.categoryId) ||
                window.TARANG_DATA.brandCategories?.find(c => c.id === p.categoryId);
    
    if (cat) {
      openCategoryModal(cat, p.subcategory);
    }
  };

  // --- RENDER HIGH-END LUXURY CATEGORIES GRID ---
  function renderCategoriesGrid() {
    if (!categoriesGrid || !window.TARANG_DATA.categories) return;

    let allCats = window.TARANG_DATA.categories;
    const q = (state.categoryFilterQuery || '').toLowerCase().trim();

    let filteredCats = allCats;
    if (q) {
      filteredCats = allCats.filter(cat => {
        const titleMatch = (cat.title || '').toLowerCase().includes(q);
        const subMatch = (cat.subcategories || []).some(s => (s || '').toLowerCase().includes(q));
        const tagMatch = (cat.tagline || '').toLowerCase().includes(q);
        return titleMatch || subMatch || tagMatch;
      });
    }

    if (categoryCountDisplay) {
      categoryCountDisplay.textContent = `${filteredCats.length} ${filteredCats.length === 1 ? 'Category' : 'Categories'}`;
    }

    if (filteredCats.length === 0) {
      categoriesGrid.innerHTML = `
        <div class="category-empty-state">
          <div class="empty-icon">🔍</div>
          <h4>No matching categories found</h4>
          <p>Try searching for a different keyword or view all categories.</p>
          <button class="btn-primary" onclick="window.clearCategoryFilter()" style="margin-top: 1rem; padding: 0.5rem 1.25rem;">
            Show All Categories
          </button>
        </div>
      `;
      return;
    }

    categoriesGrid.innerHTML = filteredCats.map(cat => {
      const subCount = cat.subcategories ? cat.subcategories.length : 0;
      const prodsCount = window.TARANG_DATA.products ? window.TARANG_DATA.products.filter(p => p.categoryId === cat.id).length : 0;
      const displayTagline = cat.tagline || `${prodsCount > 0 ? prodsCount + ' products' : 'Complete catalog'} in ${subCount} ${subCount === 1 ? 'section' : 'subsections'}`;

      return `
        <div class="category-card" onclick="window.selectCategoryCard('${cat.id}')">
          <div class="cat-card-accent-bar"></div>
          <div class="cat-card-img-container">
            <img src="${formatImageUrl(cat.image)}" alt="${cat.title}" loading="lazy" onerror="this.src='https://via.placeholder.com/600'" />
            <div class="cat-card-sub-badge">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 2 7 12 12 22 7 12 2"></polygon><polyline points="2 17 12 22 22 17"></polyline><polyline points="2 12 12 17 22 12"></polyline></svg>
              <span>${subCount} ${subCount === 1 ? 'Subcategory' : 'Subcategories'}</span>
            </div>
          </div>
          <div class="cat-card-body">
            <h3 class="category-card-heading" title="${cat.title}">${cat.title}</h3>
            <p class="category-card-meta">${displayTagline}</p>
            <div class="category-card-action">
              <span class="cat-action-label">Explore Catalog</span>
              <div class="cat-action-circle">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
              </div>
            </div>
          </div>
        </div>
      `;
    }).join('');

    if (window.lucide) window.lucide.createIcons();
  }

  window.clearCategoryFilter = () => {
    state.categoryFilterQuery = '';
    if (categorySearchInput) categorySearchInput.value = '';
    if (clearCategorySearchBtn) clearCategorySearchBtn.style.display = 'none';
    renderCategoriesGrid();
  };

  if (categorySearchInput) {
    categorySearchInput.addEventListener('input', (e) => {
      state.categoryFilterQuery = e.target.value;
      if (clearCategorySearchBtn) {
        clearCategorySearchBtn.style.display = e.target.value.trim() ? 'block' : 'none';
      }
      renderCategoriesGrid();
    });
  }

  if (clearCategorySearchBtn) {
    clearCategorySearchBtn.addEventListener('click', () => {
      window.clearCategoryFilter();
    });
  }

  window.selectCategoryCard = (catId) => {
    const cat = window.TARANG_DATA.categories.find(c => c.id === catId);
    if (cat) {
      openCategoryModal(cat);
    }
  };

  // --- IMAGE ZOOM LIGHTBOX MODAL EVENT ---
  window.openImageZoomModal = (imgUrl, caption) => {
    const modal = document.getElementById('imageZoomModal');
    const displayImg = document.getElementById('zoomedImageDisplay');
    const displayCaption = document.getElementById('zoomedImageCaption');

    if (displayImg) displayImg.src = formatImageUrl(imgUrl);
    if (displayCaption) displayCaption.textContent = caption || '';
    if (modal) modal.classList.add('open');
  };

  const closeZoomModalBtn = document.getElementById('closeZoomModalBtn');
  if (closeZoomModalBtn) {
    closeZoomModalBtn.addEventListener('click', () => {
      const modal = document.getElementById('imageZoomModal');
      if (modal) modal.classList.remove('open');
    });
  }

  const zoomModal = document.getElementById('imageZoomModal');
  if (zoomModal) {
    zoomModal.addEventListener('click', (e) => {
      if (e.target === zoomModal) {
        zoomModal.classList.remove('open');
      }
    });
  }

  // --- CATEGORY & SUBCATEGORY PRODUCT SHOWROOM MODAL ---
  function openCategoryModal(cat, targetSubcategory = null) {
    state.selectedCategoryForModal = cat;
    state.selectedBrandForModal = null;
    state.activeSubcategoryFilter = targetSubcategory;

    const prods = window.TARANG_DATA.products ? window.TARANG_DATA.products.filter(p => p.categoryId === cat.id) : [];
    const subCount = cat.subcategories ? cat.subcategories.length : 0;

    if (modalCategoryTitle) modalCategoryTitle.textContent = cat.title;
    if (modalCategorySubtitle) {
      modalCategorySubtitle.innerHTML = `
        <span class="modal-sub-tagline">${cat.tagline || 'Explore verified catalog components and parts'}</span>
        <div class="modal-meta-chips">
          <span class="meta-chip">📁 ${subCount} ${subCount === 1 ? 'Subcategory' : 'Subcategories'}</span>
          <span class="meta-chip">⚡ ${prods.length} Certified Products</span>
        </div>
      `;
    }

    renderSubcategoryPills();
    renderModalProducts();

    if (subcategoryModal) subcategoryModal.classList.add('open');
  }

  function renderSubcategoryPills() {
    if (!modalSubcategoryPills) return;

    let subcategories = [];
    let products = [];

    if (state.selectedCategoryForModal) {
      subcategories = state.selectedCategoryForModal.subcategories || [];
      products = window.TARANG_DATA.products.filter(p => p.categoryId === state.selectedCategoryForModal.id);
    } else if (state.selectedBrandForModal) {
      const brandCats = window.TARANG_DATA.brandCategories.filter(c => c.brandId === state.selectedBrandForModal.id);
      brandCats.forEach(c => {
        if (c.subcategories) subcategories.push(...c.subcategories);
      });
      subcategories = Array.from(new Set(subcategories));
      products = window.TARANG_DATA.products.filter(p => p.brandId === state.selectedBrandForModal.id || (p.brand && p.brand.toLowerCase() === state.selectedBrandForModal.name.toLowerCase()));
    }

    const totalCount = products.length;
    let html = `
      <button class="sub-pill ${!state.activeSubcategoryFilter ? 'active' : ''}" onclick="window.setSubcategoryFilter(null)">
        <span>All Subcategories</span>
        <span class="sub-pill-count">${totalCount}</span>
      </button>
    `;

    subcategories.forEach(sub => {
      const count = products.filter(p => p.subcategory === sub).length;
      html += `
        <button class="sub-pill ${state.activeSubcategoryFilter === sub ? 'active' : ''}" onclick="window.setSubcategoryFilter('${sub}')">
          <span>${sub}</span>
          <span class="sub-pill-count">${count}</span>
        </button>
      `;
    });

    modalSubcategoryPills.innerHTML = html;
  }

  window.setSubcategoryFilter = (sub) => {
    state.activeSubcategoryFilter = sub;
    renderSubcategoryPills();
    renderModalProducts();
  };

  function renderModalProducts() {
    if (!modalProductsGrid) return;

    let products = [];
    let subcategoriesList = [];

    if (state.selectedCategoryForModal) {
      const cat = state.selectedCategoryForModal;
      products = window.TARANG_DATA.products.filter(p => p.categoryId === cat.id);
      subcategoriesList = cat.subcategories || [];
    } else if (state.selectedBrandForModal) {
      const brand = state.selectedBrandForModal;
      products = window.TARANG_DATA.products.filter(p => p.brandId === brand.id || (p.brand && p.brand.toLowerCase() === brand.name.toLowerCase()));
      
      const brandCats = window.TARANG_DATA.brandCategories.filter(c => c.brandId === brand.id);
      brandCats.forEach(c => {
        if (c.subcategories) subcategoriesList.push(...c.subcategories);
      });
      subcategoriesList = Array.from(new Set(subcategoriesList));
    }

    if (products.length === 0) {
      modalProductsGrid.innerHTML = `
        <div style="text-align: center; padding: 4rem 1rem; color: var(--text-muted); font-weight: 600;">
          <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">📦</div>
          No products listed under this category yet.
        </div>
      `;
      return;
    }

    // Filter by specific subcategory pill if selected
    if (state.activeSubcategoryFilter) {
      const filtered = products.filter(p => p.subcategory === state.activeSubcategoryFilter);
      if (filtered.length === 0) {
        modalProductsGrid.innerHTML = `<div style="text-align: center; padding: 3rem; color: var(--text-muted); font-weight: 600;">No items found in "${state.activeSubcategoryFilter}".</div>`;
        return;
      }

      modalProductsGrid.innerHTML = `
        <div class="subcat-group">
          <div class="subcat-group-header">
            <h4 class="subcat-group-title">${state.activeSubcategoryFilter}</h4>
          </div>
          <div class="subcat-products-grid">
            ${filtered.map(p => renderSingleProductCard(p)).join('')}
          </div>
        </div>
      `;
      return;
    }

    // Group products by their Subcategories (Structure: Category -> Subcategory -> Products)
    let html = '';
    const renderedSubcats = new Set();

    subcategoriesList.forEach(subName => {
      const subProds = products.filter(p => p.subcategory === subName);
      if (subProds.length > 0) {
        renderedSubcats.add(subName);
        html += `
          <div class="subcat-group">
            <div class="subcat-group-header">
              <h4 class="subcat-group-title">${subName}</h4>
            </div>
            <div class="subcat-products-grid">
              ${subProds.map(p => renderSingleProductCard(p)).join('')}
            </div>
          </div>
        `;
      }
    });

    // Uncategorized products directly under category
    const remainingProds = products.filter(p => !p.subcategory || !renderedSubcats.has(p.subcategory));
    if (remainingProds.length > 0) {
      html += `
        <div class="subcat-group">
          <div class="subcat-group-header">
            <h4 class="subcat-group-title">${subcategoriesList.length > 0 ? 'General Products' : 'Products'}</h4>
          </div>
          <div class="subcat-products-grid">
            ${remainingProds.map(p => renderSingleProductCard(p)).join('')}
          </div>
        </div>
      `;
    }

    modalProductsGrid.innerHTML = html;
  }

  // Single Product Card Markup: Product Image, Actual Product Name, Price
  function renderSingleProductCard(p) {
    const isWishlisted = state.wishlist.includes(p.id);
    const safeName = (p.name || '').replace(/'/g, "\\'");
    const priceContent = formatPriceHtml(p.price);

    return `
      <div class="subcat-product-card" onclick="window.openImageZoomModal('${p.image}', '${safeName}')">
        <div class="subcat-card-img-container">
          <img src="${formatImageUrl(p.image)}" alt="${p.name}" loading="lazy" onerror="this.src='https://via.placeholder.com/600'" />
          <button class="card-wishlist-btn ${isWishlisted ? 'active' : ''}" title="${isWishlisted ? 'Selected in Wishlist' : 'Select to Wishlist'}" onclick="event.stopPropagation(); window.toggleProductWishlist('${p.id}')">
            ♥
          </button>
        </div>
        <div class="subcat-card-content">
          <h4 class="subcat-product-name">${p.name}</h4>
          ${priceContent}
        </div>
      </div>
    `;
  }

  window.toggleProductWishlist = (id) => {
    toggleWishlist(id);
    if (subcategoryModal && subcategoryModal.classList.contains('open')) {
      renderModalProducts();
    }
  };

  if (modalCloseBtn) {
    modalCloseBtn.addEventListener('click', () => {
      if (subcategoryModal) subcategoryModal.classList.remove('open');
    });
  }

  // --- THE BRANDS WE DEAL WITH SECTION ---
  function renderBrands() {
    if (!brandsGrid || !window.TARANG_DATA.brands) return;
    brandsGrid.innerHTML = window.TARANG_DATA.brands.map(b => `
      <div class="brand-card" onclick="window.filterByBrand('${b.id}', '${(b.name || '').replace(/'/g, "\\'")}')">
        <div class="brand-logo-text">${b.name}</div>
      </div>
    `).join('');
  }

  window.filterByBrand = (brandId, brandName) => {
    const brand = window.TARANG_DATA.brands.find(b => b.id === brandId || b.name.toLowerCase() === brandName.toLowerCase());
    if (!brand) return;

    state.selectedBrandForModal = brand;
    state.selectedCategoryForModal = null;
    state.activeSubcategoryFilter = null;

    if (modalCategoryTitle) modalCategoryTitle.textContent = `${brand.name} Products`;
    if (modalCategorySubtitle) modalCategorySubtitle.textContent = `Official catalog & spare parts from ${brand.name}`;

    renderSubcategoryPills();
    renderModalProducts();

    if (subcategoryModal) subcategoryModal.classList.add('open');
  };

  // Contact Form
  const contactForm = document.getElementById('contactForm');
  if (contactForm) {
    contactForm.addEventListener('submit', (e) => {
      e.preventDefault();
      alert('Thank you for contacting Tarang Radios! Our radio specialist will call/WhatsApp you shortly.');
      contactForm.reset();
    });
  }

  // Load dynamic data first then initialize UI
  await loadDynamicStoreData();
  updateWishlistBadge();
  renderCategoriesGrid();
  renderBrands();
});
