console.log("[SyncShopper] content script loaded");

const DEFAULT_BACKEND_BASE_URL = "http://localhost:8080";
const DEFAULT_FRONTEND_BASE_URL = "http://localhost:5173";
const DEFAULT_TOAST_DURATION_MS = 3000;

let currentVideo = null;
let captureButton = null;
let observer = null;
let captureOverlay = null;
let selectionBox = null;
let captureGuide = null;
let toastTimer = null;
let pendingLoginSuccessCallback = null;

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

  button.addEventListener("click", async () => {
    console.log("[SyncShopper] capture button clicked");

    if (await isLoggedIn()) {
      startAreaSelection();
      return;
    }

    showLoginPanel(() => {
      startAreaSelection();
    });
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

  const resultContent = document.createElement("div");
  resultContent.id = "syncshopper-result-content";
  resultContent.textContent = "\uACB0\uACFC\uB97C \uAE30\uB2E4\uB9AC\uB294 \uC911...";

  panel.appendChild(closeButton);
  panel.appendChild(title);
  panel.appendChild(previewTitle);
  panel.appendChild(previewImage);
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

  resultContent.replaceChildren(renderResultForPanel(result));
}

function renderResultForPanel(result) {
  const fragment = document.createDocumentFragment();

  if (typeof result === "string") {
    fragment.appendChild(createPanelMessage(result));
    return fragment;
  }

  if (result === null || result === undefined) {
    fragment.appendChild(createPanelMessage("\uBD84\uC11D \uACB0\uACFC\uAC00 \uBE44\uC5B4 \uC788\uC2B5\uB2C8\uB2E4."));
    return fragment;
  }

  const analysis = result && typeof result === "object" && result.data ? result.data : result;

  if (analysis.error) {
    fragment.appendChild(createPanelMessage(analysis.error));
    return fragment;
  }

  const targetName = analysis.detection?.targetName || analysis.targetName || "\uC54C \uC218 \uC5C6\uB294 \uC0C1\uD488";
  const products = Array.isArray(analysis.products) ? analysis.products : [];

  const detectionBlock = document.createElement("section");
  detectionBlock.className = "syncshopper-detection-summary";

  const detectionLabel = document.createElement("div");
  detectionLabel.className = "syncshopper-section-label";
  detectionLabel.textContent = "AI \uD0D0\uC9C0 \uACB0\uACFC:";

  const detectionValue = document.createElement("div");
  detectionValue.className = "syncshopper-detection-target";
  detectionValue.textContent = targetName;

  detectionBlock.appendChild(detectionLabel);
  detectionBlock.appendChild(detectionValue);
  fragment.appendChild(detectionBlock);
  fragment.appendChild(createRecaptureButton());
  fragment.appendChild(createNaverSearchQueryBlock(analysis));

  fragment.appendChild(createProductResultsBlock(products));
  return fragment;
}

function createPanelMessage(message) {
  const messageElement = document.createElement("p");
  messageElement.className = "syncshopper-panel-message";
  messageElement.textContent = message;
  return messageElement;
}

function createRecaptureButton() {
  const button = document.createElement("button");
  button.className = "syncshopper-recapture-button";
  button.type = "button";
  button.textContent = "\uB2E4\uC2DC \uCEA1\uCCD0\uD558\uAE30";
  button.addEventListener("click", () => {
    const panel = document.getElementById("syncshopper-result-panel");

    if (panel) {
      panel.remove();
    }

    startAreaSelection();
  });

  return button;
}

function createNaverSearchQueryBlock(analysis) {
  const query = analysis.commerceQuery?.primary_query || analysis.commerceQuery?.fallback_queries?.[0] || analysis.targetName || analysis.detection?.targetName || "";

  const block = document.createElement("section");
  block.className = "syncshopper-query-block";

  const label = document.createElement("label");
  label.className = "syncshopper-section-label";
  label.setAttribute("for", "syncshopper-naver-search-query");
  label.textContent = "\uB124\uC774\uBC84 \uAC80\uC0C9 \uCFFC\uB9AC";

  const row = document.createElement("div");
  row.className = "syncshopper-query-row";

  const input = document.createElement("input");
  input.id = "syncshopper-naver-search-query";
  input.className = "syncshopper-query-input";
  input.type = "text";
  input.value = query;
  input.placeholder = "\uB124\uC774\uBC84\uC5D0\uC11C \uAC80\uC0C9\uD560 \uD0A4\uC6CC\uB4DC";

  const searchButton = document.createElement("button");
  searchButton.className = "syncshopper-query-search-button";
  searchButton.type = "button";
  searchButton.textContent = "\uAC80\uC0C9";

  async function submitSearch() {
    if (searchButton.disabled) {
      return;
    }

    const trimmedQuery = input.value.trim();

    if (!trimmedQuery) {
      showToast("\uAC80\uC0C9\uC5B4\uB97C \uC785\uB825\uD574\uC8FC\uC138\uC694.", "warning");
      input.focus();
      return;
    }

    searchButton.disabled = true;
    searchButton.textContent = "\uAC80\uC0C9\uC911";
    setProductResultsLoading();

    try {
      const products = await requestCommerceTop3Products(trimmedQuery);
      updateProductResults(products);
      showToast("\uB124\uC774\uBC84 \uAC80\uC0C9\uACB0\uACFC\uB97C \uC5C5\uB370\uC774\uD2B8\uD588\uC2B5\uB2C8\uB2E4.", "success");
    } catch (error) {
      console.error("[SyncShopper] commerce search failed", error);
      updateProductResults([]);
      showToast(error.message || "\uB124\uC774\uBC84 \uAC80\uC0C9\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4.", "error");
    } finally {
      searchButton.disabled = false;
      searchButton.textContent = "\uAC80\uC0C9";
    }
  }

  input.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      submitSearch();
    }
  });

  searchButton.addEventListener("click", submitSearch);

  row.appendChild(input);
  row.appendChild(searchButton);
  block.appendChild(label);
  block.appendChild(row);

  return block;
}

