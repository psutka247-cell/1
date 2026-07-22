import re
from dataclasses import dataclass, field
from typing import Callable, Iterable

Rule = Callable[[str], str]


@dataclass
class TextPostProcessor:
    """Rule-based postprocessor for GigaSTT text that preserves meaning."""

    user_replacements: dict[str, str] = field(default_factory=dict)
    asr_fixes: dict[str, str] = field(default_factory=lambda: {
        "щас": "сейчас",
        "чё": "что",
        "че": "что",
        "шо": "что",
    })
    name_forms: dict[str, str] = field(default_factory=lambda: {
        "саш": "Саша",
        "маш": "Маша",
        "димость": "Дима",
    })
    yo_context: dict[str, str] = field(default_factory=lambda: {
        "еще": "ещё",
        "все": "всё",
        "ее": "её",
    })
    extra_rules: list[Rule] = field(default_factory=list)

    def process(self, text: str) -> str:
        result = text.strip()
        for mapping in (self.asr_fixes, self.name_forms, self.yo_context, self.user_replacements):
            result = self._replace_words(result, mapping)
        for rule in self.extra_rules:
            result = rule(result)
        return re.sub(r"\s+", " ", result).strip()

    def add_rule(self, rule: Rule) -> None:
        self.extra_rules.append(rule)

    @staticmethod
    def _replace_words(text: str, replacements: dict[str, str]) -> str:
        for source, target in replacements.items():
            text = re.sub(rf"(?<!\w){re.escape(source)}(?!\w)", target, text, flags=re.IGNORECASE)
        return text
