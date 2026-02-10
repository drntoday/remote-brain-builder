const statusEl = document.getElementById("status");
const pairCodeInput = document.getElementById("pairCode");
const pairBtn = document.getElementById("pairBtn");
const keyboardInput = document.getElementById("keyboardInput");
const reconnectBtn = document.getElementById("reconnectBtn");
const touchpad = document.getElementById("touchpad");
const controlsStatus = document.getElementById("controlsStatus");
const cursorSpeedInput = document.getElementById("cursorSpeed");
const cursorSpeedValue = document.getElementById("cursorSpeedValue");

const wsUrl = `ws://${window.location.hostname}:8765`;

function uuidv4() {
  if (crypto && crypto.randomUUID) {
    return crypto.randomUUID();
  }

  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;

  const hex = Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0"));
  return `${hex.slice(0, 4).join("")}-${hex.slice(4, 6).join("")}-${hex
    .slice(6, 8)
    .join("")}-${hex.slice(8, 10).join("")}-${hex.slice(10, 16).join("")}`;
}

const deviceId = localStorage.getItem("device_id") || uuidv4();
localStorage.setItem("device_id", deviceId);

const CURSOR_SPEED_KEY = "cursor_speed";
const DEFAULT_CURSOR_SPEED = 2.0;
const MIN_CURSOR_SPEED = 0.5;
const MAX_CURSOR_SPEED = 4.0;

function readCursorSpeed() {
  const stored = Number.parseFloat(localStorage.getItem(CURSOR_SPEED_KEY) || "");
  if (!Number.isFinite(stored)) {
    return DEFAULT_CURSOR_SPEED;
  }
  return Math.min(MAX_CURSOR_SPEED, Math.max(MIN_CURSOR_SPEED, stored));
}

let cursorSpeed = readCursorSpeed();

function updateCursorSpeedUi(value) {
  cursorSpeedInput.value = value.toFixed(1);
  cursorSpeedValue.textContent = `${value.toFixed(1)}x`;
}

updateCursorSpeedUi(cursorSpeed);
localStorage.setItem(CURSOR_SPEED_KEY, cursorSpeed.toFixed(1));

let ws;
let paired = false;
let lastSingleTouch = null;
let lastTwoFingerCenter = null;
let pendingTap = false;

function nonce() {
  const bytes = new Uint8Array(16);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join("");
}

function setStatus(text, className) {
  statusEl.textContent = text;
  statusEl.className = `status ${className}`;
}

function setPairedState(nextPaired) {
  paired = nextPaired;
  keyboardInput.disabled = !paired;
  touchpad.classList.toggle("disabled", !paired);
  controlsStatus.textContent = paired
    ? "Controls enabled (paired)"
    : "Controls locked until pairing succeeds";
}

function envelope(type, payload) {
  return {
    protocol_version: "1.0",
    type,
    id: uuidv4(),
    ts: Date.now(),
    nonce: nonce(),
    device_id: deviceId,
    payload,
  };
}

function send(type, payload) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    return;
  }

  if ((type.startsWith("input.") || type.startsWith("system.")) && !paired) {
    setStatus("Pair first to use controls", "disconnected");
    return;
  }

  ws.send(JSON.stringify(envelope(type, payload)));
}

function sendClick(button = "left") {
  send("input.mouse_click", { button, action: "down" });
  send("input.mouse_click", { button, action: "up" });
}

function connect() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  setPairedState(false);
  setStatus(`Connecting to ${wsUrl}...`, "connecting");
  ws = new WebSocket(wsUrl);

  ws.onopen = () => setStatus(`Connected (${deviceId})`, "connected");
  ws.onclose = () => {
    setPairedState(false);
    setStatus("Disconnected", "disconnected");
  };
  ws.onerror = () => setStatus("WebSocket error", "disconnected");
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      if (msg.type === "pair.result") {
        if (msg.payload?.success) {
          setPairedState(true);
          setStatus("Pairing result: success", "connected");
          return;
        }

        if (msg.payload?.reason) {
          setStatus(`Pairing result: ${msg.payload.reason}`, "disconnected");
        }
      }
    } catch {
      // ignore non-JSON server messages
    }
  };
}

