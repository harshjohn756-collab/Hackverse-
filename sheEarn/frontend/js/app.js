/**
 * SheEarn Shared Utilities — toast, loader, helpers, navbar
 */

/* ── Toast ───────────────────────────────────────────────────────────────────── */
function showToast(message, type = 'info', duration = 3500) {
  let container = document.querySelector('.toast-container');
  if (!container) {
    container = document.createElement('div');
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const icons = { success: '✅', error: '❌', info: 'ℹ️' };
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span class="toast-icon ${type}">${icons[type] || icons.info}</span><span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.animation = 'slideOutRight .3s ease forwards';
    setTimeout(() => toast.remove(), 300);
  }, duration);
}

/* ── Loader ──────────────────────────────────────────────────────────────────── */
function showLoader(msg = 'Loading…') {
  let el = document.getElementById('global-loader');
  if (!el) {
    el = document.createElement('div');
    el.id = 'global-loader';
    el.className = 'loading-overlay';
    el.innerHTML = `<div class="loader"></div><p>${msg}</p>`;
    document.body.appendChild(el);
  }
  el.querySelector('p').textContent = msg;
  el.classList.add('show');
}
function hideLoader() {
  const el = document.getElementById('global-loader');
  if (el) el.classList.remove('show');
}

/* ── Stars ───────────────────────────────────────────────────────────────────── */
function renderStars(avg, count = 0) {
  const full  = Math.floor(avg);
  const half  = avg - full >= 0.5 ? 1 : 0;
  const empty = 5 - full - half;
  return `${'★'.repeat(full)}${'½'.repeat(half)}${'☆'.repeat(empty)} <span style="color:var(--text-muted);font-size:.8rem">(${count})</span>`;
}

function renderInteractiveStars(containerId, onChange) {
  const el = document.getElementById(containerId);
  if (!el) return;
  let selected = 0;
  el.innerHTML = '';
  for (let i = 1; i <= 5; i++) {
    const s = document.createElement('span');
    s.className = 'star'; s.textContent = '☆';
    s.dataset.v = i;
    s.addEventListener('mouseover', () => {
      el.querySelectorAll('.star').forEach((st, idx) => st.textContent = idx < i ? '★' : '☆');
    });
    s.addEventListener('mouseleave', () => {
      el.querySelectorAll('.star').forEach((st, idx) => st.textContent = idx < selected ? '★' : '☆');
    });
    s.addEventListener('click', () => {
      selected = i;
      el.querySelectorAll('.star').forEach((st, idx) => { st.textContent = idx < i ? '★' : '☆'; st.classList.toggle('active', idx < i); });
      if (onChange) onChange(i);
    });
    el.appendChild(s);
  }
}

/* ── Avatar ──────────────────────────────────────────────────────────────────── */
function avatarHtml(name, image, cls = '') {
  const initials = (name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  return image
    ? `<div class="avatar ${cls}"><img src="${image}" alt="${name}"></div>`
    : `<div class="avatar ${cls}">${initials}</div>`;
}

/* ── Time Format ─────────────────────────────────────────────────────────────── */
function timeAgo(iso) {
  if (!iso) return '';
  if (!iso.endsWith('Z') && !iso.includes('+')) iso += 'Z'; // Treat naive backend datetimes as UTC
  const diff = Date.now() - new Date(iso);
  const mins  = Math.floor(diff / 60000);
  if (mins < 1)   return 'just now';
  if (mins < 60)  return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)   return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7)   return `${days}d ago`;
  return new Date(iso).toLocaleDateString();
}

function formatDate(iso) {
  if (!iso) return '—';
  if (!iso.endsWith('Z') && !iso.includes('+')) iso += 'Z';
  return new Date(iso).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
}

