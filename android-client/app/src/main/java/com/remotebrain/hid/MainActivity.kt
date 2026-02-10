package com.remotebrain.hid

import android.Manifest
import android.os.Build
import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity(), HidDeviceManager.Listener {
    private lateinit var statusText: TextView
    private lateinit var connectButton: Button
    private lateinit var keyboardInput: EditText
    private lateinit var sendButton: Button
    private lateinit var touchpad: TouchpadView

    private lateinit var hidManager: HidDeviceManager

    private val permissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestMultiplePermissions()
    ) {
        val granted = it.values.all { value -> value }
        onStatusChanged(if (granted) "Permissions granted" else "Bluetooth permissions required")
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        statusText = findViewById(R.id.statusText)
        connectButton = findViewById(R.id.registerButton)
        keyboardInput = findViewById(R.id.keyboardInput)
        sendButton = findViewById(R.id.sendButton)
        touchpad = findViewById(R.id.touchpad)

        hidManager = HidDeviceManager(this, this)
        hidManager.bindService()

        connectButton.setOnClickListener {
            ensureBluetoothPermissions()
            hidManager.registerAndConnect()
        }

        sendButton.setOnClickListener {
            val text = keyboardInput.text.toString()
            hidManager.sendText(text)
            keyboardInput.setText("")
        }

        touchpad.listener = object : TouchpadView.Listener {
            override fun onMove(dx: Int, dy: Int) {
                hidManager.sendMouseMove(dx, dy)
            }

            override fun onTap() {
                hidManager.sendMouseClickLeft()
            }

            override fun onTwoFingerScroll(deltaY: Int) {
                hidManager.sendScroll(deltaY)
            }
        }
    }

    private fun ensureBluetoothPermissions() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            permissionLauncher.launch(
                arrayOf(
                    Manifest.permission.BLUETOOTH_CONNECT,
                    Manifest.permission.BLUETOOTH_SCAN
                )
            )
        }
    }

    override fun onStatusChanged(text: String) {
        runOnUiThread { statusText.text = text }
    }

    override fun onDeviceConnected(connected: Boolean) {
        runOnUiThread {
            connectButton.text = if (connected) getString(R.string.connected) else getString(R.string.register_connect)
        }
    }
}
