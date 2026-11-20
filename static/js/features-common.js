/**
 * SignTalk - features-common.js
 * Logika terpadu untuk Penerjemah, Latihan Kata, Kuis Isyarat, & Game Puzzle.
 */

// =============================================================
// 1. DATASET REFERENSI KAMUS BISINDO (26 Huruf, 10 Angka, 10 Kata)
// HANYA 10 KATA RESMI: Belajar, Permisi, Maaf, Terimakasih, Sama sama,
//                      Teman-teman, Bisa, Sedikit, Bahasa isyarat, Tolong.
// =============================================================
const KAMUS_DATA = [
  // Huruf A-Z (26 Huruf)
  { char: 'A', type: 'Huruf', desc: 'Kepalan tangan menghadap ke depan dengan ibu jari tegak di samping.', example: 'A untuk Apel' },
  { char: 'B', type: 'Huruf', desc: 'Empat jari tegak rapat ke atas dengan ibu jari ditekuk di depan telapak.', example: 'B untuk Bola' },
  { char: 'C', type: 'Huruf', desc: 'Jari-jari melengkung membentuk setengah lingkaran menyerupai huruf C.', example: 'C untuk Cacing' },
  { char: 'D', type: 'Huruf', desc: 'Jari telunjuk tegak ke atas, jari lainnya melingkar menyentuh ibu jari.', example: 'D untuk Daun' },
  { char: 'E', type: 'Huruf', desc: 'Seluruh ujung jari ditekuk ke bawah menyentuh ujung ibu jari.', example: 'E untuk Elang' },
  { char: 'F', type: 'Huruf', desc: 'Ujung telunjuk dan ibu jari bertemu, tiga jari lainnya tegak lurus.', example: 'F untuk Foto' },
  { char: 'G', type: 'Huruf', desc: 'Ibu jari dan telunjuk mengarah horizontal ke samping sejajar.', example: 'G untuk Gajah' },
  { char: 'H', type: 'Huruf', desc: 'Telunjuk dan jari tengah lurus ke samping sejajar.', example: 'H untuk Harimau' },
  { char: 'I', type: 'Huruf', desc: 'Kelingking tegak ke atas, jari-jari lainnya menggenggam rapat.', example: 'I untuk Ikan' },
  { char: 'J', type: 'Huruf', desc: 'Kelingking tegak lalu digerakkan melengkung membentuk pola J.', example: 'J untuk Jagung' },
  { char: 'K', type: 'Huruf', desc: 'Telunjuk dan jari tengah membentuk V dengan ibu jari di antaranya.', example: 'K untuk Kucing' },
  { char: 'L', type: 'Huruf', desc: 'Telunjuk dan ibu jari membentuk sudut siku-siku 90 derajat menyerupai L.', example: 'L untuk Lemon' },
  { char: 'M', type: 'Huruf', desc: 'Ibu jari diselipkan di bawah tiga jari (telunjuk, tengah, manis).', example: 'M untuk Matahari' },
  { char: 'N', type: 'Huruf', desc: 'Ibu jari diselipkan di bawah dua jari (telunjuk dan tengah).', example: 'N untuk Nanas' },
  { char: 'O', type: 'Huruf', desc: 'Seluruh ujung jari melengkung bertemu membentuk lingkaran huruf O.', example: 'O untuk Ombak' },
  { char: 'P', type: 'Huruf', desc: 'Sama seperti bentuk K namun posisi tangan mengarah ke bawah.', example: 'P untuk Pohon' },
  { char: 'Q', type: 'Huruf', desc: 'Bentuk G namun posisi jari diarahkan ke bawah.', example: 'Q untuk Quran' },
  { char: 'R', type: 'Huruf', desc: 'Jari tengah menyilang di atas jari telunjuk yang tegak lurus.', example: 'R untuk Rumah' },
  { char: 'S', type: 'Huruf', desc: 'Kepalan tangan rapat dengan ibu jari melintang di depan jari-jari.', example: 'S untuk Sepatu' },
  { char: 'T', type: 'Huruf', desc: 'Ibu jari diselipkan di antara telunjuk dan jari tengah.', example: 'T untuk Topi' },
  { char: 'U', type: 'Huruf', desc: 'Telunjuk dan jari tengah tegak rapat lurus ke atas.', example: 'U untuk Ular' },
  { char: 'V', type: 'Huruf', desc: 'Telunjuk dan jari tengah membentuk huruf V terbuka (peace sign).', example: 'V untuk Vas' },
  { char: 'W', type: 'Huruf', desc: 'Tiga jari (telunjuk, tengah, manis) tegak membentuk huruf W.', example: 'W untuk Wortel' },
  { char: 'X', type: 'Huruf', desc: 'Jari telunjuk ditekuk melengkung seperti kait/cakar.', example: 'X untuk Xilofon' },
  { char: 'Y', type: 'Huruf', desc: 'Ibu jari dan kelingking terentang keluar membentuk pola Y.', example: 'Y untuk Yoyo' },
  { char: 'Z', type: 'Huruf', desc: 'Telunjuk membentuk garis zig-zag huruf Z di udara.', example: 'Z untuk Zebra' },

  // Angka 1-10 (10 Angka)
  { char: '1', type: 'Angka', desc: 'Telunjuk tegak ke atas, jari lainnya menggenggam.', example: 'Angka Satu' },
  { char: '2', type: 'Angka', desc: 'Telunjuk dan jari tengah tegak ke atas terbuka.', example: 'Angka Dua' },
  { char: '3', type: 'Angka', desc: 'Ibu jari, telunjuk, dan jari tengah dibuka ke atas.', example: 'Angka Tiga' },
  { char: '4', type: 'Angka', desc: 'Empat jari tegak ke atas dengan ibu jari ditekuk ke telapak.', example: 'Angka Empat' },
  { char: '5', type: 'Angka', desc: 'Seluruh lima jari terbuka lebar ke atas.', example: 'Angka Lima' },
  { char: '6', type: 'Angka', desc: 'Kelingking ditekuk menyentuh ujung ibu jari, tiga jari lainnya tegak.', example: 'Angka Enam' },
  { char: '7', type: 'Angka', desc: 'Jari manis menyentuh ujung ibu jari, tiga jari lainnya tegak.', example: 'Angka Tujuh' },
  { char: '8', type: 'Angka', desc: 'Jari tengah menyentuh ujung ibu jari, tiga jari lainnya tegak.', example: 'Angka Delapan' },
  { char: '9', type: 'Angka', desc: 'Jari telunjuk menyentuh ujung ibu jari, tiga jari lainnya tegak.', example: 'Angka Sembilan' },
  { char: '10', type: 'Angka', desc: 'Ibu jari diacungkan (jempol) lalu digoyangkan ke kanan dan kiri.', example: 'Angka Sepuluh' },

  // TEPAT 10 KATA BISINDO RESMI
  { char: 'Belajar', type: 'Kata', desc: 'Ujung jari tangan kanan menyentuh telapak tangan kiri lalu diangkat ke arah kening secara mantap.', example: 'Menuntut ilmu' },
  { char: 'Permisi', type: 'Kata', desc: 'Satu telapak tangan merunduk lembut di depan tubuh bergerak santun ke arah depan.', example: 'Memohon izin lewat' },
  { char: 'Maaf', type: 'Kata', desc: 'Kepalan tangan melingkar perlahan di atas dada dengan ekspresi penyesalan tulus.', example: 'Permohonan maaf' },
  { char: 'Terimakasih', type: 'Kata', desc: 'Ujung jari menyentuh bibir bawah atau dagu lalu digerakkan terbuka maju ke depan sambil tersenyum.', example: 'Ungkapan terima kasih' },
  { char: 'Sama sama', type: 'Kata', desc: 'Kedua telapak tangan terbuka digerakkan bersamaan ke arah depan secara lembut.', example: 'Membalas terima kasih' },
  { char: 'Teman-teman', type: 'Kata', desc: 'Kedua jari telunjuk saling mengait secara bergantian menunjukkan ikatan persahabatan.', example: 'Menyapa sahabat' },
  { char: 'Bisa', type: 'Kata', desc: 'Tangan dengan posisi kepalan ditekan ke bawah dengan tegas menunjukkan kesanggupan.', example: 'Mampu melakukan' },
  { char: 'Sedikit', type: 'Kata', desc: 'Ibu jari dan jari telunjuk didekatkan dengan celah kecil menunjukkan porsi minim.', example: 'Kuantitas sedikit' },
  { char: 'Bahasa isyarat', type: 'Kata', desc: 'Kedua tangan dengan jari terbuka bergerak melingkar bergantian di depan dada.', example: 'Komunikasi visual' },
  { char: 'Tolong', type: 'Kata', desc: 'Kedua telapak tangan menangkup rapat di depan dada dengan ekspresi memohon pertolongan.', example: 'Meminta bantuan' }
];

