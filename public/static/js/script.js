const video = document.getElementById("video");
const canvas = document.getElementById("canvas");

const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");

const cameraPlaceholder = document.getElementById("cameraPlaceholder");
const cameraStatus = document.getElementById("cameraStatus");

const predictionElement = document.getElementById("prediction");
const resultMessage = document.getElementById("resultMessage");
const confidenceElement = document.getElementById("confidence");
const confidenceBar = document.getElementById("confidenceBar");

const speakButton = document.getElementById("speakButton");
const speechToggle = document.getElementById("speechToggle");

// ---------------------------------------------------------------
// PENGATURAN (boleh diubah untuk menyetel kestabilan)
// ---------------------------------------------------------------
// Frame berikutnya dikirim begitu jawaban sebelumnya datang, dengan jeda
// minimal ini (membatasi beban server, ~12 frame/detik).
const MIN_FRAME_GAP_MS = 80;

// Label baru dianggap "stabil" jika muncul berturut-turut minimal
// CONFIRM_FRAMES kali DAN bertahan minimal CONFIRM_MS.
// Lebih kecil = lebih cepat bereaksi, tetapi lebih mudah salah sesaat.
const CONFIRM_FRAMES = 2;
const CONFIRM_MS = 250;

// Frame dengan confidence di bawah ini dianggap "tangan sedang berpindah"
// dan diabaikan (tidak memutus atau membentuk label baru).
const MIN_FRAME_CONFIDENCE = 35;

// Saat tangan bergerak cepat, MediaPipe kadang gagal 1-2 frame (blur).
// Hasil baru direset jika tangan hilang lebih lama dari ini.
const LOST_HAND_RESET_MS = 500;

// Suara: lebih cepat & lebih pendek = lebih sinkron dengan tangan.
const SPEECH_RATE = 1.25;
const SAY_LETTER_PREFIX = false; // true -> "Huruf B", false -> "B"

let cameraStream = null;
let isPredicting = false;
let loopId = 0; // naik setiap start/stop agar hanya ada 1 loop aktif
let lastSpokenText = "";

// Status penstabil
let stableLabel = null; // label yang sedang ditampilkan
let candidate = null; // { label, since, frames, totalConfidence }
let lastHandSeenAt = 0;

// 1. MENGAKTIFKAN KAMERA
async function startCamera() {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 640 },
        height: { ideal: 480 },
        facingMode: "user",
      },
      audio: false,
    });

    video.srcObject = cameraStream;
    await video.play();

    // Manipulasi kelas Tailwind agar video tampil sempurna
    video.classList.remove("hidden");
    cameraPlaceholder.classList.add("hidden");

    startButton.disabled = true;
    startButton.classList.add("opacity-50", "cursor-not-allowed");
    stopButton.disabled = false;
    stopButton.classList.remove(
      "opacity-50",
      "cursor-not-allowed",
      "bg-gray-100",
      "text-gray-400",
    );
    stopButton.classList.add("bg-red-500", "text-white", "hover:bg-red-600");

    resetStabilizer();

    // Mulai loop pengiriman frame
    runPredictionLoop(++loopId);

    console.log("Kamera berhasil diaktifkan!");
  } catch (error) {
    console.error("Kesalahan kamera:", error);
    alert(
      "Kamera tidak dapat diakses. Pastikan izin kamera telah diberikan dan tidak digunakan oleh aplikasi lain.",
    );
  }
}

// 2. LOOP PREDIKSI: kirim frame -> tunggu jawaban -> langsung kirim lagi.
//    (setInterval lama melewatkan tick saat server masih memproses,
//    sehingga frame rate jatuh ke ~4 fps.)
async function runPredictionLoop(id) {
  while (id === loopId && cameraStream) {
    const startedAt = performance.now();
    await sendFrame();
    const elapsed = performance.now() - startedAt;
    const wait = Math.max(0, MIN_FRAME_GAP_MS - elapsed);
    await new Promise((resolve) => setTimeout(resolve, wait || 0));
  }
}

// MENGIRIM GAMBAR KE FLASK API
async function sendFrame() {
  if (!cameraStream || isPredicting || video.readyState < 2) {
    return;
  }

  isPredicting = true;

  try {
    const context = canvas.getContext("2d");

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    const blob = await new Promise((resolve) => {
      canvas.toBlob(resolve, "image/jpeg", 0.8);
    });

    if (!blob) {
      throw new Error("Gagal mengambil gambar dari kamera.");
    }

    const formData = new FormData();
    formData.append("frame", blob, "frame.jpg");

    const response = await fetch("/api/predict", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok || !data.success) {
      throw new Error(data.message || "Prediksi gagal.");
    }

    displayPrediction(data);
  } catch (error) {
    console.error("Kesalahan prediksi:", error);
    resultMessage.textContent = "Gagal melakukan prediksi.";
  } finally {
    isPredicting = false;
  }
}

// 3. PENSTABIL HASIL: label harus muncul BERTURUT-TURUT sebentar.
//    Versi lama memakai voting 4 dari 7 frame terakhir: label baru harus
//    "mengalahkan" sisa suara label lama dulu, sehingga tertinggal ~1 detik.
function resetStabilizer() {
  stableLabel = null;
  candidate = null;
  lastHandSeenAt = 0;
}

