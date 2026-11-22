# file: voice/tts.py
# Haven TTS engine using Kokoro ONNX for natural-sounding speech

import os
import re
import numpy as np
import soundfile as sf
from io import BytesIO

try:
    from kokoro_onnx import Kokoro
    _KOKORO_AVAILABLE = True
except ImportError:
    _KOKORO_AVAILABLE = False



def expand_temperature_for_speech(text: str) -> str:
    """Haven Agent v1.1 - say the full temperature names out loud.

    Chat can show 60.1°F / 18°C, but Kokoro should say
    "60.1 degrees Fahrenheit" / "18 degrees Celsius",
    not "60.1 degrees F" or "18 degrees C".
    """
    import re
    # 60.1°F / 60.1 °F / 60°F -> 60.1 degrees Fahrenheit
    text = re.sub(r"(\d+(?:\.\d+)?)\s*°\s*F\b", r"\1 degrees Fahrenheit", text)
    text = re.sub(r"(\d+(?:\.\d+)?)\s*°\s*C\b", r"\1 degrees Celsius", text)
    # 64F / 18C after a number, without the degree sign
    text = re.sub(r"(\d+(?:\.\d+)?)\s*Fahrenheit\b", r"\1 degrees Fahrenheit", text)
    # Lone °F / °C with no number, e.g. "high in F" - just say the word
    text = text.replace("°F", " degrees Fahrenheit").replace("°C", " degrees Celsius")
    text = text.replace("°", " degrees ")
    return text

def _even_out_volume(audio, target_rms=0.18):
    """Haven Agent v1.9 - steady voice volume.

    Scale a whole reply so its average loudness (RMS) is the same
    every time, instead of pushing its single loudest sample to full
    volume. Returns float32 audio with peaks kept under 0.98.
    """
    if audio is None or audio.size == 0:
        return audio
    audio = audio.astype(np.float32)
    rms = float(np.sqrt(np.mean(audio * audio)))
    if rms <= 0.0001:
        return audio
    gain = target_rms / rms
    # Do not boost a very quiet reply more than 4x, or cut a very
    # loud reply to less than a quarter - that would sound unnatural.
    gain = max(0.25, min(4.0, gain))
    audio = audio * gain
    peak = float(np.max(np.abs(audio)))
    if peak > 0.98:
        audio = audio * (0.98 / peak)
    return audio


class TTS:
    """Text-to-Speech engine using Kokoro ONNX."""

    def __init__(self, model_path: str = None, voices_path: str = None, voice: str = "af_heart"):
        self.loaded = False
        self.voice_name = voice
        self.kokoro = None

        if not _KOKORO_AVAILABLE:
            print("[TTS] kokoro-onnx not installed.")
            return

        # Default paths — Kokoro looks for models in its package data by default
        try:
            self.kokoro = Kokoro(model_path=model_path, voices_path=voices_path)
            self.loaded = True
            print(f"[TTS] Kokoro TTS loaded — default voice: {self.voice_name}")
        except Exception as e:
            print(f"[TTS] Failed to load Kokoro: {e}")
            self.loaded = False

    def get_available_voices(self) -> list:
        """Return list of available voice names."""
        if not self.loaded or self.kokoro is None:
            return []
        try:
            voices = self.kokoro.get_voices()
            return list(voices)
        except Exception:
            return []

    def set_voice(self, voice_name: str) -> bool:
        """Switch to a different voice."""
        if not self.loaded:
            return False
        available = self.get_available_voices()
        if voice_name in available:
            self.voice_name = voice_name
            print(f"[TTS] Voice changed to: {voice_name}")
            return True
        print(f"[TTS] Voice '{voice_name}' not available.")
        return False

    def generate(self, text: str, speed: float = 1.0) -> bytes:
        """
        Generate speech audio from text.
        Returns WAV audio as bytes, or empty bytes on failure.
        """
        if not self.loaded or not text:
            return b""

        # Haven Agent v1 fix: never speak brackets or stars out loud.
        # This is a safety net - repository.py already cleans the reply,
        # but if anything slips through, TTS cleans it again here.
        text = re.sub(r"\*\*([^*]{1,200})\*\*", r"\1", text)
        text = re.sub(r"\[\[[^\]]*\]\]", "", text)
        text = re.sub(r"\[[^\]\n]{1,120}\]", "", text)
        text = re.sub(r"\*[^*\n]{1,120}\*", "", text)
        text = text.replace("[", "").replace("]", "").replace("*", "").strip()
        # Say temperature units in full, so voice does not read "C" / "F" as letters
        text = expand_temperature_for_speech(text)
        if not text:
            return b""

        try:
            # Kokoro.create() returns (audio_array, sample_rate)
            audio_array, sample_rate = self.kokoro.create(text, voice=self.voice_name, speed=speed)

            if audio_array is None or audio_array.size == 0:
                return b""

            # Haven Agent v1.9: even out the volume.
            # Old code divided by the loudest single sample, so one
            # loud word made a whole reply quiet and an even reply
            # came out loud. Now the whole reply is scaled to the
            # same average loudness (RMS) every time.
            full_audio = _even_out_volume(audio_array)

            # Write to WAV bytes
            buffer = BytesIO()
            sf.write(buffer, full_audio, sample_rate, format="WAV", subtype="PCM_16")
            return buffer.getvalue()

        except Exception as e:
            print(f"[TTS] Generation error: {e}")
            return b""

    def generate_to_file(self, text: str, output_path: str, speed: float = 1.0) -> bool:
        """Generate speech and save to a WAV file."""
        audio_bytes = self.generate(text, speed)
        if audio_bytes:
            with open(output_path, "wb") as f:
                f.write(audio_bytes)
            print(f"[TTS] Saved audio to: {output_path}")
            return True
        return False
