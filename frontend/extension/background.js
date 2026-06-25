console.log("[SyncShopper] background service worker loaded");

// previous: const DEFAULT_BACKEND_BASE_URL = "http://70.12.60.52:8080";
// previous: const DEFAULT_FRONTEND_BASE_URL = "http://70.12.60.52:5173";
const DEFAULT_BACKEND_BASE_URL = "http://localhost:8080";
const DEFAULT_FRONTEND_BASE_URL = "http://localhost:5173";
const OAUTH_CALLBACK_URL = `${DEFAULT_FRONTEND_BASE_URL}/oauth/callback`;

chrome.runtime.onInstalled.addListener(() => {
  console.log("[SyncShopper] extension installed");
});

chrome.tabs.onUpdated.addListener((tabId, changeInfo) => {
  if (!changeInfo.url) {
    return;
  }

  handleOAuthCallbackUrl(changeInfo.url);
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

  if (message.type === "SYNC_SHOPPER_LOG_USER_EVENT") {
    sendUserEventLogRequest(message, sendResponse);
    return true;
  }

  if (message.type === "SYNC_SHOPPER_LOGIN") {
    sendLoginRequest(message, sendResponse);
    return true;
  }

  if (message.type === "SYNC_SHOPPER_OPEN_SIGNUP") {
    chrome.tabs.create({ url: message.url || `${DEFAULT_FRONTEND_BASE_URL}/signup` });
    return false;
  }

  if (message.type === "SYNC_SHOPPER_OPEN_SOCIAL_LOGIN") {
    chrome.tabs.create({ url: message.url || `${DEFAULT_BACKEND_BASE_URL}/oauth2/authorization/google` });
    return false;
  }

  if (message.type === "SYNC_SHOPPER_OPEN_FRONTEND_PAGE") {
    chrome.tabs.create({ url: message.url || DEFAULT_FRONTEND_BASE_URL });
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

async function handleOAuthCallbackUrl(url) {
  let callbackUrl = null;

  try {
    callbackUrl = new URL(url);
  } catch {
    return;
  }

  if (`${callbackUrl.origin}${callbackUrl.pathname}` !== OAUTH_CALLBACK_URL) {
    return;
  }

  const accessToken = callbackUrl.searchParams.get("accessToken");

  if (!accessToken) {
    return;
  }

  try {
    const authUser = await fetchAuthenticatedUser(accessToken);

    await chrome.storage.local.set({
      backendBaseUrl: DEFAULT_BACKEND_BASE_URL,
      frontendBaseUrl: DEFAULT_FRONTEND_BASE_URL,
      accessToken,
      authUser
    });

    console.log("[SyncShopper] OAuth login token saved");
  } catch (error) {
    console.error("[SyncShopper] failed to save OAuth login token", error);
  }
}

async function fetchAuthenticatedUser(accessToken) {
  const response = await fetch(`${DEFAULT_BACKEND_BASE_URL}/api/auth/me`, {
    method: "GET",
    headers: {
      "Authorization": `Bearer ${accessToken}`
    }
  });

  if (!response.ok) {
    throw new Error(`Failed to load OAuth user: ${response.status}`);
  }

  const result = await response.json();
  return result && typeof result === "object" && Object.prototype.hasOwnProperty.call(result, "data")
    ? result.data
    : result;
}

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

async function sendUserEventLogRequest(message, sendResponse) {
  const { requestUrl, accessToken, requestBody } = message;

  if (!requestUrl || !accessToken || !requestBody) {
    sendResponse({
      success: false,
      errorMessage: "Missing user event log request data"
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
    console.error("[SyncShopper] user event log request failed", error);

    sendResponse({
      success: false,
      errorCode: "NETWORK_ERROR",
      errorMessage: error.message
    });
  }
}
