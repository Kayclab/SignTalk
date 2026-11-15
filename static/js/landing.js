// Inisialisasi Lucide Icons
lucide.createIcons();

// Mobile Navigation Toggle
const menuBtn = document.getElementById('menu-btn');
const mobileMenu = document.getElementById('mobile-menu');
if (menuBtn && mobileMenu) {
  menuBtn.addEventListener('click', () => {
    mobileMenu.classList.toggle('hidden');
  });
}

// =============================================================
// 1. HERO BUBBLES: HANYA MELAYANG DI ATAS LAPTOP (TIDAK SAMPAI LANGIT)
// =============================================================
(function initHeroBubbles() {
  const stage = document.getElementById('bubble-stage');
  const screen = document.getElementById('laptop-screen');
  const screenLetter = document.getElementById('screen-letter');
  const heroVisual = document.getElementById('hero-visual');
  if (!stage || !screen || !heroVisual) return;

  const VOCABULARY = [
    'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J',
    'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
    'U', 'V', 'W', 'X', 'Y', 'Z',
    '1', '2', '3', '4', '5', '6', '7', '8', '9', '10',
    'Halo', 'Bisa', 'Belajar', 'Teman', 'Terima Kasih', 'Sama-sama', 'Maaf', 'Tolong', 'Permisi', 'Isyarat'
  ];

  const VARIANTS = ['purple', 'yellow', 'pastel-1', 'plum', 'rose', 'yellow', 'pastel-2', 'mauve', 'peach', 'white', 'pastel-3'];
  const COLORS = {
    'purple':   '#2B124C',
    'plum':     '#522B5B',
    'mauve':    '#854F6C',
    'rose':     '#DFB6B2',
    'peach':    '#FBE4DB',
    'yellow':   '#F9C74F',
    'white':    '#FAFAFA',
    'pastel-1': '#E9D5FF',
    'pastel-2': '#C4B5FD',
    'pastel-3': '#D8B4E2',
    'pastel':   '#C4B5FD'
  };

  const SPAWN_INTERVAL = 900;
  const MAX_BUBBLES = 8;

  let vocabIndex = 0;
  let liveCount = 0;
  let heroOnScreen = true;

  const rand = (min, max) => min + Math.random() * (max - min);
  const clamp = (val, min, max) => Math.min(max, Math.max(min, val));

  function getEmitterPoint() {
    const s = stage.getBoundingClientRect();
    const r = screen.getBoundingClientRect();
    return {
      x: r.left - s.left + r.width / 2,
      y: r.top - s.top + r.height * 0.45,
      width: s.width,
    };
  }

  function createBubbleElement(text, variant, size) {
    const el = document.createElement('div');
    el.className = `bubble bubble--${variant}`;
    el.style.setProperty('--s', `${size}px`);
    el.dataset.variant = variant;
    
    const fontSize = text.length > 3 ? Math.max(12, size * 0.22) : Math.max(16, size * 0.4);
    
    el.innerHTML = `
      <div class="bubble-inner" style="--sway:${rand(2.0, 3.2).toFixed(2)}s; font-size: ${fontSize}px;">
        ${text}
      </div>
    `;
    stage.appendChild(el);
    return el;
  }

  function showDetectedText(text) {
    if (screenLetter) screenLetter.textContent = text;
    screen.classList.remove('flash');
    void screen.offsetWidth;
    screen.classList.add('flash');
  }

  function popBubble(el, flightAnimation) {
    if (el.dataset.popped) return;
    el.dataset.popped = '1';

    const matrix = new DOMMatrixReadOnly(getComputedStyle(el).transform);
    const x = matrix.m41;
    const y = matrix.m42;
    const color = COLORS[el.dataset.variant] || '#F9C74F';
    const size = parseFloat(el.style.getPropertyValue('--s'));

    if (flightAnimation) flightAnimation.cancel();

    el.style.pointerEvents = 'none';
    el.animate(
      [
        { transform: `translate(${x}px, ${y}px) scale(1)`, opacity: 1 },
        { transform: `translate(${x}px, ${y}px) scale(1.35)`, opacity: 0 },
      ],
      { duration: 200, easing: 'ease-out', fill: 'forwards' }
    ).onfinish = () => {
      el.remove();
      liveCount = Math.max(0, liveCount - 1);
    };

    const ring = document.createElement('div');
    ring.className = 'pop-ring';
    ring.style.setProperty('--s', `${size}px`);
    ring.style.setProperty('--c', color);
    stage.appendChild(ring);
    ring.animate(
      [
        { transform: `translate(${x}px, ${y}px) scale(0.6)`, opacity: 1 },
        { transform: `translate(${x}px, ${y}px) scale(1.5)`, opacity: 0 },
      ],
      { duration: 380, easing: 'ease-out', fill: 'forwards' }
    ).onfinish = () => ring.remove();

    for (let i = 0; i < 5; i++) {
      const angle = (Math.PI * 2 * i) / 5 + rand(-0.2, 0.2);
      const distance = size * rand(0.65, 1.05);
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
        { duration: rand(320, 440), easing: 'cubic-bezier(.2,.7,.3,1)', fill: 'forwards' }
      ).onfinish = () => drop.remove();
    }
  }

  function spawnBubble() {
    if (!heroOnScreen || document.hidden || liveCount >= MAX_BUBBLES) return;

    const item = VOCABULARY[vocabIndex % VOCABULARY.length];
    const variant = VARIANTS[vocabIndex % VARIANTS.length];
    vocabIndex++;

    const emitter = getEmitterPoint();
    const scaleFactor = clamp(emitter.width / 540, 0.75, 1.1);
    const baseSize = item.length > 4 ? rand(70, 90) : rand(54, 74);
    const size = Math.round(baseSize * scaleFactor);

    const bubbleEl = createBubbleElement(item, variant, size);
    liveCount++;
    showDetectedText(item);

    const side = Math.random() < 0.5 ? -1 : 1;
    const endX = clamp(emitter.x + side * rand(50, 180) * scaleFactor, size, emitter.width - size);
    
    // Cukup melayang di atas laptop saja (sekitar 110px - 160px di atas layar)
    const endY = emitter.y - rand(110, 160) * scaleFactor;
    const dx = endX - emitter.x;
    const dy = endY - emitter.y;

    const flight = bubbleEl.animate(
      [
        {
          transform: `translate(${emitter.x}px, ${emitter.y}px) scale(0.25)`,
          opacity: 0,
        },
        {
          transform: `translate(${emitter.x + dx * 0.3}px, ${emitter.y + dy * 0.35}px) scale(1.05)`,
          opacity: 1,
          offset: 0.25,
        },
        {
          transform: `translate(${emitter.x + dx * 0.8}px, ${emitter.y + dy * 0.8}px) scale(1)`,
          opacity: 0.95,
          offset: 0.75,
        },
        {
          transform: `translate(${endX}px, ${endY}px) scale(0.95)`,
          opacity: 0,
        },
      ],
      {
        duration: rand(4200, 5500),
        easing: 'cubic-bezier(.16,.65,.3,1)',
        fill: 'forwards',
      }
    );

    bubbleEl.addEventListener('click', (e) => {
      e.stopPropagation();
      popBubble(bubbleEl, flight);
    });

    flight.onfinish = () => {
      if (!bubbleEl.dataset.popped) {
        bubbleEl.remove();
        liveCount = Math.max(0, liveCount - 1);
      }
    };
  }

  if ('IntersectionObserver' in window) {
    const obs = new IntersectionObserver((entries) => {
      heroOnScreen = entries[0].isIntersecting;
    }, { threshold: 0.1 });
    obs.observe(heroVisual);
  }

  setInterval(spawnBubble, SPAWN_INTERVAL);
  setTimeout(spawnBubble, 300);
  setTimeout(spawnBubble, 900);
})();

