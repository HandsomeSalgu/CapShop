console.log("[SyncShopper] background service worker loaded");

chrome.runtime.onInstalled.addListener(() => {
  console.log("[SyncShopper] extension installed");
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message) {
    return false;
  }

  if (message.type === "SYNC_SHOPPER_ANALYZE_DETECTION") {
    sendDetectionAnalyzeRequest(message, sendResponse);
    return true;
  }

  if (message.type === "SYNC_SHOPPER_SEARCH_COMMERCE") {
    sendCommerceSearchRequest(message, sendResponse);
    return true;
  }

  if (message.type === "SYNC_SHOPPER_LOGIN") {
    sendLoginRequest(message, sendResponse);
    return true;
  }

  if (message.type === "SYNC_SHOPPER_OPEN_SIGNUP") {
    chrome.tabs.create({ url: message.url || "http://localhost:5173/signup" });
    return false;
  }

  if (message.type !== "SYNC_SHOPPER_CAPTURE_VISIBLE_TAB") {
    return false;
  }

  if (!sender.tab || typeof sender.tab.windowId !== "number") {
    sendResponse({
      success: false,
      errorMessage: "No sender tab available for captureVisibleTab"
    });

    return false;
  }

  chrome.tabs.captureVisibleTab(
    sender.tab.windowId,
    { format: "png" },
    (dataUrl) => {
      if (chrome.runtime.lastError) {
        console.error("[SyncShopper] capture failed", chrome.runtime.lastError.message);

        sendResponse({
          success: false,
          errorMessage: chrome.runtime.lastError.message
        });

        return;
      }

      if (!dataUrl) {
        sendResponse({
          success: false,
          errorMessage: "No dataUrl returned from captureVisibleTab"
        });

        return;
      }

      sendResponse({
        success: true,
        dataUrl
      });
    }
  );

  return true;
});

async function sendLoginRequest(message, sendResponse) {
  const { requestUrl, requestBody } = message;

  if (!requestUrl || !requestBody) {
    sendResponse({
      success: false,
      errorMessage: "Missing login request data"
    });
    return;
  }

  try {
    const response = await fetch(requestUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify(requestBody)
    });

    let result = null;
    const responseText = await response.text();

    if (responseText) {
      try {
        result = JSON.parse(responseText);
      } catch (error) {
        result = responseText;
      }
    }

    const isApiResponse = result && typeof result === "object" && Object.prototype.hasOwnProperty.call(result, "success");
    const data = isApiResponse ? result.data : result;
    const accessToken = data && typeof data === "object" ? data.accessToken : null;
    const isSuccess = response.ok && (!isApiResponse || result.success === true) && Boolean(accessToken);

    sendResponse({
      success: isSuccess,
      status: response.status,
      result: data,
      message: isApiResponse ? result.message : null,
      errorMessage: isSuccess ? null : (isApiResponse ? result.message : `Login failed: ${response.status}`)
    });
  } catch (error) {
    console.error("[SyncShopper] login request failed", error);

    sendResponse({
      success: false,
      errorCode: "NETWORK_ERROR",
      errorMessage: error.message
    });
  }
}

async function sendDetectionAnalyzeRequest(message, sendResponse) {
  const { requestUrl, accessToken, requestBody } = message;

  if (!requestUrl || !accessToken || !requestBody) {
    sendResponse({
      success: false,
      errorMessage: "Missing detection request data"
    });
    return;
  }

  try {
    const response = await fetch(requestUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${accessToken}`
      },
      body: JSON.stringify(requestBody)
    });

    let result = null;
    const responseText = await response.text();

    if (responseText) {
      try {
        result = JSON.parse(responseText);
      } catch (error) {
        result = responseText;
      }
    }

    const isApiResponse = result && typeof result === "object" && Object.prototype.hasOwnProperty.call(result, "success");
    const isSuccess = response.ok && (!isApiResponse || result.success === true);

    sendResponse({
      success: isSuccess,
      status: response.status,
      result: isApiResponse ? result.data : result,
      message: isApiResponse ? result.message : null,
      errorMessage: isSuccess ? null : (isApiResponse ? result.message : `Request failed: ${response.status}`)
    });
  } catch (error) {
    console.error("[SyncShopper] detection request failed", error);

    sendResponse({
      success: false,
      errorCode: "NETWORK_ERROR",
      errorMessage: error.message
    });
  }
}

async function sendCommerceSearchRequest(message, sendResponse) {
  const { requestUrl, accessToken } = message;

  if (!requestUrl || !accessToken) {
    sendResponse({
      success: false,
      errorMessage: "Missing commerce search request data"
    });
    return;
  }

  try {
    const response = await fetch(requestUrl, {
      method: "GET",
      headers: {
        "Authorization": `Bearer ${accessToken}`
      }
    });

    let result = null;
    const responseText = await response.text();

    if (responseText) {
      try {
        result = JSON.parse(responseText);
      } catch (error) {
        result = responseText;
      }
    }

    const isApiResponse = result && typeof result === "object" && Object.prototype.hasOwnProperty.call(result, "success");
    const isSuccess = response.ok && (!isApiResponse || result.success === true);

    sendResponse({
      success: isSuccess,
      status: response.status,
      result: isApiResponse ? result.data : result,
      message: isApiResponse ? result.message : null,
      errorMessage: isSuccess ? null : (isApiResponse ? result.message : `Request failed: ${response.status}`)
    });
  } catch (error) {
    console.error("[SyncShopper] commerce search request failed", error);

    sendResponse({
      success: false,
      errorCode: "NETWORK_ERROR",
      errorMessage: error.message
    });
  }
}
