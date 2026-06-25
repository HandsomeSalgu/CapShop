console.log("[SyncShopper] content script loaded");

// previous: const DEFAULT_BACKEND_BASE_URL = "http://70.12.60.52:8080";
// previous: const DEFAULT_FRONTEND_BASE_URL = "http://70.12.60.52:5173";
const DEFAULT_BACKEND_BASE_URL = "http://localhost:8080";
const DEFAULT_FRONTEND_BASE_URL = "http://localhost:5173";
const SOCIAL_LOGIN_PROVIDERS = {
  google: {
    label: "\uAD6C\uAE00\uB85C \uB85C\uADF8\uC778",
    iconType: "image",
    iconAlt: "Google",
    iconSrc: "data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA0OCA0OCIgd2lkdGg9IjQ4cHgiIGhlaWdodD0iNDhweCI+PHBhdGggZmlsbD0iI0ZGQzEwNyIgZD0iTTQzLjYxMSwyMC4wODNINDJWMjBIMjR2OGgxMS4zMDNjLTEuNjQ5LDQuNjU3LTYuMDgsOC0xMS4zMDMsOGMtNi42MjcsMC0xMi01LjM3My0xMi0xMmMwLTYuNjI3LDUuMzczLTEyLDEyLTEyYzMuMDU5LDAsNS44NDIsMS4xNTQsNy45NjEsMy4wMzlsNS42NTctNS42NTdDMzQuMDQ2LDYuMDUzLDI5LjI2OCw0LDI0LDRDMTIuOTU1LDQsNCwxMi45NTUsNCwyNGMwLDExLjA0NSw4Ljk1NSwyMCwyMCwyMGMxMS4wNDUsMCwyMC04Ljk1NSwyMC0yMEM0NCwyMi42NTksNDMuODYyLDIxLjM1LDQzLjYxMSwyMC4wODN6Ii8+PHBhdGggZmlsbD0iI0ZGM0QwMCIgZD0iTTYuMzA2LDE0LjY5MWw2LjU3MSw0LjgxOUMxNC42NTUsMTUuMTA4LDE4Ljk2MSwxMiwyNCwxMmMzLjA1OSwwLDUuODQyLDEuMTU0LDcuOTYxLDMuMDMxbDUuNjU3LTUuNjU3QzM0LjA0Niw2LjA1MywyOS4yNjgsNCwyNCw0QzE2LjMxOCw0LDkuNjU2LDguMzM3LDYuMzA2LDE0LjY5MXoiLz48cGF0aCBmaWxsPSIjNENBRjUwIiBkPSJNMjQsNDRjNS4xNjYsMCw5Ljg2LTEuOTc3LDEzLjQwOS01LjE5MmwtNi4xOS01LjIzOEMyOS4yMTEsMzUuMDkxLDI2LjcxNSwzNiwyNCwzNmMtNS4yMDIsMC05LjYxOS0zLjMxNy0xMS4yODMtNy45NDZsLTYuNTIyLDUuMDI1QzkuNTA1LDM5LjU1NiwxNi4yMjcsNDQsMjQsNDR6Ii8+PHBhdGggZmlsbD0iIzE5NzZEMiIgZD0iTTQzLjYxMSwyMC4wODNINDJWMjBIMjR2OGgxMS4zMDNjLTAuNzkyLDIuMjM3LTIuMjMxLDQuMTY2LTQuMDg3LDUuNTcxYzAuMDAxLTAuMDAxLDAuMDAyLTAuMDAxLDAuMDAzLTAuMDAybDYuMTksNS4yMzhDMzYuOTcxLDM5LjIwNSw0NCwzNCw0NCwyNEM0NCwyMi42NTksNDMuODYyLDIxLjM1LDQzLjYxMSwyMC4wODN6Ii8+PC9zdmc+"
  },
  kakao: {
    label: "\uCE74\uCE74\uC624\uB85C \uB85C\uADF8\uC778",
    iconType: "fontawesome",
    iconClass: "fa-solid fa-comment"
  }
};
const DEFAULT_TOAST_DURATION_MS = 3000;
const EXTENSION_RESULT_SOURCE_PAGE = "EXTENSION_RESULT_PANEL";
const DEFAULT_ANALYSIS_PROGRESS_MESSAGE = "\u0041\u0049 \uBD84\uC11D\uC744 \uC900\uBE44\uD558\uACE0 \uC788\uC5B4\uC694...";
const ANALYSIS_PROGRESS_MESSAGES = [
  "\uC774\uBBF8\uC9C0\uC5D0\uC11C \uC0C1\uD488\uC744 \uCC3E\uACE0 \uC788\uC5B4\uC694...",
  "\uAC80\uC0C9\uC5B4\uB97C \uB9CC\uB4E4\uACE0 \uC788\uC5B4\uC694...",
  "\uC1FC\uD551 \uACB0\uACFC\uB97C \uAC80\uC0C9\uD558\uACE0 \uC788\uC5B4\uC694...",
  "\uAD00\uB828 \uC788\uB294 \uC0C1\uD488\uB9CC \uCD94\uB824\uB0B4\uACE0 \uC788\uC5B4\uC694...",
  "\uBE44\uC2B7\uD55C \uC0C1\uD488\uC744 \uC815\uB9AC\uD558\uACE0 \uC788\uC5B4\uC694...",
  "\uCD94\uCC9C \uACB0\uACFC\uB97C \uC900\uBE44\uD558\uACE0 \uC788\uC5B4\uC694..."
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
let currentCapturedDataUrl = null;
let currentSearchMode = null;
let currentSearchHint = "";
let productSearchRequestToken = 0;

chrome.storage.onChanged.addListener((changes, areaName) => {
  if (areaName !== "local" || !changes.accessToken?.newValue) {
    return;
  }

  handleStoredOAuthLogin();
});

const PET_ATLAS = {
  frameWidth: 128,
  frameHeight: 128,
  size: 104,
  image: "pet/pet_atlas.png",
  animations: {
    idle_seed: {
      row: 0,
      frames: 6,
      fps: 4,
      loop: true
    },
    capture_camera: {
      row: 1,
      frames: 6,
      fps: 8,
      loop: false
    },
    analyzing_detective: {
      row: 2,
      frames: 8,
      fps: 8,
      loop: true
    },
    searching_box: {
      row: 3,
      frames: 8,
      fps: 10,
      loop: true
    },
    reranking_cards: {
      row: 4,
      frames: 8,
      fps: 8,
      loop: true
    },
    success_cheer: {
      row: 5,
      frames: 6,
      fps: 8,
      loop: false
    },
    failed_cry: {
      row: 6,
      frames: 6,
      fps: 4,
      loop: false
    },
    hover_wave: {
      row: 7,
      frames: 4,
      fps: 5,
      loop: false
    },
    dragging_run: {
      row: 8,
      frames: 6,
      fps: 12,
      loop: true
    }
  }
};

const PET_STORAGE_KEY = "capshopPetPosition";
const PET_DEFAULT_MESSAGES = {
  capture_camera: "\uC88B\uC544, \uCC0D\uC5B4\uBCFC\uAC8C!",
  analyzing_detective: "\uB2E8\uC11C\uB97C \uCC3E\uB294 \uC911!",
  searching_box: "\uBE44\uC2B7\uD55C \uC0C1\uD488\uC744 \uCC3E\uB294 \uC911!",
  reranking_cards: "\uAC00\uC7A5 \uBE44\uC2B7\uD55C \uC0C1\uD488\uC744 \uACE0\uB974\uB294 \uC911!",
  success_cheer: "\uCC3E\uC558\uB2E4!",
  failed_cry: "\uC774\uBC88\uC5D4 \uBABB \uCC3E\uC558\uC5B4...",
  hover_wave: "\uB0A0 \uB20C\uB7EC\uBD10",
  initial_greeting: "\uC548\uB155!!"
};
const PET_LONG_MOTION_OPTIONS = {
  failed_cry: {
    duration: 3600,
    settleMs: 2600
  },
  success_cheer: {
    duration: 2800,
    settleMs: 2200
  },
  hover_wave: {
    duration: 2600,
    settleMs: 1800
  }
};

let capShopPetRoot = null;
let capShopPetSprite = null;
let capShopPetBubble = null;
let capShopPetController = null;
let capShopPetStateManager = null;
let capShopPetBubbleTimer = null;
let capShopPetDragState = null;
let capShopPetInitialGreetingShown = false;
let capShopPanelDragState = null;

function createPetController(spriteElement) {
  let frame = 0;
  let timer = null;
  let currentAnimationName = null;
  let currentDirection = "right";

  function renderFrame(animation, frameIndex) {
    const x = -(frameIndex * PET_ATLAS.size);
    const y = -(animation.row * PET_ATLAS.size);
    spriteElement.style.backgroundPosition = `${x}px ${y}px`;
  }

  function stop() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  function setDirection(direction) {
    currentDirection = direction === "left" ? "left" : "right";
    spriteElement.dataset.direction = currentDirection;
  }

  function play(animationName, options = {}) {
    const animation = PET_ATLAS.animations[animationName] || PET_ATLAS.animations.idle_seed;
    const fps = options.fps || animation.fps || 8;
    currentAnimationName = animationName;
    frame = 0;
    stop();
    renderFrame(animation, frame);

    timer = setInterval(() => {
      frame += 1;

      if (frame >= animation.frames) {
        if (!animation.loop) {
          stop();
          if (typeof options.onComplete === "function") {
            options.onComplete(animationName);
          }
          return;
        }

        frame = 0;
      }

      renderFrame(animation, frame);
    }, Math.max(50, Math.round(1000 / fps)));
  }

  function setSpeed(fps) {
    if (currentAnimationName) {
      play(currentAnimationName, { fps });
    }
  }

  return {
    play,
    stop,
    setDirection,
    setSpeed
  };
}

function showPetBubble(message, duration = 2200) {
  ensureCapShopPet();

  if (!capShopPetBubble || !message) {
    hidePetBubble();
    return;
  }

  if (capShopPetBubbleTimer) {
    clearTimeout(capShopPetBubbleTimer);
    capShopPetBubbleTimer = null;
  }

  capShopPetBubble.textContent = message;
  capShopPetBubble.hidden = false;

  if (duration > 0) {
    capShopPetBubbleTimer = setTimeout(() => {
      hidePetBubble();
    }, duration);
  }
}

function hidePetBubble() {
  if (capShopPetBubbleTimer) {
    clearTimeout(capShopPetBubbleTimer);
    capShopPetBubbleTimer = null;
  }

  if (capShopPetBubble) {
    capShopPetBubble.hidden = true;
    capShopPetBubble.textContent = "";
  }
}

function createPetStateManager(controller) {
  let currentState = "idle_seed";
  let previousWorkState = "idle_seed";
  let overlayState = null;
  let settleTimer = null;

  function setPetState(state, options = {}) {
    if (!PET_ATLAS.animations[state]) {
      state = "idle_seed";
    }

    if (settleTimer) {
      clearTimeout(settleTimer);
      settleTimer = null;
    }

    if (options.openPanel) {
      openCapShopPanel();
    }

    const isOverlay = state === "hover_wave" || state === "dragging_run";
    if (isOverlay) {
      overlayState = state;
    } else {
      previousWorkState = state;
      overlayState = null;
    }

    currentState = state;
    const animation = PET_ATLAS.animations[state];
    const message = options.message || PET_DEFAULT_MESSAGES[state];
    controller.play(state, {
      onComplete: () => {
        if (state === "hover_wave") {
          overlayState = null;
          setPetState(previousWorkState || "idle_seed");
          return;
        }

        if (!animation.loop && state !== "idle_seed" && !options.holdFinalFrame) {
          settleTimer = setTimeout(() => {
            setPetState("idle_seed");
          }, options.settleMs ?? 1200);
        }
      }
    });

    if (message) {
      showPetBubble(message, options.duration ?? (animation.loop ? 2600 : 2200));
    } else if (!isOverlay) {
      hidePetBubble();
    }
  }

  function restoreAfterOverlay() {
    if (!overlayState) {
      return;
    }

    overlayState = null;
    setPetState(previousWorkState || "idle_seed");
  }

  return {
    setPetState,
    restoreAfterOverlay,
    getCurrentState: () => currentState,
    getPreviousWorkState: () => previousWorkState
  };
}

function getDefaultPetPosition() {
  return {
    left: Math.max(12, window.innerWidth - PET_ATLAS.size - 24),
    top: Math.max(12, window.innerHeight - PET_ATLAS.size - 28)
  };
}

function clampPetPosition(left, top) {
  const padding = 8;
  const rootWidth = capShopPetRoot?.offsetWidth || PET_ATLAS.size;
  const rootHeight = capShopPetRoot?.offsetHeight || PET_ATLAS.size;

  return {
    left: Math.min(Math.max(padding, left), Math.max(padding, window.innerWidth - rootWidth - padding)),
    top: Math.min(Math.max(padding, top), Math.max(padding, window.innerHeight - rootHeight - padding))
  };
}

function applyPetPosition(position) {
  if (!capShopPetRoot) {
    return;
  }

  const clamped = clampPetPosition(position.left, position.top);
  capShopPetRoot.style.left = `${clamped.left}px`;
  capShopPetRoot.style.top = `${clamped.top}px`;
  capShopPetRoot.style.right = "auto";
  capShopPetRoot.style.bottom = "auto";
}

function savePetPosition() {
  if (!capShopPetRoot || typeof chrome === "undefined" || !chrome.storage?.local) {
    return;
  }

  const rect = capShopPetRoot.getBoundingClientRect();
  const position = clampPetPosition(rect.left, rect.top);
  chrome.storage.local.set({
    [PET_STORAGE_KEY]: position
  });
}

function restorePetPosition() {
  if (typeof chrome === "undefined" || !chrome.storage?.local) {
    applyPetPosition(getDefaultPetPosition());
    return;
  }

  chrome.storage.local.get([PET_STORAGE_KEY], (result) => {
    const saved = result && result[PET_STORAGE_KEY];
    if (saved && Number.isFinite(saved.left) && Number.isFinite(saved.top)) {
      applyPetPosition(saved);
      return;
    }

    applyPetPosition(getDefaultPetPosition());
  });
}

function bindPetDragController(root) {
  root.addEventListener("pointerdown", (event) => {
    if (event.button !== 0) {
      return;
    }

    const rect = root.getBoundingClientRect();
    capShopPetDragState = {
      pointerId: event.pointerId,
      offsetX: event.clientX - rect.left,
      offsetY: event.clientY - rect.top,
      startX: event.clientX,
      startY: event.clientY,
      lastX: event.clientX,
      moved: false
    };

    root.setPointerCapture(event.pointerId);
  });

  root.addEventListener("pointermove", (event) => {
    if (!capShopPetDragState || capShopPetDragState.pointerId !== event.pointerId) {
      return;
    }

    const dx = event.clientX - capShopPetDragState.lastX;
    if (Math.abs(dx) > 1) {
      capShopPetController.setDirection(dx < 0 ? "left" : "right");
    }

    if (!capShopPetDragState.moved && Math.hypot(event.clientX - capShopPetDragState.startX, event.clientY - capShopPetDragState.startY) > 3) {
      capShopPetDragState.moved = true;
      capShopPetStateManager.setPetState("dragging_run");
    }

    capShopPetDragState.lastX = event.clientX;
    applyPetPosition({
      left: event.clientX - capShopPetDragState.offsetX,
      top: event.clientY - capShopPetDragState.offsetY
    });
  });

  root.addEventListener("pointerup", (event) => {
    if (!capShopPetDragState || capShopPetDragState.pointerId !== event.pointerId) {
      return;
    }

    const wasMoved = capShopPetDragState.moved;
    capShopPetDragState = null;
    savePetPosition();
    capShopPetStateManager.restoreAfterOverlay();

    if (!wasMoved) {
      toggleCapShopPanel();
    }
  });

  root.addEventListener("pointercancel", () => {
    capShopPetDragState = null;
    savePetPosition();
    capShopPetStateManager.restoreAfterOverlay();
  });
}

function ensureCapShopPet() {
  if (capShopPetRoot) {
    return capShopPetRoot;
  }

  const root = document.createElement("button");
  root.id = "capshop-pet-root";
  root.type = "button";
  root.setAttribute("aria-label", "CapShop pet launcher");
  root.style.setProperty("--cs-pet-size", `${PET_ATLAS.size}px`);

  const bubble = document.createElement("div");
  bubble.id = "capshop-pet-bubble";
  bubble.hidden = true;

  const sprite = document.createElement("span");
  sprite.id = "capshop-pet-sprite";
  sprite.style.backgroundImage = `url("${chrome.runtime.getURL(PET_ATLAS.image)}")`;
  sprite.style.backgroundSize = `${PET_ATLAS.size * 8}px ${PET_ATLAS.size * 9}px`;

  root.appendChild(bubble);
  root.appendChild(sprite);
  document.body.appendChild(root);

  capShopPetRoot = root;
  capShopPetSprite = sprite;
  capShopPetBubble = bubble;
  capShopPetController = createPetController(sprite);
  capShopPetStateManager = createPetStateManager(capShopPetController);

  root.addEventListener("mouseenter", () => {
    if (capShopPetDragState) {
      return;
    }

    capShopPetStateManager.setPetState("hover_wave", {
      message: PET_DEFAULT_MESSAGES.hover_wave,
      ...PET_LONG_MOTION_OPTIONS.hover_wave
    });
  });

  bindPetDragController(root);
  restorePetPosition();
  capShopPetStateManager.setPetState("idle_seed");
  showInitialPetGreeting();

  return root;
}

function showInitialPetGreeting() {
  if (capShopPetInitialGreetingShown) {
    return;
  }

  capShopPetInitialGreetingShown = true;
  setTimeout(() => {
    if (!capShopPetStateManager || capShopPetDragState) {
      return;
    }

    capShopPetStateManager.setPetState("hover_wave", {
      message: PET_DEFAULT_MESSAGES.initial_greeting,
      ...PET_LONG_MOTION_OPTIONS.hover_wave
    });
  }, 500);
}

function openCapShopPanel() {
  const resultPanel = document.getElementById("syncshopper-result-panel");
  if (resultPanel) {
    resultPanel.hidden = false;
    return resultPanel;
  }

  const loginPanel = document.getElementById("syncshopper-login-panel");
  if (loginPanel) {
    loginPanel.hidden = false;
    return loginPanel;
  }

  const launcher = createCaptureLauncher();
  launcher.dataset.capshopOpen = "true";
  launcher.hidden = false;
  return launcher;
}

function closeCapShopPanel() {
  stopAnalysisProgressSequence();

  const resultPanel = document.getElementById("syncshopper-result-panel");
  if (resultPanel) {
    resultPanel.remove();
  }

  const loginPanel = document.getElementById("syncshopper-login-panel");
  if (loginPanel) {
    loginPanel.remove();
  }

  const launcher = document.getElementById("syncshopper-capture-launcher");
  if (launcher) {
    launcher.dataset.capshopOpen = "false";
    launcher.hidden = true;
  }

  updateCaptureLauncherVisibility();
}

function toggleCapShopPanel() {
  const visiblePanel = [document.getElementById("syncshopper-result-panel"), document.getElementById("syncshopper-login-panel"), document.getElementById("syncshopper-capture-launcher")]
    .find((element) => element && !element.hidden);

  if (visiblePanel) {
    closeCapShopPanel();
    return;
  }

  openCapShopPanel();
}

function setPetState(state, options = {}) {
  ensureCapShopPet();
  capShopPetStateManager.setPetState(state, options);
}

function bindDraggableCapShopPanel(panel, storageKey) {
  if (!panel || panel.dataset.capshopPanelDraggable === "true") {
    return;
  }

  panel.dataset.capshopPanelDraggable = "true";
  panel.classList.add("syncshopper-draggable-panel");
  restoreDraggablePanelPosition(panel, storageKey);

  panel.addEventListener("pointerdown", (event) => {
    if (event.button !== 0 || shouldSkipPanelDrag(event.target)) {
      return;
    }

    const rect = panel.getBoundingClientRect();
    capShopPanelDragState = {
      panel,
      storageKey,
      pointerId: event.pointerId,
      offsetX: event.clientX - rect.left,
      offsetY: event.clientY - rect.top
    };

    panel.classList.add("syncshopper-panel-dragging");
    panel.setPointerCapture(event.pointerId);
  });

  panel.addEventListener("pointermove", (event) => {
    if (!capShopPanelDragState || capShopPanelDragState.panel !== panel || capShopPanelDragState.pointerId !== event.pointerId) {
      return;
    }

    applyDraggablePanelPosition(panel, {
      left: event.clientX - capShopPanelDragState.offsetX,
      top: event.clientY - capShopPanelDragState.offsetY
    });
  });

  panel.addEventListener("pointerup", (event) => {
    if (!capShopPanelDragState || capShopPanelDragState.panel !== panel || capShopPanelDragState.pointerId !== event.pointerId) {
      return;
    }

    finishPanelDrag();
  });

  panel.addEventListener("pointercancel", finishPanelDrag);
}

function shouldSkipPanelDrag(target) {
  return Boolean(target?.closest?.("button, input, textarea, select, a, img, .syncshopper-product-card"));
}

function finishPanelDrag() {
  if (!capShopPanelDragState) {
    return;
  }

  const { panel, storageKey } = capShopPanelDragState;
  panel.classList.remove("syncshopper-panel-dragging");
  saveDraggablePanelPosition(panel, storageKey);
  capShopPanelDragState = null;
}

function clampDraggablePanelPosition(panel, left, top) {
  const padding = 8;
  const rect = panel.getBoundingClientRect();

  return {
    left: Math.min(Math.max(padding, left), Math.max(padding, window.innerWidth - rect.width - padding)),
    top: Math.min(Math.max(padding, top), Math.max(padding, window.innerHeight - rect.height - padding))
  };
}

function applyDraggablePanelPosition(panel, position) {
  const clamped = clampDraggablePanelPosition(panel, position.left, position.top);
  panel.style.left = `${clamped.left}px`;
  panel.style.top = `${clamped.top}px`;
  panel.style.right = "auto";
  panel.style.bottom = "auto";
}

function saveDraggablePanelPosition(panel, storageKey) {
  if (!storageKey || typeof chrome === "undefined" || !chrome.storage?.local) {
    return;
  }

  const rect = panel.getBoundingClientRect();
  const position = clampDraggablePanelPosition(panel, rect.left, rect.top);
  chrome.storage.local.set({
    [storageKey]: position
  });
}

function restoreDraggablePanelPosition(panel, storageKey) {
  if (!storageKey || typeof chrome === "undefined" || !chrome.storage?.local) {
    return;
  }

  chrome.storage.local.get([storageKey], (result) => {
    const saved = result && result[storageKey];
    if (saved && Number.isFinite(saved.left) && Number.isFinite(saved.top)) {
      applyDraggablePanelPosition(panel, saved);
    }
  });
}

function exposeCapShopPetApi() {
  window.CapShopPet = {
    setState: setPetState,
    showBubble: showPetBubble,
    openPanel: openCapShopPanel,
    closePanel: closeCapShopPanel,
    togglePanel: toggleCapShopPanel
  };

  window.CapShopPetDemo = {
    run() {
      runPetDemo([
        ["idle_seed"],
        ["capture_camera", { message: PET_DEFAULT_MESSAGES.capture_camera }],
        ["analyzing_detective", { message: PET_DEFAULT_MESSAGES.analyzing_detective }],
        ["searching_box", { message: "\uBE44\uC2B7\uD55C \uC0C1\uD488\uC744 \uCC3E\uB294 \uC911!" }],
        ["reranking_cards", { message: PET_DEFAULT_MESSAGES.reranking_cards }],
        ["success_cheer", { message: PET_DEFAULT_MESSAGES.success_cheer, openPanel: true, ...PET_LONG_MOTION_OPTIONS.success_cheer }],
        ["idle_seed"]
      ]);
    },
    fail() {
      runPetDemo([
        ["idle_seed"],
        ["capture_camera", { message: PET_DEFAULT_MESSAGES.capture_camera }],
        ["analyzing_detective", { message: PET_DEFAULT_MESSAGES.analyzing_detective }],
        ["searching_box", { message: "\uBE44\uC2B7\uD55C \uC0C1\uD488\uC744 \uCC3E\uB294 \uC911!" }],
        ["failed_cry", { message: PET_DEFAULT_MESSAGES.failed_cry, ...PET_LONG_MOTION_OPTIONS.failed_cry }],
        ["idle_seed"]
      ]);
    }
  };
}

function runPetDemo(steps) {
  let delay = 0;
  steps.forEach(([state, options = {}]) => {
    setTimeout(() => {
      setPetState(state, options);
    }, delay);
    delay += state === "idle_seed" ? 700 : Math.max(1800, (options.settleMs || 0) + 400);
  });
}

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

  button.addEventListener("click", async () => {
    console.log("[SyncShopper] capture button clicked");

    if (!prepareVideoForCapture()) {
      showToast("\uC601\uC0C1 \uD654\uBA74\uC744 \uCC3E\uC744 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.", "warning");
      setPetState("failed_cry", {
        message: PET_DEFAULT_MESSAGES.failed_cry,
        ...PET_LONG_MOTION_OPTIONS.failed_cry
      });
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

      showToast("\uC601\uC0C1 \uD654\uBA74\uC744 \uCC3E\uC744 \uC218 \uC5C6\uC2B5\uB2C8\uB2E4.", "warning");
    });
  });

  captureButton = button;

  return captureButton;
}

