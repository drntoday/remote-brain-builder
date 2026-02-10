package com.remotebrain.hid

import android.content.Context
import android.graphics.Color
import android.util.AttributeSet
import android.view.MotionEvent
import android.view.View
import kotlin.math.abs

class TouchpadView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null
) : View(context, attrs) {

    interface Listener {
        fun onMove(dx: Int, dy: Int)
        fun onTap()
        fun onTwoFingerScroll(deltaY: Int)
    }

    var listener: Listener? = null

    private var lastX = 0f
    private var lastY = 0f
    private var downX = 0f
    private var downY = 0f
    private var downAt = 0L

    init {
        setBackgroundColor(Color.parseColor("#1F1F1F"))
    }

    override fun onTouchEvent(event: MotionEvent): Boolean {
        when (event.actionMasked) {
            MotionEvent.ACTION_DOWN -> {
                downX = event.x
                downY = event.y
                lastX = event.x
                lastY = event.y
                downAt = event.eventTime
            }

            MotionEvent.ACTION_MOVE -> {
                if (event.pointerCount >= 2) {
                    val avgY = (event.getY(0) + event.getY(1)) / 2f
                    val deltaY = (avgY - lastY).toInt()
                    if (deltaY != 0) {
                        listener?.onTwoFingerScroll(deltaY / 2)
                    }
                    lastY = avgY
                } else {
                    val dx = (event.x - lastX).toInt()
                    val dy = (event.y - lastY).toInt()
                    if (dx != 0 || dy != 0) {
                        listener?.onMove(dx, dy)
                    }
                    lastX = event.x
                    lastY = event.y
                }
            }

            MotionEvent.ACTION_POINTER_DOWN -> {
                if (event.pointerCount >= 2) {
                    lastY = (event.getY(0) + event.getY(1)) / 2f
                }
            }

            MotionEvent.ACTION_UP -> {
                val dt = event.eventTime - downAt
                val moved = abs(event.x - downX) + abs(event.y - downY)
                if (dt < 180 && moved < 25f) {
                    listener?.onTap()
                }
            }
        }
        return true
    }
}