function getGestureDescription(char) {
  if (!char || char === '-') {
    return 'Posisikan tangan Anda di depan kamera untuk memulai pengenalan isyarat.';
  }
  const cleanChar = String(char).replace(/[- ]/g, '').toUpperCase();
  const item = KAMUS_DATA.find(k => k.char.replace(/[- ]/g, '').toUpperCase() === cleanChar);
  if (item) {
    return `${item.desc} (${item.example})`;
  }
  return `Isyarat ${char} terdeteksi.`;
}

// SVG Illustration Generator untuk Kartu Kamus & Game
// Bentuk tangan asli diambil dari dataset (static/js/hand-shapes.js, dibuat oleh
// scripts/generate_hand_shapes.py). Jika label tidak ada, dipakai ilustrasi bawaan.
const HAND_FINGERS = [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12], [13, 14, 15, 16], [17, 18, 19, 20]];
const HAND_PALM = [0, 1, 5, 9, 13, 17];

function renderDatasetHandSVG(hands, gid) {
  // Susun tangan berdampingan, lalu skala agar pas di dalam lingkaran kartu
  const gap = 0.35;
  let cursor = 0;
  const placed = hands.map(rawHand => {
    // Dataset dinormalisasi memakai max(|x|,|y|,|z|); z sering mendominasi sehingga
    // tangan tampak mengecil. Untuk gambar, skala ulang hanya berdasarkan x,y.
    const m = Math.max(...rawHand.map(p => Math.max(Math.abs(p[0]), Math.abs(p[1]))), 1e-6);
    const hand = rawHand.map(p => [p[0] / m, p[1] / m, p[2] / m]);
    const xs = hand.map(p => p[0]);
    const min = Math.min(...xs), max = Math.max(...xs);
    const dx = cursor - min;
    cursor += (max - min) + gap;
    return hand.map(p => [p[0] + dx, p[1], p[2]]);
  });
  const all = placed.flat();
  const minX = Math.min(...all.map(p => p[0])), maxX = Math.max(...all.map(p => p[0]));
  const minY = Math.min(...all.map(p => p[1])), maxY = Math.max(...all.map(p => p[1]));
  const box = 84;
  const scale = box / Math.max(maxX - minX, maxY - minY, 0.01);
  const offX = 80 - ((minX + maxX) / 2) * scale;
  const offY = 80 - ((minY + maxY) / 2) * scale;
  const T = p => [(p[0] * scale + offX).toFixed(1), (p[1] * scale + offY).toFixed(1)];

  return placed.map(hand => {
    const pts = hand.map(T);
    const palm = HAND_PALM.map(i => pts[i].join(',')).join(' ');
    // Jari yang lebih jauh dari kamera (z lebih besar) digambar lebih dulu
    const fingers = HAND_FINGERS
      .map(f => ({ f, z: f.reduce((a, i) => a + hand[i][2], 0) / f.length }))
      .sort((a, b) => b.z - a.z)
      .map(({ f }) => f.map(i => pts[i].join(',')).join(' '));
    const outline = 'fill="none" stroke="#2B124C" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"';
    const inner = 'fill="none" stroke="#F9D14F" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"';
    return `
      <polygon points="${palm}" fill="#2B124C" stroke="#2B124C" stroke-width="9" stroke-linejoin="round"/>
      ${fingers.map(f => `<polyline points="${f}" ${outline}/>`).join('')}
      <polygon points="${palm}" fill="url(#${gid})" stroke="url(#${gid})" stroke-width="7" stroke-linejoin="round"/>
      ${fingers.map(f => `<polyline points="${f}" ${inner}/>`).join('')}
      ${HAND_FINGERS.map(f => f.map(i => `<circle cx="${pts[i][0]}" cy="${pts[i][1]}" r="1.8" fill="#6346D8"/>`).join('')).join('')}
    `;
  }).join('');
}

