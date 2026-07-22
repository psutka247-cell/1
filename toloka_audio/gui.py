import tkinter as tk
from tkinter import ttk
from typing import Callable

from .config import ConfigStore, ScreenRegion


class TolokaAutomationGui(tk.Tk):
    """Russian dark-themed GUI shell with horizontal resizing and region selection."""

    def __init__(self, config: ConfigStore, on_region_selected: Callable[[ScreenRegion], None]) -> None:
        super().__init__()
        self.config = config
        self.on_region_selected = on_region_selected
        self.title("Автоматизация Toloka")
        self.geometry("720x420")
        self.minsize(560, 420)
        self.resizable(True, False)
        self.configure(bg="#1f1f1f")
        self._setup_style()
        ttk.Label(self, text="Состояние: ожидание", style="Dark.TLabel").pack(anchor="w", padx=16, pady=16)
        ttk.Button(self, text="Выбрать область", command=self.select_region, style="Dark.TButton").pack(anchor="w", padx=16)
        ttk.Label(self, text="Пользователь проверяет текст и подтверждает одним Enter.", style="Dark.TLabel").pack(anchor="w", padx=16, pady=16)

    def _setup_style(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("Dark.TLabel", background="#1f1f1f", foreground="#eeeeee")
        style.configure("Dark.TButton", background="#333333", foreground="#ffffff")

    def select_region(self) -> None:
        selector = RegionSelector(self)
        self.wait_window(selector)
        if selector.region:
            self.config.save_region(selector.region)
            self.on_region_selected(selector.region)


class RegionSelector(tk.Toplevel):
    def __init__(self, parent: tk.Tk) -> None:
        super().__init__(parent)
        self.attributes("-fullscreen", True)
        self.attributes("-alpha", 0.3)
        self.configure(bg="black")
        self.region: ScreenRegion | None = None
        self._start: tuple[int, int] | None = None
        self.canvas = tk.Canvas(self, cursor="cross", bg="black")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<ButtonPress-1>", self._press)
        self.canvas.bind("<ButtonRelease-1>", self._release)

    def _press(self, event) -> None:
        self._start = (event.x_root, event.y_root)

    def _release(self, event) -> None:
        if not self._start:
            self.destroy()
            return
        x1, y1 = self._start
        x2, y2 = event.x_root, event.y_root
        left, top = min(x1, x2), min(y1, y2)
        self.region = ScreenRegion(left=left, top=top, width=abs(x2 - x1), height=abs(y2 - y1))
        self.destroy()
