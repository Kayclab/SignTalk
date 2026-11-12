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
const SEND_INTERVAL_MS = 200; // jeda antar pengiriman frame
const HISTORY_SIZE = 7; // jumlah hasil terakhir yang dipertimbangkan
const MIN_VOTES = 4; // minimal berapa kali label yang sama muncul
const CONFIDENCE_THRESHOLD = 40; // rata-rata confidence minimal (%) agar ditampilkan

let cameraStream = null;
let predictionInterval = null;
let isPredicting = false;
let lastSpokenText = "";
let predictionHistory = [];

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

    predictionHistory = [];

    // Mulai kirim frame secara berkala
    predictionInterval = setInterval(sendFrame, SEND_INTERVAL_MS);

    console.log("Kamera berhasil diaktifkan!");
  } catch (error) {
    console.error("Kesalahan kamera:", error);
    alert(
      "Kamera tidak dapat diakses. Pastikan izin kamera telah diberikan dan tidak digunakan oleh aplikasi lain.",
    );
  }
}

// 2. MENGIRIM GAMBAR KE FLASK API
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

// 3. PENSTABIL HASIL: pemungutan suara dari beberapa hasil terakhir
function getStablePrediction() {
  if (predictionHistory.length < MIN_VOTES) {
    return null;
  }

  const votes = new Map();

  predictionHistory.forEach((item) => {
    if (!votes.has(item.label)) {
      votes.set(item.label, { count: 0, total: 0 });
    }
    const entry = votes.get(item.label);
    entry.count += 1;
    entry.total += item.confidence;
  });

  let bestLabel = null;
  let bestEntry = null;

  votes.forEach((entry, label) => {
    if (bestEntry === null || entry.count > bestEntry.count) {
      bestLabel = label;
      bestEntry = entry;
    }
  });

  if (bestEntry.count < MIN_VOTES) {
    return null;
  }

  const averageConfidence = bestEntry.total / bestEntry.count;

  if (averageConfidence < CONFIDENCE_THRESHOLD) {
    return null;
  }

  return {
    label: bestLabel,
    confidence: Math.round(averageConfidence * 10) / 10,
  };
}

// 4. MENAMPILKAN HASIL PREDIKSI & FITUR SUARA
function displayPrediction(data) {
  if (!data.detected) {
    predictionHistory = [];
    predictionElement.textContent = "-";
    resultMessage.textContent = "Tangan tidak terdeteksi.";
    confidenceElement.textContent = "0%";
    confidenceBar.style.width = "0%";
    speakButton.disabled = true;
    lastSpokenText = "";
    return;
  }

  predictionHistory.push({
    label: String(data.prediction),
    confidence: Number(data.confidence) || 0,
  });

  if (predictionHistory.length > HISTORY_SIZE) {
    predictionHistory.shift();
  }

  const stable = getStablePrediction();

  if (!stable) {
    predictionElement.textContent = "-";
    resultMessage.textContent = `${data.detected_hands} tangan terdeteksi, isyarat belum jelas`;
    confidenceElement.textContent = "0%";
    confidenceBar.style.width = "0%";
    speakButton.disabled = true;
    return;
  }

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
  if (predictionInterval) {
    clearInterval(predictionInterval);
    predictionInterval = null;
  }

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

  predictionHistory = [];
  lastSpokenText = "";
  console.log("Kamera berhasil dihentikan!");
}

// 6. FITUR TEXT-TO-SPEECH (SUARA)
function speakText(text) {
  if (!("speechSynthesis" in window) || !text || text === "-") return;

  window.speechSynthesis.cancel(); // Hentikan suara sebelumnya jika ada

  const cleanText = text.trim();
  let textToSpeak = cleanText;

  // Jika hanya 1 karakter huruf (A-Z / a-z), beri awalan "Huruf"
  if (/^[a-zA-Z]$/.test(cleanText)) {
    textToSpeak = `Huruf ${cleanText}`;
  }
  // Untuk angka (1-10), kata, atau kalimat: langsung dibaca kodenya saja tanpa awalan

  const utterance = new SpeechSynthesisUtterance(textToSpeak);
  utterance.lang = "id-ID";
  utterance.rate = 1.0;
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
