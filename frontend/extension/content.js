console.log("[SyncShopper] content script loaded");

const DEFAULT_BACKEND_BASE_URL = "http://localhost:8080";
const DEFAULT_FRONTEND_BASE_URL = "http://localhost:5173";
const DEFAULT_TOAST_DURATION_MS = 3000;
const EXTENSION_RESULT_SOURCE_PAGE = "EXTENSION_RESULT_PANEL";
const DEFAULT_ANALYSIS_PROGRESS_MESSAGE = "AI 분석 준비중...";
const ANALYSIS_PROGRESS_MESSAGES = [
  "이미지 속 상품을 탐지중...",
  "쇼핑 검색어를 만드는 중...",
  "네이버 쇼핑에서 검색중...",
  "관련 있는 상품만 걸러내는 중...",
  "유사한 친구 찾는 중...",
  "추천 결과를 정리중..."
];
const ANALYSIS_PROGRESS_STEP_MS = 2400;

let currentVideo = null;
let captureLauncher = null;
let captureButton = null;
let observer = null;
let captureOverlay = null;
let selectionBox = null;
let captureGuide = null;
let toastTimer = null;
let pendingLoginSuccessCallback = null;
let analysisProgressTypingTimer = null;
let analysisProgressTypingToken = 0;
let analysisProgressSequenceTimer = null;
let analysisProgressSequenceIndex = 0;

function createCaptureButton() {
  const existingButton = document.getElementById("syncshopper-capture-button");

  if (existingButton) {
    captureButton = existingButton;
    return captureButton;
  }

  const button = document.createElement("button");
  button.id = "syncshopper-capture-button";
  button.type = "button";
  button.textContent = "상품 캡쳐";

  button.addEventListener("click", async () => {
    console.log("[SyncShopper] capture button clicked");

    if (!prepareVideoForCapture()) {
      showToast("영상 화면을 찾을 수 없습니다.", "warning");
      return;
    }

    if (await isLoggedIn()) {
      startAreaSelection();
      return;
    }

    showLoginPanel(() => {
      if (prepareVideoForCapture()) {
        startAreaSelection();
        return;
      }

      showToast("영상 화면을 찾을 수 없습니다.", "warning");
    });
  });

  captureButton = button;

  return captureButton;
}

function createCaptureLauncher() {
  const existingLauncher = document.getElementById("syncshopper-capture-launcher");

  if (existingLauncher) {
    captureLauncher = existingLauncher;
    return captureLauncher;
  }

  const launcher = document.createElement("aside");
  launcher.id = "syncshopper-capture-launcher";
  launcher.setAttribute("aria-label", "SyncShopper capture launcher");

  const title = document.createElement("div");
  title.className = "syncshopper-launcher-title";
  title.textContent = "CapShop";

  const description = document.createElement("p");
  description.className = "syncshopper-launcher-description";
  description.textContent = "영상 속 상품을 바로 캡쳐하세요.";

  const button = createCaptureButton();

  launcher.appendChild(title);
  launcher.appendChild(description);
  launcher.appendChild(button);
  document.body.appendChild(launcher);
  captureLauncher = launcher;

  return captureLauncher;
}

function showCaptureButton() {
  const launcher = createCaptureLauncher();
  launcher.hidden = false;
}

function hideCaptureButton() {
  const launcher = document.getElementById("syncshopper-capture-launcher");

  if (launcher) {
    launcher.hidden = true;
  }
}

function isSupportedYouTubePage() {
  return Boolean(getYouTubeVideoId());
}

function updateCaptureLauncherVisibility() {
  if (isSupportedYouTubePage()) {
    showCaptureButton();
    return;
  }

  hideCaptureButton();
}

function prepareVideoForCapture() {
  const video = currentVideo || document.querySelector("video");

  if (!video) {
    return false;
  }

  currentVideo = video;

  if (!video.paused) {
    video.pause();
  }

  return true;
}