/* ── Build Navbar ────────────────────────────────────────────────────────────── */
function buildNavbar(activePage = '') {
  const user = Auth.getUser();
  const isLoggedIn = Auth.isLoggedIn();

  const navEl = document.getElementById('navbar');
  if (!navEl) return;

  const viewId = new URLSearchParams(location.search).get('id');
  const isPublicProfile = location.pathname.includes('profile.html') && viewId && viewId !== String(user?.id);

  let links = [
    { href: 'browse.html',   label: '🔍 Browse',   key: 'browse' },
    { href: 'schemes.html',  label: '🏛️ Schemes',  key: 'schemes' },
  ];
  if (isLoggedIn) {
    links.push({ href: 'bookings.html', label: '📅 Bookings', key: 'bookings' });
    links.push({ href: 'chat.html',     label: '💬 Chat',    key: 'chat' });
    links.push({ href: 'wallet.html',   label: '💰 Wallet',  key: 'wallet' });
    if (user?.role === 'admin') links.push({ href: 'admin.html', label: '🛠️ Admin', key: 'admin' });
  }

  if (isPublicProfile) {
    links = []; // Hide links when viewing other profiles as per privacy request
  }

  const linksHtml = links.map(l =>
    `<a href="${l.href}" class="${activePage === l.key ? 'active' : ''}">${l.label}</a>`
  ).join('');

  const themeBtn = `<button onclick="toggleTheme()" class="btn btn-secondary btn-sm" title="Toggle Theme" style="border-radius:50%; width: 34px; height: 34px; padding:0; display:flex; align-items:center; justify-content:center; margin-right: 8px;">🌓</button>`;

  const actionsHtml = themeBtn + (isLoggedIn
    ? `<a href="profile.html" class="btn btn-secondary btn-sm">${avatarHtml(user?.name, null, '')} ${user?.name?.split(' ')[0]}</a>
       <button onclick="logout()" class="btn btn-outline btn-sm">Logout</button>`
    : `<a href="auth.html" class="btn btn-secondary btn-sm">Login</a>
       <a href="auth.html?tab=register" class="btn btn-primary btn-sm">Get Started</a>`);

  navEl.innerHTML = `
    <a href="index.html" class="nav-logo">She<span>Earn</span></a>
    <nav class="nav-links" id="nav-links">${linksHtml}</nav>
    <div class="nav-actions">${actionsHtml}</div>
    <button class="nav-hamburger" id="nav-ham" onclick="document.getElementById('nav-links').classList.toggle('open')">
      <span></span><span></span><span></span>
    </button>`;

  window.addEventListener('scroll', () => {
    navEl.classList.toggle('scrolled', window.scrollY > 20);
  });
}

/* ── Logout ──────────────────────────────────────────────────────────────────── */
function logout() {
  Auth.clearTokens();
  localStorage.removeItem('she_lang');
  document.cookie = 'googtrans=/en/en; path=/';
  document.cookie = 'googtrans=/en/en; domain=' + window.location.hostname + '; path=/';
  window.location.href = 'index.html';
}

/* ── Setup Tabs ──────────────────────────────────────────────────────────────── */
function setupTabs(containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  const btns   = container.querySelectorAll('.tab-btn');
  const panels = container.querySelectorAll('.tab-panel');
  btns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.tab;
      btns.forEach(b => b.classList.toggle('active', b.dataset.tab === target));
      panels.forEach(p => p.classList.toggle('active', p.id === target));
    });
  });
}

/* ── Open / Close Modal ──────────────────────────────────────────────────────── */
function openModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add('open');
}
function closeModal(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove('open');
}
function closeModalOnOverlay(id) {
  const el = document.getElementById(id);
  if (el) el.addEventListener('click', e => { if (e.target === el) closeModal(id); });
}