// Foto/gambar tangan penuh untuk sisi belakang kartu.
// Taruh file di static/img/hands/<nama>.jpeg (atau .jpg / .png / .webp), mis. A.jpeg, 10.jpeg,
// Bahasa-isyarat.jpeg (spasi jadi "-"; huruf besar/kecil keduanya dicoba).
// Jika file tidak ada, kartu otomatis memakai ilustrasi dari dataset.
function handPhotoName(label) {
  return String(label).trim().replace(/\s+/g, '-');
}

function attachHandPhoto(cardBack, label) {
  const img = cardBack.querySelector('.cf-card-photo');
  if (!img) return;
  const name = handPhotoName(label);
  // Kata (mis. "Belajar") memakai WebP/GIF berhuruf kecil -> coba itu dulu agar tidak
  // membuang banyak request 404 (server Linux/Vercel membedakan huruf besar/kecil).
  const isWord = String(label).trim().length > 2 && isNaN(Number(label));
  const isNumber = !isWord && !isNaN(Number(label));
  const names = [...new Set(isWord ? [name.toLowerCase(), name] : [name, name.toLowerCase()])];
  const exts = isWord
    ? ['webp', 'gif', 'jpg', 'jpeg', 'png']
    : (isNumber ? ['jpeg', 'jpg', 'png', 'webp', 'gif'] : ['jpg', 'jpeg', 'png', 'webp', 'gif']);
  const candidates = [];
  names.forEach(n => exts.forEach(e => candidates.push('/static/img/hands/' + encodeURIComponent(n) + '.' + e)));
  let i = 0;
  img.decoding = 'async';
  img.onload = () => cardBack.classList.add('has-photo');
  img.onerror = () => {
    i += 1;
    if (i < candidates.length) img.src = candidates[i];
    else img.remove();
  };
  img.src = candidates[0];
}

function generateHandIllustrationSVG(item) {
  const isWord = item.type === 'Kata';
  const label = item.char;
  const gid = 'handGrad_' + label.replace(/[^a-zA-Z0-9]/g, '_');
  const shape = (typeof HAND_SHAPES !== 'undefined') ? HAND_SHAPES[label] : null;

  const defs = `
      <defs>
        <linearGradient id="${gid}" gradientUnits="userSpaceOnUse" x1="30" y1="30" x2="130" y2="130">
          <stop offset="0%" stop-color="#F9D14F" />
          <stop offset="100%" stop-color="#F0B8A8" />
        </linearGradient>
      </defs>`;

  if (shape && shape.length) {
    return `
    <svg viewBox="0 0 160 160" class="w-full h-full drop-shadow-sm select-none" xmlns="http://www.w3.org/2000/svg">
      ${defs}
      <circle cx="80" cy="80" r="66" fill="#FFF8EE" stroke="#E9D5FF" stroke-width="2"/>
      <circle cx="80" cy="80" r="58" fill="#EADBFC" stroke="#F9D14F" stroke-dasharray="3 3" stroke-width="1.5"/>
      <g>${renderDatasetHandSVG(shape, gid)}</g>
    </svg>
  `;
  }

  return `
    <svg viewBox="0 0 160 160" class="w-full h-full drop-shadow-sm select-none" xmlns="http://www.w3.org/2000/svg">
      ${defs}
      <circle cx="80" cy="80" r="66" fill="#FFF8EE" stroke="#E9D5FF" stroke-width="2"/>
      <circle cx="80" cy="80" r="54" fill="#EADBFC" stroke="#F9C74F" stroke-dasharray="3 3" stroke-width="1.5"/>
      <g>
        ${isWord ? `
          <path d="M54 110 C54 85, 46 70, 58 60 C65 55, 75 62, 70 78 L66 88 L75 88 C82 88, 86 98, 78 108 Z" fill="url(#${gid})" stroke="#2B124C" stroke-width="2.5"/>
          <path d="M106 110 C106 85, 114 70, 102 60 C95 55, 85 62, 90 78 L94 88 L85 88 C78 88, 74 98, 82 108 Z" fill="url(#${gid})" stroke="#2B124C" stroke-width="2.5"/>
        ` : `
          <path d="M60 115 L60 92 C60 84, 66 76, 76 76 C82 76, 86 80, 86 86 L86 68 C86 62, 92 58, 97 62 C101 65, 101 72, 101 78 L101 72 C101 66, 107 63, 112 67 C116 70, 116 76, 115 86 L115 115 Z" fill="url(#${gid})" stroke="#2B124C" stroke-width="2.5"/>
          <path d="M50 98 C44 92, 46 82, 55 78 C62 74, 70 80, 72 90 Z" fill="url(#${gid})" stroke="#2B124C" stroke-width="2.5"/>
        `}
      </g>
    </svg>
  `;
}