// =============================================================
// 2. KEPALA DINO MENGIKUTI KURSOR (SECTION FITUR)
// =============================================================
(function initDinoHeadTracking() {
  const dinoHead = document.getElementById('dino-head-img');
  if (!dinoHead) return;

  window.addEventListener('mousemove', (e) => {
    const rect = dinoHead.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    const deltaX = e.clientX - centerX;
    const deltaY = e.clientY - centerY;

    const maxRotY = 16;
    const maxRotX = 14;
    const maxShiftX = 18;
    const maxShiftY = 16;

    const rotY = Math.max(-maxRotY, Math.min(maxRotY, (deltaX / window.innerWidth) * 35));
    const rotX = Math.max(-6, Math.min(maxRotX, (deltaY / window.innerHeight) * 32));

    const shiftX = Math.max(-maxShiftX, Math.min(maxShiftX, (deltaX / window.innerWidth) * 28));
    const shiftY = Math.max(-6, Math.min(maxShiftY, (deltaY / window.innerHeight) * 26));

    dinoHead.style.transform = `translate(${shiftX}px, ${shiftY}px) rotateY(${rotY}deg) rotateX(${-rotX}deg)`;
  });
})();

// =============================================================
// ALUR PENGGUNAAN SIGNTALK: AUTO ROTATING ZOOM 1 -> 2 -> 3 -> 4
// =============================================================
(function initAlurZoomRotation() {
  const alurCards = document.querySelectorAll('.alur-card');
  if (!alurCards || alurCards.length === 0) return;

  let currentIndex = 0;
  let intervalId = null;
  let isHovered = false;

  function setActiveStep(index) {
    alurCards.forEach((card, idx) => {
      if (idx === index) {
        card.classList.add('active');
      } else {
        card.classList.remove('active');
      }
    });
  }

  // Set awal langkah 1 aktif
  setActiveStep(0);

  function startRotation() {
    if (intervalId) clearInterval(intervalId);
    intervalId = setInterval(() => {
      if (!isHovered) {
        currentIndex = (currentIndex + 1) % alurCards.length;
        setActiveStep(currentIndex);
      }
    }, 2200);
  }

  alurCards.forEach((card, idx) => {
    card.addEventListener('mouseenter', () => {
      isHovered = true;
      currentIndex = idx;
      setActiveStep(currentIndex);
    });

    card.addEventListener('mouseleave', () => {
      isHovered = false;
    });

    card.addEventListener('click', () => {
      currentIndex = idx;
      setActiveStep(currentIndex);
    });
  });

  startRotation();
})();

