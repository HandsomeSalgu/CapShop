(function () {
  const API_BASE_URL = "http://localhost:8080";

  async function sendDetectionAnalyzeRequest(croppedDataUrl, options = {}) {
    const accessToken = await getAccessToken();
    const response = await fetch(`${API_BASE_URL}/api/detections/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {})
      },
      body: JSON.stringify({
        videoId: options.videoId || getCurrentVideoId(),
        timestampSec: options.timestampSec ?? getCurrentVideoTimestamp(),
        imageBase64: croppedDataUrl,
        subtitleText: options.subtitleText || null
      })
    });

    const body = await response.json();
    const result = body && Object.prototype.hasOwnProperty.call(body, "data") ? body.data : body;

    console.log("[SyncShopper] detection analyze response", result);

    if (!response.ok || body.success === false) {
      showToast(body.message || "상품 분석에 실패했습니다.", "error");
      return result;
    }

    showToast(result.message || "상품 분석 완료", "success");
    renderDetectionResultPanel(result);

    return result;
  }

  function renderDetectionResultPanel(result) {
    removeDetectionResultPanel();

    const panel = document.createElement("div");
    panel.id = "syncshopper-result-panel";

    const detection = result?.detection || result || {};
    const commerceQuery = result?.commerceQuery || {};
    const products = Array.isArray(result?.products) ? result.products.slice(0, 3) : [];

    const productHtml = products.length > 0
      ? products.map((product) => `
          <div class="syncshopper-product-card">
            <img
              class="syncshopper-product-image"
              src="${escapeAttribute(product.imageUrl || "")}"
              alt=""
            />
            <div class="syncshopper-product-info">
              <div class="syncshopper-product-title">${escapeHtml(product.title || "상품명 없음")}</div>
              <div class="syncshopper-product-meta">${escapeHtml(product.mallName || "")}</div>
              <div class="syncshopper-product-price">${formatPrice(product.price)}</div>
              <button
                class="syncshopper-product-button"
                type="button"
                data-url="${encodeURIComponent(product.affiliateUrl || "")}"
              >
                상품 보기
              </button>
            </div>
          </div>
        `).join("")
      : `
        <div class="syncshopper-empty-products">
          검색된 상품이 없습니다.<br />
          다른 영역을 다시 캡처해보세요.
        </div>
      `;

    panel.innerHTML = `
      <div class="syncshopper-result-header">
        <div class="syncshopper-result-title">SyncShopper 분석 결과</div>
        <button class="syncshopper-result-close" type="button" aria-label="닫기">x</button>
      </div>

      <div class="syncshopper-result-section">
        <div class="syncshopper-result-label">감지 상품</div>
        <div class="syncshopper-result-value">${escapeHtml(detection.targetName || "-")}</div>
      </div>

      <div class="syncshopper-result-section">
        <div class="syncshopper-result-label">검색어</div>
        <div class="syncshopper-result-value">${escapeHtml(commerceQuery.primaryQuery || "-")}</div>
      </div>

      <div class="syncshopper-result-section">
        <div class="syncshopper-result-label">추천 상품 Top 3</div>
        ${productHtml}
      </div>
    `;

    document.body.appendChild(panel);

    panel.querySelector(".syncshopper-result-close").addEventListener("click", removeDetectionResultPanel);
    panel.querySelectorAll(".syncshopper-product-button").forEach((button) => {
      button.addEventListener("click", () => {
        const url = decodeURIComponent(button.dataset.url || "");
        if (url) {
          window.open(url, "_blank");
        }
      });
    });
  }

  function removeDetectionResultPanel() {
    const existingPanel = document.getElementById("syncshopper-result-panel");
    if (existingPanel) {
      existingPanel.remove();
    }
  }

  function formatPrice(price) {
    const numberPrice = Number(price);
    if (!Number.isFinite(numberPrice) || numberPrice <= 0) {
      return "가격 정보 없음";
    }
    return `${numberPrice.toLocaleString("ko-KR")}원`;
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll("\"", "&quot;")
      .replaceAll("'", "&#039;");
  }

  function escapeAttribute(value) {
    return escapeHtml(value).replaceAll("`", "&#096;");
  }

  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `syncshopper-toast syncshopper-toast-${type}`;
    toast.textContent = message;
    document.body.appendChild(toast);
    window.setTimeout(() => toast.remove(), 2800);
  }

  function getCurrentVideoId() {
    return new URLSearchParams(window.location.search).get("v") || "";
  }

  function getCurrentVideoTimestamp() {
    const video = document.querySelector("video");
    return video ? Math.floor(video.currentTime) : 0;
  }

  function getAccessToken() {
    return new Promise((resolve) => {
      if (!globalThis.chrome?.storage?.local) {
        resolve(null);
        return;
      }

      chrome.storage.local.get(["accessToken"], (items) => {
        resolve(items.accessToken || null);
      });
    });
  }

  chrome.runtime?.onMessage?.addListener((message, _sender, sendResponse) => {
    if (message?.type !== "SYNC_SHOPPER_ANALYZE_FRAME") {
      return false;
    }

    sendDetectionAnalyzeRequest(message.imageBase64, message)
      .then((result) => sendResponse({ ok: true, result }))
      .catch((error) => {
        showToast("상품 분석에 실패했습니다.", "error");
        sendResponse({ ok: false, message: error.message });
      });

    return true;
  });

  window.syncShopperRenderDetectionResultPanel = renderDetectionResultPanel;
  window.syncShopperRemoveDetectionResultPanel = removeDetectionResultPanel;
  window.syncShopperSendDetectionAnalyzeRequest = sendDetectionAnalyzeRequest;
})();
