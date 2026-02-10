# How to run Bluetooth HID Android client (BT-HID MVP)

## 1) Pair Android phone with Windows over Bluetooth
1. On Windows, open **Settings → Bluetooth & devices** and enable Bluetooth.
2. Click **Add device → Bluetooth**.
3. On Android, open Bluetooth settings and make the phone discoverable if needed.
4. Pair the phone with the Windows machine and confirm pairing codes on both sides.
5. Keep the device bonded (paired) before launching the HID connect flow.

> The app currently connects to the **first bonded device** on the phone. If multiple hosts are paired, unpair unused devices for predictable behavior.

## 2) Run app from Android Studio
1. Open Android Studio and choose **Open**.
2. Select the `android-client/` folder from this repository.
3. Let Gradle sync finish.
4. Connect a physical Android device (API 28+ required, Bluetooth hardware required).
5. Run the `app` configuration.
6. In app:
   - Tap **Register / Connect HID**.
   - Grant Bluetooth permissions when prompted.
   - Confirm connection status changes to connected.

## 3) Use controls
- **Touchpad drag**: sends relative mouse movement.
- **Tap touchpad**: sends left click.
- **Two-finger drag**: sends mouse wheel scroll.
- **Keyboard input field**: type text and tap **Send keyboard input**.

## 4) Common permission and pairing issues
- **No permission dialog appears / connect fails on Android 12+**:
  - Ensure app has `BLUETOOTH_CONNECT` and `BLUETOOTH_SCAN` in system app permissions.
  - Revoke and re-grant permissions from app settings if needed.
- **Status shows HID service not ready**:
  - Wait a moment after app startup; HID profile proxy binding is asynchronous.
- **Status shows pair first**:
  - Pair phone with Windows in system Bluetooth settings before registering/connecting.
- **No pointer movement on Windows**:
  - Confirm Windows still shows the phone as connected Bluetooth input device.
  - Retry by toggling Bluetooth off/on and reconnecting.
