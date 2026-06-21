console.log("[SyncShopper] content script loaded");

const DEFAULT_TOAST_DURATION_MS = 3000;

let currentVideo = null;
let captureButton = null;
let observer = null;
let captureOverlay = null;
let selectionBox = null;
let captureGuide = null;
let toastTimer = null;

function createCaptureButton() {
  const existingButton = document.getElementById("syncshopper-capture-button");

  if (existingButton) {
    captureButton = existingButton;
    return captureButton;
  }

  const button = document.createElement("button");
  button.id = "syncshopper-capture-button";
  button.type = "button";
  button.textContent = "\uC0C1\uD488 \uCEA1\uCCD0";
  button.style.display = "none";

  button.addEventListener("click", () => {
    console.log("[SyncShopper] capture button clicked");
    startAreaSelection();
  });

  document.body.appendChild(button);
  captureButton = button;

  return captureButton;
}

function showCaptureButton() {
  const button = createCaptureButton();
  button.style.display = "block";
}

function hideCaptureButton() {
  const button = document.getElementById("syncshopper-capture-button");

  if (button) {
    button.style.display = "none";
  }
}

function bindVideoEvents(video) {
  if (!video) {
    return;
  }

  if (video.dataset.syncShopperBound === "true") {
    return;
  }

  currentVideo = video;
  video.dataset.syncShopperBound = "true";

  console.log("[SyncShopper] video element found", video);

  video.addEventListener("pause", () => {
    console.log("[SyncShopper] video paused");
    showCaptureButton();
  });

  video.addEventListener("play", () => {
    console.log("[SyncShopper] video played");
    hideCaptureButton();
    removeAreaSelectionOverlay();
  });
}

function findAndBindVideo() {
  const video = document.querySelector("video");

  if (!video) {
    return false;
  }

  if (currentVideo !== video) {
    bindVideoEvents(video);
  }

  return true;
}

function startVideoObserver() {
  if (observer) {
    return;
  }

  observer = new MutationObserver(() => {
    findAndBindVideo();
  });

  observer.observe(document.body, {
    childList: true,
    subtree: true
  });
}

function startAreaSelection() {
  removeAreaSelectionOverlay();
  hideCaptureButton();

  let isDragging = false;
  let startX = 0;
  let startY = 0;

  captureOverlay = document.createElement("div");
  captureOverlay.id = "syncshopper-capture-overlay";

  selectionBox = document.createElement("div");
  selectionBox.id = "syncshopper-selection-box";
  selectionBox.style.display = "none";

  captureGuide = document.createElement("div");
  captureGuide.id = "syncshopper-capture-guide";
  captureGuide.textContent = "\uCEA1\uCCD0\uD560 \uC0C1\uD488 \uC601\uC5ED\uC744 \uB4DC\uB798\uADF8\uD558\uC138\uC694";

  captureOverlay.addEventListener("mousedown", (event) => {
    isDragging = true;
    startX = event.clientX;
    startY = event.clientY;

    selectionBox.style.display = "block";
    updateSelectionBox(startX, startY, startX, startY);
  });

  captureOverlay.addEventListener("mousemove", (event) => {
    if (!isDragging) {
      return;
    }

    updateSelectionBox(startX, startY, event.clientX, event.clientY);
  });

  captureOverlay.addEventListener("mouseup", async (event) => {
    if (!isDragging) {
      return;
    }

    isDragging = false;

    const rect = calculateSelectionRect(startX, startY, event.clientX, event.clientY);

    console.log("[SyncShopper] selected rect", rect);

    removeAreaSelectionOverlay();

    if (rect.width < 30 || rect.height < 30) {
      console.warn("[SyncShopper] selected area is too small");
      showToast("\uC120\uD0DD \uC601\uC5ED\uC774 \uB108\uBB34 \uC791\uC2B5\uB2C8\uB2E4.", "warning");
      return;
    }

    try {
      const fullPageDataUrl = await requestVisibleTabCapture();

      console.log("[SyncShopper] captured full tab dataUrl", fullPageDataUrl.slice(0, 100));

      const croppedDataUrl = await cropCapturedImage(fullPageDataUrl, rect);

      console.log("[SyncShopper] cropped dataUrl", croppedDataUrl.slice(0, 100));

      previewCroppedImage(croppedDataUrl);

      showToast("\uCEA1\uCCD0 \uC601\uC5ED \uC120\uD0DD \uC644\uB8CC", "success");
      showToast("AI \uBD84\uC11D \uC694\uCCAD \uC911...", "info");

      const analysisResult = await sendDetectionAnalyzeRequest(croppedDataUrl);
      updateCapturePanelResult(analysisResult);
    } catch (error) {
      console.error("[SyncShopper] capture process failed", error);
      updateCapturePanelResult({
        error: error.message || "\uBD84\uC11D \uC2E4\uD328"
      });

      if (!document.getElementById("syncshopper-toast")) {
        showToast("\uBD84\uC11D \uC2E4\uD328. \uB2E4\uC2DC \uC2DC\uB3C4\uD574\uC8FC\uC138\uC694.", "error");
      }
    }
  });

  document.body.appendChild(captureOverlay);
  document.body.appendChild(selectionBox);
  document.body.appendChild(captureGuide);
}