// Mengembalikan { label, confidence } jika label baru terkonfirmasi.
function updateStabilizer(label, confidence, now) {
  if (confidence < MIN_FRAME_CONFIDENCE) {
    return null; // frame transisi: abaikan
  }

  if (candidate && candidate.label === label) {
    candidate.frames += 1;
    candidate.totalConfidence += confidence;
  } else {
    candidate = { label, since: now, frames: 1, totalConfidence: confidence };
  }

  const confirmed =
    candidate.frames >= CONFIRM_FRAMES && now - candidate.since >= CONFIRM_MS;

  if (!confirmed) {
    return null;
  }

  const average = candidate.totalConfidence / candidate.frames;
  return {
    label: candidate.label,
    confidence: Math.round(average * 10) / 10,
  };
}

function clearDisplay(message) {
  predictionElement.textContent = "-";
  resultMessage.textContent = message;
  confidenceElement.textContent = "0%";
  confidenceBar.style.width = "0%";
  speakButton.disabled = true;
}

// 4. MENAMPILKAN HASIL PREDIKSI & FITUR SUARA
function displayPrediction(data) {
  const now = performance.now();

  if (!data.detected) {
    // Hilang sesaat (blur gerakan cepat): pertahankan hasil terakhir.
    if (now - lastHandSeenAt < LOST_HAND_RESET_MS) {
      return;
    }
    resetStabilizer();
    lastSpokenText = "";
    clearDisplay("Tangan tidak terdeteksi.");
    return;
  }

  lastHandSeenAt = now;

  const stable = updateStabilizer(
    String(data.prediction),
    Number(data.confidence) || 0,
    now,
  );

  if (!stable) {
    if (stableLabel === null) {
      clearDisplay(`${data.detected_hands} tangan terdeteksi, isyarat belum jelas`);
    }
    return; // tetap tampilkan label stabil sebelumnya
  }

  stableLabel = stable.label;
  predictionElement.textContent = stable.label;
  resultMessage.textContent = `${data.detected_hands} tangan terdeteksi`;

  confidenceElement.textContent = `${stable.confidence}%`;
  confidenceBar.style.width = `${stable.confidence}%`;

  speakButton.disabled = false;

  // Baca hasil secara otomatis jika toggle suara aktif dan hasil stabil berubah
  if (speechToggle && speechToggle.checked && stable.label !== lastSpokenText) {
    lastSpokenText = stable.label;
    speakText(stable.label);
  }
}

// 5. MENGHENTIKAN KAMERA
function stopCamera() {
  loopId += 1; // menghentikan loop prediksi yang sedang berjalan

  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => {
      track.stop();
    });
    cameraStream = null;
  }

  video.srcObject = null;
  video.classList.add("hidden");
  cameraPlaceholder.classList.remove("hidden");

  if (cameraStatus) {
    cameraStatus.className =
      "inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 text-xs font-bold text-gray-600 border border-gray-200 transition-all";
  }

  predictionElement.textContent = "-";
  resultMessage.textContent = "Belum ada isyarat yang dikenali";
  confidenceElement.textContent = "0%";
  confidenceBar.style.width = "0%";

  speakButton.disabled = true;
  startButton.disabled = false;
  startButton.classList.remove("opacity-50", "cursor-not-allowed");

  stopButton.disabled = true;
  stopButton.className =
    "flex-1 bg-gray-100 text-gray-400 py-3.5 px-6 rounded-full font-bold text-sm border border-gray-200 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed";

  resetStabilizer();
  lastSpokenText = "";
  if ("speechSynthesis" in window) window.speechSynthesis.cancel();
  console.log("Kamera berhasil dihentikan!");
}

// 6. FITUR TEXT-TO-SPEECH (SUARA)
function speakText(text) {
  if (!("speechSynthesis" in window) || !text || text === "-") return;

  window.speechSynthesis.cancel(); // Hentikan suara sebelumnya jika ada

  const cleanText = text.trim();
  let textToSpeak = cleanText;

  // Huruf tunggal: opsional diberi awalan "Huruf" (lebih jelas, tapi lebih lama)
  if (SAY_LETTER_PREFIX && /^[a-zA-Z]$/.test(cleanText)) {
    textToSpeak = `Huruf ${cleanText}`;
  }
  // Untuk angka (1-10), kata, atau kalimat: langsung dibaca kodenya saja tanpa awalan

  const utterance = new SpeechSynthesisUtterance(textToSpeak);
  utterance.lang = "id-ID";
  utterance.rate = SPEECH_RATE;
  window.speechSynthesis.speak(utterance);
}

// 7. EVENT LISTENERS
startButton.addEventListener("click", startCamera);
stopButton.addEventListener("click", stopCamera);

speakButton.addEventListener("click", () => {
  const currentPrediction = predictionElement.textContent;
  if (currentPrediction && currentPrediction !== "-") {
    speakText(currentPrediction);
  }
});
