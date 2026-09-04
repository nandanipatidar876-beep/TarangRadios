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
    cart: JSON.parse(localStorage.getItem('tarang_cart') || '[]'),
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
  const profileCartCount = document.getElementById('profileCartCount');
  
  const wishlistToggleBtn = document.getElementById('wishlistToggleBtn');
  const wishlistBadge = document.getElementById('wishlistBadge');
  const wishlistDrawer = document.getElementById('wishlistDrawer');
  const drawerOverlay = document.getElementById('drawerOverlay');
  const closeWishlistBtn = document.getElementById('closeWishlistBtn');
  const wishlistItemsContainer = document.getElementById('wishlistItemsContainer');

  const cartToggleBtn = document.getElementById('cartToggleBtn');
  const cartBadge = document.getElementById('cartBadge');
  const cartDrawer = document.getElementById('cartDrawer');
  const closeCartBtn = document.getElementById('closeCartBtn');
  const cartItemsContainer = document.getElementById('cartItemsContainer');
  const cartTotalItems = document.getElementById('cartTotalItems');
  const cartGrandTotal = document.getElementById('cartGrandTotal');
  const cartSubtotalRow = document.getElementById('cartSubtotalRow');
  const cartToast = document.getElementById('cartToast');
  const cartToastTitle = document.getElementById('cartToastTitle');
  const cartToastSub = document.getElementById('cartToastSub');
  
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
          updateCartBadge();
          renderCart();
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
      return '<div class="subcat-product-price" style="font-size: 0.78rem; color: var(--text-muted); font-weight: 700;">Price Hidden</div>';
    }
    const val = Number(priceNum) || 0;
    if (val <= 0) {
      return '<div class="subcat-product-price" style="font-size: 0.8rem; color: #B84A14; font-weight: 800;">Price on Request</div>';
    }
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
      renderCart();
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

  // --- WISHLIST & CART DRAWER HANDLERS ---
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
      if (cartDrawer) cartDrawer.classList.remove('open');
      wishlistDrawer.classList.add('open');
      drawerOverlay.classList.add('open');
      renderWishlist();
    });
  }

  if (cartToggleBtn) {
    cartToggleBtn.addEventListener('click', () => {
      if (wishlistDrawer) wishlistDrawer.classList.remove('open');
      if (cartDrawer) cartDrawer.classList.add('open');
      if (drawerOverlay) drawerOverlay.classList.add('open');
      renderCart();
    });
  }

  if (closeWishlistBtn) closeWishlistBtn.addEventListener('click', closeDrawers);
  if (closeCartBtn) closeCartBtn.addEventListener('click', closeDrawers);
  if (drawerOverlay) drawerOverlay.addEventListener('click', closeDrawers);

  function closeDrawers() {
    if (wishlistDrawer) wishlistDrawer.classList.remove('open');
    if (cartDrawer) cartDrawer.classList.remove('open');
    if (drawerOverlay) drawerOverlay.classList.remove('open');
    if (subcategoryModal) subcategoryModal.classList.remove('open');
  }

  // --- SHOPPING CART STATE & LOGIC ---
  function updateCartBadge() {
    const totalItems = state.cart.reduce((sum, item) => sum + (item.qty || 1), 0);
    if (cartBadge) {
      cartBadge.textContent = totalItems;
    }
    if (profileCartCount) {
      profileCartCount.textContent = totalItems;
    }
  }

  let cartToastTimer = null;
  function showCartToast(title, sub) {
    if (!cartToast) return;
    if (cartToastTitle) cartToastTitle.textContent = title || 'Item added to cart';
    if (cartToastSub) cartToastSub.textContent = sub || 'Click View Cart to inspect your order';
    cartToast.classList.add('show');
    if (cartToastTimer) clearTimeout(cartToastTimer);
    cartToastTimer = setTimeout(() => {
      cartToast.classList.remove('show');
    }, 3200);
  }

  function addToCart(productId, qty = 1, showToast = true) {
    const existingIndex = state.cart.findIndex(item => item.id === productId);
    let newQty = qty;
    if (existingIndex > -1) {
      state.cart[existingIndex].qty += qty;
      newQty = state.cart[existingIndex].qty;
    } else {
      state.cart.push({ id: productId, qty: qty });
    }
    localStorage.setItem('tarang_cart', JSON.stringify(state.cart));
    updateCartBadge();
    renderCart();

    const p = window.TARANG_DATA.products ? window.TARANG_DATA.products.find(item => item.id === productId) : null;
    const name = p ? p.name : 'Product';

    if (showToast) {
      showCartToast(`Added to Cart: ${name}`, `${newQty} unit${newQty > 1 ? 's' : ''} in cart • Tap to view`);
    }

    if (cartBadge) {
      cartBadge.classList.remove('cart-badge-pulse');
      void cartBadge.offsetWidth;
      cartBadge.classList.add('cart-badge-pulse');
    }
  }

  function updateCartQty(productId, delta) {
    const idx = state.cart.findIndex(item => item.id === productId);
    if (idx > -1) {
      state.cart[idx].qty += delta;
      if (state.cart[idx].qty <= 0) {
        state.cart.splice(idx, 1);
      }
      localStorage.setItem('tarang_cart', JSON.stringify(state.cart));
      updateCartBadge();
      renderCart();
      if (subcategoryModal && subcategoryModal.classList.contains('open')) {
        renderModalProducts();
      }
    }
  }

  function removeFromCart(productId) {
    const idx = state.cart.findIndex(item => item.id === productId);
    if (idx > -1) {
      state.cart.splice(idx, 1);
      localStorage.setItem('tarang_cart', JSON.stringify(state.cart));
      updateCartBadge();
      renderCart();
      if (subcategoryModal && subcategoryModal.classList.contains('open')) {
        renderModalProducts();
      }
    }
  }

  function clearCart() {
    if (state.cart.length === 0) return;
    if (confirm('Are you sure you want to empty your shopping cart?')) {
      state.cart = [];
      localStorage.setItem('tarang_cart', JSON.stringify(state.cart));
      updateCartBadge();
      renderCart();
      if (subcategoryModal && subcategoryModal.classList.contains('open')) {
        renderModalProducts();
      }
    }
  }

  window.addToCart = addToCart;
  window.updateCartItemQty = updateCartQty;
  window.removeCartItem = removeFromCart;
  window.clearCart = clearCart;

  window.handleAddToCart = (event, id) => {
    if (event) event.stopPropagation();
    addToCart(id, 1, true);

    const btn = document.getElementById(`cartBtn_${id}`);
    if (btn) {
      btn.classList.add('added-success');
      btn.innerHTML = `<span>✓ Added</span>`;
      setTimeout(() => {
        btn.classList.remove('added-success');
        const entry = state.cart.find(item => item.id === id);
        const qty = entry ? entry.qty : 0;
        btn.innerHTML = `
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="8" cy="21" r="1"/>
            <circle cx="19" cy="21" r="1"/>
            <path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>
          </svg>
          <span>${qty > 0 ? `In Cart (${qty})` : 'Add to Cart'}</span>
        `;
        if (qty > 0) {
          btn.classList.add('in-cart');
        } else {
          btn.classList.remove('in-cart');
        }
      }, 1200);
    }
  };

  function renderCart() {
    if (!cartItemsContainer) return;

    if (state.cart.length === 0) {
      cartItemsContainer.innerHTML = `
        <div class="cart-empty-state">
          <div class="cart-empty-icon">🛒</div>
          <h4 class="cart-empty-title">Your Cart is Empty</h4>
          <p class="cart-empty-desc">Explore our electronic components, relays, cables, and brand catalogs to add items.</p>
          <button class="cart-shop-now-btn" onclick="document.getElementById('cartDrawer').classList.remove('open'); document.getElementById('drawerOverlay').classList.remove('open'); document.getElementById('categoriesGrid').scrollIntoView({behavior: 'smooth'});">
            Browse Categories
          </button>
        </div>
      `;
      if (cartTotalItems) cartTotalItems.textContent = '0 Items';
      if (cartGrandTotal) cartGrandTotal.textContent = '₹0';
      const cartFooter = document.getElementById('cartFooter');
      if (cartFooter) cartFooter.style.opacity = '0.6';
      return;
    }

    const cartFooter = document.getElementById('cartFooter');
    if (cartFooter) cartFooter.style.opacity = '1';

    let totalItems = 0;
    let grandTotal = 0;

    const html = state.cart.map(entry => {
      const p = window.TARANG_DATA.products ? window.TARANG_DATA.products.find(item => item.id === entry.id) : null;
      if (!p) {
        return `
          <div class="cart-item-card">
            <div class="cart-item-details">
              <h5 class="cart-item-title">Product (${entry.id})</h5>
              <div class="cart-item-bottom-row">
                <div class="cart-qty-stepper">
                  <button class="cart-qty-btn" onclick="window.updateCartItemQty('${entry.id}', -1)">−</button>
                  <span class="cart-qty-val">${entry.qty}</span>
                  <button class="cart-qty-btn" onclick="window.updateCartItemQty('${entry.id}', 1)">+</button>
                </div>
                <button class="cart-item-delete" onclick="window.removeCartItem('${entry.id}')" title="Remove item">&times;</button>
              </div>
            </div>
          </div>
        `;
      }

      const unitPrice = Number(p.price) || 0;
      const lineTotal = unitPrice * entry.qty;
      totalItems += entry.qty;
      grandTotal += lineTotal;

      return `
        <div class="cart-item-card" id="cartItem_${p.id}">
          <img src="${formatImageUrl(p.image)}" alt="${p.name}" class="cart-item-img" onerror="this.src='https://via.placeholder.com/60'" />
          <div class="cart-item-details">
            <h5 class="cart-item-title" title="${p.name}">${p.name}</h5>
            <div class="cart-item-meta">
              <span class="cart-item-subcat">${p.subcategory || p.brand || 'General'}</span>
              ${!state.priceHidden ? `<span class="cart-item-price">₹${unitPrice.toLocaleString('en-IN')}</span>` : '<span class="cart-item-price" style="font-size: 0.75rem; color: var(--text-muted);">Price on Request</span>'}
            </div>
            <div class="cart-item-bottom-row">
              <div class="cart-qty-stepper">
                <button class="cart-qty-btn" onclick="window.updateCartItemQty('${p.id}', -1)" aria-label="Decrease quantity">−</button>
                <span class="cart-qty-val">${entry.qty}</span>
                <button class="cart-qty-btn" onclick="window.updateCartItemQty('${p.id}', 1)" aria-label="Increase quantity">+</button>
              </div>
              ${!state.priceHidden ? `<div class="cart-item-total">₹${lineTotal.toLocaleString('en-IN')}</div>` : ''}
              <button class="cart-item-delete" onclick="window.removeCartItem('${p.id}')" title="Remove item" aria-label="Remove item">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>
              </button>
            </div>
          </div>
        </div>
      `;
    }).join('');

    cartItemsContainer.innerHTML = html;
    if (cartTotalItems) cartTotalItems.textContent = `${totalItems} ${totalItems === 1 ? 'Item' : 'Items'}`;
    if (cartGrandTotal) {
      cartGrandTotal.textContent = !state.priceHidden ? `₹${grandTotal.toLocaleString('en-IN')}` : 'Price on Request';
    }
  }

  // --- CHECKOUT VIA WHATSAPP (+91 9907473375) ---
  window.checkoutViaWhatsApp = () => {
    if (state.cart.length === 0) {
      alert('Your cart is empty! Please add products before sending an order or inquiry.');
      return;
    }

    let message = `*TARANG RADIOS - ORDER & INQUIRY*\n`;
    message += `------------------------------------\n`;
    message += `Hello Tarang Radios, I would like to inquire/order the following items from my cart:\n\n`;

    let totalItems = 0;
    let grandTotal = 0;

    state.cart.forEach((entry, idx) => {
      const p = window.TARANG_DATA.products ? window.TARANG_DATA.products.find(item => item.id === entry.id) : null;
      const name = p ? p.name : entry.id;
      const price = p ? Number(p.price) || 0 : 0;
      const lineTotal = price * entry.qty;
      totalItems += entry.qty;
      grandTotal += lineTotal;

      if (!state.priceHidden && price > 0) {
        message += `${idx + 1}. *${name}*\n   Qty: ${entry.qty} × ₹${price.toLocaleString('en-IN')} = *₹${lineTotal.toLocaleString('en-IN')}*\n`;
      } else {
        message += `${idx + 1}. *${name}*\n   Qty: ${entry.qty} (Price on Request)\n`;
      }
    });

    message += `------------------------------------\n`;
    message += `*Total Items:* ${totalItems}\n`;
    if (!state.priceHidden && grandTotal > 0) {
      message += `*Estimated Grand Total:* ₹${grandTotal.toLocaleString('en-IN')}\n`;
    }
    message += `\nPlease confirm availability, delivery timelines, and dealer/bulk pricing.\nThank you!`;

    const encoded = encodeURIComponent(message);
    window.open(`https://wa.me/919907473375?text=${encoded}`, '_blank');
  };

  // --- CHECKOUT VIA WEB INQUIRY FORM ---
  window.checkoutViaInquiryForm = () => {
    if (state.cart.length === 0) {
      alert('Your cart is empty! Please add products before sending an inquiry.');
      return;
    }

    let text = `Order / Inquiry Items from Cart:\n`;
    let totalItems = 0;
    let grandTotal = 0;

    state.cart.forEach((entry, idx) => {
      const p = window.TARANG_DATA.products ? window.TARANG_DATA.products.find(item => item.id === entry.id) : null;
      const name = p ? p.name : entry.id;
      const price = p ? Number(p.price) || 0 : 0;
      const lineTotal = price * entry.qty;
      totalItems += entry.qty;
      grandTotal += lineTotal;

      if (!state.priceHidden && price > 0) {
        text += `${idx + 1}. ${name} — Qty: ${entry.qty} (₹${lineTotal.toLocaleString('en-IN')})\n`;
      } else {
        text += `${idx + 1}. ${name} — Qty: ${entry.qty}\n`;
      }
    });

    text += `\nTotal Items: ${totalItems}`;
    if (!state.priceHidden && grandTotal > 0) {
      text += ` | Estimated Total: ₹${grandTotal.toLocaleString('en-IN')}`;
    }
    text += `\nPlease let me know availability and delivery details.`;

    const inquiryMsg = document.getElementById('inquiryMsg');
    if (inquiryMsg) {
      inquiryMsg.value = text;
    }

    closeDrawers();
    const contactSection = document.getElementById('contactSection');
    if (contactSection) {
      contactSection.scrollIntoView({ behavior: 'smooth' });
    }
    const userName = document.getElementById('userName');
    if (userName) {
      setTimeout(() => userName.focus(), 600);
    }
  };

  // Initial cart count rendering
  updateCartBadge();
  renderCart();

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
  let currentZoomProductId = null;

  window.openImageZoomModal = (imgUrl, caption, productId = null) => {
    currentZoomProductId = productId;
    const modal = document.getElementById('imageZoomModal');
    const displayImg = document.getElementById('zoomedImageDisplay');
    const displayCaption = document.getElementById('zoomedImageCaption');
    const zoomAddToCartBtn = document.getElementById('zoomAddToCartBtn');

    if (displayImg) displayImg.src = formatImageUrl(imgUrl);
    if (displayCaption) displayCaption.textContent = caption || '';
    if (zoomAddToCartBtn) {
      zoomAddToCartBtn.style.display = productId ? 'inline-flex' : 'none';
      zoomAddToCartBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>
        <span>Add to Cart</span>
      `;
    }
    if (modal) modal.classList.add('open');
  };

  window.addZoomProductToCart = () => {
    if (!currentZoomProductId) return;
    window.addToCart(currentZoomProductId, 1);
    const zoomAddToCartBtn = document.getElementById('zoomAddToCartBtn');
    if (zoomAddToCartBtn) {
      zoomAddToCartBtn.innerHTML = `<span>✓ Added to Cart</span>`;
      setTimeout(() => {
        if (zoomAddToCartBtn) {
          zoomAddToCartBtn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>
            <span>Add to Cart</span>
          `;
        }
      }, 1200);
    }
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

    let pillsList = [];
    let products = [];

    if (state.selectedCategoryForModal) {
      const cat = state.selectedCategoryForModal;
      products = window.TARANG_DATA.products.filter(p => p.categoryId === cat.id);
      const subcategories = cat.subcategories || [];
      
      pillsList.push({
        label: 'All Subcategories',
        id: null,
        count: products.length
      });

      subcategories.forEach(sub => {
        const count = products.filter(p => p.subcategory === sub).length;
        pillsList.push({
          label: sub,
          id: sub,
          count: count
        });
      });
    } else if (state.selectedBrandForModal) {
      const brand = state.selectedBrandForModal;
      products = window.TARANG_DATA.products.filter(p => 
        p.brandId === brand.id || (p.brand && p.brand.toLowerCase() === brand.name.toLowerCase())
      );

      pillsList.push({
        label: `All ${brand.name} Products`,
        id: null,
        count: products.length
      });

      // Collect Brand Categories
      const brandCats = window.TARANG_DATA.brandCategories.filter(c => c.brandId === brand.id);
      if (brandCats.length > 0) {
        brandCats.forEach(c => {
          const count = products.filter(p => p.categoryId === c.id || (p.category_title && p.category_title.toLowerCase() === c.title.toLowerCase())).length;
          pillsList.push({
            label: c.title,
            id: `cat:${c.id}`,
            count: count
          });
        });
      } else {
        // Collect distinct subcategories if no brand categories
        const distinctSubs = Array.from(new Set(products.map(p => p.subcategory).filter(Boolean)));
        distinctSubs.forEach(sub => {
          const count = products.filter(p => p.subcategory === sub).length;
          pillsList.push({
            label: sub,
            id: sub,
            count: count
          });
        });
      }
    }

    modalSubcategoryPills.innerHTML = pillsList.map(pill => {
      const isActive = state.activeSubcategoryFilter === pill.id;
      const safeId = pill.id ? `'${pill.id.replace(/'/g, "\\'")}'` : 'null';
      return `
        <button class="sub-pill ${isActive ? 'active' : ''}" onclick="window.setSubcategoryFilter(${safeId})">
          <span>${pill.label}</span>
          <span class="sub-pill-count">${pill.count}</span>
        </button>
      `;
    }).join('');
  }

  window.setSubcategoryFilter = (filterKey) => {
    state.activeSubcategoryFilter = filterKey;
    renderSubcategoryPills();
    renderModalProducts();
  };

  function renderModalProducts() {
    if (!modalProductsGrid) return;

    let products = [];
    let isBrandView = false;
    let brandCats = [];

    if (state.selectedCategoryForModal) {
      const cat = state.selectedCategoryForModal;
      products = window.TARANG_DATA.products.filter(p => p.categoryId === cat.id);
    } else if (state.selectedBrandForModal) {
      isBrandView = true;
      const brand = state.selectedBrandForModal;
      products = window.TARANG_DATA.products.filter(p => 
        p.brandId === brand.id || (p.brand && p.brand.toLowerCase() === brand.name.toLowerCase())
      );
      brandCats = window.TARANG_DATA.brandCategories.filter(c => c.brandId === brand.id);
    }

    if (products.length === 0) {
      modalProductsGrid.innerHTML = `
        <div style="text-align: center; padding: 4rem 1rem; color: var(--text-muted); font-weight: 600;">
          <div style="font-size: 2.8rem; margin-bottom: 0.5rem;">📦</div>
          <h4>No products listed here yet</h4>
          <p>Check back soon or explore other categories.</p>
        </div>
      `;
      return;
    }

    // Filter active selection
    if (state.activeSubcategoryFilter) {
      let filtered = products;
      const filter = state.activeSubcategoryFilter;

      if (filter.startsWith('cat:')) {
        const targetCatId = filter.replace('cat:', '');
        const targetCat = brandCats.find(c => c.id === targetCatId);
        filtered = products.filter(p => p.categoryId === targetCatId || (targetCat && p.category_title && p.category_title.toLowerCase() === targetCat.title.toLowerCase()));
      } else {
        filtered = products.filter(p => p.subcategory === filter);
      }

      if (filtered.length === 0) {
        modalProductsGrid.innerHTML = `<div style="text-align: center; padding: 3rem; color: var(--text-muted); font-weight: 600;">No items found under this filter.</div>`;
        return;
      }

      const activeLabel = filter.startsWith('cat:') 
        ? (brandCats.find(c => c.id === filter.replace('cat:', ''))?.title || 'Selected Category')
        : filter;

      modalProductsGrid.innerHTML = `
        <div class="subcat-group">
          <div class="subcat-group-header">
            <h4 class="subcat-group-title">${activeLabel}</h4>
            <span class="badge-stock in-stock" style="font-size: 0.8rem; padding: 3px 10px;">${filtered.length} Items</span>
          </div>
          <div class="subcat-products-grid">
            ${filtered.map(p => renderSingleProductCard(p)).join('')}
          </div>
        </div>
      `;
      return;
    }

    // Default "All Products" view
    let html = '';

    if (isBrandView && brandCats.length > 0) {
      // Group by Brand Categories
      const renderedCatIds = new Set();

      brandCats.forEach(cat => {
        const catProds = products.filter(p => p.categoryId === cat.id || (p.category_title && p.category_title.toLowerCase() === cat.title.toLowerCase()));
        if (catProds.length > 0) {
          renderedCatIds.add(cat.id);
          html += `
            <div class="subcat-group">
              <div class="subcat-group-header">
                <h4 class="subcat-group-title">${cat.title}</h4>
                <span class="badge-stock in-stock" style="font-size: 0.78rem; padding: 2px 8px;">${catProds.length} ${catProds.length === 1 ? 'Item' : 'Items'}</span>
              </div>
              <div class="subcat-products-grid">
                ${catProds.map(p => renderSingleProductCard(p)).join('')}
              </div>
            </div>
          `;
        }
      });

      // Remaining products
      const remainingProds = products.filter(p => !renderedCatIds.has(p.categoryId));
      if (remainingProds.length > 0) {
        html += `
          <div class="subcat-group">
            <div class="subcat-group-header">
              <h4 class="subcat-group-title">Additional Products</h4>
              <span class="badge-stock in-stock" style="font-size: 0.78rem; padding: 2px 8px;">${remainingProds.length} Items</span>
            </div>
            <div class="subcat-products-grid">
              ${remainingProds.map(p => renderSingleProductCard(p)).join('')}
            </div>
          </div>
        `;
      }
    } else {
      // Normal Category: Group by Subcategories
      const cat = state.selectedCategoryForModal;
      const subcategoriesList = (cat && cat.subcategories) ? cat.subcategories : [];
      const renderedSubcats = new Set();

      subcategoriesList.forEach(subName => {
        const subProds = products.filter(p => p.subcategory === subName);
        if (subProds.length > 0) {
          renderedSubcats.add(subName);
          html += `
            <div class="subcat-group">
              <div class="subcat-group-header">
                <h4 class="subcat-group-title">${subName}</h4>
                <span class="badge-stock in-stock" style="font-size: 0.78rem; padding: 2px 8px;">${subProds.length} ${subProds.length === 1 ? 'Item' : 'Items'}</span>
              </div>
              <div class="subcat-products-grid">
                ${subProds.map(p => renderSingleProductCard(p)).join('')}
              </div>
            </div>
          `;
        }
      });

      const remainingProds = products.filter(p => !p.subcategory || !renderedSubcats.has(p.subcategory));
      if (remainingProds.length > 0) {
        html += `
          <div class="subcat-group">
            <div class="subcat-group-header">
              <h4 class="subcat-group-title">${subcategoriesList.length > 0 ? 'General Products' : 'Products'}</h4>
              <span class="badge-stock in-stock" style="font-size: 0.78rem; padding: 2px 8px;">${remainingProds.length} Items</span>
            </div>
            <div class="subcat-products-grid">
              ${remainingProds.map(p => renderSingleProductCard(p)).join('')}
            </div>
          </div>
        `;
      }
    }

    modalProductsGrid.innerHTML = html;
  }

  // Single Product Card Markup: Product Image, Actual Product Name, Price & Add to Cart
  function renderSingleProductCard(p) {
    const isWishlisted = state.wishlist.includes(p.id);
    const cartEntry = state.cart.find(item => item.id === p.id);
    const inCartQty = cartEntry ? cartEntry.qty : 0;
    const safeName = (p.name || '').replace(/'/g, "\\'");
    const priceContent = formatPriceHtml(p.price);

    return `
      <div class="subcat-product-card" onclick="window.openImageZoomModal('${p.image}', '${safeName}', '${p.id}')">
        <div class="subcat-card-img-container">
          <img src="${formatImageUrl(p.image)}" alt="${p.name}" loading="lazy" onerror="this.src='https://via.placeholder.com/600'" />
          <button class="card-wishlist-btn ${isWishlisted ? 'active' : ''}" title="${isWishlisted ? 'Selected in Wishlist' : 'Select to Wishlist'}" onclick="event.stopPropagation(); window.toggleProductWishlist('${p.id}')">
            ♥
          </button>
        </div>
        <div class="subcat-card-content">
          <h4 class="subcat-product-name" title="${p.name}">${p.name}</h4>
          <div class="subcat-card-bottom-row">
            ${priceContent}
            <button class="subcat-cart-btn ${inCartQty > 0 ? 'in-cart' : ''}" id="cartBtn_${p.id}" title="${inCartQty > 0 ? inCartQty + ' in cart' : 'Add to cart'}" onclick="window.handleAddToCart(event, '${p.id}')">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">
                <circle cx="8" cy="21" r="1"/>
                <circle cx="19" cy="21" r="1"/>
                <path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/>
              </svg>
              <span>${inCartQty > 0 ? `In Cart (${inCartQty})` : 'Add to Cart'}</span>
            </button>
          </div>
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

  // --- THE BRANDS WE DEAL WITH SECTION (PREMIUM SHOWCASE) ---
  function renderBrands() {
    if (!brandsGrid || !window.TARANG_DATA.brands) return;

    brandsGrid.innerHTML = window.TARANG_DATA.brands.map((b, idx) => {
      const bProdsCount = window.TARANG_DATA.products ? window.TARANG_DATA.products.filter(p => p.brandId === b.id || (p.brand && p.brand.toLowerCase() === b.name.toLowerCase())).length : 0;
      const bCatsCount = window.TARANG_DATA.brandCategories ? window.TARANG_DATA.brandCategories.filter(c => c.brandId === b.id).length : 0;
      
      const badgeText = bProdsCount > 0 
        ? `${bProdsCount} Verified Products` 
        : (bCatsCount > 0 ? `${bCatsCount} Categories` : 'Official Partner');

      // Stagger delay between 80ms - 120ms (using 95ms for ultra-smooth fluid cascading)
      const staggerDelay = idx * 95;

      return `
        <div class="brand-card" style="--brand-stagger-delay: ${staggerDelay}ms;" role="button" tabindex="0" onkeydown="if(event.key==='Enter'||event.key===' '){event.preventDefault(); window.filterByBrand('${b.id}', '${(b.name || '').replace(/'/g, "\\'")}')}" onclick="window.filterByBrand('${b.id}', '${(b.name || '').replace(/'/g, "\\'")}')">
          <!-- Subtle Inner Golden Radial Glow -->
          <div class="brand-card-glow" aria-hidden="true"></div>
          
          <!-- Single Light-Sweep Shimmer on Hover -->
          <div class="brand-shimmer" aria-hidden="true"></div>

          <!-- Top Status Pill -->
          <div class="brand-card-header">
            <span class="brand-partner-badge">
              <span class="brand-badge-dot"></span>
              <span>AUTHORISED</span>
            </span>
          </div>

          <!-- Center Brand Identity & Volume -->
          <div class="brand-card-main">
            <div class="brand-logo-text">${b.name}</div>
            <div class="brand-meta-row">
              <span class="brand-products-count">${badgeText}</span>
            </div>
          </div>

          <!-- Bottom Action Prompt & Interactive Arrow -->
          <div class="brand-card-footer">
            <span class="brand-action-text">Explore Catalog</span>
            <svg class="brand-card-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
              <path d="M5 12h14"></path>
              <path d="m12 5 7 7-7 7"></path>
            </svg>
          </div>

          <!-- Animated Bottom Golden Accent Line -->
          <div class="brand-bottom-line" aria-hidden="true"></div>
        </div>
      `;
    }).join('');

    initBrandsSectionAnimations();
  }

  // Brands Section Scroll-Reveal Observer
  const initBrandsSectionAnimations = () => {
    const brandsSection = document.getElementById('brandsSection');
    if (!brandsSection) return;

    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            brandsSection.classList.add('brands-in-view');
            observer.unobserve(brandsSection);
          }
        });
      }, { threshold: 0.18, rootMargin: '0px 0px -40px 0px' });

      observer.observe(brandsSection);
    } else {
      brandsSection.classList.add('brands-in-view');
    }
  };


  window.filterByBrand = (brandId, brandName) => {
    const brand = window.TARANG_DATA.brands.find(b => b.id === brandId || b.name.toLowerCase() === brandName.toLowerCase());
    if (!brand) return;

    state.selectedBrandForModal = brand;
    state.selectedCategoryForModal = null;
    state.activeSubcategoryFilter = null;

    const brandProds = window.TARANG_DATA.products ? window.TARANG_DATA.products.filter(p => p.brandId === brand.id || (p.brand && p.brand.toLowerCase() === brand.name.toLowerCase())) : [];
    const brandCats = window.TARANG_DATA.brandCategories ? window.TARANG_DATA.brandCategories.filter(c => c.brandId === brand.id) : [];

    if (modalCategoryTitle) modalCategoryTitle.textContent = `${brand.name} Official Catalog`;
    if (modalCategorySubtitle) {
      modalCategorySubtitle.innerHTML = `
        <span class="modal-sub-tagline">Genuine components, soldering equipment & tools from ${brand.name}</span>
        <div class="modal-meta-chips">
          <span class="meta-chip">🏷️ Official Brand</span>
          <span class="meta-chip">📁 ${brandCats.length} Categories</span>
          <span class="meta-chip">⚡ ${brandProds.length} Verified Products</span>
        </div>
      `;
    }

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

  // ==========================================================================
  // ABOUT US SECTION - INTERACTIVE 3D TILT & SMOOTH SCROLL REVEAL
  // ==========================================================================
  const initAboutSectionAnimations = () => {
    const aboutSection = document.getElementById('aboutSection');
    const visualFrame = document.getElementById('aboutVisualFrame');

    if (!aboutSection || !visualFrame) return;

    // 1. Mouse Tracking 3D Tilt Effect
    let isHovered = false;
    visualFrame.addEventListener('mouseenter', () => {
      isHovered = true;
      visualFrame.style.transition = 'transform 0.12s ease-out, box-shadow 0.3s ease';
    });

    visualFrame.addEventListener('mousemove', (e) => {
      if (!isHovered) return;
      const rect = visualFrame.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      const centerX = rect.width / 2;
      const centerY = rect.height / 2;

      // Subtle professional tilt angles (-8 to +8 degrees)
      const rotateX = ((centerY - y) / centerY) * 8;
      const rotateY = ((x - centerX) / centerX) * 8;

      visualFrame.style.transform = `perspective(1000px) rotateX(${rotateX.toFixed(2)}deg) rotateY(${rotateY.toFixed(2)}deg) scale3d(1.025, 1.025, 1.025)`;
    });

    visualFrame.addEventListener('mouseleave', () => {
      isHovered = false;
      visualFrame.style.transition = 'transform 0.6s cubic-bezier(0.25, 0.8, 0.25, 1), box-shadow 0.35s ease';
      visualFrame.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
    });

    // 2. Intersection Observer Scroll Reveal
    if ('IntersectionObserver' in window) {
      const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            aboutSection.classList.add('about-in-view');
            observer.unobserve(aboutSection);
          }
        });
      }, { threshold: 0.2 });

      observer.observe(aboutSection);
    }
  };

  initAboutSectionAnimations();

  // Load dynamic data first then initialize UI
  await loadDynamicStoreData();
  updateWishlistBadge();
  renderCategoriesGrid();
  renderBrands();
  if (window.lucide) window.lucide.createIcons();
});