function removeAreaSelectionOverlay() {
  const overlay = document.getElementById("syncshopper-capture-overlay");
  const box = document.getElementById("syncshopper-selection-box");
  const guide = document.getElementById("syncshopper-capture-guide");

  if (overlay) {
    overlay.remove();
  }

  if (box) {
    box.remove();
  }

  if (guide) {
    guide.remove();
  }

  captureOverlay = null;
  selectionBox = null;
  captureGuide = null;
}

function updateSelectionBox(startX, startY, currentX, currentY) {
  if (!selectionBox) {
    return;
  }

  const x = Math.min(startX, currentX);
  const y = Math.min(startY, currentY);
  const width = Math.abs(currentX - startX);
  const height = Math.abs(currentY - startY);

  selectionBox.style.left = `${x}px`;
  selectionBox.style.top = `${y}px`;
  selectionBox.style.width = `${width}px`;
  selectionBox.style.height = `${height}px`;
}

function calculateSelectionRect(startX, startY, endX, endY) {
  return {
    x: Math.min(startX, endX),
    y: Math.min(startY, endY),
    width: Math.abs(endX - startX),
    height: Math.abs(endY - startY),
    devicePixelRatio: window.devicePixelRatio || 1
  };
}

function requestVisibleTabCapture() {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      { type: "SYNC_SHOPPER_CAPTURE_VISIBLE_TAB" },
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }

        if (!response || !response.success) {
          reject(new Error(response?.errorMessage || "Failed to capture visible tab"));
          return;
        }

        resolve(response.dataUrl);
      }
    );
  });
}

function cropCapturedImage(dataUrl, rect) {
  return new Promise((resolve, reject) => {
    const image = new Image();

    image.onload = () => {
      const ratio = rect.devicePixelRatio || 1;

      const sourceX = rect.x * ratio;
      const sourceY = rect.y * ratio;
      const sourceWidth = rect.width * ratio;
      const sourceHeight = rect.height * ratio;

      const maxOutputSide = 1024;
      const scale = Math.min(1, maxOutputSide / Math.max(sourceWidth, sourceHeight));
      const outputWidth = Math.max(1, Math.round(sourceWidth * scale));
      const outputHeight = Math.max(1, Math.round(sourceHeight * scale));

      const canvas = document.createElement("canvas");
      canvas.width = outputWidth;
      canvas.height = outputHeight;

      const context = canvas.getContext("2d");

      if (!context) {
        reject(new Error("Canvas context is not available"));
        return;
      }

      context.drawImage(
        image,
        sourceX,
        sourceY,
        sourceWidth,
        sourceHeight,
        0,
        0,
        outputWidth,
        outputHeight
      );

      resolve(canvas.toDataURL("image/jpeg", 0.86));
    };

    image.onerror = () => {
      reject(new Error("Failed to load captured image"));
    };

    image.src = dataUrl;
  });
}

