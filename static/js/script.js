
/* =========================================
   Engineering Drawing Comparison System
   Vanilla JS Frontend Controller
========================================= */

/* -------------------------
   ELEMENT REFERENCES
-------------------------- */
const form = document.getElementById("uploadForm");
const file1 = document.getElementById("file1");
const file2 = document.getElementById("file2");

const compareBtn = document.getElementById("compareBtn");
const loading = document.getElementById("loading");
const loadingText = document.getElementById("loadingText");
const resultsSection = document.getElementById("resultsSection");

const alertBox = document.getElementById("alertBox");

/* -------------------------
   VALIDATION SETTINGS
-------------------------- */
const allowedExtensions = ["pdf", "png", "jpg", "jpeg"];

/* -------------------------
   ALERT SYSTEM
-------------------------- */
function showAlert(message, type = "info") {
    alertBox.innerHTML = `
        <div class="alert alert-${type} alert-dismissible fade show">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
}

/* -------------------------
   FILE VALIDATION
-------------------------- */
function validateFile(file) {
    if (!file) return false;

    const ext = file.name.split(".").pop().toLowerCase();
    return allowedExtensions.includes(ext);
}

/* -------------------------
   IMAGE PREVIEW (optional)
   Works only for images (not PDFs)
-------------------------- */
function previewImage(file, containerId) {
    const container = document.getElementById(containerId);

    if (!container) return;

    const ext = file.name.split(".").pop().toLowerCase();

    if (ext === "png" || ext === "jpg" || ext === "jpeg") {
        const reader = new FileReader();

        reader.onload = function (e) {
            container.innerHTML = `
                <img src="${e.target.result}" class="img-fluid rounded shadow-sm mt-2" />
            `;
        };

        reader.readAsDataURL(file);
    } else {
        container.innerHTML = `
            <div class="text-muted small mt-2">
                PDF selected (preview not available)
            </div>
        `;
    }
}

/* -------------------------
   LOADING PROGRESS SIMULATION
-------------------------- */
let progressInterval;

function startLoading() {
    let progress = 0;
    loading.classList.remove("d-none");

    loadingText.innerText = "Processing drawings... 0%";

    progressInterval = setInterval(() => {
        progress += Math.floor(Math.random() * 10) + 5;

        if (progress >= 95) progress = 95;

        loadingText.innerText = `Processing drawings... ${progress}%`;
    }, 400);
}

function stopLoading() {
    clearInterval(progressInterval);
    loadingText.innerText = "Processing completed...";
}

/* -------------------------
   RESET UI
-------------------------- */
function resetUI() {
    resultsSection.classList.add("d-none");
    alertBox.innerHTML = "";
}

/* -------------------------
   FORM SUBMISSION
-------------------------- */
form.addEventListener("submit", async function (e) {
    e.preventDefault();

    resetUI();

    /* -------- validation -------- */
    if (!file1.files[0] || !file2.files[0]) {
        showAlert("Please upload both drawings.", "danger");
        return;
    }

    if (!validateFile(file1.files[0]) || !validateFile(file2.files[0])) {
        showAlert("Only PDF, PNG, JPG, JPEG files are allowed.", "danger");
        return;
    }

    /* -------- UI state -------- */
    compareBtn.disabled = true;
    compareBtn.innerText = "Processing...";

    startLoading();

    /* -------- API call -------- */
    const formData = new FormData();
    formData.append("file1", file1.files[0]);
    formData.append("file2", file2.files[0]);

    try {
        const response = await fetch("/process", {
            method: "POST",
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.error || "Processing failed");
        }

        const data = await response.json();

        stopLoading();

        showAlert("Analysis completed successfully!", "success");

        resultsSection.classList.remove("d-none");

        console.log("Result:", data);

    } catch (error) {
        stopLoading();
        showAlert(error.message, "danger");
    } finally {
        compareBtn.disabled = false;
        compareBtn.innerText = "Compare Drawings";
    }
});

/* -------------------------
   LIVE FILE PREVIEW HOOKS
   (optional enhancement)
-------------------------- */
file1.addEventListener("change", () => {
    previewImage(file1.files[0], "preview1");
});

file2.addEventListener("change", () => {
    previewImage(file2.files[0], "preview2");
});