reconnectBtn.addEventListener("click", () => {
  if (ws) {
    ws.close();
  }
  connect();
});

pairBtn.addEventListener("click", () => {
  const code = pairCodeInput.value.trim();
  if (!/^\d{6}$/.test(code)) {
    setStatus("Enter a valid 6-digit pairing code", "disconnected");
    return;
  }

  send("pair.request", { device_name: "Phone Web UI", public_key: "web-ui" });
  send("pair.confirm", { code, accepted: true });
});

keyboardInput.addEventListener("keydown", (event) => {
  if (!paired) {
    return;
  }

  if (event.key.length === 1 || event.key === "Enter" || event.key === "Backspace" || event.key === "Tab") {
    send("input.keypress", { key: event.key, action: "down" });
    send("input.keypress", { key: event.key, action: "up" });
  }
});

keyboardInput.addEventListener("input", (event) => {
  if (!paired) {
    return;
  }

  const value = event.target.value;
  const last = value.at(-1);
  if (last) {
    send("input.keypress", { key: last, action: "down" });
    send("input.keypress", { key: last, action: "up" });
  }

  if (value.length > 32) {
    event.target.value = "";
  }
});

touchpad.addEventListener("touchstart", (event) => {
  if (!paired) {
    return;
  }

  if (event.touches.length === 1) {
    const touch = event.touches[0];
    lastSingleTouch = { x: touch.clientX, y: touch.clientY };
    pendingTap = true;
    lastTwoFingerCenter = null;
    return;
  }

  if (event.touches.length === 2) {
    const first = event.touches[0];
    const second = event.touches[1];
    lastTwoFingerCenter = {
      x: (first.clientX + second.clientX) / 2,
      y: (first.clientY + second.clientY) / 2,
    };
    lastSingleTouch = null;
    pendingTap = false;
  }
});

touchpad.addEventListener("touchmove", (event) => {
  if (!paired) {
    return;
  }

  event.preventDefault();

  if (event.touches.length === 1 && lastSingleTouch) {
    const touch = event.touches[0];
    const dx = touch.clientX - lastSingleTouch.x;
    const dy = touch.clientY - lastSingleTouch.y;
    if (Math.abs(dx) > 1 || Math.abs(dy) > 1) {
      pendingTap = false;
      send("input.mouse_move", { dx: dx * cursorSpeed, dy: dy * cursorSpeed });
    }
    lastSingleTouch = { x: touch.clientX, y: touch.clientY };
    return;
  }

  if (event.touches.length === 2 && lastTwoFingerCenter) {
    const first = event.touches[0];
    const second = event.touches[1];
    const centerY = (first.clientY + second.clientY) / 2;
    const deltaY = centerY - lastTwoFingerCenter.y;
    if (Math.abs(deltaY) > 1) {
      send("input.mouse_scroll", { delta_x: 0, delta_y: -deltaY * 2 });
    }
    lastTwoFingerCenter = {
      x: (first.clientX + second.clientX) / 2,
      y: centerY,
    };
    pendingTap = false;
  }
});

touchpad.addEventListener("touchend", () => {
  if (!paired) {
    return;
  }

  if (pendingTap) {
    sendClick("left");
  }
  pendingTap = false;
  lastSingleTouch = null;
  lastTwoFingerCenter = null;
});

cursorSpeedInput.addEventListener("input", (event) => {
  const nextSpeed = Number.parseFloat(event.target.value);
  if (!Number.isFinite(nextSpeed)) {
    return;
  }

  cursorSpeed = Math.min(MAX_CURSOR_SPEED, Math.max(MIN_CURSOR_SPEED, nextSpeed));
  updateCursorSpeedUi(cursorSpeed);
  localStorage.setItem(CURSOR_SPEED_KEY, cursorSpeed.toFixed(1));
});

setPairedState(false);
connect();