function createProductResultsBlock(products) {
  const productBlock = document.createElement("section");
  productBlock.className = "syncshopper-product-results";

  const productLabel = document.createElement("div");
  productLabel.className = "syncshopper-section-label";
  productLabel.textContent = "\uB124\uC774\uBC84 \uAC80\uC0C9\uACB0\uACFC";

  const productList = document.createElement("div");
  productList.id = "syncshopper-product-list";

  productBlock.appendChild(productLabel);
  productBlock.appendChild(productList);
  renderProductList(productList, products);

  return productBlock;
}

function setProductResultsLoading() {
  const productList = document.getElementById("syncshopper-product-list");

  if (!productList) {
    return;
  }

  productList.replaceChildren(createPanelMessage("\uB124\uC774\uBC84 \uAC80\uC0C9 \uC911..."));
}

function updateProductResults(products) {
  const productList = document.getElementById("syncshopper-product-list");

  if (!productList) {
    return;
  }

  renderProductList(productList, products);
}

function renderProductList(productList, products) {
  productList.replaceChildren();

  if (!Array.isArray(products) || products.length === 0) {
    productList.appendChild(createPanelMessage("\uD45C\uC2DC\uD560 \uC0C1\uD488\uC774 \uC5C6\uC2B5\uB2C8\uB2E4."));
    return;
  }

  products.forEach((product) => {
    productList.appendChild(createProductCard(product));
  });
}

function createProductCard(product) {
  const card = document.createElement("article");
  card.className = "syncshopper-product-card";

  const image = document.createElement("img");
  image.className = "syncshopper-product-image";
  image.alt = product.title || "\uC0C1\uD488 \uC774\uBBF8\uC9C0";
  image.loading = "lazy";

  if (product.imageUrl) {
    image.src = product.imageUrl;
  }

  const details = document.createElement("div");
  details.className = "syncshopper-product-details";

  const title = document.createElement("div");
  title.className = "syncshopper-product-title";
  title.textContent = product.title || "\uC0C1\uD488\uBA85 \uC5C6\uC74C";

  const meta = document.createElement("div");
  meta.className = "syncshopper-product-meta";
  meta.textContent = [product.mallName, product.brand].filter(Boolean).join(" \u00B7 ");

  const price = document.createElement("div");
  price.className = "syncshopper-product-price";
  price.textContent = formatProductPrice(product.price);

  const link = document.createElement("a");
  link.className = "syncshopper-product-link";
  link.textContent = "\uC0C1\uD488 \uD310\uB9E4 \uD398\uC774\uC9C0\uB85C \uC774\uB3D9";
  link.href = product.affiliateUrl || "#";
  link.target = "_blank";
  link.rel = "noopener noreferrer";

  if (!product.affiliateUrl) {
    link.removeAttribute("href");
    link.setAttribute("aria-disabled", "true");
  }

  details.appendChild(title);

  if (meta.textContent) {
    details.appendChild(meta);
  }

  details.appendChild(price);
  details.appendChild(link);

  card.appendChild(image);
  card.appendChild(details);

  return card;
}

