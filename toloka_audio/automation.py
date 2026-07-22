import logging
from typing import Protocol

from .postprocessing import TextPostProcessor
from .states import AutomationMode

log = logging.getLogger(__name__)


class TolokaDriver(Protocol):
    def select_category(self, category: int) -> None: ...
    def press_enter_once(self) -> None: ...
    def wait_for_transcription_field(self) -> None: ...
    def insert_text(self, text: str) -> None: ...
    def finish_current_task(self) -> None: ...


class CategoryOneFlow:
    def __init__(self, driver: TolokaDriver, postprocessor: TextPostProcessor) -> None:
        self.driver = driver
        self.postprocessor = postprocessor
        self.mode = AutomationMode.RUNNING

    def handle_recognition_result(self, recognized_text: str) -> str:
        log.info("Запуск обработки результата распознавания для категории 1")
        text = self.postprocessor.process(recognized_text)
        self.driver.select_category(1)
        self.driver.press_enter_once()
        self.driver.wait_for_transcription_field()
        self.driver.insert_text(text)
        self.mode = AutomationMode.WAIT_USER_CONFIRMATION
        log.info("WAIT_USER_CONFIRMATION: автоматические действия в Toloka запрещены")
        return text

    def user_confirmed(self) -> None:
        log.info("Пользователь подтвердил текст одним Enter; завершаем текущее задание")
        self.driver.finish_current_task()
        self.mode = AutomationMode.RUNNING