function previewCroppedImage(croppedDataUrl) {
  const panel = createCaptureResultPanel();
  const previewImage = panel.querySelector("#syncshopper-result-preview");
  const resultContent = panel.querySelector("#syncshopper-result-content");

  if (!previewImage || !resultContent) {
    return;
  }

  previewImage.src = croppedDataUrl;
  resultContent.textContent = "AI \uBD84\uC11D \uC694\uCCAD \uC911...";
}

function createCaptureResultPanel() {
  const existingPanel = document.getElementById("syncshopper-result-panel");

  if (existingPanel) {
    return existingPanel;
  }

  const panel = document.createElement("aside");
  panel.id = "syncshopper-result-panel";

  const title = document.createElement("h2");
  title.textContent = "SyncShopper";

  const closeButton = document.createElement("button");
  closeButton.id = "syncshopper-result-close-button";
  closeButton.type = "button";
  closeButton.textContent = "\u00D7";
  closeButton.setAttribute("aria-label", "Close SyncShopper result panel");
  closeButton.addEventListener("click", () => {
    panel.remove();
  });

  const previewTitle = document.createElement("h3");
  previewTitle.textContent = "\uCEA1\uCCD0 \uBBF8\uB9AC\uBCF4\uAE30";

  const previewImage = document.createElement("img");
  previewImage.id = "syncshopper-result-preview";
  previewImage.alt = "\uCEA1\uCCD0 \uACB0\uACFC";

  const resultTitle = document.createElement("h3");
  resultTitle.textContent = "\uBD84\uC11D \uACB0\uACFC";

  const resultContent = document.createElement("pre");
  resultContent.id = "syncshopper-result-content";
  resultContent.textContent = "\uACB0\uACFC\uB97C \uAE30\uB2E4\uB9AC\uB294 \uC911...";

  panel.appendChild(closeButton);
  panel.appendChild(title);
  panel.appendChild(previewTitle);
  panel.appendChild(previewImage);
  panel.appendChild(resultTitle);
  panel.appendChild(resultContent);
  document.body.appendChild(panel);

  return panel;
}

function updateCapturePanelResult(result) {
  const panel = createCaptureResultPanel();
  const resultContent = panel.querySelector("#syncshopper-result-content");

  if (!resultContent) {
    return;
  }

  resultContent.textContent = formatResultForPanel(result);
}

function formatResultForPanel(result) {
  if (typeof result === "string") {
    return result;
  }

  if (result === null || result === undefined) {
    return "\uBD84\uC11D \uACB0\uACFC\uAC00 \uBE44\uC5B4 \uC788\uC2B5\uB2C8\uB2E4.";
  }

  return JSON.stringify(result, null, 2);
}