// =============================================================
// 2. TEXT-TO-SPEECH (TTS) BAHASA INDONESIA
// =============================================================
function speakText(text) {
  if (!text || text === '-' || !('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'id-ID';
  utterance.rate = 1.15;
  utterance.pitch = 1.05;
  window.speechSynthesis.speak(utterance);
}

// =============================================================
// 3. PREDICTION STABILIZER (MENCEGAH TEBAKAN JITTER/LONCAT-LONCAT)
// =============================================================
class PredictionStabilizer {
  constructor(confirmFrames = 3, confirmMs = 320, minConfidence = 52) {
    this.confirmFrames = confirmFrames;
    this.confirmMs = confirmMs;
    this.minConfidence = minConfidence;
    this.stableLabel = '-';
    this.stableConfidence = 0;
    this.candidate = null;
    this.lastHandSeen = 0;
  }

  update(label, confidence, detected) {
    const now = performance.now();

    // Jika tangan hilang atau keyakinan di bawah batas
    if (!detected || label === '-' || confidence < this.minConfidence) {
      if (now - this.lastHandSeen > 650) {
        this.stableLabel = '-';
        this.stableConfidence = 0;
        this.candidate = null;
      }
      return {
        label: this.stableLabel,
        confidence: this.stableConfidence,
        detected: this.stableLabel !== '-'
      };
    }

    this.lastHandSeen = now;

    // Cek apakah label sama dengan kandidat saat ini
    if (this.candidate && this.candidate.label === label) {
      this.candidate.frames += 1;
      this.candidate.totalConfidence += confidence;
    } else {
      this.candidate = {
        label: label,
        since: now,
        frames: 1,
        totalConfidence: confidence
      };
    }

    const duration = now - this.candidate.since;

    // Label baru hanya disahkan jika muncul berturut-turut minimal 3 frame DAN 320ms
    if (this.candidate.frames >= this.confirmFrames && duration >= this.confirmMs) {
      this.stableLabel = this.candidate.label;
      this.stableConfidence = Math.round(this.candidate.totalConfidence / this.candidate.frames);
    }

    return {
      label: this.stableLabel,
      confidence: this.stableConfidence,
      detected: this.stableLabel !== '-'
    };
  }
}

// =============================================================
// 4. HAND SKELETON CONNECTIONS & RENDERER (PERSIS GAMBAR NO. 1)
// - Garis Ungu muda (#C4B5FD) tipis 2px
// - Titik Sendi Kuning (#F9D14F) dengan titik putih di tengah
// =============================================================
const HAND_CONNECTIONS = [
  // Radiasi dari pergelangan tangan (0)
  [0, 1], [0, 5], [0, 9], [0, 13], [0, 17],
  // Telapak melintang
  [5, 9], [9, 13], [13, 17],
  // Ibu Jari
  [1, 2], [2, 3], [3, 4],
  // Telunjuk
  [5, 6], [6, 7], [7, 8],
  // Jari Tengah
  [9, 10], [10, 11], [11, 12],
  // Jari Manis
  [13, 14], [14, 15], [15, 16],
  // Kelingking
  [17, 18], [18, 19], [19, 20]
];

function drawHandSkeleton(ctx, landmarks, canvasW, canvasH, isFlipped = false) {
  if (!landmarks || landmarks.length === 0) return;

  landmarks.forEach(hand => {
    // 1. Gambar Garis Kerangka Hijau Neon (Persis Gambar MediaPipe No. 1 / Gambar 2)
    ctx.save();
    ctx.strokeStyle = '#C4B5FD';
    ctx.lineWidth = 2;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';
    ctx.shadowColor = 'rgba(196, 181, 253, 0.6)';
    ctx.shadowBlur = 3;

    HAND_CONNECTIONS.forEach(([i, j]) => {
      const p1 = hand[i];
      const p2 = hand[j];
      if (!p1 || !p2) return;

      const normX1 = isFlipped ? p1.x : (1 - p1.x);
      const normX2 = isFlipped ? p2.x : (1 - p2.x);

      const x1 = normX1 * canvasW;
      const y1 = p1.y * canvasH;
      const x2 = normX2 * canvasW;
      const y2 = p2.y * canvasH;

      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
    });
    ctx.restore();

    // 2. Gambar Titik Sendi Magenta dengan Titik Putih di Tengah (Persis Gambar MediaPipe)
    hand.forEach(lm => {
      const normX = isFlipped ? lm.x : (1 - lm.x);
      const x = normX * canvasW;
      const y = lm.y * canvasH;

      // Outer magenta circle
      ctx.beginPath();
      ctx.arc(x, y, 4, 0, 2 * Math.PI);
      ctx.fillStyle = '#F9D14F';
      ctx.fill();

      // White inner center dot
      ctx.beginPath();
      ctx.arc(x, y, 1.5, 0, 2 * Math.PI);
      ctx.fillStyle = '#FFFFFF';
      ctx.fill();
    });
  });
}

// =============================================================
// 5. SIGNTALK CAMERA CONTROLLER
// =============================================================
class SignTalkCamera {
  constructor({
    videoElementId = 'camera-video',
    canvasElementId = 'camera-canvas',
    placeholderId = 'camera-placeholder',
    startButtonId = 'start-camera-btn',
    stopButtonId = 'stop-camera-btn',
    pipelineToggleId = null,
    flipButtonId = 'flip-camera-btn',
    onPrediction = null,
    minFrameGapMs = 60,
    trackOnly = false,   // true: server hanya mendeteksi tangan (tanpa prediksi huruf)
    smoothTauMs = 0,     // >0: landmark dihaluskan (waktu respons dalam ms)
    holdMs = null,       // !=null: pertahankan landmark sekian ms saat deteksi hilang
    onFrame = null       // dipanggil tiap frame render: ({hands, dt, now})
  }) {
    this.video = document.getElementById(videoElementId);
    this.canvas = document.getElementById(canvasElementId);
    this.placeholder = document.getElementById(placeholderId);
    this.startBtn = document.getElementById(startButtonId);
    this.stopBtn = document.getElementById(stopButtonId);
    this.pipelineToggle = pipelineToggleId ? document.getElementById(pipelineToggleId) : null;
    this.flipBtn = document.getElementById(flipButtonId);

    this.onPrediction = onPrediction;
    this.minFrameGapMs = minFrameGapMs;
    this.trackOnly = trackOnly;
    this.smoothTauMs = smoothTauMs;
    this.holdMs = holdMs;
    this.onFrame = onFrame;
    this.displayLandmarks = [];
    this.lastSeenAt = 0;
    this._lastFrameT = 0;

    this.stream = null;
    this.isPredicting = false;
    this.loopId = 0;
    this.isFlipped = false; // Default: non-mirror (sesuai instruksi user)

    this.stabilizer = new PredictionStabilizer(3, 320, 52);

    this.offscreenCanvas = document.createElement('canvas');
    this.offscreenCanvas.width = 320;
    this.offscreenCanvas.height = 240;
    this.offscreenCtx = this.offscreenCanvas.getContext('2d');

    this.latestLandmarks = [];

    this.initEvents();
  }

  initEvents() {
    if (this.startBtn) {
      this.startBtn.addEventListener('click', () => this.start());
    }
    if (this.stopBtn) {
      this.stopBtn.addEventListener('click', () => this.stop());
    }
    if (this.flipBtn) {
      this.flipBtn.addEventListener('click', () => this.toggleFlip());
    }
  }

  toggleFlip() {
    this.isFlipped = !this.isFlipped;
  }

  // HP: samakan rasio kotak kamera dengan rasio video (kamera HP biasanya potret)
  // supaya gambar tidak terpotong dan posisi tangan tetap sejajar.
  _fitBoxToVideo() {
    const box = this.canvas && this.canvas.parentElement;
    if (!box || !this.video) return;
    const apply = () => {
      const vw = this.video.videoWidth;
      const vh = this.video.videoHeight;
      if (!vw || !vh) return;
      const small = window.matchMedia('(max-width: 767px)').matches;
      box.style.aspectRatio = (small || vh > vw) ? `${vw} / ${vh}` : '';
    };
    apply();
    this.video.addEventListener('loadedmetadata', apply, { once: true });
  }

  _resetBoxAspect() {
    const box = this.canvas && this.canvas.parentElement;
    if (box) box.style.aspectRatio = '';
  }

  async start() {
    try {
      this.stream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 640 },
          height: { ideal: 480 },
          facingMode: 'user'
        },
        audio: false
      });

      this.video.srcObject = this.stream;
      await this.video.play();
      this._fitBoxToVideo();

      if (this.placeholder) {
        this.placeholder.classList.add('hidden');
        this.placeholder.style.display = 'none';
      }

      if (this.startBtn) {
        this.startBtn.disabled = true;
        this.startBtn.classList.add('opacity-40', 'cursor-not-allowed');
      }
      if (this.stopBtn) {
        this.stopBtn.disabled = false;
        this.stopBtn.classList.remove('opacity-40', 'cursor-not-allowed');
        this.stopBtn.classList.add('active-stop');
      }

      this.loopId++;
      this.runPredictionLoop(this.loopId);
      this.startCanvasRenderLoop(this.loopId);
    } catch (err) {
      console.error('Kamera error:', err);
      alert('Tidak dapat mengakses kamera. Pastikan izin webcam aktif.');
    }
  }

  stop() {
    this.loopId++;
    this._resetBoxAspect();

    if (this.stream) {
      this.stream.getTracks().forEach(track => track.stop());
      this.stream = null;
    }

    if (this.video) {
      this.video.srcObject = null;
    }

    if (this.canvas) {
      const ctx = this.canvas.getContext('2d');
      ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }

    if (this.placeholder) {
      this.placeholder.classList.remove('hidden');
      this.placeholder.style.display = 'flex';
    }

    if (this.startBtn) {
      this.startBtn.disabled = false;
      this.startBtn.classList.remove('opacity-40', 'cursor-not-allowed');
    }
    if (this.stopBtn) {
      this.stopBtn.disabled = true;
      this.stopBtn.classList.add('opacity-40', 'cursor-not-allowed');
      this.stopBtn.classList.remove('active-stop');
    }

    this.latestLandmarks = [];
    this.displayLandmarks = [];

    if (this.onPrediction) {
      this.onPrediction({
        detected: false,
        prediction: '-',
        confidence: 0,
        landmarks: [],
        message: 'Kamera dihentikan.'
      });
    }
  }

  // Haluskan landmark dari server (yang datang ~10-15x/detik) menjadi gerakan mulus per frame
  updateDisplayLandmarks(dt) {
    const target = this.latestLandmarks || [];
    if (!this.smoothTauMs || target.length === 0) {
      this.displayLandmarks = target;
      return;
    }
    const shown = this.displayLandmarks;
    const sameShape = shown.length === target.length &&
      shown.every((hand, i) => hand.length === target[i].length);
    if (!sameShape) {
      this.displayLandmarks = target.map(hand => hand.map(p => ({ x: p.x, y: p.y })));
      return;
    }
    const a = 1 - Math.exp(-dt / this.smoothTauMs);
    target.forEach((hand, i) => hand.forEach((p, j) => {
      const q = shown[i][j];
      q.x += (p.x - q.x) * a;
      q.y += (p.y - q.y) * a;
    }));
  }

  startCanvasRenderLoop(id) {
    const render = () => {
      if (id !== this.loopId || !this.stream) return;

      const nowT = performance.now();
      const dt = this._lastFrameT ? Math.min(nowT - this._lastFrameT, 100) : 16;
      this._lastFrameT = nowT;
      this.updateDisplayLandmarks(dt);

      if (this.canvas && this.video && this.video.videoWidth > 0 && this.video.videoHeight > 0) {
        if (this.canvas.width !== this.video.videoWidth || this.canvas.height !== this.video.videoHeight) {
          this.canvas.width = this.video.videoWidth;
          this.canvas.height = this.video.videoHeight;
        }

        const ctx = this.canvas.getContext('2d');

        // 1. Render frame video webcam secara real-time langsung ke canvas
        if (this.isFlipped) {
          ctx.save();
          ctx.translate(this.canvas.width, 0);
          ctx.scale(-1, 1);
          ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
          ctx.restore();
        } else {
          ctx.drawImage(this.video, 0, 0, this.canvas.width, this.canvas.height);
        }

        // 2. Render Kerangka Sendi Tangan (Pipeline Landmark Overlay)
        // Di Game, pipeline selalu aktif (pipelineToggleId = null).
        // Di menu lain (Penerjemah, Latihan, Kuis), mengikuti switch toggle.
        const showPipeline = !this.pipelineToggle || this.pipelineToggle.checked;

        if (showPipeline && this.displayLandmarks && this.displayLandmarks.length > 0) {
          drawHandSkeleton(
            ctx,
            this.displayLandmarks,
            this.canvas.width,
            this.canvas.height,
            this.isFlipped
          );
        }
      }

      if (this.onFrame) {
        try {
          this.onFrame({ hands: this.displayLandmarks, dt, now: nowT });
        } catch (err) {
          console.warn('onFrame error:', err);
        }
      }

      requestAnimationFrame(render);
    };
    requestAnimationFrame(render);
  }

  async runPredictionLoop(id) {
    while (id === this.loopId && this.stream) {
      const startTime = performance.now();
      await this.captureAndPredict();
      const elapsed = performance.now() - startTime;
      const wait = Math.max(0, this.minFrameGapMs - elapsed);
      await new Promise(r => setTimeout(r, wait));
    }
  }

  async captureAndPredict() {
    if (!this.stream || this.isPredicting || !this.video || this.video.readyState < 2) return;
    this.isPredicting = true;

    try {
      this.offscreenCtx.drawImage(
        this.video,
        0, 0,
        this.offscreenCanvas.width,
        this.offscreenCanvas.height
      );

      const blob = await new Promise(res => this.offscreenCanvas.toBlob(res, 'image/jpeg', 0.65));
      if (!blob) throw new Error('Blob kosong');

      const formData = new FormData();
      formData.append('frame', blob, 'frame.jpg');
      if (this.trackOnly) formData.append('mode', 'track');

      const response = await fetch('/api/predict', {
        method: 'POST',
        body: formData
      });

      const rawResult = await response.json();

      if (rawResult && rawResult.landmarks && rawResult.landmarks.length > 0) {
        this.latestLandmarks = rawResult.landmarks;
        this.missedLandmarksCount = 0;
        this.lastSeenAt = performance.now();
      } else {
        this.missedLandmarksCount = (this.missedLandmarksCount || 0) + 1;
        if (this.holdMs != null) {
          // Pertahankan kerangka sekian ms agar deteksi yang hilang sesaat tidak memutus gerakan
          if (performance.now() - this.lastSeenAt > this.holdMs) {
            this.latestLandmarks = [];
          }
        } else if (this.missedLandmarksCount >= 3) {
          // Pertahankan kerangka selama 3 siklus agar tidak berkedip (smooth tracking)
          this.latestLandmarks = [];
        }
      }

      if (this.onPrediction && rawResult) {
        const stable = this.stabilizer.update(
          rawResult.prediction || '-',
          rawResult.confidence || 0,
          rawResult.detected
        );

        this.onPrediction({
          success: true,
          detected: stable.detected,
          detected_hands: rawResult.detected_hands || 0,
          prediction: stable.label,
          confidence: stable.confidence,
          message: rawResult.message || '',
          landmarks: this.latestLandmarks
        });
      }
    } catch (err) {
      console.warn('Prediksi error:', err);
    } finally {
      this.isPredicting = false;
    }
  }
}