/* ── Pagination Helper ───────────────────────────────────────────────────────── */
function buildPagination(containerId, current, total, onPage) {
  const el = document.getElementById(containerId);
  if (!el || total <= 1) { if(el) el.innerHTML=''; return; }
  let html = `<button class="page-btn" ${current===1?'disabled':''} onclick="(${onPage.toString()})(${current-1})">‹</button>`;
  for (let i = 1; i <= total; i++) {
    if (total > 7 && Math.abs(i - current) > 2 && i !== 1 && i !== total) {
      if (i === 2 || i === total - 1) html += `<span class="page-btn" style="cursor:default">…</span>`;
      continue;
    }
    html += `<button class="page-btn ${i===current?'active':''}" onclick="(${onPage.toString()})(${i})">${i}</button>`;
  }
  html += `<button class="page-btn" ${current===total?'disabled':''} onclick="(${onPage.toString()})(${current+1})">›</button>`;
  el.innerHTML = html;
}

/* ── Service Card HTML ───────────────────────────────────────────────────────── */
function serviceCardHtml(s) {
  const emoji  = CATEGORY_EMOJI[s.category] || '✨';
  const stars  = renderStars(s.avg_rating, s.rating_count);
  const dist   = s.distance_km ? `<span style="color:var(--teal);font-size:.78rem">📍 ${s.distance_km} km</span>` : '';
  return `
  <div class="service-card" onclick="window.location.href='service.html?id=${s.id}'">
    <div class="service-card-img">${emoji}</div>
    <div class="service-card-body">
      <div class="service-card-cat">${CATEGORY_LABEL[s.category] || s.category}</div>
      <div class="service-card-title">${s.title}</div>
      <div class="service-card-provider">by ${s.provider?.name || 'Provider'}</div>
      <div class="service-card-footer">
        <div class="service-card-price">₹${s.price}</div>
        <div class="service-card-rating">${stars}</div>
      </div>
      ${dist}
    </div>
  </div>`;
}

/* ── Global Translation (Google Translate) ──────────────────────────────────── */
function applyLanguageTranslation() {
  const user = Auth.getUser();
  let lang = localStorage.getItem('she_lang') || 'en';
  
  if (user && user.language) {
    lang = user.language;
    localStorage.setItem('she_lang', lang);
  }

  const currentCookieMatch = document.cookie.match(/(^|;\s*)googtrans=([^;]*)/);
  const currentCookie = currentCookieMatch ? currentCookieMatch[2] : null;
  const desiredCookie = lang === 'en' ? '/en/en' : `/en/${lang}`;

  if (currentCookie !== desiredCookie) {
    document.cookie = `googtrans=${desiredCookie}; path=/`;
    document.cookie = `googtrans=${desiredCookie}; domain=${window.location.hostname}; path=/`;
    if (currentCookie) {
       window.location.reload();
       return;
    }
  }

  if (lang !== 'en') {
    const script = document.createElement('script');
    script.src = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';
    document.body.appendChild(script);

    window.googleTranslateElementInit = function() {
      new google.translate.TranslateElement({
        pageLanguage: 'en',
        includedLanguages: 'en,hi,kn',
        autoDisplay: false
      }, 'google_translate_element');
    };

    if (!document.getElementById('google_translate_element')) {
      const div = document.createElement('div');
      div.id = 'google_translate_element';
      div.style.display = 'none';
      document.body.appendChild(div);
    }

    const style = document.createElement('style');
    style.innerHTML = `
      .skiptranslate iframe { display: none !important; }
      body { top: 0px !important; }
    `;
    document.head.appendChild(style);
  }
}

applyLanguageTranslation();

/* ── Theme Toggling ─────────────────────────────────────────────────────────── */
function applyTheme() {
  const theme = localStorage.getItem('she_theme') || 'dark';
  if (theme === 'light') {
    document.documentElement.setAttribute('data-theme', 'light');
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
  }
}

function toggleTheme() {
  const current = localStorage.getItem('she_theme') || 'dark';
  if (current === 'dark') {
    localStorage.setItem('she_theme', 'light');
  } else {
    localStorage.setItem('she_theme', 'dark');
  }
  applyTheme();
}

applyTheme();
