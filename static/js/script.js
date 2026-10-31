const video = document.getElementById("video");
const canvas = document.getElementById("canvas");

const startButton = document.getElementById("startButton");
const stopButton = document.getElementById("stopButton");

const cameraStatus = document.getElementById("cameraStatus");
const cameraPlaceholder = document.getElementById("cameraPlaceholder");

const predictionElement = document.getElementById("prediction");
const resultMessage = document.getElementById("resultMessage");
const confidenceElement = document.getElementById("confidence");
const confidenceBar = document.getElementById("confidenceBar");
const speakButton = document.getElementById("speakButton");

let cameraStream = null;
let predictionInterval = null;
let isPredicting = false;

// 1. MENGAKTIFKAN KAMERA

async function startCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: {
                width: { ideal: 640 },
                height: { ideal: 480 },
                facingMode: "user"
            },
            audio: false
        });

        video.srcObject = cameraStream;
        await video.play();

        video.style.display = "block";
        cameraPlaceholder.style.display = "none";

        cameraStatus.innerHTML = `
            <span class="status-dot" style="background: #20B486;"></span>
            Kamera aktif
        `;

        startButton.disabled = true;
        stopButton.disabled = false;

        // Mulai mengirim gambar untuk prediksi
        predictionInterval = setInterval(sendFrame, 500);

        console.log("Kamera berhasil diaktifkan!");

    } catch (error) {
        console.error("Kesalahan kamera:", error);
        alert("Kamera tidak dapat diakses. Periksa izin kamera browser.");
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

        const blob = await new Promise(resolve => {
            canvas.toBlob(resolve, "image/jpeg", 0.8);
        });

        if (!blob) {
            throw new Error("Gagal mengambil gambar dari kamera.");
        }

        const formData = new FormData();
        formData.append("frame", blob, "frame.jpg");

        const response = await fetch("/api/predict", {
            method: "POST",
            body: formData
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

// 3. MENAMPILKAN HASIL PREDIKSI

function displayPrediction(data) {

    if (!data.detected) {
        predictionElement.textContent = "-";
        resultMessage.textContent = "Tangan tidak terdeteksi.";
        confidenceElement.textContent = "0%";
        confidenceBar.style.width = "0%";
        speakButton.disabled = true;
        return;
    }

    predictionElement.textContent = data.prediction;
    resultMessage.textContent =
        `${data.detected_hands} tangan terdeteksi`;

    confidenceElement.textContent = `${data.confidence}%`;
    confidenceBar.style.width = `${data.confidence}%`;

    speakButton.disabled = false;
}

// 4. MENGHENTIKAN KAMERA

function stopCamera() {

    if (predictionInterval) {
        clearInterval(predictionInterval);
        predictionInterval = null;
    }

    if (cameraStream) {
        cameraStream.getTracks().forEach(track => {
            track.stop();
        });

        cameraStream = null;
    }

    video.srcObject = null;
    video.style.display = "none";

    cameraPlaceholder.style.display = "flex";

    cameraStatus.innerHTML = `
        <span class="status-dot"></span>
        Kamera belum aktif
    `;

    predictionElement.textContent = "-";
    resultMessage.textContent = "Belum ada isyarat yang dikenali";
    confidenceElement.textContent = "0%";
    confidenceBar.style.width = "0%";

    speakButton.disabled = true;
    startButton.disabled = false;
    stopButton.disabled = true;

    console.log("Kamera berhasil dihentikan!");
}

// 5. EVENT TOMBOL

startButton.addEventListener("click", startCamera);
stopButton.addEventListener("click", stopCamera);
