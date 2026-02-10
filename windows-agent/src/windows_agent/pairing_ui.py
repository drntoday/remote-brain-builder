from __future__ import annotations

import threading
import tkinter as tk


class PairingCodeWindow:
    def __init__(self, code: str) -> None:
        self.code = code
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        def run() -> None:
            root = tk.Tk()
            root.title("Remote Brain Builder Pairing")
            root.geometry("340x140")
            tk.Label(root, text="Pairing Code", font=("Segoe UI", 14)).pack(pady=6)
            tk.Label(root, text=self.code, font=("Consolas", 34, "bold")).pack(pady=3)
            tk.Label(root, text="Enter this code in your controller app.").pack(pady=3)
            root.mainloop()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()
