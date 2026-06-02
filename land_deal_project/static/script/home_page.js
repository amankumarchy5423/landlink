/**
 * LandLink — home-page.js
 * Requires: LANDS, IS_SELLER, TOKEN_COUNT injected by Flask template
 */

/* ══════════════════════════════════════
   MOUSE GLOW
══════════════════════════════════════ */
const glow = document.getElementById('glow-effect');
if (glow) {
  window.addEventListener('mousemove', (e) => {
    glow.style.left = e.clientX + 'px';
    glow.style.top  = e.clientY + 'px';
  });
}


/* ══════════════════════════════════════
   HEADER SCROLL SHADOW
══════════════════════════════════════ */
window.addEventListener('scroll', () => {
  document.getElementById('header')?.classList.toggle('scrolled', window.scrollY > 10);
});


/* ══════════════════════════════════════
   MOBILE MENU TOGGLE
══════════════════════════════════════ */
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileNav     = document.getElementById('mobileNav');

if (mobileMenuBtn && mobileNav) {
  mobileMenuBtn.addEventListener('click', () => {
    mobileNav.classList.toggle('open');
  });

  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!mobileMenuBtn.contains(e.target) && !mobileNav.contains(e.target)) {
      mobileNav.classList.remove('open');
    }
  });
}


/* ══════════════════════════════════════
   PROFILE DROPDOWN (click toggle for mobile)
══════════════════════════════════════ */
const profileBtn = document.getElementById('profileBtn');
const profileDropdown = document.getElementById('profileDropdown');

if (profileBtn && profileDropdown) {
  profileBtn.addEventListener('click', (e) => {
    e.stopPropagation();
    profileDropdown.classList.toggle('open');
  });

  document.addEventListener('click', () => {
    profileDropdown.classList.remove('open');
  });
}


/* ══════════════════════════════════════
   SAVED / WISHLIST BADGE (buyer only)
══════════════════════════════════════ */
if (!IS_SELLER) {
  try {
    const saved = JSON.parse(localStorage.getItem('landlink_saved') || '{}');
    const cnt = Object.keys(saved).length;
    const badge = document.getElementById('savedBadge');
    if (badge && cnt > 0) {
      badge.textContent = cnt;
      badge.style.display = 'flex';
    }
  } catch (e) { /* ignore */ }
}


/* ══════════════════════════════════════
   HERO SLIDER
══════════════════════════════════════ */
let slides = [];
let currentSlide = 0;
let slideTimer;

function buildSlider() {
  const frame  = document.getElementById('sliderFrame');
  const dotsEl = document.getElementById('slideDots');
  if (!frame || !dotsEl) return;

  // Choose which lands to show
  let pool = [];
  if (LANDS && LANDS.length > 0) {
    pool = IS_SELLER ? LANDS.slice(0, 3) : LANDS.slice(-5).reverse();
  }

  if (pool.length === 0) {
    updateFloatCards(null, null);
    startAutoSlide();
    return;
  }

  // Build slides
  frame.innerHTML = '';
  dotsEl.innerHTML = '';

  pool.forEach((land, i) => {
    const imgSrc = land.image
      ? (land.image.startsWith('http') ? land.image : `/static/${land.image}`)
      : '';
    const landId = land.id !== undefined ? land.id : i;

    const slide = document.createElement('div');
    slide.className = 'slide' + (i === 0 ? ' active' : '');
    slide.dataset.id = landId;

    slide.innerHTML = imgSrc
      ? `<img src="${imgSrc}" alt="${escapeHtml(land.title)}"
             onerror="this.style.display='none';this.nextElementSibling.style.display='flex';">
         <div class="slide-fallback" style="display:none;width:100%;height:100%;align-items:center;justify-content:center;
              flex-direction:column;gap:8px;background:linear-gradient(135deg,#1a2e1e,#1d1b20);
              font-size:0.8rem;color:#cbc4d2;"><span style='font-size:3rem'>🌾</span>${escapeHtml(land.title)}</div>`
      : `<div style="width:100%;height:100%;display:flex;align-items:center;justify-content:center;
              flex-direction:column;gap:8px;background:linear-gradient(135deg,#1a2e1e,#1d1b20);
              font-size:0.8rem;color:#cbc4d2;"><span style='font-size:3rem'>🌾</span>${escapeHtml(land.title)}</div>`;

    slide.innerHTML += `
      <div class="slide-overlay"></div>
      <div class="slide-info">
        <div>
          <h4>${escapeHtml(land.title)}</h4>
          <p>${escapeHtml(land.location || '')}${land.area ? ' · ' + land.area + ' sq.ft' : ''}</p>
        </div>
        <div class="slide-price">₹${escapeHtml(String(land.price || ''))}</div>
      </div>
      <div class="slide-redirect-hint">View Details →</div>
    `;

    slide.addEventListener('click', () => {
      window.location.href = `/land/${landId}`;
    });

    frame.appendChild(slide);

    // Dot
    const dot = document.createElement('div');
    dot.className = 'dot' + (i === 0 ? ' active' : '');
    dot.addEventListener('click', () => { goSlide(i); resetAutoSlide(); });
    dotsEl.appendChild(dot);
  });

  slides = Array.from(frame.querySelectorAll('.slide'));

  // Float cards
  const newest   = pool[0];
  const priciest = [...pool].sort((a, b) => {
    const pa = parseFloat(String(a.price || '0').replace(/[^0-9.]/g, ''));
    const pb = parseFloat(String(b.price || '0').replace(/[^0-9.]/g, ''));
    return pb - pa;
  })[0];

  updateFloatCards(newest, priciest);
  startAutoSlide();
}

