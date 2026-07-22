import logging
import threading
import time
from pathlib import Path
from typing import Callable, Optional

import cv2
import mss
import numpy as np

from .config import ScreenRegion
from .states import AutomationMode, PlayerState

log = logging.getLogger(__name__)
StateCallback = Callable[[PlayerState, PlayerState], None]


class TemplateDetector:
    """Detects Toloka player state with preloaded OpenCV templates only."""

    def __init__(self, templates_dir: str | Path = "templates", threshold: float = 0.85) -> None:
        self.templates_dir = Path(templates_dir)
        self.threshold = threshold
        self.templates = {
            PlayerState.LOADING: self._load_template("loading.png"),
            PlayerState.PLAY: self._load_template("play.png"),
            PlayerState.PAUSE: self._load_template("pause.png"),
        }
        log.info("Шаблоны Toloka загружены из %s", self.templates_dir)

    def _load_template(self, name: str) -> np.ndarray:
        path = self.templates_dir / name
        template = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        if template is None:
            raise FileNotFoundError(f"Не удалось загрузить шаблон {path}")
        return template

    def detect(self, image_bgr: np.ndarray) -> PlayerState:
        gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)
        for state in (PlayerState.LOADING, PlayerState.PLAY, PlayerState.PAUSE):
            if self._matches(gray, self.templates[state]):
                return state
        return PlayerState.UNKNOWN

    def _matches(self, gray: np.ndarray, template: np.ndarray) -> bool:
        if gray.shape[0] < template.shape[0] or gray.shape[1] < template.shape[1]:
            return False
        result = cv2.matchTemplate(gray, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, _ = cv2.minMaxLoc(result)
        return max_val >= self.threshold


class TolokaPlayerWatcher:
    """Watches selected screen region and fires once on each new PLAY -> PAUSE transition."""

    def __init__(self, detector: TemplateDetector, region: ScreenRegion, on_play_to_pause: StateCallback,
                 interval_seconds: float = 0.5) -> None:
        self.detector = detector
        self.region = region
        self.on_play_to_pause = on_play_to_pause
        self.interval_seconds = interval_seconds
        self.mode = AutomationMode.RUNNING
        self._last_state = PlayerState.UNKNOWN
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def start(self, synchronize: bool = True) -> None:
        with self._lock:
            if self._thread and self._thread.is_alive():
                return
            self._stop_event.clear()
            if synchronize:
                self._last_state = PlayerState.UNKNOWN
                log.info("Синхронизация Watcher с текущим состоянием плеера перед возобновлением")
            self._thread = threading.Thread(target=self._run, name="toloka-player-watcher", daemon=True)
            self._thread.start()
            log.info("Watcher запущен")

    def stop(self) -> None:
        self._stop_event.set()
        thread = self._thread
        if thread and thread.is_alive():
            thread.join(timeout=2)
        log.info("Watcher остановлен: захват экрана и поиск шаблонов не выполняются")

    def enter_wait_user_confirmation(self) -> None:
        self.mode = AutomationMode.WAIT_USER_CONFIRMATION
        log.info("Переход в WAIT_USER_CONFIRMATION")
        self.stop()

    def confirm_user_enter(self) -> None:
        log.info("Подтверждение пользователем получено")
        self.mode = AutomationMode.RUNNING
        self.start(synchronize=True)

    def _run(self) -> None:
        monitor = {"left": self.region.left, "top": self.region.top, "width": self.region.width, "height": self.region.height}
        with mss.mss() as sct:
            while not self._stop_event.is_set() and self.mode == AutomationMode.RUNNING:
                frame = np.asarray(sct.grab(monitor))[:, :, :3]
                state = self.detector.detect(frame)
                if state != self._last_state:
                    log.info("Состояние Toloka изменилось: %s -> %s", self._last_state.value, state.value)
                    previous = self._last_state
                    self._last_state = state
                    if previous == PlayerState.PLAY and state == PlayerState.PAUSE:
                        log.info("Обнаружен новый переход PLAY -> PAUSE, запуск обработки разрешён")
                        self.on_play_to_pause(previous, state)
                time.sleep(self.interval_seconds)