// =============================================================
// 6. KAMUS BISINDO: 3D COVERFLOW & SMOOTH INTERACTIVE FLIP CARD
// =============================================================
function initKamusCoverFlow({
  stageId = 'coverflow-stage',
  searchInputId = 'kamus-search',
  prevBtnId = 'cf-prev-btn',
  nextBtnId = 'cf-next-btn'
}) {
  const stage = document.getElementById(stageId);
  const searchInput = document.getElementById(searchInputId);
  const prevBtn = document.getElementById(prevBtnId);
  const nextBtn = document.getElementById(nextBtnId);

  if (!stage) return;

  let currentIndex = 0;
  let activePool = [...KAMUS_DATA];
  let autoSlideTimer = null;
  let isHovered = false;

  let cardElements = [];
  let cardElementsInitialized = false;

  // Ukuran font adaptif agar tidak overflow/terpotong
  function charFontSize(char) {
    if (char.length === 1) return '4rem';
    if (char.length <= 3) return '2.5rem';
    if (char.length <= 7) return '1.5rem';
    return '1.1rem';
  }

  // Buat DOM Element Card dengan struktur 3D Flip Card murni
  function createCardElement(item, idx) {
    const card = document.createElement('div');
    card.className = 'coverflow-card card-hidden';
    card.dataset.index = idx;

    const fontSize = charFontSize(item.char);

    card.innerHTML = `
      <div class="cf-card-inner">
        <!-- MUKA DEPAN KARTU -->
        <div class="cf-card-front">
          <span class="font-heading font-extrabold tracking-wide cf-char-text select-none" style="font-size:${fontSize};word-break:break-word;text-align:center;line-height:1.1;">
            ${item.char}
          </span>
          <span class="font-bold uppercase tracking-widest mt-2 select-none opacity-80" style="font-size:0.65rem;">
            ${item.type}
          </span>
          <span class="text-[9px] text-[#2B124C]/60 mt-3 font-semibold select-none flex items-center gap-1">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m15 18-6-6 6-6"/></svg>
            Klik untuk balik
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="m9 18 6-6-6-6"/></svg>
          </span>
        </div>

        <!-- MUKA BELAKANG KARTU (3D FLIP) -->
        <div class="cf-card-back">
          <img class="cf-card-photo" alt="Isyarat ${item.char}" draggable="false">
          <div class="cf-card-label">${item.char}</div>
          <span class="cf-card-badge">${item.char.length > 2 ? item.char[0] : item.char}</span>
          <div class="w-20 h-20 pointer-events-none mt-1">
            ${generateHandIllustrationSVG(item)}
          </div>
          <span class="font-heading font-extrabold text-sm text-[#F9C74F] mt-1 text-center select-none">
            ${item.char}
          </span>
          <p class="text-[10px] font-semibold text-white/90 line-clamp-3 mt-1 text-center leading-tight select-none">
            ${item.desc}
          </p>
        </div>
      </div>
    `;

    // Foto dimuat malas (lazy): baru diminta saat kartu mendekat ke tengah
    card._loadPhoto = () => {
      if (card._photoRequested) return;
      card._photoRequested = true;
      attachHandPhoto(card.querySelector('.cf-card-back'), item.char);
    };

    card.addEventListener('click', () => {
      const isCenter = card.classList.contains('card-center');
      if (isCenter) {
        // Balik kartu 3D
        card.classList.toggle('is-flipped');
      } else {
        // Geser kartu ini ke tengah secara smooth
        goToIndex(idx);
      }
    });

    return card;
  }

  function initCards() {
    if (activePool.length === 0) {
      stage.innerHTML = `
        <div class="py-12 text-center text-[#2B124C]/70 font-semibold font-heading text-sm">
          Tidak ditemukan isyarat untuk pencarian tersebut.
        </div>
      `;
      cardElements = [];
      cardElementsInitialized = false;
      return;
    }

    stage.innerHTML = '';
    cardElements = [];

    activePool.forEach((item, idx) => {
      const card = createCardElement(item, idx);
      stage.appendChild(card);
      cardElements.push(card);
    });

    cardElementsInitialized = true;
  }

  function renderStage() {
    if (!cardElementsInitialized || cardElements.length !== activePool.length) {
      initCards();
      if (activePool.length === 0) return;
    }

    const total = activePool.length;

    // Kartu tengah dimuat paling dulu
    const centerCard = cardElements[currentIndex];
    if (centerCard && centerCard._loadPhoto) centerCard._loadPhoto();

    cardElements.forEach((card, idx) => {
      const diff = idx - currentIndex;
      let wrappedDiff = diff;
      while (wrappedDiff > total / 2)  wrappedDiff -= total;
      while (wrappedDiff < -total / 2) wrappedDiff += total;

      card.classList.remove(
        'card-center', 'card-prev-1', 'card-next-1',
        'card-prev-2', 'card-next-2', 'card-hidden'
      );

      // Kartu yang bergeser dari tengah otomatis kembali ke muka depan
      if (wrappedDiff !== 0) {
        card.classList.remove('is-flipped');
      }

      if (wrappedDiff === 0) {
        card.classList.add('card-center');
      } else if (wrappedDiff === -1 || wrappedDiff === total - 1) {
        card.classList.add('card-prev-1');
      } else if (wrappedDiff === 1 || wrappedDiff === -(total - 1)) {
        card.classList.add('card-next-1');
      } else if (wrappedDiff === -2 || wrappedDiff === total - 2) {
        card.classList.add('card-prev-2');
      } else if (wrappedDiff === 2 || wrappedDiff === -(total - 2)) {
        card.classList.add('card-next-2');
      } else {
        card.classList.add('card-hidden');
      }

      // Muat foto hanya untuk kartu yang terlihat (hemat bandwidth)
      if (!card.classList.contains('card-hidden') && card._loadPhoto) card._loadPhoto();
    });
  }

  function goToIndex(index) {
    const total = activePool.length;
    if (total === 0) return;
    currentIndex = (index + total) % total;
    renderStage();
  }

  function nextSlide() {
    goToIndex(currentIndex + 1);
  }

  function prevSlide() {
    goToIndex(currentIndex - 1);
  }

  function startAutoSlide() {
    stopAutoSlide();
    autoSlideTimer = setInterval(() => {
      if (!isHovered && activePool.length > 1) {
        nextSlide();
      }
    }, 3200);
  }

  function stopAutoSlide() {
    if (autoSlideTimer) {
      clearInterval(autoSlideTimer);
      autoSlideTimer = null;
    }
  }

  stage.addEventListener('mouseenter', () => { isHovered = true; });
  stage.addEventListener('mouseleave', () => { isHovered = false; });

  // Geser jari (HP/tablet): geser kiri = berikutnya, geser kanan = sebelumnya
  let touchStartX = null;
  let touchStartY = null;
  stage.addEventListener('touchstart', (e) => {
    const t = e.touches[0];
    touchStartX = t.clientX;
    touchStartY = t.clientY;
    isHovered = true; // jeda putar otomatis saat disentuh
  }, { passive: true });
  stage.addEventListener('touchend', (e) => {
    isHovered = false;
    if (touchStartX === null) return;
    const t = e.changedTouches[0];
    const dx = t.clientX - touchStartX;
    const dy = t.clientY - touchStartY;
    touchStartX = null;
    if (Math.abs(dx) > 45 && Math.abs(dx) > Math.abs(dy) * 1.3) {
      if (dx < 0) nextSlide(); else prevSlide();
    }
  }, { passive: true });

  if (prevBtn) prevBtn.addEventListener('click', prevSlide);
  if (nextBtn) nextBtn.addEventListener('click', nextSlide);

  // Pencarian Kamus
  if (searchInput) {
    searchInput.addEventListener('input', (e) => {
      const q = e.target.value.trim().toLowerCase();
      if (!q) {
        activePool = [...KAMUS_DATA];
        currentIndex = 0;
        cardElementsInitialized = false;
        renderStage();
        startAutoSlide();
        return;
      }

      stopAutoSlide();

      const exactMatches = KAMUS_DATA.filter(item => item.char.toLowerCase() === q);
      const startMatches = KAMUS_DATA.filter(item => item.char.toLowerCase().startsWith(q) && item.char.toLowerCase() !== q);
      const otherMatches = KAMUS_DATA.filter(item => !item.char.toLowerCase().startsWith(q) && (item.char.toLowerCase().includes(q) || item.desc.toLowerCase().includes(q) || item.type.toLowerCase().includes(q)));

      const combined = [...exactMatches, ...startMatches, ...otherMatches];

      activePool = combined;
      currentIndex = 0;
      cardElementsInitialized = false;
      renderStage();
    });

    searchInput.addEventListener('focus', () => stopAutoSlide());
    searchInput.addEventListener('blur', () => {
      if (!searchInput.value.trim()) startAutoSlide();
    });
  }

  renderStage();
  startAutoSlide();
}