function updateFloatCards(newest, priciest) {
  const fc1 = document.getElementById('fc1Text');
  const fc2 = document.getElementById('fc2Text');
  if (!fc1 || !fc2) return;

  if (newest) {
    fc1.textContent = newest.location || newest.title;
    const fc1Label = document.querySelector('#floatCard1 .float-text p:first-child');
    if (fc1Label) fc1Label.textContent = IS_SELLER ? 'Your Listing' : 'New Listing';
  } else {
    fc1.textContent = 'Nashik, Maharashtra';
  }

  if (priciest) {
    fc2.textContent = '₹' + priciest.price + ' — ' + (priciest.land_type || 'Land');
    const fc2Label = document.querySelector('#floatCard2 .float-text p:first-child');
    if (fc2Label) fc2Label.textContent = 'Top Listing';
  } else {
    fc2.textContent = '₹32L — Closed Today';
  }

  // Seller variant: show token buyers on card-2
  if (IS_SELLER && TOKEN_COUNT > 0) {
    const fc2Icon  = document.querySelector('#floatCard2 .float-icon');
    const fc2Label = document.querySelector('#floatCard2 .float-text p:first-child');
    if (fc2Icon)  { fc2Icon.textContent = '🤝'; fc2Icon.className = 'float-icon blue'; }
    if (fc2Label)   fc2Label.textContent = 'Token Paid';
    fc2.textContent = TOKEN_COUNT + ' Buyer' + (TOKEN_COUNT > 1 ? 's' : '') + ' Interested';
  }
}

function goSlide(n) {
  if (!slides.length) return;
  slides[currentSlide].classList.remove('active');
  document.querySelectorAll('.dot')[currentSlide]?.classList.remove('active');
  currentSlide = (n + slides.length) % slides.length;
  slides[currentSlide].classList.add('active');
  document.querySelectorAll('.dot')[currentSlide]?.classList.add('active');
}

function nextSlide() { goSlide(currentSlide + 1); resetAutoSlide(); }
function prevSlide()  { goSlide(currentSlide - 1); resetAutoSlide(); }

function startAutoSlide() {
  slideTimer = setInterval(() => goSlide(currentSlide + 1), 4500);
}

function resetAutoSlide() {
  clearInterval(slideTimer);
  startAutoSlide();
}


/* ══════════════════════════════════════
   FEATURED LAND SLIDER (manual scroll)
══════════════════════════════════════ */
function manualScroll(direction) {
  const slider = document.getElementById('slider');
  if (!slider) return;
  slider.style.animationPlayState = 'paused';
  const matrix = new DOMMatrix(getComputedStyle(slider).transform);
  slider.style.transform = `translateX(${matrix.m41 + direction * 322}px)`;
  // Resume after 3s idle
  clearTimeout(slider._resumeTimer);
  slider._resumeTimer = setTimeout(() => {
    slider.style.transform = '';
    slider.style.animationPlayState = 'running';
  }, 3000);
}


/* ══════════════════════════════════════
   PARALLAX (hero grid overlay)
══════════════════════════════════════ */
window.addEventListener('scroll', () => {
  const overlay = document.querySelector('.hero-grid-overlay');
  if (overlay) {
    overlay.style.transform = `translateY(${window.pageYOffset * 0.08}px)`;
  }
}, { passive: true });


/* ══════════════════════════════════════
   FADE-UP ON SCROLL
══════════════════════════════════════ */
const fadeObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      fadeObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.1 });

document.querySelectorAll('.fade-up').forEach(el => fadeObserver.observe(el));


/* ══════════════════════════════════════
   SMOOTH SCROLL FOR ANCHOR LINKS
══════════════════════════════════════ */
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const target = document.querySelector(this.getAttribute('href'));
    if (target) {
      e.preventDefault();
      target.scrollIntoView({ behavior: 'smooth' });
    }
  });
});


/* ══════════════════════════════════════
   STAT COUNTER ANIMATION
══════════════════════════════════════ */
function animateCounter(el) {
  const raw = el.textContent.trim();
  const num = parseFloat(raw.replace(/[^0-9.]/g, ''));
  if (isNaN(num) || num < 10) return;

  const suffix = raw.replace(/[0-9.,]/g, '');
  let start = 0;
  const duration = 1400;
  const step = timestamp => {
    if (!start) start = timestamp;
    const progress = Math.min((timestamp - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    el.textContent = Math.floor(eased * num).toLocaleString('en-IN') + suffix;
    if (progress < 1) requestAnimationFrame(step);
  };
  requestAnimationFrame(step);
}

const counterObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      animateCounter(entry.target);
      counterObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.5 });

document.querySelectorAll('.stat-card-num').forEach(el => counterObserver.observe(el));


/* ══════════════════════════════════════
   UTILITY
══════════════════════════════════════ */
function escapeHtml(str) {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(str));
  return d.innerHTML;
}


/* ══════════════════════════════════════
   INIT
══════════════════════════════════════ */
buildSlider();
