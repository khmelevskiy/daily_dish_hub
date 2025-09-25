(function () {
  const currencySymbol = (document.querySelector('meta[name="app:currency_symbol"]') || {}).content || '₾';
  const appLocale = (document.querySelector('meta[name="app:locale"]') || {}).content || 'ru-RU';
  const MENU_REFRESH_MS = 60_000; // 1 minute

  const menuContainer = document.getElementById('menu-container');
  const validitySection = document.getElementById('menu-validity');
  const startTimeEl = document.getElementById('menu-start-time');
  const endTimeEl = document.getElementById('menu-end-time');
  const statusLabel = document.getElementById('menu-status-label');
  const cartEl = document.getElementById('cart');
  const cartItemsEl = document.getElementById('cart-items');
  const cartCountEl = document.getElementById('cart-count');
  const cartTotalEl = document.getElementById('cart-total');

  let cart = [];
  let cartOpen = false;
  let menuItemsData = Object.create(null);
  let menuCategoryOrder = [];
  let lastMenuData = null;
  let lastMenuFetchTs = 0;
  let menuFetchPromise = null;

  // Basic HTML escaping to prevent XSS when rendering untrusted content
  function escapeHTML(input) {
    if (input === null || input === undefined) return '';
    return String(input).replace(/[&<>"']/g, (ch) => ({
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#39;',
    })[ch]);
  }

  function normalizeMultilineText(input) {
    if (input === null || input === undefined) return '';
    return String(input).replace(/\r\n?/g, '\n').trim();
  }

  function formatMultilineHTML(input) {
    const normalized = normalizeMultilineText(input);
    if (!normalized) return '';
    return escapeHTML(normalized);
  }

  function getCartItemQuantity(itemId) {
    const cartItem = cart.find((item) => item.id === itemId);
    return cartItem ? cartItem.quantity : 0;
  }

  function applyMenuData(data) {
    lastMenuData = data && typeof data === 'object' ? data : null;
    menuItemsData = Object.create(null);
    menuCategoryOrder = [];

    const items = (lastMenuData && Array.isArray(lastMenuData.items)) ? lastMenuData.items : [];
    for (const entry of items) {
      if (!entry || !entry.item) continue;
      const item = entry.item;
      const category = item.category_title || 'Uncategorized';
      if (!menuCategoryOrder.includes(category)) {
        menuCategoryOrder.push(category);
      }
      menuItemsData[item.id] = {
        id: item.id,
        name: item.name,
        price: item.price,
        description: normalizeMultilineText(item.description) || null,
        image_filename: item.image_filename,
        image_id: item.image_id,
        image_url: item.image_url,
        unit_name: item.unit_name,
        category_title: category,
      };
    }
  }

  function renderMenu() {
    if (!menuContainer) return;

    if (!lastMenuData) {
      menuContainer.innerHTML = '<div class="loading"><div class="spinner"></div><h3>Loading menu...</h3></div>';
      return;
    }

    const items = Array.isArray(lastMenuData.items) ? lastMenuData.items : [];
    if (items.length === 0) {
      menuContainer.innerHTML = '<div class="empty-menu"><h3>🍽️ Menu is empty</h3><p>Check back later!</p></div>';
      return;
    }

    const groupedItems = {};
    for (const category of menuCategoryOrder) {
      groupedItems[category] = [];
    }
    for (const entry of items) {
      if (!entry || !entry.item) continue;
      const category = entry.item.category_title || 'Uncategorized';
      if (!groupedItems[category]) {
        groupedItems[category] = [];
        if (!menuCategoryOrder.includes(category)) {
          menuCategoryOrder.push(category);
        }
      }
      groupedItems[category].push(entry);
    }
    Object.keys(groupedItems).forEach((category) => {
      groupedItems[category].sort((a, b) => a.item.name.localeCompare(b.item.name));
    });

    let menuHTML = '<div class="menu-grid">';
    for (const category of menuCategoryOrder) {
      const entries = groupedItems[category] || [];
      if (entries.length === 0) continue;
      const safeCategory = escapeHTML(category);
      const itemsMarkup = entries
        .map((entry) => {
          const item = entry.item;
          const displayDescription = formatMultilineHTML(item.description);
          const quantity = getCartItemQuantity(item.id);
          return `
            <div class="item">
              <div class="item-top-row">
                <div class="item-main">
                  <div class="item-image">
                    ${
                      item.image_url
                        ? `<img src="${escapeHTML(item.image_url)}" alt="${escapeHTML(item.name)}" class="item-img">`
                        : '<div class="item-placeholder">📷</div>'
                    }
                  </div>
                  <div class="item-info">
                    <div class="item-name">${escapeHTML(item.name)}</div>
                    <div class="item-price-unit">
                      <span class="item-price">${Number(item.price).toFixed(2)} ${currencySymbol}</span>
                      <span class="item-unit">/ ${escapeHTML(item.unit_name || 'pcs')}</span>
                    </div>
                  </div>
                </div>
                <div class="item-actions">
                  <button class="quantity-control-btn remove" data-action="remove-from-cart" data-item-id="${item.id}">-</button>
                  <span class="item-quantity">${quantity}</span>
                  <button class="quantity-control-btn add" data-action="add-to-cart" data-item-id="${item.id}">+</button>
                </div>
              </div>
              ${displayDescription ? `<div class="item-description">${displayDescription}</div>` : ''}
            </div>`;
        })
        .join('');

      if (!itemsMarkup) continue;
      menuHTML += `
        <div class="category-card">
          <h2 class="category-title">${safeCategory}</h2>
          <div class="category-header">
            <div class="header-item">Item</div>
            <div class="header-actions">Quantity</div>
          </div>
          ${itemsMarkup}
        </div>`;
    }
    menuHTML += '</div>';
    menuContainer.innerHTML = menuHTML;
  }

  async function refreshMenu(options = {}) {
    const { force = false } = options;
    const now = Date.now();

    if (!force && lastMenuData && now - lastMenuFetchTs < MENU_REFRESH_MS) {
      renderMenu();
      return lastMenuData;
    }

    if (menuFetchPromise) {
      return menuFetchPromise;
    }

    menuFetchPromise = (async () => {
      try {
        const response = await fetch('/public/daily-menu');
        if (!response.ok) {
          throw new Error(`Failed to load menu: HTTP ${response.status}`);
        }
        const data = await response.json();
        lastMenuFetchTs = Date.now();
        applyMenuData(data);
        renderMenu();
        return data;
      } catch (e) {
        console.error('Error loading menu:', e);
        if (!lastMenuData && menuContainer) {
          menuContainer.innerHTML = '<div class="error"><h3>❌ Error loading menu</h3></div>';
        }
        throw e;
      } finally {
        menuFetchPromise = null;
      }
    })();

    return menuFetchPromise;
  }

  function scheduleMenuRefresh() {
    setInterval(() => {
      void refreshMenu({ force: true }).catch(() => {
        /* keep previous data */
      });
    }, MENU_REFRESH_MS);
  }

  async function loadMenuDate() {
    try {
      const response = await fetch('/public/menu-date');
      if (!response.ok) {
        throw new Error(`Failed to load menu date: HTTP ${response.status}`);
      }
      const data = await response.json();
      if (data.menu_date && validitySection && startTimeEl && endTimeEl) {
        const startDate = parseIsoLike(data.menu_date.start_date);
        const endDate = parseIsoLike(data.menu_date.end_date);

        startTimeEl.textContent = formatDateTime(startDate);
        endTimeEl.textContent = formatDateTime(endDate);
        applyMenuValidityStatus(startDate, endDate);
        validitySection.classList.remove('hidden');
      } else {
        applyMenuValidityStatus(null, null);
      }
    } catch (e) {
      console.error('Error loading menu date:', e);
      applyMenuValidityStatus(null, null);
    }
  }

  function parseIsoLike(dateString) {
    try {
      return new Date(String(dateString || '').replace(' ', 'T'));
    } catch {
      return new Date(NaN);
    }
  }

  function formatDateTime(dateInput) {
    const d = dateInput instanceof Date ? dateInput : parseIsoLike(dateInput);
    if (!isFinite(d.getTime())) return '';
    try {
      return new Intl.DateTimeFormat(appLocale || 'ru-RU', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false,
      }).format(d);
    } catch {
      const pad = (n) => String(n).padStart(2, '0');
      return `${pad(d.getDate())}.${pad(d.getMonth() + 1)}.${d.getFullYear()}, ${pad(d.getHours())}:${pad(d.getMinutes())}`;
    }
  }

  function resetMenuValidityStatus() {
    if (!statusLabel || !startTimeEl || !endTimeEl) return;
    const targets = [statusLabel, startTimeEl, endTimeEl];
    for (const el of targets) {
      el.classList.remove('status-available', 'status-unavailable');
    }
    statusLabel.textContent = '';
  }

  function applyMenuValidityStatus(startDate, endDate) {
    if (!statusLabel || !startTimeEl || !endTimeEl) return;
    resetMenuValidityStatus();

    if (!(startDate instanceof Date) || Number.isNaN(startDate.getTime()) ||
        !(endDate instanceof Date) || Number.isNaN(endDate.getTime())) {
      return;
    }

    const now = new Date();
    const className = now >= startDate && now < endDate ? 'status-available' : 'status-unavailable';
    let label = '';

    if (now < startDate) {
      label = '(Starts later)';
    } else if (now >= endDate) {
      label = '(Menu closed)';
    } else {
      label = '(Available now)';
    }

    statusLabel.textContent = label;
    statusLabel.classList.add(className);
    startTimeEl.classList.add(className);
    endTimeEl.classList.add(className);
  }

  function addToCart(itemId, itemName, itemPrice, itemImageUrl, itemDescription, itemUnitName, itemCategoryTitle) {
    const normalizedDescription = normalizeMultilineText(itemDescription) || null;
    const existingItem = cart.find((item) => item.id === itemId);
    if (existingItem) {
      existingItem.quantity += 1;
    } else {
      cart.push({
        id: itemId,
        name: itemName,
        price: itemPrice,
        image_url: itemImageUrl,
        description: normalizedDescription,
        unit_name: itemUnitName,
        category_title: itemCategoryTitle,
        quantity: 1,
      });
    }
    updateCart();
    renderMenu();
  }

  function addToCartFromMenu(itemId) {
    const itemData = menuItemsData[itemId];
    if (itemData) {
      addToCart(
        itemData.id,
        itemData.name,
        itemData.price,
        itemData.image_url,
        itemData.description,
        itemData.unit_name,
        itemData.category_title
      );
    }
  }

  function removeFromCart(itemId) {
    const item = cart.find((entry) => entry.id === itemId);
    if (item) {
      if (item.quantity > 1) {
        item.quantity -= 1;
      } else {
        cart = cart.filter((entry) => entry.id !== itemId);
      }
    }
    updateCart();
    renderMenu();
  }

  function clearCart() {
    if (cart.length === 0) return;
    if (window.confirm('Are you sure you want to clear the cart?')) {
      cart = [];
      updateCart();
      renderMenu();
    }
  }

  function updateQuantity(itemId, delta) {
    const item = cart.find((entry) => entry.id === itemId);
    if (item) {
      item.quantity += delta;
      if (item.quantity <= 0) {
        removeFromCart(itemId);
      } else {
        updateCart();
        renderMenu();
      }
    }
  }

  function updateCart() {
    if (!cartItemsEl || !cartCountEl || !cartTotalEl) return;

    const totalItems = cart.reduce((sum, item) => sum + item.quantity, 0);
    cartCountEl.textContent = String(totalItems);

    if (cart.length === 0) {
      cartItemsEl.innerHTML = '<div class="empty-cart">Cart is empty</div>';
    } else {
      const groupedCartItems = {};
      cart.forEach((item) => {
        const category = item.category_title || 'Uncategorized';
        if (!groupedCartItems[category]) groupedCartItems[category] = [];
        groupedCartItems[category].push(item);
      });

      Object.keys(groupedCartItems).forEach((category) => {
        groupedCartItems[category].sort((a, b) => a.name.localeCompare(b.name));
      });

      const cartCategories = Object.keys(groupedCartItems);
      const orderedCategories = [];
      menuCategoryOrder.forEach((category) => {
        if (cartCategories.includes(category)) orderedCategories.push(category);
      });
      cartCategories.forEach((category) => {
        if (!orderedCategories.includes(category)) orderedCategories.push(category);
      });

      cartItemsEl.innerHTML = orderedCategories
        .map((category) => {
          const categoryItems = groupedCartItems[category];
          if (!categoryItems || categoryItems.length === 0) return '';
          const safeCategory = escapeHTML(category);
          return `
            <div class="cart-category">
              <h4 class="cart-category-title">📂 ${safeCategory}</h4>
              ${categoryItems
                .map(
                  (item) => `
                  <div class="cart-item">
                    ${
                      item.image_url
                        ? `<img src="${escapeHTML(item.image_url)}" alt="${escapeHTML(item.name)}" class="cart-item-image">`
                        : '<div class="cart-item-image-placeholder">📷</div>'
                    }
                    <div class="cart-item-content">
                      <div class="cart-item-name">${escapeHTML(item.name)}</div>
                      ${item.description ? `<div class="cart-item-description">${formatMultilineHTML(item.description)}</div>` : ''}
                      <div class="cart-item-details">
                        <span class="cart-item-price">${Number(item.price).toFixed(2)} ${currencySymbol}</span>
                        <span class="cart-item-unit">📏 ${escapeHTML(item.unit_name || 'pcs')}</span>
                      </div>
                    </div>
                    <div class="cart-item-quantity">
                      <button class="quantity-btn" data-action="update-qty" data-item-id="${item.id}" data-delta="-1">-</button>
                      <span>${item.quantity}</span>
                      <button class="quantity-btn" data-action="update-qty" data-item-id="${item.id}" data-delta="1">+</button>
                    </div>
                  </div>`
                )
                .join('')}
            </div>`;
        })
        .join('');
    }

    const total = cart.reduce((sum, item) => sum + item.price * item.quantity, 0);
    cartTotalEl.textContent = Number(total).toFixed(2);
    localStorage.setItem('cart', JSON.stringify(cart));
  }

  function toggleCart() {
    if (!cartEl) return;
    cartOpen = !cartOpen;
    if (cartOpen) {
      void syncCartWithMenu();
      cartEl.classList.add('open');
    } else {
      cartEl.classList.remove('open');
    }
  }

  async function syncCartWithMenu() {
    if (cart.length === 0) return;

    let menuData = lastMenuData;
    try {
      menuData = await refreshMenu({ force: true });
    } catch (e) {
      console.error('Error refreshing menu during cart sync:', e);
    }

    const items = menuData && Array.isArray(menuData.items) ? menuData.items : [];
    if (items.length === 0) return;

    const currentMenuItemIds = new Set(items.map((entry) => entry.item && entry.item.id).filter(Boolean));
    const updatedCart = [];
    let cartChanged = false;

    for (const cartItem of cart) {
      if (!currentMenuItemIds.has(cartItem.id)) {
        cartChanged = true;
        continue;
      }
      const menuEntry = items.find((entry) => entry.item && entry.item.id === cartItem.id);
      if (!menuEntry || !menuEntry.item) {
        cartChanged = true;
        continue;
      }
      const item = menuEntry.item;
      const normalizedDescription = normalizeMultilineText(item.description) || null;
      const hasChanges =
        cartItem.name !== item.name ||
        cartItem.price !== item.price ||
        cartItem.description !== normalizedDescription ||
        cartItem.image_url !== item.image_url ||
        cartItem.unit_name !== item.unit_name ||
        cartItem.category_title !== (item.category_title || 'Uncategorized');
      if (hasChanges) {
        cartChanged = true;
      }
      updatedCart.push({
        ...cartItem,
        name: item.name,
        price: item.price,
        description: normalizedDescription,
        image_url: item.image_url,
        unit_name: item.unit_name,
        category_title: item.category_title || 'Uncategorized',
      });
    }

    if (cartChanged || updatedCart.length !== cart.length) {
      cart = updatedCart;
      updateCart();
      renderMenu();
    }
  }

  document.addEventListener('DOMContentLoaded', async () => {
    const savedCart = localStorage.getItem('cart');
    if (savedCart) {
      try {
        cart = JSON.parse(savedCart) || [];
      } catch {
        cart = [];
      }
      updateCart();
    }

    await refreshMenu({ force: true }).catch(() => {
      /* handled inside refreshMenu */
    });
    await loadMenuDate();
    scheduleMenuRefresh();

    if (cart.length > 0) {
      setTimeout(() => {
        void syncCartWithMenu();
      }, 1_000);
    }

    const clearBtn = document.getElementById('clear-cart-btn');
    const closeBtn = document.getElementById('close-cart-btn');
    const toggleBtn = document.getElementById('cart-toggle-btn');
    if (clearBtn) clearBtn.addEventListener('click', clearCart);
    if (closeBtn) closeBtn.addEventListener('click', toggleCart);
    if (toggleBtn) toggleBtn.addEventListener('click', toggleCart);

    if (menuContainer) {
      menuContainer.addEventListener('click', (event) => {
        const target = event.target;
        if (!(target instanceof Element)) return;
        const btn = target.closest('button');
        if (!btn) return;
        const action = btn.getAttribute('data-action');
        if (!action) return;
        const id = parseInt(btn.getAttribute('data-item-id') || '0', 10);
        if (!id) return;
        if (action === 'add-to-cart') addToCartFromMenu(id);
        else if (action === 'remove-from-cart') removeFromCart(id);
      });
    }

    if (cartItemsEl) {
      cartItemsEl.addEventListener('click', (event) => {
        const target = event.target;
        if (!(target instanceof Element)) return;
        const btn = target.closest('button');
        if (!btn) return;
        const action = btn.getAttribute('data-action');
        if (action !== 'update-qty') return;
        const id = parseInt(btn.getAttribute('data-item-id') || '0', 10);
        const delta = parseInt(btn.getAttribute('data-delta') || '0', 10);
        if (!id || !delta) return;
        updateQuantity(id, delta);
      });
    }
  });
})();