function bindVideoEvents(video) {
  if (!video) {
    return;
  }

  currentVideo = video;

  if (video.dataset.syncShopperBound === "true") {
    updateCaptureLauncherVisibility();
    return;
  }

  video.dataset.syncShopperBound = "true";

  console.log("[SyncShopper] video element found", video);
  updateCaptureLauncherVisibility();

  video.addEventListener("pause", () => {
    console.log("[SyncShopper] video paused");
  });

  video.addEventListener("play", () => {
    console.log("[SyncShopper] video played");
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
  captureGuide.textContent = "캡쳐할 상품 영역을 드래그하세요";

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
      showToast("선택 영역이 너무 작습니다.", "warning");
      updateCaptureLauncherVisibility();
      return;
    }

    try {
      const fullPageDataUrl = await requestVisibleTabCapture();

      console.log("[SyncShopper] captured full tab dataUrl", fullPageDataUrl.slice(0, 100));

      const croppedDataUrl = await cropCapturedImage(fullPageDataUrl, rect);

      console.log("[SyncShopper] cropped dataUrl", croppedDataUrl.slice(0, 100));

      previewCroppedImage(croppedDataUrl);

      showToast("캡쳐 영역 선택 완료", "success");
      showToast("AI 분석 요청 중...", "info");

      const analysisResult = await sendDetectionAnalyzeRequest(croppedDataUrl);
      updateCapturePanelResult(analysisResult);
    } catch (error) {
      console.error("[SyncShopper] capture process failed", error);
      updateCapturePanelResult({
        error: error.message || "분석 실패"
      });

      if (!document.getElementById("syncshopper-toast")) {
        showToast("분석 실패. 다시 시도해주세요.", "error");
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
  renderAnalysisProgress(DEFAULT_ANALYSIS_PROGRESS_MESSAGE);
}

function createCaptureResultPanel() {
  const existingPanel = document.getElementById("syncshopper-result-panel");

  if (existingPanel) {
    return existingPanel;
  }

  const panel = document.createElement("aside");
  panel.id = "syncshopper-result-panel";

  const title = document.createElement("h2");
  title.textContent = "CapShop";

  const closeButton = document.createElement("button");
  closeButton.id = "syncshopper-result-close-button";
  closeButton.type = "button";
  closeButton.textContent = "×";
  closeButton.setAttribute("aria-label", "Close SyncShopper result panel");
  closeButton.addEventListener("click", () => {
    stopAnalysisProgressSequence();
    panel.remove();
    updateCaptureLauncherVisibility();
  });

  const previewTitle = document.createElement("h3");
  previewTitle.textContent = "캡쳐 미리보기";

  const previewImage = document.createElement("img");
  previewImage.id = "syncshopper-result-preview";
  previewImage.alt = "캡쳐 결과";

  const resultContent = document.createElement("div");
  resultContent.id = "syncshopper-result-content";
  resultContent.textContent = "결과를 기다리는 중...";

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

  stopAnalysisProgressSequence();
  resultContent.replaceChildren(renderResultForPanel(result));
}

function renderAnalysisProgress(message) {
  const panel = createCaptureResultPanel();
  const resultContent = panel.querySelector("#syncshopper-result-content");

  if (!resultContent) {
    return;
  }

  let progressText = resultContent.querySelector(".syncshopper-progress-text");

  if (!progressText) {
    resultContent.replaceChildren(createAnalysisProgressElement());
    progressText = resultContent.querySelector(".syncshopper-progress-text");
  }

  if (progressText) {
    typeAnalysisProgressText(progressText, message || DEFAULT_ANALYSIS_PROGRESS_MESSAGE);
  }
}

function startAnalysisProgressSequence() {
  stopAnalysisProgressSequence();

  analysisProgressSequenceIndex = 0;
  renderAnalysisProgress(ANALYSIS_PROGRESS_MESSAGES[analysisProgressSequenceIndex]);

  analysisProgressSequenceTimer = setInterval(() => {
    analysisProgressSequenceIndex += 1;

    if (analysisProgressSequenceIndex >= ANALYSIS_PROGRESS_MESSAGES.length) {
      analysisProgressSequenceIndex = ANALYSIS_PROGRESS_MESSAGES.length - 1;
      clearInterval(analysisProgressSequenceTimer);
      analysisProgressSequenceTimer = null;
      return;
    }

    renderAnalysisProgress(ANALYSIS_PROGRESS_MESSAGES[analysisProgressSequenceIndex]);
  }, ANALYSIS_PROGRESS_STEP_MS);
}

function stopAnalysisProgressSequence() {
  if (analysisProgressSequenceTimer) {
    clearInterval(analysisProgressSequenceTimer);
    analysisProgressSequenceTimer = null;
  }

  stopAnalysisProgressTyping();
}

function createAnalysisProgressElement() {
  const wrapper = document.createElement("section");
  wrapper.className = "syncshopper-analysis-progress";
  wrapper.setAttribute("aria-live", "polite");

  const indicator = document.createElement("div");
  indicator.className = "syncshopper-progress-indicator";

  const spinner = document.createElement("span");
  spinner.className = "syncshopper-progress-spinner";

  const text = document.createElement("span");
  text.className = "syncshopper-progress-text";

  const cursor = document.createElement("span");
  cursor.className = "syncshopper-progress-cursor";
  cursor.textContent = "|";

  indicator.appendChild(spinner);
  indicator.appendChild(text);
  indicator.appendChild(cursor);
  wrapper.appendChild(indicator);

  return wrapper;
}

function typeAnalysisProgressText(element, message) {
  stopAnalysisProgressTyping();

  const token = analysisProgressTypingToken + 1;
  analysisProgressTypingToken = token;
  element.textContent = "";

  let index = 0;
  analysisProgressTypingTimer = setInterval(() => {
    if (analysisProgressTypingToken !== token) {
      return;
    }

    index += 1;
    element.textContent = message.slice(0, index);

    if (index >= message.length) {
      stopAnalysisProgressTyping(false);
    }
  }, 38);
}

function stopAnalysisProgressTyping(invalidate = true) {
  if (analysisProgressTypingTimer) {
    clearInterval(analysisProgressTypingTimer);
    analysisProgressTypingTimer = null;
  }

  if (invalidate) {
    analysisProgressTypingToken += 1;
  }
}

function renderResultForPanel(result) {
  const fragment = document.createDocumentFragment();

  if (typeof result === "string") {
    fragment.appendChild(createPanelMessage(result));
    return fragment;
  }

  if (result === null || result === undefined) {
    fragment.appendChild(createPanelMessage("분석 결과가 비어 있습니다."));
    return fragment;
  }

  const analysis = result && typeof result === "object" && result.data ? result.data : result;

  if (analysis.error) {
    fragment.appendChild(createPanelMessage(analysis.error));
    return fragment;
  }

  const targetName = analysis.detection?.targetName || analysis.targetName || "알 수 없는 상품";
  const products = Array.isArray(analysis.products) ? analysis.products : [];

  const detectionBlock = document.createElement("section");
  detectionBlock.className = "syncshopper-detection-summary";

  const detectionLabel = document.createElement("div");
  detectionLabel.className = "syncshopper-section-label";
  detectionLabel.textContent = "AI 탐지 결과:";

  const detectionValue = document.createElement("div");
  detectionValue.className = "syncshopper-detection-target";
  detectionValue.textContent = targetName;

  detectionBlock.appendChild(detectionLabel);
  detectionBlock.appendChild(detectionValue);
  detectionBlock.appendChild(createAiDetectionEvidenceBlock(analysis));
  fragment.appendChild(detectionBlock);
  fragment.appendChild(createRecaptureButton());
  fragment.appendChild(createNaverSearchQueryBlock(analysis));

  fragment.appendChild(createProductResultsBlock(analysis, products));
  return fragment;
}

function createAiDetectionEvidenceBlock(analysis) {
  const ocr = analysis.ocrAnalysis || analysis.ocr_analysis || {};
  const visual = analysis.visualAnalysis || analysis.visual_analysis || {};
  const identification = analysis.searchIdentification || analysis.search_identification || {};
  const googleResults = analysis.googleSearchResults || analysis.google_search_results || [];

  const block = document.createElement("div");
  block.className = "syncshopper-ai-evidence";

  const ocrText = [
    ...(Array.isArray(ocr.visible_text_candidates) ? ocr.visible_text_candidates : []),
    ...(Array.isArray(ocr.visibleTextCandidates) ? ocr.visibleTextCandidates : [])
  ].filter(Boolean).slice(0, 4).join(", ") || ocr.raw_text || ocr.rawText || "감지된 텍스트 없음";

  const visualText = [
    visual.product_type || visual.productType,
    visual.color,
    visual.style,
    visual.shape
  ].filter(Boolean).join(" · ") || "시각 특징 없음";

  const featureList = visual.key_features || visual.keyFeatures || [];
  const identificationText = [
    identification.target_name || identification.targetName,
    identification.brand,
    identification.model_name || identification.modelName
  ].filter(Boolean).join(" · ");

  block.appendChild(createAiEvidenceRow("OCR", ocrText));
  block.appendChild(createAiEvidenceRow("이미지", visualText));

  if (Array.isArray(featureList) && featureList.length > 0) {
    block.appendChild(createAiEvidenceRow("특징", featureList.slice(0, 4).join(", ")));
  }

  if (identificationText) {
    block.appendChild(createAiEvidenceRow("검색 식별", identificationText));
  }

  const evidence = identification.evidence || [];
  if (Array.isArray(evidence) && evidence.length > 0) {
    block.appendChild(createAiEvidenceRow("근거", evidence.slice(0, 2).join(" / ")));
  } else if (Array.isArray(googleResults) && googleResults.length > 0) {
    const googleText = googleResults
      .slice(0, 2)
      .map((item) => item.title || item.displayLink || item.link)
      .filter(Boolean)
      .join(" / ");
    if (googleText) {
      block.appendChild(createAiEvidenceRow("Google", googleText));
    }
  }

  return block;
}

function createAiEvidenceRow(labelText, valueText) {
  const row = document.createElement("div");
  row.className = "syncshopper-ai-evidence-row";

  const label = document.createElement("span");
  label.className = "syncshopper-ai-evidence-label";
  label.textContent = labelText;

  const value = document.createElement("span");
  value.className = "syncshopper-ai-evidence-value";
  value.textContent = valueText;

  row.appendChild(label);
  row.appendChild(value);
  return row;
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
  button.textContent = "다시 캡쳐하기";
  button.addEventListener("click", () => {
    const panel = document.getElementById("syncshopper-result-panel");

    if (panel) {
      stopAnalysisProgressSequence();
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
  label.textContent = "네이버 검색 쿼리";

  const row = document.createElement("div");
  row.className = "syncshopper-query-row";

  const input = document.createElement("input");
  input.id = "syncshopper-naver-search-query";
  input.className = "syncshopper-query-input";
  input.type = "text";
  input.value = query;
  input.placeholder = "네이버에서 검색할 키워드";

  const searchButton = document.createElement("button");
  searchButton.className = "syncshopper-query-search-button";
  searchButton.type = "button";
  searchButton.textContent = "검색";

  async function submitSearch() {
    if (searchButton.disabled) {
      return;
    }

    const trimmedQuery = input.value.trim();

    if (!trimmedQuery) {
      showToast("검색어를 입력해주세요.", "warning");
      input.focus();
      return;
    }

    searchButton.disabled = true;
    searchButton.textContent = "검색중";
    setProductResultsLoading();

    try {
      const products = await requestCommerceTop3Products(trimmedQuery);
      updateProductResults(products, createSearchAnalysisPatch(trimmedQuery));
      showToast("네이버 검색결과를 업데이트했습니다.", "success");
    } catch (error) {
      console.error("[SyncShopper] commerce search failed", error);
      updateProductResults([], createSearchAnalysisPatch(trimmedQuery));
      showToast(error.message || "네이버 검색에 실패했습니다.", "error");
    } finally {
      searchButton.disabled = false;
      searchButton.textContent = "검색";
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

function createProductResultsBlock(analysis, products) {
  const productBlock = document.createElement("section");
  productBlock.className = "syncshopper-product-results";

  const productLabel = document.createElement("div");
  productLabel.className = "syncshopper-section-label";
  productLabel.textContent = "네이버 검색결과";

  const productList = document.createElement("div");
  productList.id = "syncshopper-product-list";
  productList.syncShopperAnalysis = analysis;

  productBlock.appendChild(productLabel);
  productBlock.appendChild(productList);
  renderProductList(productList, products, analysis);

  return productBlock;
}

function setProductResultsLoading() {
  const productList = document.getElementById("syncshopper-product-list");

  if (!productList) {
    return;
  }

  productList.replaceChildren(createPanelMessage("네이버 검색 중..."));
}

function updateProductResults(products, analysisPatch = null) {
  const productList = document.getElementById("syncshopper-product-list");

  if (!productList) {
    return;
  }

  const analysis = mergeAnalysisContext(productList.syncShopperAnalysis || {}, analysisPatch);
  productList.syncShopperAnalysis = analysis;
  renderProductList(productList, products, analysis);
}

function renderProductList(productList, products, analysis) {
  productList.replaceChildren();

  if (!Array.isArray(products) || products.length === 0) {
    productList.appendChild(createPanelMessage("표시할 상품이 없습니다."));
    return;
  }

  products.forEach((product, index) => {
    productList.appendChild(createProductCard(product, analysis, index + 1));
  });
}

function createProductCard(product, analysis, rank) {
  const card = document.createElement("article");
  card.className = "syncshopper-product-card";
  card.dataset.productId = product.productId || "";
  card.addEventListener("click", () => {
    logExtensionProductEvent("PRODUCT_CLICK", analysis, product, rank, null);
  });

  const image = document.createElement("img");
  image.className = "syncshopper-product-image";
  image.alt = product.title || "상품 이미지";
  image.loading = "lazy";

  if (product.imageUrl) {
    image.src = product.imageUrl;
  }

  const details = document.createElement("div");
  details.className = "syncshopper-product-details";

  const title = document.createElement("div");
  title.className = "syncshopper-product-title";
  title.textContent = product.title || "상품명 없음";

  const meta = document.createElement("div");
  meta.className = "syncshopper-product-meta";
  meta.textContent = [product.mallName, product.brand].filter(Boolean).join(" · ");

  const price = document.createElement("div");
  price.className = "syncshopper-product-price";
  price.textContent = formatProductPrice(product.price);

  const link = document.createElement("a");
  link.className = "syncshopper-product-link";
  link.textContent = "상품 판매 페이지로 이동";
  link.href = product.affiliateUrl || "#";
  link.target = "_blank";
  link.rel = "noopener noreferrer";
  link.addEventListener("click", (event) => {
    event.stopPropagation();

    if (!product.affiliateUrl) {
      event.preventDefault();
      return;
    }

    logExtensionProductEvent("AFFILIATE_CLICK", analysis, product, rank, product.affiliateUrl);
  });

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

function createSearchAnalysisPatch(query) {
  return {
    commerceQuery: {
      primary_query: query,
      primaryQuery: query
    }
  };
}

function mergeAnalysisContext(baseAnalysis, analysisPatch) {
  if (!analysisPatch) {
    return baseAnalysis;
  }

  return {
    ...baseAnalysis,
    ...analysisPatch,
    commerceQuery: {
      ...(baseAnalysis.commerceQuery || {}),
      ...(analysisPatch.commerceQuery || {})
    }
  };
}

function logExtensionProductEvent(eventType, analysis, product, rank, targetUrl) {
  const eventAnalysis = analysis || {};
  const productId = toPositiveNumber(product.productId);

  if (!productId) {
    console.warn("[SyncShopper] user event skipped. productId is missing");
    return;
  }

  logUserEvent({
    eventType,
    productId,
    recommendationId: null,
    sourcePage: EXTENSION_RESULT_SOURCE_PAGE,
    videoId: eventAnalysis.videoId || null,
    categoryName: firstDefined(product.categoryName, eventAnalysis.categoryName, eventAnalysis.detection?.categoryName),
    brand: firstDefined(product.brand, eventAnalysis.brand, eventAnalysis.detection?.brand),
    targetUrl: eventType === "AFFILIATE_CLICK" ? targetUrl : null,
    metadataJson: buildExtensionEventMetadata(eventAnalysis, product, rank)
  });
}

function buildExtensionEventMetadata(analysis, product, rank) {
  const detection = analysis.detection || {};
  const commerceQuery = analysis.commerceQuery || {};

  return {
    rank,
    query: firstDefined(commerceQuery.primaryQuery, commerceQuery.primary_query),
    fallbackQueries: firstDefined(commerceQuery.fallbackQueries, commerceQuery.fallback_queries, []),
    detectionId: analysis.detectionId || null,
    confidence: firstDefined(detection.confidence, analysis.confidence),
    queryConfidence: firstDefined(commerceQuery.queryConfidence, commerceQuery.query_confidence),
    mallName: product.mallName || null,
    source: product.source || null,
    externalProductId: product.externalProductId || null
  };
}

function toPositiveNumber(value) {
  const numericValue = Number(value);
  return Number.isFinite(numericValue) && numericValue > 0 ? numericValue : null;
}

function firstDefined(...values) {
  return values.find((value) => value !== null && value !== undefined) ?? null;
}

function formatProductPrice(price) {
  const numericPrice = Number(price);

  if (!Number.isFinite(numericPrice) || numericPrice <= 0) {
    return "가격 정보 없음";
  }

  return `${new Intl.NumberFormat("ko-KR").format(numericPrice)}원`;
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

async function logUserEvent(eventPayload) {
  try {
    const { backendBaseUrl, accessToken } = await getExtensionSettings();

    if (!backendBaseUrl || !accessToken) {
      console.warn("[SyncShopper] user event log skipped. Missing backendBaseUrl or accessToken");
      return;
    }

    const requestUrl = `${backendBaseUrl.replace(/\/$/, "")}/api/user-events`;
    const response = await requestUserEventLog({
      requestUrl,
      accessToken,
      requestBody: eventPayload
    });

    if (!response.success) {
      console.warn("[SyncShopper] user event log failed", response.status, response.errorMessage);
      return;
    }

    console.log("[SyncShopper] user event logged", response.result);
  } catch (error) {
    console.warn("[SyncShopper] user event log error", error);
  }
}

function requestUserEventLog({ requestUrl, accessToken, requestBody }) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(
      {
        type: "SYNC_SHOPPER_LOG_USER_EVENT",
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
  closeButton.textContent = "×";
  closeButton.setAttribute("aria-label", "Close SyncShopper login panel");
  closeButton.addEventListener("click", () => {
    pendingLoginSuccessCallback = null;
    panel.remove();
    updateCaptureLauncherVisibility();
  });

  const title = document.createElement("h2");
  title.textContent = "SyncShopper 로그인";

  const description = document.createElement("p");
  description.textContent = "상품 캡쳐 분석을 사용하려면 먼저 로그인해주세요.";

  const loginIdLabel = document.createElement("label");
  loginIdLabel.setAttribute("for", "syncshopper-login-id");
  loginIdLabel.textContent = "아이디";

  const loginIdInput = document.createElement("input");
  loginIdInput.id = "syncshopper-login-id";
  loginIdInput.type = "text";
  loginIdInput.autocomplete = "username";
  loginIdInput.placeholder = "이메일을 입력하세요";

  const passwordLabel = document.createElement("label");
  passwordLabel.setAttribute("for", "syncshopper-login-password");
  passwordLabel.textContent = "비밀번호";

  const passwordInput = document.createElement("input");
  passwordInput.id = "syncshopper-login-password";
  passwordInput.type = "password";
  passwordInput.autocomplete = "current-password";
  passwordInput.placeholder = "비밀번호를 입력하세요";

  const errorMessage = document.createElement("div");
  errorMessage.id = "syncshopper-login-error";

  const loginButton = document.createElement("button");
  loginButton.id = "syncshopper-login-submit-button";
  loginButton.type = "button";
  loginButton.textContent = "로그인";

  const signupButton = document.createElement("button");
  signupButton.id = "syncshopper-signup-button";
  signupButton.type = "button";
  signupButton.textContent = "회원가입";

  async function submitLogin() {
    const loginId = loginIdInput.value.trim();
    const password = passwordInput.value;

    errorMessage.textContent = "";

    if (!loginId) {
      errorMessage.textContent = "아이디를 입력해주세요.";
      loginIdInput.focus();
      return;
    }

    if (!password) {
      errorMessage.textContent = "비밀번호를 입력해주세요.";
      passwordInput.focus();
      return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "로그인 중...";

    try {
      const authResult = await requestLogin(loginId, password);

      await chrome.storage.local.set({
        backendBaseUrl: DEFAULT_BACKEND_BASE_URL,
        frontendBaseUrl: DEFAULT_FRONTEND_BASE_URL,
        accessToken: authResult.accessToken,
        authUser: authResult.user || null
      });

      panel.remove();
      showToast("로그인되었습니다.", "success");

      if (typeof pendingLoginSuccessCallback === "function") {
        const callback = pendingLoginSuccessCallback;
        pendingLoginSuccessCallback = null;
        callback();
      }
    } catch (error) {
      errorMessage.textContent = error.message || "로그인에 실패했습니다.";
    } finally {
      loginButton.disabled = false;
      loginButton.textContent = "로그인";
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
          reject(new Error(response?.errorMessage || "로그인에 실패했습니다."));
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
    showToast("영상 ID를 찾을 수 없습니다.", "error");
    throw new Error("YouTube videoId not found");
  }

  const timestampSec = getCurrentTimestampSec();

  if (timestampSec === null || timestampSec === undefined) {
    showToast("영상 정보를 찾을 수 없습니다.", "error");
    throw new Error("Video timestamp not found");
  }

  const { backendBaseUrl, accessToken } = await getExtensionSettings();

  if (!backendBaseUrl) {
    showToast("백엔드 주소가 없습니다. 익스텐션 설정에서 백엔드 주소를 입력해주세요.", "warning");
    throw new Error("backendBaseUrl is missing");
  }

  if (!accessToken) {
    showToast("로그인이 필요합니다.", "warning");
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

  startAnalysisProgressSequence();

  const response = await requestDetectionAnalyze({
    requestUrl,
    accessToken,
    requestBody
  });

  if (!response.success && response.errorCode === "NETWORK_ERROR") {
    showToast("백엔드 서버에 연결할 수 없습니다.", "error");
    throw new Error(response.errorMessage || "Network error");
  }

  if (response.status === 401) {
    await chrome.storage.local.remove(["accessToken", "authUser"]);
    showLoginPanel();
    showToast("로그인이 만료되었습니다. 다시 로그인해주세요.", "error");
    throw new Error("Unauthorized");
  }

  if (response.status >= 500) {
    showToast("서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.", "error");
    throw new Error(`Server error: ${response.status}`);
  }

  if (!response.success) {
    showToast("분석 실패. 다시 시도해주세요.", "error");
    throw new Error(response.errorMessage || `Request failed: ${response.status}`);
  }

  const result = response.result;

  console.log("[SyncShopper] detection analyze response", result);
  showToast("상품 분석 완료", "success");

  return result;
}

async function requestCommerceTop3Products(query) {
  const { backendBaseUrl, accessToken } = await getExtensionSettings();

  if (!backendBaseUrl) {
    throw new Error("백엔드 주소가 없습니다.");
  }

  if (!accessToken) {
    showLoginPanel();
    throw new Error("로그인이 필요합니다.");
  }

  const requestUrl = `${backendBaseUrl.replace(/\/$/, "")}/api/commerce/top3?query=${encodeURIComponent(query)}`;
  const response = await requestCommerceSearch({
    requestUrl,
    accessToken
  });

  if (!response.success && response.errorCode === "NETWORK_ERROR") {
    throw new Error(response.errorMessage || "백엔드 서버에 연결할 수 없습니다.");
  }

  if (response.status === 401) {
    await chrome.storage.local.remove(["accessToken", "authUser"]);
    showLoginPanel();
    throw new Error("로그인이 만료되었습니다.");
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
  updateCaptureLauncherVisibility();

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
    updateCaptureLauncherVisibility();
  }, 500);
});

initSyncShopperExtension();
