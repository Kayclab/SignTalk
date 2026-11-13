// Initialize Lucide Icons
lucide.createIcons();

// Mobile Navigation Toggle
const menuBtn = document.getElementById('menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
menuBtn.addEventListener('click', () => {
  mobileMenu.classList.toggle('hidden');
});

// Populate Alphabet Flip Cards
const carouselContainer = document.getElementById('carousel-container');
const letters = "ABCDEFGHIJKLMNOPQRSTUVWXYZ".split('');
// Duplicate 2x for seamless continuous loop marquee
const doubleLetters = [...letters, ...letters]; 

doubleLetters.forEach((letter) => {
  const cardWrapper = document.createElement('div');
  cardWrapper.className = 'relative w-56 h-72 perspective cursor-pointer flex-shrink-0 mx-4 select-none';

  cardWrapper.innerHTML = `
    <div class="card-inner w-full h-full preserve-3d transition-transform duration-700">
      <!-- Front -->
      <div class="absolute inset-0 backface-hidden bg-gradient-to-br from-[#F0EBFF] to-white rounded-3xl flex flex-col items-center justify-center border-2 border-[#DCEBFF] shadow-lg hover:shadow-xl transition-shadow">
        <span class="text-8xl font-black text-[#6346D8]">${letter}</span>
        <span class="absolute bottom-4 text-xs font-semibold text-[#A78BFA] tracking-widest uppercase">Klik untuk lihat</span>
      </div>
      <!-- Back -->
      <div class="absolute inset-0 backface-hidden bg-white rounded-3xl flex flex-col items-center p-4 border-2 border-[#A78BFA] shadow-lg rotate-y-180">
        <div class="w-full flex-1 bg-[#F8F6FF] rounded-2xl mb-3 flex items-center justify-center overflow-hidden border border-[#F0EBFF]">
          <span class="text-sm font-bold text-[#6346D8]">[Foto Isyarat ${letter}]</span>
        </div>
        <div class="text-center w-full">
          <h4 class="text-lg font-bold text-[#19143A]">Isyarat '${letter}'</h4>
          <p class="text-xs text-gray-500 mt-1">Genggam tangan seperti pola ini</p>
        </div>
      </div>
    </div>
  `;

  // 3D Flip Click Interaction
  const innerCard = cardWrapper.querySelector('.card-inner');
  cardWrapper.addEventListener('click', (e) => {
    e.stopPropagation();
    innerCard.classList.toggle('rotate-y-180');
  });

  carouselContainer.appendChild(cardWrapper);
});

// Arrow Nav Controls for Marquee Scroll Shift
const marqueeContainer = document.getElementById('carousel-container');

document.getElementById('scroll-left').addEventListener('click', () => {
  const currentTransform = new WebKitCSSMatrix(window.getComputedStyle(marqueeContainer).transform);
  marqueeContainer.style.transform = `translateX(${currentTransform.m41 + 320}px)`; 
});

document.getElementById('scroll-right').addEventListener('click', () => {
  const currentTransform = new WebKitCSSMatrix(window.getComputedStyle(marqueeContainer).transform);
  marqueeContainer.style.transform = `translateX(${currentTransform.m41 - 320}px)`;
});

const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

// =============================================================
// HERO: gelembung huruf yang keluar dari layar laptop
// =============================================================
(function heroBubbles() {
  const stage = document.getElementById('bubble-stage');
  const screen = document.getElementById('laptop-screen');
  const screenLetter = document.getElementById('screen-letter');
  const heroVisual = document.getElementById('hero-visual');
  if (!stage || !screen || !heroVisual) return;

  const LETTERS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('');
  const VARIANTS = ['purple', 'amber', 'glass', 'purple', 'glass', 'amber'];
  const COLORS = { purple: '#6346D8', amber: '#FFB938', glass: '#A78BFA' };
  const SPAWN_EVERY_MS = 750;
  const MAX_BUBBLES = 9;

  let index = 0;
  let liveCount = 0;
  let heroOnScreen = true;

  const rand = (min, max) => min + Math.random() * (max - min);
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));

  // Titik keluar = tengah layar laptop, relatif terhadap panggung gelembung
  function emitterPoint() {
    const s = stage.getBoundingClientRect();
    const r = screen.getBoundingClientRect();
    return {
      x: r.left - s.left + r.width / 2,
      y: r.top - s.top + r.height * 0.45,
      width: s.width,
    };
  }

  function makeBubble(letter, variant, size) {
    const el = document.createElement('div');
    el.className = `bubble bubble--${variant}`;
    el.style.setProperty('--s', `${size}px`);
    el.dataset.variant = variant;
    el.innerHTML = `<div class="bubble-inner" style="--sway:${rand(2.2, 3.6).toFixed(2)}s">${letter}</div>`;
    stage.appendChild(el);
    return el;
  }

  function showOnScreen(letter) {
    if (screenLetter) {
      screenLetter.textContent = letter;
      screenLetter.classList.remove('tick');
      void screenLetter.offsetWidth; // restart animasi
      screenLetter.classList.add('tick');
    }
    screen.classList.remove('flash');
    void screen.offsetWidth;
    screen.classList.add('flash');
  }

  // Efek pecah: gelembung membesar & hilang + cincin + percikan
  function pop(el, flight) {
    if (el.dataset.popped) return;
    el.dataset.popped = '1';

    const matrix = new DOMMatrixReadOnly(getComputedStyle(el).transform);
    const x = matrix.m41;
    const y = matrix.m42;
    const color = COLORS[el.dataset.variant];
    const size = parseFloat(el.style.getPropertyValue('--s'));
    if (flight) flight.cancel();

    el.style.pointerEvents = 'none';
    el.animate(
      [
        { transform: `translate(${x}px, ${y}px) scale(1)`, opacity: 1 },
        { transform: `translate(${x}px, ${y}px) scale(1.45)`, opacity: 0 },
      ],
      { duration: 220, easing: 'ease-out', fill: 'forwards' }
    ).onfinish = () => {
      el.remove();
      liveCount -= 1;
    };

    const ring = document.createElement('div');
    ring.className = 'pop-ring';
    ring.style.setProperty('--s', `${size}px`);
    ring.style.setProperty('--c', color);
    stage.appendChild(ring);
    ring.animate(
      [
        { transform: `translate(${x}px, ${y}px) scale(0.7)`, opacity: 0.9 },
        { transform: `translate(${x}px, ${y}px) scale(1.6)`, opacity: 0 },
      ],
      { duration: 450, easing: 'ease-out', fill: 'forwards' }
    ).onfinish = () => ring.remove();

    for (let i = 0; i < 6; i += 1) {
      const angle = (Math.PI * 2 * i) / 6 + rand(-0.3, 0.3);
      const distance = size * rand(0.7, 1.05);
      const drop = document.createElement('div');
      drop.className = 'pop-drop';
      drop.style.setProperty('--c', color);
      stage.appendChild(drop);
      drop.animate(
        [
          { transform: `translate(${x}px, ${y}px) scale(1)`, opacity: 1 },
          {
            transform: `translate(${x + Math.cos(angle) * distance}px, ${y + Math.sin(angle) * distance}px) scale(0.2)`,
            opacity: 0,
          },
        ],
        { duration: rand(380, 520), easing: 'cubic-bezier(.2,.7,.3,1)', fill: 'forwards' }
      ).onfinish = () => drop.remove();
    }
  }

  function spawn() {
    if (!heroOnScreen || document.hidden || liveCount >= MAX_BUBBLES) return;

    const letter = LETTERS[index % LETTERS.length];
    const variant = VARIANTS[index % VARIANTS.length];
    index += 1;

    const o = emitterPoint();
    const scale = clamp(o.width / 540, 0.65, 1);
    const size = Math.round(rand(52, 74) * scale);
    const el = makeBubble(letter, variant, size);
    liveCount += 1;
    showOnScreen(letter);

    // Lintasan: keluar dari layar, melambung ke atas & menyebar ke samping
    const side = Math.random() < 0.5 ? -1 : 1;
    const endX = clamp(o.x + side * rand(70, 240) * scale, size, o.width - size);
    const endY = Math.max(o.y - rand(210, 330) * scale, size * 0.6);
    const dx = endX - o.x;
    const dy = endY - o.y;

    const flight = el.animate(
      [
        { transform: `translate(${o.x}px, ${o.y}px) scale(0.1)`, opacity: 0 },
        { transform: `translate(${o.x + dx * 0.06}px, ${o.y - 42 * scale}px) scale(1.18)`, opacity: 1, offset: 0.1 },
        { transform: `translate(${o.x + dx * 0.1}px, ${o.y - 56 * scale}px) scale(0.94)`, offset: 0.16 },
        { transform: `translate(${o.x + dx * 0.45 + rand(-25, 25)}px, ${o.y + dy * 0.5}px) scale(1)`, offset: 0.5 },
        { transform: `translate(${endX}px, ${endY}px) scale(1.04)`, opacity: 1 },
      ],
      { duration: rand(4300, 5600), easing: 'cubic-bezier(.25,.6,.3,1)', fill: 'forwards' }
    );
    flight.onfinish = () => pop(el, null);

    // Interaktif: sentuh / arahkan kursor ke gelembung untuk memecahkannya
    el.addEventListener('pointerenter', () => pop(el, flight), { once: true });
    el.addEventListener('click', () => pop(el, flight), { once: true });
  }

  // Tanpa animasi (pengguna memilih "kurangi gerakan"): gelembung statis
  if (prefersReducedMotion) {
    const o = emitterPoint();
    const scale = clamp(o.width / 540, 0.65, 1);
    [
      ['S', 'purple', -150, -170],
      ['I', 'amber', -60, -250],
      ['G', 'glass', 50, -230],
      ['N', 'purple', 150, -160],
    ].forEach(([letter, variant, dx, dy]) => {
      const el = makeBubble(letter, variant, Math.round(62 * scale));
      el.style.transform = `translate(${o.x + dx * scale}px, ${o.y + dy * scale}px)`;
    });
    return;
  }

  // Hemat CPU: berhenti membuat gelembung saat hero tidak terlihat
  new IntersectionObserver((entries) => {
    heroOnScreen = entries[0].isIntersecting;
  }).observe(heroVisual);

  // Mulai setelah animasi masuk hero selesai
  setTimeout(() => {
    spawn();
    setTimeout(spawn, 280);
    setInterval(spawn, SPAWN_EVERY_MS);
  }, 1100);
})();

// =============================================================
// HERO: parallax ringan mengikuti kursor (hanya perangkat mouse)
// =============================================================
(function heroParallax() {
  const hero = document.getElementById('home');
  const scene = document.getElementById('hero-scene');
  if (!hero || !scene || prefersReducedMotion) return;
  if (!window.matchMedia('(pointer: fine)').matches) return;

  hero.addEventListener('pointermove', (event) => {
    const rect = hero.getBoundingClientRect();
    scene.style.setProperty('--px', ((event.clientX - rect.left) / rect.width - 0.5).toFixed(3));
    scene.style.setProperty('--py', ((event.clientY - rect.top) / rect.height - 0.5).toFixed(3));
  });
  hero.addEventListener('pointerleave', () => {
    scene.style.setProperty('--px', 0);
    scene.style.setProperty('--py', 0);
  });
})();

// =============================================================
// Reveal saat scroll untuk section di bawah hero
// =============================================================
(function scrollReveal() {
  const targets = document.querySelectorAll('[data-reveal]');
  if (!targets.length || prefersReducedMotion || !('IntersectionObserver' in window)) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-visible');
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
  );

  targets.forEach((el) => {
    el.classList.add('reveal');
    observer.observe(el);
  });
})();