// =============================================================
// 3. PESAN TEMAN TULI: 3 BUBBLE DI ATAS (BERANTAKAN) & 4 DI BAWAH TETAP
//    - LOVE MENYEBAR KANAN, KIRI, ATAS
//    - ZERO CLIPPING (TIDAK TERPOTONG DI ATAS)
//    - TIDAK BISA MENABRAK DINO
// =============================================================
(function initGravityPills() {
  const canvas = document.getElementById('gravity-canvas');
  const container = document.getElementById('gravity-container');
  const btnShuffle = document.getElementById('btn-shuffle-capsules');
  const dinoSuratContainer = document.getElementById('dino-surat-container');
  const dinoSuratImg = document.getElementById('dino-surat-img');

  // Efek Love Menyebar Kanan, Kiri, dan Atas saat Dino ditekan
  if (dinoSuratContainer) {
    dinoSuratContainer.addEventListener('click', (e) => {
      const rect = dinoSuratContainer.getBoundingClientRect();
      const count = 9; // 9 love hearts menyebar serempak

      for (let i = 0; i < count; i++) {
        setTimeout(() => {
          const bubble = document.createElement('div');
          bubble.className = 'love-bubble-single';
          const size = 34 + Math.random() * 16;
          bubble.style.width = `${size}px`;
          bubble.style.height = `${size}px`;

          // Posisi awal tepat di dada / amplop surat dino
          bubble.style.left = `${rect.width * 0.5}px`;
          bubble.style.top = `${rect.height * 0.52}px`;

          // Sudut menyebar: dari -160 derajat (kiri) hingga -20 derajat (kanan)
          const baseAngle = -160 + (i / (count - 1)) * 140;
          const jitter = (Math.random() - 0.5) * 16;
          const rad = (baseAngle + jitter) * (Math.PI / 180);
          const dist = 110 + Math.random() * 85;

          const dx = Math.cos(rad) * dist;
          const dy = Math.sin(rad) * dist;
          const rot = (Math.random() - 0.5) * 46;

          bubble.style.setProperty('--dx', `${dx.toFixed(1)}px`);
          bubble.style.setProperty('--dy', `${dy.toFixed(1)}px`);
          bubble.style.setProperty('--rot', `${rot.toFixed(1)}deg`);
          bubble.innerHTML = `<span style="font-size: ${size * 0.52}px;">❤️</span>`;

          dinoSuratContainer.appendChild(bubble);
          setTimeout(() => bubble.remove(), 2500);
        }, i * 40);
      }
    });
  }

  if (!canvas || !container) return;

  const ctx = canvas.getContext('2d');
  let width = (canvas.width = container.clientWidth);
  let height = (canvas.height = container.clientHeight || 380);

  window.addEventListener('resize', () => {
    width = canvas.width = container.clientWidth;
    height = canvas.height = container.clientHeight || 380;
  });

  // 11 Pil Total: 3 Stay di Atas + 4 Melayang di Tengah + 4 Gravity di Bawah
  const PILL_CONFIGS = [
    // === 3 BUBBLE STAY DI ATAS (Letak Berantakan, Tinggi ~50-75px) ===
    { text: 'Semangat Terus! 💪',   isTop: true, layer: 'top', anchorXRatio: 0.18, anchorY: 54, baseAngle: -0.14, theme: { bg: '#F9C74F', text: '#2B124C' } },
    { text: 'Kamu Luar Biasa! ✨',  isTop: true, layer: 'top', anchorXRatio: 0.52, anchorY: 44, baseAngle: 0.11,  theme: { bg: '#DFB6B2', text: '#2B124C' } },
    { text: 'Tanganmu Bersuara 🤟', isTop: true, layer: 'top', anchorXRatio: 0.84, anchorY: 62, baseAngle: -0.08, theme: { bg: '#C4B5FD', text: '#2B124C' } },

    // === 4 BUBBLE MELAYANG DI TENGAH (Tinggi ~130-165px, Letak Berantakan) ===
    { text: 'Jangan Menyerah! 🔥',   isTop: true, layer: 'mid', anchorXRatio: 0.12, anchorY: 142, baseAngle: 0.10,  theme: { bg: '#FBE4DB', text: '#2B124C' } },
    { text: 'Kamu Pasti Bisa! 🌟',   isTop: true, layer: 'mid', anchorXRatio: 0.42, anchorY: 130, baseAngle: -0.12, theme: { bg: '#E9D5FF', text: '#2B124C' } },
    { text: 'Dunia Mendengarmu 🌍',  isTop: true, layer: 'mid', anchorXRatio: 0.70, anchorY: 150, baseAngle: 0.09,  theme: { bg: '#522B5B', text: '#FFFFFF' } },
    { text: 'Terus Berkarya! 🚀',    isTop: true, layer: 'mid', anchorXRatio: 0.94, anchorY: 136, baseAngle: -0.07, theme: { bg: '#F9C74F', text: '#2B124C' } },

    // === 4 BUBBLE DI BAWAH TETAP (Gravity — mengendap di lantai) ===
    { text: 'Penuh Cinta ❤️',         isTop: false, layer: 'bot', theme: { bg: '#F9C74F', text: '#2B124C' } },
    { text: 'Setara & Bangga 🤝',     isTop: false, layer: 'bot', theme: { bg: '#DFB6B2', text: '#2B124C' } },
    { text: 'Inspirasi Kita 🌸',      isTop: false, layer: 'bot', theme: { bg: '#C4B5FD', text: '#2B124C' } },
    { text: 'Karyamu Indah 🎨',       isTop: false, layer: 'bot', theme: { bg: '#FBE4DB', text: '#2B124C' } },
  ];

  // Hitung Barrier / Penghalang Dino agar Pil Tidak Bisa Menabrak Dino
  function getDinoBarrier() {
    const dinoTarget = dinoSuratImg || dinoSuratContainer;
    if (!dinoTarget) return { right: 0, bottom: 0 };
    const cRect = canvas.getBoundingClientRect();
    const dRect = dinoTarget.getBoundingClientRect();
    return {
      right: dRect.right - cRect.left,
      bottom: dRect.bottom - cRect.top
    };
  }

  class Pill {
    constructor(cfg, initialX, initialY) {
      this.text = cfg.text;
      this.theme = cfg.theme;
      this.isTop = cfg.isTop;
      this.layer = cfg.layer || (cfg.isTop ? 'top' : 'bot');
      this.anchorXRatio = cfg.anchorXRatio || 0.5;
      this.anchorY = cfg.anchorY || 60;
      this.baseAngle = cfg.baseAngle || 0;
      this.phase = Math.random() * Math.PI * 2;

      ctx.font = 'bold 14px Fredoka, cursive';
      const textWidth = ctx.measureText(this.text).width;
      this.w = Math.max(92, textWidth + 34);
      this.h = 38;
      this.r = this.h / 2;

      this.x = initialX;
      this.y = initialY;
      this.vx = (Math.random() - 0.5) * 2;
      this.vy = 0;
      this.angle = this.baseAngle;
      this.vAngle = 0;
      this.isDragging = false;
    }

    update(time) {
      if (this.isDragging) return;

      const halfW = this.w / 2;
      const halfH = this.h / 2;

      // Penghalang Dino (Pil tidak bisa menabrak dino)
      const dino = getDinoBarrier();
      const minLeftAllowed = Math.max(12, dino.right + 12);

      if (this.layer === 'top' || this.layer === 'mid') {
        // BUBBLE MELAYANG (top + mid): Hover di posisi anchor masing-masing
        const targetX = minLeftAllowed + halfW + this.anchorXRatio * Math.max(60, width - minLeftAllowed - this.w - 18);
        const hoverOffsetY = Math.sin(time * 0.0022 + this.phase) * 5;
        const targetY = this.anchorY + hoverOffsetY;

        // Pegas elastis mengembalikan ke posisi anchor saat selesai di-drag
        this.vx += (targetX - this.x) * 0.045;
        this.vy += (targetY - this.y) * 0.045;
        this.vx *= 0.87;
        this.vy *= 0.87;

        this.x += this.vx;
        this.y += this.vy;

        // Ayunan sudut halus
        this.angle = this.baseAngle + Math.cos(time * 0.0018 + this.phase) * 0.035;
      } else {
        // BUBBLE DI BAWAH (bot): Gravity — mengendap di lantai
        const gravity = 0.38;
        const friction = 0.985;
        const bounce = 0.52;

        this.vy += gravity;
        this.vx *= friction;
        this.vy *= friction;
        this.vAngle *= 0.96;

        this.x += this.vx;
        this.y += this.vy;
        this.angle += this.vAngle;

        // Pantulan lantai (Dasar Kotak Ungu)
        if (this.y + halfH > height) {
          this.y = height - halfH;
          this.vy = -Math.abs(this.vy) * bounce;
          this.vx *= 0.86;
          this.vAngle *= 0.82;
        }
      }

      // Pastikan pembatas kiri & kanan
      if (this.x - halfW < minLeftAllowed) {
        this.x = minLeftAllowed + halfW;
        this.vx = Math.abs(this.vx) * 0.5 + 0.6;
      } else if (this.x + halfW > width - 10) {
        this.x = width - 10 - halfW;
        this.vx = -Math.abs(this.vx) * 0.5;
      }

      // ZERO CLIPPING ATAS: Jangan sampai ada bagian sudut/teks yang terpotong di atas!
      const maxExt = Math.sin(Math.abs(this.angle)) * halfW + Math.cos(this.angle) * halfH;
      const minAllowedY = maxExt + 14;
      if (this.y < minAllowedY) {
        this.y = minAllowedY;
        this.vy = Math.abs(this.vy) * 0.4;
      }
    }

    draw() {
      ctx.save();
      ctx.translate(this.x, this.y);
      ctx.rotate(this.angle);

      // Bayangan lembut pil
      ctx.shadowColor = 'rgba(43, 18, 76, 0.16)';
      ctx.shadowBlur = 10;
      ctx.shadowOffsetY = 4;

      // Gambar Pil / Kapsul
      ctx.fillStyle = this.theme.bg;
      ctx.strokeStyle = '#2B124C';
      ctx.lineWidth = 2.2;

      ctx.beginPath();
      ctx.roundRect(-this.w / 2, -this.h / 2, this.w, this.h, this.r);
      ctx.fill();
      ctx.stroke();

      // Reset bayangan untuk teks agar tajam
      ctx.shadowColor = 'transparent';

      // Gambar Teks Semangat
      ctx.fillStyle = this.theme.text;
      ctx.font = 'bold 14px Fredoka, cursive';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(this.text, 0, 1.5);

      ctx.restore();
    }

    contains(px, py) {
      const dx = px - this.x;
      const dy = py - this.y;
      return Math.sqrt(dx * dx + dy * dy) < Math.max(this.w / 2, this.h);
    }
  }

  // Buat 11 Pil: 3 di Atas (top) + 4 Melayang Tengah (mid) + 4 Gravity Bawah (bot)
  const pills = [];
  const dinoInit = getDinoBarrier();
  const spawnLeft = Math.max(20, dinoInit.right + 25);
  const spawnWidth = Math.max(220, width - spawnLeft - 40);

  let botCount = 0;
  PILL_CONFIGS.forEach((cfg, i) => {
    let initX, initY;
    if (cfg.layer === 'top' || cfg.layer === 'mid') {
      initX = spawnLeft + (cfg.anchorXRatio || 0.5) * spawnWidth;
      initY = cfg.anchorY || 60;
    } else {
      // bot: sebar di bawah
      initX = spawnLeft + botCount * (spawnWidth / 4) + Math.random() * 20;
      initY = height - 50 - Math.random() * 20;
      botCount++;
    }
    pills.push(new Pill(cfg, initX, initY));
  });

  // Interaksi Drag dengan Kursor
  let draggedPill = null;
  let lastMouse = { x: 0, y: 0 };

  canvas.addEventListener('mousedown', (e) => {
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    lastMouse = { x: mx, y: my };

    for (let i = pills.length - 1; i >= 0; i--) {
      if (pills[i].contains(mx, my)) {
        draggedPill = pills[i];
        draggedPill.isDragging = true;
        pills.splice(i, 1);
        pills.push(draggedPill);
        break;
      }
    }
  });

  window.addEventListener('mousemove', (e) => {
    if (!draggedPill) return;
    const rect = canvas.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    draggedPill.vx = (mx - lastMouse.x) * 0.7;
    draggedPill.vy = (my - lastMouse.y) * 0.7;

    // Pastikan saat di-drag juga tidak bisa menabrak dino & tidak terpotong di atas
    const dino = getDinoBarrier();
    const minLeft = Math.max(12, dino.right + 12) + draggedPill.w / 2;
    const maxRight = width - 10 - draggedPill.w / 2;
    const minTop = draggedPill.h / 2 + 14;

    draggedPill.x = Math.max(minLeft, Math.min(maxRight, mx));
    draggedPill.y = Math.max(minTop, Math.min(height - draggedPill.h / 2, my));
    lastMouse = { x: mx, y: my };
  });

  window.addEventListener('mouseup', () => {
    if (draggedPill) {
      draggedPill.isDragging = false;
      draggedPill = null;
    }
  });

  // Tombol Acak Pesan dihapus — tidak ada lagi #btn-shuffle-capsules

  // Loop Fisika & Animasi (Butter Smooth 60fps)
  function animateGravity(time) {
    ctx.clearRect(0, 0, width, height);

    // Tabrakan antar pil
    for (let i = 0; i < pills.length; i++) {
      for (let j = i + 1; j < pills.length; j++) {
        const p1 = pills[i];
        const p2 = pills[j];
        const dx = p2.x - p1.x;
        const dy = p2.y - p1.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        const minDist = (p1.r + p2.r) * 1.15;

        if (dist < minDist && dist > 0) {
          const overlap = minDist - dist;
          const nx = dx / dist;
          const ny = dy / dist;

          if (!p1.isDragging && p1.layer === 'bot') {
            p1.x -= nx * overlap * 0.5;
            p1.y -= ny * overlap * 0.5;
            p1.vx -= nx * 0.6;
            p1.vy -= ny * 0.6;
          }
          if (!p2.isDragging && p2.layer === 'bot') {
            p2.x += nx * overlap * 0.5;
            p2.y += ny * overlap * 0.5;
            p2.vx += nx * 0.6;
            p2.vy += ny * 0.6;
          }
        }
      }
    }

    pills.forEach((p) => {
      p.update(time);
      p.draw();
    });

    requestAnimationFrame(animateGravity);
  }

  requestAnimationFrame(animateGravity);
})();

