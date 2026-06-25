// previous: const DEFAULT_BACKEND_BASE_URL = "http://70.12.60.52:8080";
// previous: const DEFAULT_FRONTEND_BASE_URL = "http://70.12.60.52:5173";
const DEFAULT_BACKEND_BASE_URL = "http://localhost:8080";
const DEFAULT_FRONTEND_BASE_URL = "http://localhost:5173";
const SOCIAL_LOGIN_PROVIDERS = ["google", "kakao"];

document.addEventListener("DOMContentLoaded", () => {
  const loginSection = document.getElementById("loginSection");
  const loggedInSection = document.getElementById("loggedInSection");
  const loginIdInput = document.getElementById("loginId");
  const passwordInput = document.getElementById("password");
  const loginButton = document.getElementById("loginButton");
  const googleLoginButton = document.getElementById("googleLoginButton");
  const kakaoLoginButton = document.getElementById("kakaoLoginButton");
  const signupButton = document.getElementById("signupButton");
  const logoutButton = document.getElementById("logoutButton");
  const statusMessage = document.getElementById("statusMessage");

  refreshAuthView();

  loginButton.addEventListener("click", async () => {
    const loginId = loginIdInput.value.trim();
    const password = passwordInput.value;

    if (!loginId) {
      showStatus("\uC544\uC774\uB514\uB97C \uC785\uB825\uD574 \uC8FC\uC138\uC694.", "error");
      loginIdInput.focus();
      return;
    }

    if (!password) {
      showStatus("\uBE44\uBC00\uBC88\uD638\uB97C \uC785\uB825\uD574 \uC8FC\uC138\uC694.", "error");
      passwordInput.focus();
      return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "\uB85C\uADF8\uC778 \uC911...";
    showStatus("");

    try {
      const authResult = await login(loginId, password);

      await chrome.storage.local.set({
        backendBaseUrl: DEFAULT_BACKEND_BASE_URL,
        frontendBaseUrl: DEFAULT_FRONTEND_BASE_URL,
        accessToken: authResult.accessToken,
        authUser: authResult.user || null
      });

      passwordInput.value = "";
      showStatus("\uB85C\uADF8\uC778\uB418\uC5C8\uC2B5\uB2C8\uB2E4.", "success");
      refreshAuthView();
    } catch (error) {
      showStatus(error.message || "\uB85C\uADF8\uC778\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4.", "error");
    } finally {
      loginButton.disabled = false;
      loginButton.textContent = "\uB85C\uADF8\uC778";
    }
  });

  passwordInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      loginButton.click();
    }
  });

  signupButton.addEventListener("click", () => {
    openSignupPage();
  });

  googleLoginButton.addEventListener("click", () => {
    openSocialLoginPage("google");
  });

  kakaoLoginButton.addEventListener("click", () => {
    openSocialLoginPage("kakao");
  });

  logoutButton.addEventListener("click", async () => {
    await chrome.storage.local.remove(["accessToken", "authUser"]);
    showStatus("\uB85C\uADF8\uC544\uC6C3\uB418\uC5C8\uC2B5\uB2C8\uB2E4.", "success");
    refreshAuthView();
  });

  function refreshAuthView() {
    chrome.storage.local.get(["accessToken"], (result) => {
      const isLoggedIn = Boolean(result.accessToken);

      loginSection.classList.toggle("hidden", isLoggedIn);
      loggedInSection.classList.toggle("hidden", !isLoggedIn);
    });
  }

  function login(loginId, password) {
    return new Promise((resolve, reject) => {
      chrome.runtime.sendMessage(
        {
          type: "SYNC_SHOPPER_LOGIN",
          requestUrl: `${DEFAULT_BACKEND_BASE_URL}/api/auth/login`,
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
    chrome.tabs.create({
      url: `${DEFAULT_FRONTEND_BASE_URL}/signup`
    });
  }

  function openSocialLoginPage(provider) {
    if (!SOCIAL_LOGIN_PROVIDERS.includes(provider)) {
      return;
    }

    chrome.tabs.create({
      url: `${DEFAULT_BACKEND_BASE_URL}/oauth2/authorization/${provider}`
    });
  }

  function showStatus(message, type = "info") {
    statusMessage.textContent = message;
    statusMessage.className = message ? `status-${type}` : "";
  }
});
