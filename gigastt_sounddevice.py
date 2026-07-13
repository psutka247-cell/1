"""Record speech with sounddevice and transcribe it with local GigaSTT.

The script intentionally does not use ``sr.Microphone`` because that class
requires PyAudio.  Instead, microphone samples are captured through
``sounddevice``, wrapped into SpeechRecognition's ``AudioData`` container, and
sent to a locally running GigaSTT server. GigaSTT is Russian-only, so the
old Google ``language="en-US"`` option is removed.

Before running this file, start GigaSTT in another terminal::

    gigastt serve
"""

from __future__ import annotations

import io
import wave
from dataclasses import dataclass

import requests
import sounddevice as sd
import speech_recognition as sr


@dataclass(frozen=True)
class RecordConfig:
    """Audio recording settings compatible with GigaSTT."""

    duration_seconds: float = 4.0
    sample_rate: int = 16_000
    channels: int = 1
    dtype: str = "int16"


@dataclass(frozen=True)
class GigaSTTConfig:
    """Local GigaSTT REST API settings."""

    url: str = "http://127.0.0.1:9876/v1/transcribe"
    timeout_seconds: float = 60.0
    punctuation: bool = True
    itn: bool = True
    vad: bool = True


def record_audio(config: RecordConfig = RecordConfig()) -> sr.AudioData:
    """Record microphone input with sounddevice and return SpeechRecognition audio.

    ``sounddevice.rec`` returns a NumPy array.  For ``dtype='int16'`` its byte
    representation is signed 16-bit little-endian PCM, which is exactly what
    ``sr.AudioData`` expects when ``sample_width`` is set to 2 bytes.
    """

    print("Recording for {:.1f} seconds".format(config.duration_seconds))
    frames = int(config.duration_seconds * config.sample_rate)
    recording = sd.rec(
        frames=frames,
        samplerate=config.sample_rate,
        channels=config.channels,
        dtype=config.dtype,
    )
    sd.wait()
    print("Done recording")

    return sr.AudioData(
        frame_data=recording.tobytes(),
        sample_rate=config.sample_rate,
        sample_width=2,
    )


def audio_data_to_wav_bytes(audio: sr.AudioData) -> bytes:
    """Convert SpeechRecognition AudioData to an in-memory WAV file."""

    wav_buffer = io.BytesIO()
    with wave.open(wav_buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(audio.sample_width)
        wav_file.setframerate(audio.sample_rate)
        wav_file.writeframes(audio.frame_data)
    return wav_buffer.getvalue()


def recognize_gigastt(
    audio: sr.AudioData,
    config: GigaSTTConfig = GigaSTTConfig(),
) -> str:
    """Send recorded audio to GigaSTT and return recognized text."""

    params = {
        "format": "json",
        "punctuation": str(config.punctuation).lower(),
        "itn": str(config.itn).lower(),
        "vad": str(config.vad).lower(),
    }
    response = requests.post(
        config.url,
        params=params,
        data=audio_data_to_wav_bytes(audio),
        headers={"Content-Type": "application/octet-stream"},
        timeout=config.timeout_seconds,
    )
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError:
        return response.text.strip()

    for key in ("text", "transcript", "result"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    segments = payload.get("segments")
    if isinstance(segments, list):
        parts = [
            segment.get("text", "").strip()
            for segment in segments
            if isinstance(segment, dict)
        ]
        text = " ".join(part for part in parts if part)
        if text:
            return text

    raise RuntimeError(f"GigaSTT response does not contain recognized text: {payload!r}")


def main() -> None:
    audio = record_audio()

    try:
        print("Recognizing the text with local GigaSTT")
        text = recognize_gigastt(audio)
        print("Decoded Text : {}".format(text))
    except requests.RequestException as exc:
        print(f"GigaSTT request failed: {exc}")
    except Exception as exc:  # keep CLI behavior close to the original example
        print(exc)


if __name__ == "__main__":
    main()