function formatProductPrice(price) {
  const numericPrice = Number(price);

  if (!Number.isFinite(numericPrice) || numericPrice <= 0) {
    return "\uAC00\uACA9 \uC815\uBCF4 \uC5C6\uC74C";
  }

  return `${new Intl.NumberFormat("ko-KR").format(numericPrice)}\uC6D0`;
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
    chrome.storage.local.get(["backendBaseUrl", "frontendBaseUrl", "accessToken"], (result) => {
      resolve({
        backendBaseUrl: result.backendBaseUrl || DEFAULT_BACKEND_BASE_URL,
        frontendBaseUrl: result.frontendBaseUrl || DEFAULT_FRONTEND_BASE_URL,
        accessToken: result.accessToken
      });
    });
  });
}

async function isLoggedIn() {
  const { accessToken } = await getExtensionSettings();
  return Boolean(accessToken);
}

function showLoginPanel(onLoginSuccess) {
  removeAreaSelectionOverlay();
  hideCaptureButton();

  if (typeof onLoginSuccess === "function") {
    pendingLoginSuccessCallback = onLoginSuccess;
  }

  const existingPanel = document.getElementById("syncshopper-login-panel");

  if (existingPanel) {
    const firstInput = existingPanel.querySelector("#syncshopper-login-id");

    if (firstInput) {
      firstInput.focus();
    }

    return;
  }

  const panel = document.createElement("aside");
  panel.id = "syncshopper-login-panel";

  const closeButton = document.createElement("button");
  closeButton.id = "syncshopper-login-close-button";
  closeButton.type = "button";
  closeButton.textContent = "\u00D7";
  closeButton.setAttribute("aria-label", "Close SyncShopper login panel");
  closeButton.addEventListener("click", () => {
    pendingLoginSuccessCallback = null;
    panel.remove();
    showCaptureButton();
  });

  const title = document.createElement("h2");
  title.textContent = "SyncShopper \uB85C\uADF8\uC778";

  const description = document.createElement("p");
  description.textContent = "\uC0C1\uD488 \uCEA1\uCCD0 \uBD84\uC11D\uC744 \uC0AC\uC6A9\uD558\uB824\uBA74 \uBA3C\uC800 \uB85C\uADF8\uC778\uD574\uC8FC\uC138\uC694.";

  const loginIdLabel = document.createElement("label");
  loginIdLabel.setAttribute("for", "syncshopper-login-id");
  loginIdLabel.textContent = "\uC544\uC774\uB514";

  const loginIdInput = document.createElement("input");
  loginIdInput.id = "syncshopper-login-id";
  loginIdInput.type = "text";
  loginIdInput.autocomplete = "username";
  loginIdInput.placeholder = "\uC774\uBA54\uC77C\uC744 \uC785\uB825\uD558\uC138\uC694";

  const passwordLabel = document.createElement("label");
  passwordLabel.setAttribute("for", "syncshopper-login-password");
  passwordLabel.textContent = "\uBE44\uBC00\uBC88\uD638";

  const passwordInput = document.createElement("input");
  passwordInput.id = "syncshopper-login-password";
  passwordInput.type = "password";
  passwordInput.autocomplete = "current-password";
  passwordInput.placeholder = "\uBE44\uBC00\uBC88\uD638\uB97C \uC785\uB825\uD558\uC138\uC694";

  const errorMessage = document.createElement("div");
  errorMessage.id = "syncshopper-login-error";

  const loginButton = document.createElement("button");
  loginButton.id = "syncshopper-login-submit-button";
  loginButton.type = "button";
  loginButton.textContent = "\uB85C\uADF8\uC778";

  const signupButton = document.createElement("button");
  signupButton.id = "syncshopper-signup-button";
  signupButton.type = "button";
  signupButton.textContent = "\uD68C\uC6D0\uAC00\uC785";

  async function submitLogin() {
    const loginId = loginIdInput.value.trim();
    const password = passwordInput.value;

    errorMessage.textContent = "";

    if (!loginId) {
      errorMessage.textContent = "\uC544\uC774\uB514\uB97C \uC785\uB825\uD574\uC8FC\uC138\uC694.";
      loginIdInput.focus();
      return;
    }

    if (!password) {
      errorMessage.textContent = "\uBE44\uBC00\uBC88\uD638\uB97C \uC785\uB825\uD574\uC8FC\uC138\uC694.";
      passwordInput.focus();
      return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "\uB85C\uADF8\uC778 \uC911...";

    try {
      const authResult = await requestLogin(loginId, password);

      await chrome.storage.local.set({
        backendBaseUrl: DEFAULT_BACKEND_BASE_URL,
        frontendBaseUrl: DEFAULT_FRONTEND_BASE_URL,
        accessToken: authResult.accessToken,
        authUser: authResult.user || null
      });

      panel.remove();
      showToast("\uB85C\uADF8\uC778\uB418\uC5C8\uC2B5\uB2C8\uB2E4.", "success");

      if (typeof pendingLoginSuccessCallback === "function") {
        const callback = pendingLoginSuccessCallback;
        pendingLoginSuccessCallback = null;
        callback();
      }
    } catch (error) {
      errorMessage.textContent = error.message || "\uB85C\uADF8\uC778\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4.";
    } finally {
      loginButton.disabled = false;
      loginButton.textContent = "\uB85C\uADF8\uC778";
    }
  }

  loginButton.addEventListener("click", submitLogin);
  passwordInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      submitLogin();
    }
  });
  signupButton.addEventListener("click", openSignupPage);

  panel.appendChild(closeButton);
  panel.appendChild(title);
  panel.appendChild(description);
  panel.appendChild(loginIdLabel);
  panel.appendChild(loginIdInput);
  panel.appendChild(passwordLabel);
  panel.appendChild(passwordInput);
  panel.appendChild(errorMessage);
  panel.appendChild(loginButton);
  panel.appendChild(signupButton);
  document.body.appendChild(panel);

  loginIdInput.focus();
}

