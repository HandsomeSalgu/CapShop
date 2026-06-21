const DEFAULT_BACKEND_BASE_URL = "http://localhost:8080";
const DEFAULT_FRONTEND_BASE_URL = "http://localhost:5173";

document.addEventListener("DOMContentLoaded", () => {
  const loginSection = document.getElementById("loginSection");
  const loggedInSection = document.getElementById("loggedInSection");
  const loginIdInput = document.getElementById("loginId");
  const passwordInput = document.getElementById("password");
  const loginButton = document.getElementById("loginButton");
  const signupButton = document.getElementById("signupButton");
  const logoutButton = document.getElementById("logoutButton");
  const statusMessage = document.getElementById("statusMessage");

  refreshAuthView();

  loginButton.addEventListener("click", async () => {
    const loginId = loginIdInput.value.trim();
    const password = passwordInput.value;

    if (!loginId) {
      showStatus("아이디를 입력해주세요.", "error");
      loginIdInput.focus();
      return;
    }

    if (!password) {
      showStatus("비밀번호를 입력해주세요.", "error");
      passwordInput.focus();
      return;
    }

    loginButton.disabled = true;
    loginButton.textContent = "로그인 중...";
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
      showStatus("로그인되었습니다.", "success");
      refreshAuthView();
    } catch (error) {
      showStatus(error.message || "로그인에 실패했습니다.", "error");
    } finally {
      loginButton.disabled = false;
      loginButton.textContent = "로그인";
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

  logoutButton.addEventListener("click", async () => {
    await chrome.storage.local.remove(["accessToken", "authUser"]);
    showStatus("로그아웃되었습니다.", "success");
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
            reject(new Error(response?.errorMessage || "로그인에 실패했습니다."));
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

  function showStatus(message, type = "info") {
    statusMessage.textContent = message;

    if (type === "error") {
      statusMessage.style.color = "#dc2626";
      return;
    }

    if (type === "success") {
      statusMessage.style.color = "#16a34a";
      return;
    }

    statusMessage.style.color = "#4b5563";
  }
});
