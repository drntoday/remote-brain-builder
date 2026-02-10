package com.remotebrain.hid

import android.Manifest
import android.bluetooth.BluetoothAdapter
import android.bluetooth.BluetoothDevice
import android.bluetooth.BluetoothHidDevice
import android.bluetooth.BluetoothHidDeviceAppQosSettings
import android.bluetooth.BluetoothHidDeviceAppSdpSettings
import android.bluetooth.BluetoothProfile
import android.content.Context
import android.content.pm.PackageManager
import android.os.Build
import android.util.Log
import androidx.core.content.ContextCompat
import java.util.concurrent.Executor

class HidDeviceManager(
    private val context: Context,
    private val listener: Listener
) {
    interface Listener {
        fun onStatusChanged(text: String)
        fun onDeviceConnected(connected: Boolean)
    }

    private var bluetoothHidDevice: BluetoothHidDevice? = null
    private var connectedDevice: BluetoothDevice? = null

    private val callback = object : BluetoothHidDevice.Callback() {
        override fun onAppStatusChanged(pluggedDevice: BluetoothDevice?, registered: Boolean) {
            listener.onStatusChanged(if (registered) "HID profile registered" else "HID profile not registered")
        }

        override fun onConnectionStateChanged(device: BluetoothDevice, state: Int) {
            when (state) {
                BluetoothProfile.STATE_CONNECTED -> {
                    connectedDevice = device
                    listener.onStatusChanged("Connected to ${device.name ?: device.address}")
                    listener.onDeviceConnected(true)
                }

                BluetoothProfile.STATE_CONNECTING -> listener.onStatusChanged("Connecting to ${device.name ?: device.address}...")
                else -> {
                    connectedDevice = null
                    listener.onStatusChanged("Not connected")
                    listener.onDeviceConnected(false)
                }
            }
        }
    }

    private val profileListener = object : BluetoothProfile.ServiceListener {
        override fun onServiceConnected(profile: Int, proxy: BluetoothProfile?) {
            bluetoothHidDevice = proxy as? BluetoothHidDevice
            listener.onStatusChanged("Bluetooth HID service ready")
        }

        override fun onServiceDisconnected(profile: Int) {
            bluetoothHidDevice = null
            connectedDevice = null
            listener.onStatusChanged("Bluetooth HID service disconnected")
            listener.onDeviceConnected(false)
        }
    }

    fun bindService() {
        val adapter = BluetoothAdapter.getDefaultAdapter() ?: run {
            listener.onStatusChanged("Bluetooth not supported")
            return
        }
        adapter.getProfileProxy(context, profileListener, BluetoothProfile.HID_DEVICE)
    }

    fun registerAndConnect() {
        val adapter = BluetoothAdapter.getDefaultAdapter() ?: return
        if (!adapter.isEnabled) {
            listener.onStatusChanged("Enable Bluetooth first")
            return
        }

        if (!hasConnectPermission()) {
            listener.onStatusChanged("Bluetooth permissions missing")
            return
        }

        val hid = bluetoothHidDevice
        if (hid == null) {
            listener.onStatusChanged("HID service not ready yet")
            return
        }

        val sdp = BluetoothHidDeviceAppSdpSettings(
            "RemoteBrain HID",
            "RemoteBrain phone mouse/keyboard",
            "RemoteBrain",
            BluetoothHidDevice.SUBCLASS1_COMBO,
            HID_REPORT_DESCRIPTOR
        )

        val executor = Executor { it.run() }
        val registerResult = hid.registerApp(sdp, null as BluetoothHidDeviceAppQosSettings?, null, executor, callback)
        if (!registerResult) {
            listener.onStatusChanged("Failed to register HID app")
            return
        }

        val target = adapter.bondedDevices?.firstOrNull()
        if (target == null) {
            listener.onStatusChanged("Pair with a host first (Windows, etc.)")
            return
        }

        hid.connect(target)
    }

    fun sendMouseMove(dx: Int, dy: Int) {
        val report = byteArrayOf(
            0x00,
            clampToSignedByte(dx),
            clampToSignedByte(dy),
            0x00
        )
        sendReport(REPORT_ID_MOUSE, report)
    }

    fun sendMouseClickLeft() {
        sendReport(REPORT_ID_MOUSE, byteArrayOf(0x01, 0x00, 0x00, 0x00))
        sendReport(REPORT_ID_MOUSE, byteArrayOf(0x00, 0x00, 0x00, 0x00))
    }

    fun sendScroll(deltaY: Int) {
        val report = byteArrayOf(
            0x00,
            0x00,
            0x00,
            clampToSignedByte(-deltaY)
        )
        sendReport(REPORT_ID_MOUSE, report)
    }

    fun sendText(text: String) {
        text.forEach { c ->
            val keycode = keycodeForChar(c) ?: return@forEach
            sendKeyboardKey(keycode, c.isUpperCase())
        }
    }

    private fun sendKeyboardKey(keycode: Byte, useShift: Boolean) {
        val modifier = if (useShift) 0x02.toByte() else 0x00
        val keyDown = byteArrayOf(modifier, 0x00, keycode, 0x00, 0x00, 0x00, 0x00, 0x00)
        val keyUp = byteArrayOf(0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00)
        sendReport(REPORT_ID_KEYBOARD, keyDown)
        sendReport(REPORT_ID_KEYBOARD, keyUp)
    }

    private fun sendReport(reportId: Int, data: ByteArray) {
        val hid = bluetoothHidDevice
        val device = connectedDevice
        if (hid == null || device == null) {
            listener.onStatusChanged("Not connected")
            return
        }
        val ok = hid.sendReport(device, reportId, data)
        if (!ok) {
            Log.w("HidDeviceManager", "sendReport failed for reportId=$reportId")
        }
    }

    private fun hasConnectPermission(): Boolean {
        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_CONNECT) == PackageManager.PERMISSION_GRANTED &&
                ContextCompat.checkSelfPermission(context, Manifest.permission.BLUETOOTH_SCAN) == PackageManager.PERMISSION_GRANTED
        } else {
            true
        }
    }

    private fun clampToSignedByte(value: Int): Byte {
        return value.coerceIn(-127, 127).toByte()
    }

    private fun keycodeForChar(c: Char): Byte? {
        return when (c.lowercaseChar()) {
            in 'a'..'z' -> (0x04 + (c.lowercaseChar() - 'a')).toByte()
            in '1'..'9' -> (0x1E + (c - '1')).toByte()
            '0' -> 0x27
            ' ' -> 0x2C
            '\n' -> 0x28
            else -> null
        }
    }

    companion object {
        const val REPORT_ID_MOUSE = 1
        const val REPORT_ID_KEYBOARD = 2

        val HID_REPORT_DESCRIPTOR = byteArrayOf(
            0x05, 0x01,
            0x09, 0x02,
            0xA1.toByte(), 0x01,
            0x85.toByte(), REPORT_ID_MOUSE.toByte(),
            0x09, 0x01,
            0xA1.toByte(), 0x00,
            0x05, 0x09,
            0x19, 0x01,
            0x29, 0x03,
            0x15, 0x00,
            0x25, 0x01,
            0x95.toByte(), 0x03,
            0x75, 0x01,
            0x81.toByte(), 0x02,
            0x95.toByte(), 0x01,
            0x75, 0x05,
            0x81.toByte(), 0x01,
            0x05, 0x01,
            0x09, 0x30,
            0x09, 0x31,
            0x09, 0x38,
            0x15, 0x81.toByte(),
            0x25, 0x7F,
            0x75, 0x08,
            0x95.toByte(), 0x03,
            0x81.toByte(), 0x06,
            0xC0.toByte(),
            0xC0.toByte(),

            0x05, 0x01,
            0x09, 0x06,
            0xA1.toByte(), 0x01,
            0x85.toByte(), REPORT_ID_KEYBOARD.toByte(),
            0x05, 0x07,
            0x19, 0xE0.toByte(),
            0x29, 0xE7.toByte(),
            0x15, 0x00,
            0x25, 0x01,
            0x75, 0x01,
            0x95.toByte(), 0x08,
            0x81.toByte(), 0x02,
            0x95.toByte(), 0x01,
            0x75, 0x08,
            0x81.toByte(), 0x01,
            0x95.toByte(), 0x06,
            0x75, 0x08,
            0x15, 0x00,
            0x25, 0x65,
            0x05, 0x07,
            0x19, 0x00,
            0x29, 0x65,
            0x81.toByte(), 0x00,
            0xC0.toByte()
        )
    }
}
