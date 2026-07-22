from enum import IntEnum


class Category(IntEnum):
    SPEECH = 1
    EXISTING_2 = 2
    UNINTELLIGIBLE = 3
    NO_SPEECH = 4


def classify_transcript(text: str, has_laughter: bool = False, has_distinguishable_speech: bool = True,
                        existing_classifier=None) -> int:
    """Apply updated laughter/unintelligible rules while preserving existing classifier hook."""
    normalized = (text or "").strip().lower()
    if has_laughter and not has_distinguishable_speech:
        return Category.NO_SPEECH
    if existing_classifier is not None:
        return existing_classifier(text)
    if not has_distinguishable_speech:
        return Category.UNINTELLIGIBLE
    if normalized in {"", "[неразборчиво]", "неразборчиво"}:
        return Category.UNINTELLIGIBLE
    return Category.SPEECH