function getYouTubeVideoId() {
  const url = new URL(window.location.href);
  const watchVideoId = url.searchParams.get("v");

  if (watchVideoId) {
    return watchVideoId;
  }

  const shortsMatch = url.pathname.match(/^\/shorts\/([^/?#]+)/);

  if (shortsMatch) {
    return shortsMatch[1];
  }

  return null;
}

function getCurrentTimestampSec() {
  const video = currentVideo || document.querySelector("video");

  if (!video) {
    return null;
  }

  return Math.floor(video.currentTime);
}

function getExtensionSettings() {
  return new Promise((resolve) => {
    chrome.storage.local.get(["backendBaseUrl", "accessToken"], (result) => {
      resolve({
        backendBaseUrl: result.backendBaseUrl,
        accessToken: result.accessToken
      });
    });
  });
}

function showToast(message, type = "info") {
  const existingToast = document.getElementById("syncshopper-toast");

  if (toastTimer) {
    clearTimeout(toastTimer);
    toastTimer = null;
  }

  if (existingToast) {
    existingToast.remove();
  }

  const toast = document.createElement("div");
  toast.id = "syncshopper-toast";
  toast.className = type;
  toast.textContent = message;

  document.body.appendChild(toast);

  toastTimer = setTimeout(() => {
    toast.remove();
    toastTimer = null;
  }, DEFAULT_TOAST_DURATION_MS);
}

async function sendDetectionAnalyzeRequest(croppedDataUrl) {
  const videoId = getYouTubeVideoId();

  if (!videoId) {
    showToast("\uC601\uC0C1 ID\uB97C \uCC3E\uC744 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.", "error");
    throw new Error("YouTube videoId not found");
  }

  const timestampSec = getCurrentTimestampSec();

  if (timestampSec === null || timestampSec === undefined) {
    showToast("\uC601\uC0C1 \uC815\uBCF4\uB97C \uCC3E\uC744 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.", "error");
    throw new Error("Video timestamp not found");
  }

  const { backendBaseUrl, accessToken } = await getExtensionSettings();

  if (!backendBaseUrl) {
    showToast("\uBC31\uC5D4\uB4DC \uC8FC\uC18C\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4. \uC775\uC2A4\uD150\uC158 \uC124\uC815\uC5D0\uC11C \uBC31\uC5D4\uB4DC \uC8FC\uC18C\uB97C \uC785\uB825\uD574\uC8FC\uC138\uC694.", "warning");
    throw new Error("backendBaseUrl is missing");
  }

  if (!accessToken) {
    showToast("\uD1A0\uD070\uC774 \uC5C6\uC2B5\uB2C8\uB2E4. \uC775\uC2A4\uD150\uC158 \uC124\uC815\uC5D0\uC11C \uD1A0\uD070\uC744 \uC785\uB825\uD574\uC8FC\uC138\uC694.", "warning");
    throw new Error("accessToken is missing");
  }

  const requestBody = {
    videoId,
    timestampSec,
    imageBase64: croppedDataUrl,
    subtitleText: null
  };
  const requestUrl = `${backendBaseUrl.replace(/\/$/, "")}/api/detections/analyze`;

  console.log("[SyncShopper] sending detection request", {
    requestUrl,
    videoId,
    timestampSec,
    imageSize: croppedDataUrl.length
  });

  const response = await requestDetectionAnalyze({
    requestUrl,
    accessToken,
    requestBody
  });

  if (!response.success && response.errorCode === "NETWORK_ERROR") {
    showToast("\uBC31\uC5D4\uB4DC \uC11C\uBC84\uC5D0 \uC5F0\uACB0\uD560 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.", "error");
    throw new Error(response.errorMessage || "Network error");
  }

  if (response.status === 401) {
    showToast("\uB85C\uADF8\uC778\uC774 \uB9CC\uB8CC\uB418\uC5C8\uC2B5\uB2C8\uB2E4. accessToken\uC744 \uB2E4\uC2DC \uC785\uB825\uD574\uC8FC\uC138\uC694.", "error");
    throw new Error("Unauthorized");
  }

  if (response.status >= 500) {
    showToast("\uC11C\uBC84 \uC624\uB958\uAC00 \uBC1C\uC0DD\uD588\uC2B5\uB2C8\uB2E4. \uC7A0\uC2DC \uD6C4 \uB2E4\uC2DC \uC2DC\uB3C4\uD574\uC8FC\uC138\uC694.", "error");
    throw new Error(`Server error: ${response.status}`);
  }

  if (!response.success) {
    showToast("\uBD84\uC11D \uC2E4\uD328. \uB2E4\uC2DC \uC2DC\uB3C4\uD574\uC8FC\uC138\uC694.", "error");
    throw new Error(response.errorMessage || `Request failed: ${response.status}`);
  }

  const result = response.result;

  console.log("[SyncShopper] detection analyze response", result);
  showToast("\uC0C1\uD488 \uBD84\uC11D \uC644\uB8CC", "success");

  return result;
}

function requestDetectionAnalyze({ requestUrl, accessToken, requestBody }) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      {
        type: "SYNC_SHOPPER_ANALYZE_DETECTION",
        requestUrl,
        accessToken,
        requestBody
      },
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }

        resolve(response || {
          success: false,
          errorMessage: "No response from background service worker"
        });
      }
    );
  });
}

function initSyncShopperExtension() {
  createCaptureButton();

  const found = findAndBindVideo();

  if (!found) {
    console.log("[SyncShopper] video element not found yet. Waiting...");
  }

  startVideoObserver();
}

window.addEventListener("yt-navigate-finish", () => {
  console.log("[SyncShopper] YouTube navigation finished");
  currentVideo = null;
  hideCaptureButton();
  removeAreaSelectionOverlay();

  setTimeout(() => {
    findAndBindVideo();
  }, 500);
});

initSyncShopperExtension();
