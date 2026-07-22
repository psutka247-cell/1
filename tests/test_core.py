import numpy as np

from toloka_audio.classification import Category, classify_transcript
from toloka_audio.postprocessing import TextPostProcessor
from toloka_audio.states import PlayerState
from toloka_audio.watcher import TemplateDetector


def test_laughter_without_speech_is_category_4():
    assert classify_transcript("ха-ха", has_laughter=True, has_distinguishable_speech=False) == Category.NO_SPEECH


def test_short_yes_is_not_category_3():
    assert classify_transcript("да", has_laughter=False, has_distinguishable_speech=True) != Category.UNINTELLIGIBLE


def test_postprocessor_replaces_words_without_meaning_change():
    assert TextPostProcessor().process("еще щас") == "ещё сейчас"


def test_detector_priority_with_synthetic_templates(tmp_path):
    for name, value in (("loading.png", 80), ("play.png", 120), ("pause.png", 160)):
        import cv2
        cv2.imwrite(str(tmp_path / name), np.full((5, 5), value, dtype=np.uint8))
    detector = TemplateDetector(tmp_path, threshold=0.99)
    image = np.full((20, 20, 3), 80, dtype=np.uint8)
    assert detector.detect(image) == PlayerState.LOADING