// =============================================================
// 7. CELEBRATION CONFETTI & RATING UTILITIES
// =============================================================
function launchCelebrationConfetti() {
  const canvas = document.createElement('canvas');
  canvas.className = 'confetti-canvas';
  document.body.appendChild(canvas);
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;

  const pieces = [];
  const colors = ['#F9C74F', '#2B124C', '#DFB6B2', '#EADBFC', '#22C55E', '#FF007F'];

  for (let i = 0; i < 90; i++) {
    pieces.push({
      x: canvas.width * 0.5 + (Math.random() - 0.5) * 350,
      y: canvas.height * 0.35 + (Math.random() - 0.5) * 150,
      vx: (Math.random() - 0.5) * 15,
      vy: (Math.random() - 0.7) * 18,
      size: Math.random() * 9 + 6,
      color: colors[Math.floor(Math.random() * colors.length)],
      rotation: Math.random() * 360,
      vr: (Math.random() - 0.5) * 14,
      opacity: 1
    });
  }

  let frame = 0;
  function animate() {
    frame++;
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    pieces.forEach(p => {
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.45;
      p.rotation += p.vr;
      p.opacity -= 0.012;

      ctx.save();
      ctx.translate(p.x, p.y);
      ctx.rotate((p.rotation * Math.PI) / 180);
      ctx.fillStyle = p.color;
      ctx.globalAlpha = Math.max(0, p.opacity);
      ctx.fillRect(-p.size / 2, -p.size / 2, p.size, p.size * 0.6);
      ctx.restore();
    });

    if (frame < 110) {
      requestAnimationFrame(animate);
    } else {
      canvas.remove();
    }
  }
  requestAnimationFrame(animate);
}

function renderStarsHTML(activeCount) {
  let html = '';
  for (let i = 1; i <= 5; i++) {
    if (i <= activeCount) {
      html += `<i data-lucide="star" class="w-8 h-8 fill-current text-[#F9C74F] star-pop-${i}"></i>`;
    } else {
      html += `<i data-lucide="star" class="w-8 h-8 text-[#2B124C]/20 star-pop-${i}"></i>`;
    }
  }
  return html;
}