function applyCapShopBrandTitle(titleElement, text) {
  titleElement.textContent = "";

  const icon = document.createElement("img");
  icon.className = "syncshopper-brand-icon";
  icon.src = chrome.runtime.getURL("icons/capshop_icon.png");
  icon.alt = "";
  icon.setAttribute("aria-hidden", "true");

  const label = document.createElement("span");
  label.textContent = text;

  titleElement.appendChild(icon);
  titleElement.appendChild(label);
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
  applyCapShopBrandTitle(title, "CapShop");

  const description = document.createElement("p");
  description.className = "syncshopper-launcher-description";
  description.textContent = "\uC601\uC0C1 \uC18D \uC0C1\uD488\uC744 \uBC14\uB85C \uCEA1\uCCD0\uD558\uC138\uC694.";

  const button = createCaptureButton();

  launcher.appendChild(title);
  launcher.appendChild(description);
  launcher.appendChild(button);
  document.body.appendChild(launcher);
  captureLauncher = launcher;
  bindDraggableCapShopPanel(launcher, "capshopCaptureLauncherPosition");

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
    ensureCapShopPet();

    const launcher = document.getElementById("syncshopper-capture-launcher");
    if (launcher && launcher.dataset.capshopOpen !== "true") {
      launcher.hidden = true;
    }

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
  setPetState("capture_camera", {
    message: PET_DEFAULT_MESSAGES.capture_camera,
    holdFinalFrame: true,
    duration: 2400
  });

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

    if (rect.width < 30 || rect.height < 30) {
      console.warn("[SyncShopper] selected area is too small");
      removeAreaSelectionOverlay();
      showToast("\uC120\uD0DD \uC601\uC5ED\uC774 \uB108\uBB34 \uC791\uC2B5\uB2C8\uB2E4.", "warning");
      setPetState("failed_cry", {
        message: PET_DEFAULT_MESSAGES.failed_cry,
        ...PET_LONG_MOTION_OPTIONS.failed_cry
      });
      updateCaptureLauncherVisibility();
      return;
    }

    try {
      removeAreaSelectionOverlay();
      await waitForNextPaint();

      const fullPageDataUrl = await requestVisibleTabCapture();

      console.log("[SyncShopper] captured full tab dataUrl", fullPageDataUrl.slice(0, 100));

      const croppedDataUrl = await cropCapturedImage(fullPageDataUrl, rect);

      console.log("[SyncShopper] cropped dataUrl", croppedDataUrl.slice(0, 100));

      previewCroppedImage(croppedDataUrl);
      setPetState("idle_seed");

      showToast("\uCEA1\uCCD0 \uC601\uC5ED \uC120\uD0DD \uC644\uB8CC", "success");

    } catch (error) {
      console.error("[SyncShopper] capture process failed", error);
      updateCapturePanelResult({
        error: error.message || "\uBD84\uC11D \uC2E4\uD328"
      });
      setPetState("failed_cry", {
        message: PET_DEFAULT_MESSAGES.failed_cry,
        ...PET_LONG_MOTION_OPTIONS.failed_cry
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
  currentCapturedDataUrl = croppedDataUrl;
  currentSearchMode = null;
  renderSearchModeChoice(croppedDataUrl);
}

function createCaptureResultPanel() {
  const existingPanel = document.getElementById("syncshopper-result-panel");

  if (existingPanel) {
    return existingPanel;
  }

  const panel = document.createElement("aside");
  panel.id = "syncshopper-result-panel";

  const title = document.createElement("h2");
  applyCapShopBrandTitle(title, "CapShop");

  const closeButton = document.createElement("button");
  closeButton.id = "syncshopper-result-close-button";
  closeButton.type = "button";
  closeButton.textContent = "\u00D7";
  closeButton.setAttribute("aria-label", "SyncShopper \uACB0\uACFC \uD328\uB110 \uB2EB\uAE30");
  closeButton.addEventListener("click", () => {
    closeCapShopPanel();
  });

  const minimizeButton = document.createElement("button");
  minimizeButton.id = "syncshopper-result-minimize-button";
  minimizeButton.type = "button";
  minimizeButton.textContent = "-";
  minimizeButton.setAttribute("aria-label", "SyncShopper \uACB0\uACFC \uD328\uB110 \uCD95\uC18C");
  minimizeButton.addEventListener("click", () => {
    toggleResultPanelCollapsed(panel, minimizeButton);
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
  panel.appendChild(minimizeButton);
  panel.appendChild(title);
  panel.appendChild(previewTitle);
  panel.appendChild(previewImage);
  panel.appendChild(resultContent);
  document.body.appendChild(panel);
  bindDraggableCapShopPanel(panel, "capshopResultPanelPosition");

  return panel;
}

function toggleResultPanelCollapsed(panel, button) {
  const collapsed = panel.dataset.collapsed === "true";
  panel.dataset.collapsed = collapsed ? "false" : "true";

  if (button) {
    button.textContent = collapsed ? "-" : "+";
    button.setAttribute(
      "aria-label",
      collapsed
        ? "SyncShopper \uACB0\uACFC \uD328\uB110 \uCD95\uC18C"
        : "SyncShopper \uACB0\uACFC \uD328\uB110 \uD3BC\uCE58\uAE30"
    );
  }
}

function waitForNextPaint() {
  return new Promise((resolve) => {
    requestAnimationFrame(() => {
      requestAnimationFrame(resolve);
    });
  });
}

function updateCapturePanelResult(result) {
  const panel = createCaptureResultPanel();
  const resultContent = panel.querySelector("#syncshopper-result-content");

  if (!resultContent) {
    return;
  }

  stopAnalysisProgressSequence();
  resultContent.replaceChildren(renderResultForPanel(result));
  loadProductsForRenderedNaverQuery(result);
}

function updatePetStateForAnalysisResult(result) {
  const analysis = result && typeof result === "object" && result.data ? result.data : result;
  const products = analysis && typeof analysis === "object" && Array.isArray(analysis.products) ? analysis.products : [];

  if (!analysis || typeof analysis !== "object" || analysis.error || products.length === 0) {
    setPetState("failed_cry", {
      message: PET_DEFAULT_MESSAGES.failed_cry,
      ...PET_LONG_MOTION_OPTIONS.failed_cry
    });
    return;
  }

  setPetState("success_cheer", {
    message: PET_DEFAULT_MESSAGES.success_cheer,
    openPanel: true,
    ...PET_LONG_MOTION_OPTIONS.success_cheer
  });
}

function renderSearchModeChoice(croppedDataUrl) {
  const panel = createCaptureResultPanel();
  const resultContent = panel.querySelector("#syncshopper-result-content");

  if (!resultContent) {
    return;
  }

  stopAnalysisProgressSequence();

  const wrapper = document.createElement("div");
  wrapper.className = "syncshopper-search-mode-choice";

  const title = document.createElement("div");
  title.className = "syncshopper-search-mode-title";
  title.textContent = "\uAC80\uC0C9 \uBC29\uC2DD \uC120\uD0DD";

  const buttonRow = document.createElement("div");
  buttonRow.className = "syncshopper-search-mode-buttons";

  const note = document.createElement("p");
  note.className = "syncshopper-search-mode-note";
  note.textContent = searchModeDescription("default");

  const hintLabel = document.createElement("label");
  hintLabel.className = "syncshopper-section-label";
  hintLabel.setAttribute("for", "syncshopper-search-hint");
  hintLabel.textContent = "\uD78C\uD2B8";

  const hintInput = document.createElement("input");
  hintInput.id = "syncshopper-search-hint";
  hintInput.className = "syncshopper-query-input syncshopper-hint-input";
  hintInput.type = "text";
  hintInput.maxLength = 160;
  hintInput.value = currentSearchHint || "";
  hintInput.placeholder = "\uC608: \uAC80\uC815 \uC7AC\uD0B7, \uB098\uC774\uD0A4, \uC18C\uD615 \uAC00\uBC29";

  const hintNote = document.createElement("p");
  hintNote.className = "syncshopper-search-mode-note";
  hintNote.textContent = "\uC785\uB825\uD558\uBA74 AI\uAC00 \uC774 \uD78C\uD2B8\uB97C \uC8FC\uC694 \uB2E8\uC11C\uB85C \uD65C\uC6A9\uD569\uB2C8\uB2E4.";

  const hintGroup = document.createElement("div");
  hintGroup.className = "syncshopper-search-option-group";

  const modeGroup = document.createElement("div");
  modeGroup.className = "syncshopper-search-option-group";

  buttonRow.appendChild(createSearchModeButton("\uBE60\uB978 \uAC80\uC0C9", "fast", croppedDataUrl, note, hintInput));
  buttonRow.appendChild(createSearchModeButton("\uC815\uBC00 \uAC80\uC0C9", "precise", croppedDataUrl, note, hintInput));

  hintGroup.appendChild(hintLabel);
  hintGroup.appendChild(hintInput);
  hintGroup.appendChild(hintNote);
  modeGroup.appendChild(title);
  modeGroup.appendChild(buttonRow);
  modeGroup.appendChild(note);
  wrapper.appendChild(hintGroup);
  wrapper.appendChild(modeGroup);
  resultContent.replaceChildren(wrapper);
  hintInput.focus();
}

function createSearchModeButton(label, searchMode, croppedDataUrl, noteElement = null, hintInput = null) {
  const button = document.createElement("button");
  button.className = `syncshopper-search-mode-button syncshopper-search-mode-button-${searchMode}`;
  button.type = "button";
  button.textContent = label;
  button.addEventListener("mouseenter", () => {
    updateSearchModeDescription(noteElement, searchMode);
  });
  button.addEventListener("focus", () => {
    updateSearchModeDescription(noteElement, searchMode);
  });
  button.addEventListener("mouseleave", () => {
    updateSearchModeDescription(noteElement, "default");
  });
  button.addEventListener("blur", () => {
    updateSearchModeDescription(noteElement, "default");
  });
  button.addEventListener("click", () => {
    startDetectionAnalysis(croppedDataUrl, searchMode, hintInput?.value || "");
  });
  return button;
}

function updateSearchModeDescription(noteElement, searchMode) {
  if (!noteElement) {
    return;
  }

  noteElement.textContent = searchModeDescription(searchMode);
}

function searchModeDescription(searchMode) {
  if (searchMode === "fast") {
    return "\uBE60\uB978 \uAC80\uC0C9\uC740 \uC774\uBBF8\uC9C0 \uC7AC\uC815\uB82C\uACFC \uD6C4\uBCF4 \uD310\uC815\uC744 \uAC74\uB108\uB6F0\uACE0 \uAC80\uC0C9 \uACB0\uACFC\uB97C \uBE60\uB974\uAC8C \uBCF4\uC5EC\uC90D\uB2C8\uB2E4.";
  }

  if (searchMode === "precise") {
    return "\uC815\uBC00 \uAC80\uC0C9\uC740 \uC774\uBBF8\uC9C0 \uC720\uC0AC\uB3C4 \uC7AC\uC815\uB82C\uACFC \uD6C4\uBCF4 \uD310\uC815\uC744 \uD568\uAED8 \uC218\uD589\uD574 \uB354 \uC2E0\uC911\uD558\uAC8C \uACE0\uB985\uB2C8\uB2E4.";
  }

  return "\uBC84\uD2BC\uC5D0 \uB9C8\uC6B0\uC2A4\uB97C \uC62C\uB9AC\uBA74 \uAC80\uC0C9 \uBC29\uC2DD\uC758 \uCC28\uC774\uB97C \uBCFC \uC218 \uC788\uC2B5\uB2C8\uB2E4.";
}

async function startDetectionAnalysis(croppedDataUrl, searchMode, userHint = "") {
  currentCapturedDataUrl = croppedDataUrl;
  currentSearchMode = searchMode;
  currentSearchHint = sanitizeSearchHint(userHint);
  showToast(`${searchMode === "fast" ? "\uBE60\uB978 \uAC80\uC0C9" : "\uC815\uBC00 \uAC80\uC0C9"}\uC744 \uC2DC\uC791\uD569\uB2C8\uB2E4.`, "info");
  renderAnalysisProgress(DEFAULT_ANALYSIS_PROGRESS_MESSAGE);

  try {
    const analysisResult = await sendDetectionAnalyzeRequest(croppedDataUrl, searchMode, currentSearchHint);
    updateCapturePanelResult(analysisResult);
  } catch (error) {
    console.error("[SyncShopper] analysis process failed", error);
    updateCapturePanelResult({
      error: error.message || "\uBD84\uC11D\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4."
    });

    if (!document.getElementById("syncshopper-toast")) {
      showToast("\uBD84\uC11D\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4. \uB2E4\uC2DC \uC2DC\uB3C4\uD574 \uC8FC\uC138\uC694.", "error");
    }
  }
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

function sanitizeSearchHint(value) {
  return String(value || "").replace(/\s+/g, " ").trim().slice(0, 160);
}

function setPetProgressForAnalysisIndex(index) {
  if (index <= 0) {
    setPetState("analyzing_detective", {
      message: PET_DEFAULT_MESSAGES.analyzing_detective
    });
    return;
  }

  if (index === 1) {
    setPetState("searching_box", {
      message: "\uAC80\uC0C9\uC5B4\uB97C \uB9CC\uB4E4\uACE0 \uC788\uC5B4!"
    });
    return;
  }

  if (index <= 2) {
    setPetState("searching_box", {
      message: "\uBE44\uC2B7\uD55C \uC0C1\uD488\uC744 \uCC3E\uB294 \uC911!"
    });
    return;
  }

  setPetState("reranking_cards", {
    message: PET_DEFAULT_MESSAGES.reranking_cards
  });
}

function startAnalysisProgressSequence() {
  stopAnalysisProgressSequence();

  analysisProgressSequenceIndex = 0;
  renderAnalysisProgress(ANALYSIS_PROGRESS_MESSAGES[analysisProgressSequenceIndex]);
  setPetProgressForAnalysisIndex(analysisProgressSequenceIndex);

  analysisProgressSequenceTimer = setInterval(() => {
    analysisProgressSequenceIndex += 1;

    if (analysisProgressSequenceIndex >= ANALYSIS_PROGRESS_MESSAGES.length) {
      analysisProgressSequenceIndex = ANALYSIS_PROGRESS_MESSAGES.length - 1;
      clearInterval(analysisProgressSequenceTimer);
      analysisProgressSequenceTimer = null;
      return;
    }

    renderAnalysisProgress(ANALYSIS_PROGRESS_MESSAGES[analysisProgressSequenceIndex]);
    setPetProgressForAnalysisIndex(analysisProgressSequenceIndex);
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
    fragment.appendChild(createPanelMessage("\uBD84\uC11D \uACB0\uACFC\uAC00 \uBE44\uC5B4 \uC788\uC2B5\uB2C8\uB2E4."));
    return fragment;
  }

  const analysis = result && typeof result === "object" && result.data ? result.data : result;

  if (analysis.error) {
    fragment.appendChild(createPanelMessage(analysis.error));
    return fragment;
  }

  const targetName = analysis.detection?.targetName || analysis.targetName || "\uC54C \uC218 \uC5C6\uB294 \uC0C1\uD488";

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
  fragment.appendChild(createResultActionButtons());
  fragment.appendChild(createNaverSearchQueryBlock(analysis));

  fragment.appendChild(createProductResultsBlock(analysis, null));
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
  ].filter(Boolean).slice(0, 4).join(", ") || ocr.raw_text || ocr.rawText || "\uAC10\uC9C0\uB41C \uD14D\uC2A4\uD2B8 \uC5C6\uC74C";

  const visualText = [
    visual.product_type || visual.productType,
    visual.color,
    visual.style,
    visual.shape
  ].filter(Boolean).join(" \u00B7 ") || "\uC2DC\uAC01 \uD2B9\uC9D5 \uC5C6\uC74C";

  const featureList = visual.key_features || visual.keyFeatures || [];
  const identificationText = [
    identification.target_name || identification.targetName,
    identification.brand,
    identification.model_name || identification.modelName
  ].filter(Boolean).join(" \u00B7 ");

  block.appendChild(createAiEvidenceRow("OCR", ocrText));
  block.appendChild(createAiEvidenceRow("\uC774\uBBF8\uC9C0", visualText));

  if (Array.isArray(featureList) && featureList.length > 0) {
    block.appendChild(createAiEvidenceRow("\uD2B9\uC9D5", featureList.slice(0, 4).join(", ")));
  }

  if (identificationText) {
    block.appendChild(createAiEvidenceRow("\uAC80\uC0C9 \uC2DD\uBCC4", identificationText));
  }

  const evidence = identification.evidence || [];
  if (Array.isArray(evidence) && evidence.length > 0) {
    block.appendChild(createAiEvidenceRow("\uADFC\uAC70", evidence.slice(0, 2).join(" / ")));
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
  button.textContent = "\uB2E4\uC2DC \uCEA1\uCCD0\uD558\uAE30";
  button.addEventListener("click", () => {
    const panel = document.getElementById("syncshopper-result-panel");

    if (panel) {
      stopAnalysisProgressSequence();
      panel.remove();
    }

    startAreaSelection();
  });

  button.textContent = "\uB2E4\uC2DC \uCEA1\uCCD0\uD558\uAE30";
  return button;
}

function createResultActionButtons() {
  const wrapper = document.createElement("div");
  wrapper.className = "syncshopper-result-actions";
  wrapper.appendChild(createRecaptureButton());

  const alternateButton = createAlternateSearchModeButton();
  if (alternateButton) {
    wrapper.appendChild(alternateButton);
  }

  return wrapper;
}

function createAlternateSearchModeButton() {
  if (!currentCapturedDataUrl || !currentSearchMode) {
    return null;
  }

  const nextMode = currentSearchMode === "fast" ? "precise" : "fast";
  const button = document.createElement("button");
  button.className = `syncshopper-recapture-button syncshopper-search-mode-button-${nextMode}`;
  button.type = "button";
  button.textContent = nextMode === "fast" ? "\uBE60\uB978 \uAC80\uC0C9" : "\uC815\uBC00 \uAC80\uC0C9";
  button.addEventListener("click", () => {
    startDetectionAnalysis(currentCapturedDataUrl, nextMode, currentSearchHint);
  });
  return button;
}

function createNaverSearchQueryBlock(analysis) {
  const query = resolveNaverSearchQuery(analysis);

  const block = document.createElement("section");
  block.className = "syncshopper-query-block";

  const label = document.createElement("label");
  label.className = "syncshopper-section-label";
  label.setAttribute("for", "syncshopper-naver-search-query");
  label.textContent = "\uB124\uC774\uBC84 \uAC80\uC0C9\uC5B4";

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
      showToast("\uAC80\uC0C9\uC5B4\uB97C \uC785\uB825\uD574 \uC8FC\uC138\uC694.", "warning");
      input.focus();
      return;
    }

    searchButton.disabled = true;
    searchButton.textContent = "\uAC80\uC0C9\uC911";
    const searchRequestToken = setProductResultsLoading();
    setPetState("searching_box", {
      message: "\uBE44\uC2B7\uD55C \uC0C1\uD488\uC744 \uCC3E\uB294 \uC911!"
    });

    try {
      const products = await requestCommerceTop3Products(trimmedQuery);
      if (!isLatestProductSearch(searchRequestToken)) {
        return;
      }
      updateProductResults(products, createSearchAnalysisPatch(trimmedQuery));
      if (products.length > 0) {
        setPetState("success_cheer", {
          message: PET_DEFAULT_MESSAGES.success_cheer,
          openPanel: true,
          ...PET_LONG_MOTION_OPTIONS.success_cheer
        });
        showToast("\uC0C1\uD488\uC744 \uB2E4\uC2DC \uBD88\uB7EC\uC654\uC2B5\uB2C8\uB2E4.", "success");
      } else {
        setPetState("failed_cry", {
          message: PET_DEFAULT_MESSAGES.failed_cry,
          ...PET_LONG_MOTION_OPTIONS.failed_cry
        });
        showToast("\uD45C\uC2DC\uD560 \uC0C1\uD488\uC774 \uC5C6\uC2B5\uB2C8\uB2E4.", "warning");
      }
    } catch (error) {
      if (!isLatestProductSearch(searchRequestToken)) {
        return;
      }
      console.error("[SyncShopper] commerce search failed", error);
      updateProductResults([], createSearchAnalysisPatch(trimmedQuery));
      setPetState("failed_cry", {
        message: PET_DEFAULT_MESSAGES.failed_cry,
        ...PET_LONG_MOTION_OPTIONS.failed_cry
      });
      showToast(error.message || "\uC0C1\uD488 \uAC80\uC0C9\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4.", "error");
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

function resolveNaverSearchQuery(analysis) {
  const commerceQuery = analysis?.commerceQuery || {};

  return resolveDetectedSearchQuery(analysis)
    || getAppliedRecommendationQuery(analysis)
    || commerceQuery.primary_query
    || commerceQuery.primaryQuery
    || commerceQuery.fallback_queries?.[0]
    || commerceQuery.fallbackQueries?.[0]
    || "";
}

function resolveDetectedSearchQuery(analysis) {
  const detection = analysis?.detection || {};
  const targetName = detection.targetName || analysis?.targetName;

  if (targetName && String(targetName).trim() && String(targetName).trim().toLowerCase() !== "unknown product") {
    return String(targetName).trim();
  }

  return [
    detection.brand || analysis?.brand,
    detection.color || analysis?.color,
    detection.categoryName || analysis?.categoryName
  ].filter(Boolean).join(" ").trim();
}

function getAppliedRecommendationQuery(analysis) {
  const products = Array.isArray(analysis?.products) ? analysis.products : [];
  const productQuery = products
    .map((product) => product?.queryText || product?.query_text || product?.sourceQuery || product?.source_query)
    .find((query) => query && String(query).trim());

  return productQuery ? String(productQuery).trim() : "";
}

function createProductResultsBlock(analysis, products) {
  const productBlock = document.createElement("section");
  productBlock.className = "syncshopper-product-results";

  const productLabel = document.createElement("div");
  productLabel.className = "syncshopper-section-label";
  productLabel.textContent = "\uB124\uC774\uBC84 \uAC80\uC0C9 \uC0C1\uD488";

  const productList = document.createElement("div");
  productList.id = "syncshopper-product-list";
  productList.syncShopperAnalysis = analysis;

  productBlock.appendChild(productLabel);
  productBlock.appendChild(productList);
  if (products === null) {
    productList.appendChild(createPanelMessage("\uC0C1\uD488\uC744 \uBD88\uB7EC\uC624\uB294 \uC911..."));
  } else {
    renderProductList(productList, products, analysis);
  }
  productBlock.appendChild(createMoreProductsButton(analysis));

  return productBlock;
}

function createMoreProductsButton(analysis) {
  const button = document.createElement("button");
  button.className = "syncshopper-more-products-button";
  button.type = "button";
  button.textContent = "\uB354 \uB9CE\uC740 \uC0C1\uD488 \uBCF4\uB7EC\uAC00\uAE30";

  button.addEventListener("click", () => {
    const queryInput = document.getElementById("syncshopper-naver-search-query");
    const query = (queryInput?.value || resolveNaverSearchQuery(analysis)).trim();

    if (!query) {
      showToast("\uAC80\uC0C9\uC5B4\uB97C \uC785\uB825\uD574 \uC8FC\uC138\uC694.", "warning");
      queryInput?.focus();
      return;
    }

    openCategorySearchPage(query);
  });

  return button;
}

function openCategorySearchPage(query) {
  const url = `${DEFAULT_FRONTEND_BASE_URL.replace(/\/$/, "")}/category?q=${encodeURIComponent(query)}`;

  chrome.runtime.sendMessage({
    type: "SYNC_SHOPPER_OPEN_FRONTEND_PAGE",
    url
  });
}

async function loadProductsForRenderedNaverQuery(result) {
  const analysis = result && typeof result === "object" && result.data ? result.data : result;

  if (!analysis || typeof analysis !== "object" || analysis.error) {
    updatePetStateForAnalysisResult(result);
    return;
  }

  const queryInput = document.getElementById("syncshopper-naver-search-query");
  const query = (queryInput?.value || resolveNaverSearchQuery(analysis)).trim();

  if (!query) {
    updateProductResults([], null);
    updatePetStateForAnalysisResult({ ...analysis, products: [] });
    return;
  }

  const searchRequestToken = setProductResultsLoading();

  try {
    const products = await requestCommerceTop3Products(query);
    if (!isLatestProductSearch(searchRequestToken)) {
      return;
    }
    const analysisPatch = createSearchAnalysisPatch(query);
    updateProductResults(products, analysisPatch);
    updatePetStateForAnalysisResult({
      ...mergeAnalysisContext(analysis, analysisPatch),
      products
    });
  } catch (error) {
    if (!isLatestProductSearch(searchRequestToken)) {
      return;
    }
    console.error("[SyncShopper] initial commerce search failed", error);
    updateProductResults([], createSearchAnalysisPatch(query));
    updatePetStateForAnalysisResult({ ...analysis, products: [] });
    showToast(error.message || "\uC0C1\uD488 \uAC80\uC0C9\uC5D0 \uC2E4\uD328\uD588\uC2B5\uB2C8\uB2E4.", "error");
  }
}

function setProductResultsLoading() {
  productSearchRequestToken += 1;
  const currentToken = productSearchRequestToken;
  const productList = document.getElementById("syncshopper-product-list");

  if (!productList) {
    return currentToken;
  }

  productList.replaceChildren(createPanelMessage("\uC0C1\uD488\uC744 \uBD88\uB7EC\uC624\uB294 \uC911..."));
  return currentToken;
}

function isLatestProductSearch(searchRequestToken) {
  return searchRequestToken === productSearchRequestToken;
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
    productList.appendChild(createPanelMessage("\uD45C\uC2DC\uD560 \uC0C1\uD488\uC774 \uC5C6\uC2B5\uB2C8\uB2E4."));
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
  closeButton.textContent = "\u00D7";
  closeButton.setAttribute("aria-label", "SyncShopper \uB85C\uADF8\uC778 \uD328\uB110 \uB2EB\uAE30");
  closeButton.addEventListener("click", () => {
    pendingLoginSuccessCallback = null;
    panel.remove();
    updateCaptureLauncherVisibility();
  });

  const title = document.createElement("h2");
  applyCapShopBrandTitle(title, "SyncShopper \uB85C\uADF8\uC778");

  const description = document.createElement("p");
  description.textContent = "\uC0C1\uD488 \uBD84\uC11D\uC744 \uC0AC\uC6A9\uD558\uB824\uBA74 \uB85C\uADF8\uC778\uD574 \uC8FC\uC138\uC694.";

  const loginIdLabel = document.createElement("label");
  loginIdLabel.setAttribute("for", "syncshopper-login-id");
  loginIdLabel.textContent = "\uC544\uC774\uB514";

  const loginIdInput = document.createElement("input");
  loginIdInput.id = "syncshopper-login-id";
  loginIdInput.type = "text";
  loginIdInput.autocomplete = "username";
  loginIdInput.placeholder = "\uC774\uBA54\uC77C\uC744 \uC785\uB825\uD574 \uC8FC\uC138\uC694";

  const passwordLabel = document.createElement("label");
  passwordLabel.setAttribute("for", "syncshopper-login-password");
  passwordLabel.textContent = "\uBE44\uBC00\uBC88\uD638";

  const passwordInput = document.createElement("input");
  passwordInput.id = "syncshopper-login-password";
  passwordInput.type = "password";
  passwordInput.autocomplete = "current-password";
  passwordInput.placeholder = "\uBE44\uBC00\uBC88\uD638\uB97C \uC785\uB825\uD574 \uC8FC\uC138\uC694";

  const errorMessage = document.createElement("div");
  errorMessage.id = "syncshopper-login-error";

  const loginButton = document.createElement("button");
  loginButton.id = "syncshopper-login-submit-button";
  loginButton.type = "button";
  loginButton.textContent = "\uB85C\uADF8\uC778";

  const socialLoginGroup = document.createElement("div");
  socialLoginGroup.id = "syncshopper-social-login-buttons";
  socialLoginGroup.setAttribute("aria-label", "\uC18C\uC15C \uB85C\uADF8\uC778");

  Object.entries(SOCIAL_LOGIN_PROVIDERS).forEach(([provider, config]) => {
    const socialButton = document.createElement("button");
    socialButton.type = "button";
    socialButton.className = `syncshopper-social-login-button syncshopper-social-login-button-${provider}`;
    socialButton.dataset.provider = provider;

    const icon = config.iconType === "image" ? document.createElement("img") : document.createElement("i");
    icon.className = config.iconType === "fontawesome"
      ? `syncshopper-social-login-icon ${config.iconClass}`
      : "syncshopper-social-login-icon";
    if (config.iconType === "image") {
      icon.src = config.iconSrc;
      icon.alt = config.iconAlt || "";
    }
    icon.setAttribute("aria-hidden", "true");

    const label = document.createElement("span");
    label.textContent = config.label;

    socialButton.appendChild(icon);
    socialButton.appendChild(label);
    socialButton.addEventListener("click", () => openSocialLoginPage(provider));
    socialLoginGroup.appendChild(socialButton);
  });

  const signupButton = document.createElement("button");
  signupButton.id = "syncshopper-signup-button";
  signupButton.type = "button";
  signupButton.textContent = "\uD68C\uC6D0\uAC00\uC785";

  async function submitLogin() {
    const loginId = loginIdInput.value.trim();
    const password = passwordInput.value;

    errorMessage.textContent = "";

    if (!loginId) {
      errorMessage.textContent = "\uC544\uC774\uB514\uB97C \uC785\uB825\uD574 \uC8FC\uC138\uC694.";
      loginIdInput.focus();
      return;
    }

    if (!password) {
      errorMessage.textContent = "\uBE44\uBC00\uBC88\uD638\uB97C \uC785\uB825\uD574 \uC8FC\uC138\uC694.";
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
  panel.appendChild(socialLoginGroup);
  panel.appendChild(signupButton);
  document.body.appendChild(panel);
  bindDraggableCapShopPanel(panel, "capshopLoginPanelPosition");

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

function openSocialLoginPage(provider) {
  if (!Object.prototype.hasOwnProperty.call(SOCIAL_LOGIN_PROVIDERS, provider)) {
    return;
  }

  chrome.runtime.sendMessage({
    type: "SYNC_SHOPPER_OPEN_SOCIAL_LOGIN",
    url: `${DEFAULT_BACKEND_BASE_URL}/oauth2/authorization/${provider}`
  });
}

function handleStoredOAuthLogin() {
  const loginPanel = document.getElementById("syncshopper-login-panel");

  if (loginPanel) {
    loginPanel.remove();
  }

  showToast("\uB85C\uADF8\uC778\uB418\uC5C8\uC2B5\uB2C8\uB2E4.", "success");

  if (typeof pendingLoginSuccessCallback === "function") {
    const callback = pendingLoginSuccessCallback;
    pendingLoginSuccessCallback = null;
    callback();
  }
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

async function sendDetectionAnalyzeRequest(croppedDataUrl, searchMode = "precise", userHint = "") {
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
    subtitleText: null,
    searchMode,
    userHint: sanitizeSearchHint(userHint)
  };
  const requestUrl = `${backendBaseUrl.replace(/\/$/, "")}/api/detections/analyze`;

  console.log("[SyncShopper] sending detection request", {
    requestUrl,
    videoId,
    timestampSec,
    imageSize: croppedDataUrl.length,
    searchMode,
    hasUserHint: Boolean(requestBody.userHint)
  });

  startAnalysisProgressSequence();

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
  exposeCapShopPetApi();
  ensureCapShopPet();
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
