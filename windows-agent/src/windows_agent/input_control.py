from __future__ import annotations

from dataclasses import dataclass

VALID_BUTTONS = {"left", "right", "middle"}
VALID_ACTIONS = {"down", "up"}
MEDIA_KEY_MAP = {
    "play_pause": "playpause",
    "next": "nexttrack",
    "prev": "prevtrack",
    "vol_up": "volumeup",
    "vol_down": "volumedown",
    "mute": "volumemute",
}


@dataclass(slots=True)
class InputController:
    def _pyautogui(self):
        import pyautogui  # lazy import for test/headless safety

        return pyautogui

    def mouse_move(self, *, dx: float, dy: float) -> None:
        self._pyautogui().moveRel(dx, dy, duration=0)

    def mouse_click(self, *, button: str, action: str) -> None:
        if button not in VALID_BUTTONS or action not in VALID_ACTIONS:
            raise ValueError("Invalid mouse click parameters")
        pyautogui = self._pyautogui()
        if action == "down":
            pyautogui.mouseDown(button=button)
        else:
            pyautogui.mouseUp(button=button)

    def mouse_scroll(self, *, delta_x: float, delta_y: float) -> None:
        pyautogui = self._pyautogui()
        if delta_y:
            pyautogui.scroll(int(delta_y))
        if delta_x:
            pyautogui.hscroll(int(delta_x))

    def keypress(self, *, key: str, action: str) -> None:
        if action not in VALID_ACTIONS:
            raise ValueError("Invalid key action")
        pyautogui = self._pyautogui()
        normalized_key = key.lower()
        if action == "down":
            pyautogui.keyDown(normalized_key)
        else:
            pyautogui.keyUp(normalized_key)

    def system_media(self, *, command: str) -> None:
        if command not in MEDIA_KEY_MAP:
            raise ValueError("Unsupported media command")
        self._pyautogui().press(MEDIA_KEY_MAP[command])