function requestLogin(loginId, password) {
  return new Promise((resolve, reject) => {
    const requestUrl = `${DEFAULT_BACKEND_BASE_URL}/api/auth/login`;

    chrome.runtime.sendMessage(
      {
        type: "SYNC_SHOPPER_LOGIN",
        requestUrl,
        requestBody: {
          email: loginId,
          password
        }
      },
      (response) => {
        if (chrome.runtime.lastError) {
          reject(new Error(chrome.runtime.lastError.message));
          return;
        }

        if (!response || !response.success) {
          reject(new Error(response?.errorMessage || "\uB85C\uADF8\uC778\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4."));
          return;
        }

        resolve(response.result);
      }
    );
  });
}

function openSignupPage() {
  chrome.runtime.sendMessage({
    type: "SYNC_SHOPPER_OPEN_SIGNUP",
    url: `${DEFAULT_FRONTEND_BASE_URL}/signup`
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
    showToast("\uB85C\uADF8\uC778\uC774 \uD544\uC694\uD569\uB2C8\uB2E4.", "warning");
    showLoginPanel();
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
    await chrome.storage.local.remove(["accessToken", "authUser"]);
    showLoginPanel();
    showToast("\uB85C\uADF8\uC778\uC774 \uB9CC\uB8CC\uB418\uC5C8\uC2B5\uB2C8\uB2E4. \uB2E4\uC2DC \uB85C\uADF8\uC778\uD574\uC8FC\uC138\uC694.", "error");
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

async function requestCommerceTop3Products(query) {
  const { backendBaseUrl, accessToken } = await getExtensionSettings();

  if (!backendBaseUrl) {
    throw new Error("\uBC31\uC5D4\uB4DC \uC8FC\uC18C\uAC00 \uC5C6\uC2B5\uB2C8\uB2E4.");
  }

  if (!accessToken) {
    showLoginPanel();
    throw new Error("\uB85C\uADF8\uC778\uC774 \uD544\uC694\uD569\uB2C8\uB2E4.");
  }

  const requestUrl = `${backendBaseUrl.replace(/\/$/, "")}/api/commerce/top3?query=${encodeURIComponent(query)}`;
  const response = await requestCommerceSearch({
    requestUrl,
    accessToken
  });

  if (!response.success && response.errorCode === "NETWORK_ERROR") {
    throw new Error(response.errorMessage || "\uBC31\uC5D4\uB4DC \uC11C\uBC84\uC5D0 \uC5F0\uACB0\uD560 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.");
  }

  if (response.status === 401) {
    await chrome.storage.local.remove(["accessToken", "authUser"]);
    showLoginPanel();
    throw new Error("\uB85C\uADF8\uC778\uC774 \uB9CC\uB8CC\uB418\uC5C8\uC2B5\uB2C8\uB2E4.");
  }

  if (!response.success) {
    throw new Error(response.errorMessage || `Request failed: ${response.status}`);
  }

  return Array.isArray(response.result) ? response.result : [];
}

function requestCommerceSearch({ requestUrl, accessToken }) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      {
        type: "SYNC_SHOPPER_SEARCH_COMMERCE",
        requestUrl,
        accessToken
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