// =============================================================
// 4. POPUP / MODAL INTERAKTIF: HANYA KATA-KATA TANPA PENJELASAN
// =============================================================
(function initCategoryModal() {
  const modalOverlay = document.getElementById('category-modal');
  const modalTitle = document.getElementById('modal-title');
  const modalDesc = document.getElementById('modal-desc');
  const modalBody = document.getElementById('modal-body');
  const modalClose = document.getElementById('modal-close');

  if (!modalOverlay || !modalTitle || !modalDesc || !modalBody) return;

  const DATA_CATEGORIES = {
    letters: {
      title: 'Huruf A–Z (BISINDO)',
      desc: 'Daftar huruf abjad bahasa isyarat yang dapat dideteksi.',
      items: 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').map(char => ({
        label: char
      }))
    },
    numbers: {
      title: 'Angka 1–10 (BISINDO)',
      desc: 'Daftar angka bahasa isyarat yang dapat dideteksi.',
      items: ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10'].map(num => ({
        label: num
      }))
    },
    words: {
      title: '10 Kata Penting (BISINDO)',
      desc: 'Daftar kosakata isyarat harian yang dapat dideteksi.',
      items: [
        { label: 'Halo' },
        { label: 'Terima Kasih' },
        { label: 'Sama-sama' },
        { label: 'Maaf' },
        { label: 'Tolong' },
        { label: 'Permisi' },
        { label: 'Bisa' },
        { label: 'Belajar' },
        { label: 'Teman' },
        { label: 'Isyarat' }
      ]
    }
  };

  function openCategory(catKey) {
    const cat = DATA_CATEGORIES[catKey];
    if (!cat) return;

    modalTitle.textContent = cat.title;
    modalDesc.textContent = cat.desc;
    modalBody.innerHTML = '';

    const grid = document.createElement('div');
    // Jika kata-kata, buat kolom lebih lebar dan bersih
    grid.className = catKey === 'words' 
      ? 'grid grid-cols-2 sm:grid-cols-3 gap-3.5'
      : 'grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 lg:grid-cols-6 gap-3';

    cat.items.forEach(item => {
      const card = document.createElement('div');
      card.className = 'bg-[#FAF7FD] hover:bg-[#E9D5FF] border-2 border-[#C4B5FD]/50 hover:border-[#F9C74F] rounded-2xl p-4 flex items-center justify-center text-center cursor-pointer transition-all duration-200 hover:-translate-y-1 hover:shadow-md select-none';
      
      // HANYA KATA / HURUF SAJA TANPA PENJELASAN
      card.innerHTML = `
        <span class="text-2xl sm:text-3xl font-extrabold text-[#2B124C] font-heading">${item.label}</span>
      `;

      card.addEventListener('click', () => {
        card.classList.add('scale-95', 'bg-[#F9C74F]');
        setTimeout(() => card.classList.remove('scale-95', 'bg-[#F9C74F]'), 180);
      });

      grid.appendChild(card);
    });

    modalBody.appendChild(grid);
    modalOverlay.classList.add('active');
    document.body.style.overflow = 'hidden';
  }

  function closeModal() {
    modalOverlay.classList.remove('active');
    document.body.style.overflow = '';
  }

  const btnLetters = document.getElementById('btn-modal-letters');
  const btnNumbers = document.getElementById('btn-modal-numbers');
  const btnWords = document.getElementById('btn-modal-words');

  if (btnLetters) btnLetters.addEventListener('click', () => openCategory('letters'));
  if (btnNumbers) btnNumbers.addEventListener('click', () => openCategory('numbers'));
  if (btnWords) btnWords.addEventListener('click', () => openCategory('words'));

  if (modalClose) modalClose.addEventListener('click', closeModal);
  modalOverlay.addEventListener('click', (e) => {
    if (e.target === modalOverlay) closeModal();
  });
  window.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modalOverlay.classList.contains('active')) closeModal();
  });
})();
