const logEl = document.getElementById("log");
const wsUrlInput = document.getElementById("wsUrl");
const pairCodeInput = document.getElementById("pairCode");
const keyInput = document.getElementById("keyInput");
const touchpad = document.getElementById("touchpad");

const savedWsUrl = localStorage.getItem("ws_url");
wsUrlInput.value = savedWsUrl || `ws://${location.hostname}:8765`;

const deviceId = localStorage.getItem("device_id") || crypto.randomUUID();
localStorage.setItem("device_id", deviceId);

let ws = null;
let lastTouch = null;

function setLog(text) {
  logEl.textContent = text;
}

function message(type, payload) {
  return {
    protocol_version: "1.0",
    type,
    id: crypto.randomUUID(),
    ts: Date.now(),
    nonce: Math.random().toString(16).slice(2) + Math.random().toString(16).slice(2),
    device_id: deviceId,
    payload,
  };
}

function send(type, payload) {
  if (!ws || ws.readyState !== WebSocket.OPEN) {
    setLog("WebSocket not connected");
    return;
  }
  ws.send(JSON.stringify(message(type, payload)));
}

document.getElementById("connectBtn").addEventListener("click", () => {
  const url = wsUrlInput.value.trim();
  localStorage.setItem("ws_url", url);
  ws = new WebSocket(url);

  ws.onopen = () => setLog(`Connected as ${deviceId}`);
  ws.onclose = () => setLog("Disconnected");
  ws.onerror = () => setLog("WebSocket error");
  ws.onmessage = (event) => {
    try {
      const msg = JSON.parse(event.data);
      setLog(`${msg.type}: ${msg.payload?.reason || (msg.payload?.success ? "ok" : "")}`);
    } catch {
      setLog("Received non-JSON response");
    }
  };
});

document.getElementById("pairBtn").addEventListener("click", () => {
  send("pair.request", { device_name: "Phone Web UI", public_key: "web-ui" });
  const code = pairCodeInput.value.trim();
  if (/^\d{6}$/.test(code)) {
    send("pair.confirm", { code, accepted: true });
  } else {
    setLog("Enter a valid 6-digit pairing code");
  }
});

document.querySelectorAll("[data-click]").forEach((button) => {
  button.addEventListener("click", () => {
    const btn = button.dataset.click;
    send("input.mouse_click", { button: btn, action: "down" });
    send("input.mouse_click", { button: btn, action: "up" });
  });
});

document.getElementById("scrollUp").addEventListener("click", () => {
  send("input.mouse_scroll", { delta_x: 0, delta_y: 100 });
});

document.getElementById("scrollDown").addEventListener("click", () => {
  send("input.mouse_scroll", { delta_x: 0, delta_y: -100 });
});

document.getElementById("sendKey").addEventListener("click", () => {
  const key = keyInput.value.trim();
  if (!key) {
    return;
  }
  send("input.keypress", { key, action: "down" });
  send("input.keypress", { key, action: "up" });
});

touchpad.addEventListener("touchstart", (event) => {
  if (event.touches.length !== 1) {
    return;
  }
  const touch = event.touches[0];
  lastTouch = { x: touch.clientX, y: touch.clientY };
});

touchpad.addEventListener("touchmove", (event) => {
  event.preventDefault();
  if (event.touches.length !== 1 || !lastTouch) {
    return;
  }

  const touch = event.touches[0];
  const dx = touch.clientX - lastTouch.x;
  const dy = touch.clientY - lastTouch.y;
  lastTouch = { x: touch.clientX, y: touch.clientY };

  send("input.mouse_move", { dx, dy });
});

touchpad.addEventListener("touchend", () => {
  lastTouch = null;
});
