import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScreenRegion:
    left: int
    top: int
    width: int
    height: int

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Ширина и высота области должны быть положительными")


class ConfigStore:
    def __init__(self, path: str | Path = "config.json") -> None:
        self.path = Path(path)

    def load_region(self) -> Optional[ScreenRegion]:
        if not self.path.exists():
            return None
        data = json.loads(self.path.read_text(encoding="utf-8"))
        region = data.get("toloka_search_region")
        if not region:
            return None
        result = ScreenRegion(**region)
        result.validate()
        log.info("Загружена область поиска Toloka: %s", result)
        return result

    def save_region(self, region: ScreenRegion) -> None:
        region.validate()
        data = {}
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))
        data["toloka_search_region"] = asdict(region)
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        log.info("Сохранена область поиска Toloka: %s", region)
