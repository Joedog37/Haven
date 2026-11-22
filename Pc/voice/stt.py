# file: voice/stt.py
# Haven STT engine using Vosk for speech recognition

import os
import json
import wave
import struct
from io import BytesIO

try:
    import vosk
    _VOSK_AVAILABLE = True
except ImportError:
    _VOSK_AVAILABLE = False


class STT:
    """Speech-to-Text engine using Vosk."""

    def __init__(self, model_path: str = None, sample_rate: float = 16000.0):
        self.loaded = False
        self.sample_rate = sample_rate
        self.recognizer = None

        if not _VOSK_AVAILABLE:
            print("[STT] vosk not installed.")
            return

        # Find the Vosk model
        if model_path is None:
            # Look for a model in common locations
            possible_paths = [
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "Model", "vosk-model-small-en-us-0.15"),
                os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "vosk-model-small-en-us-0.15"),
            ]
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break

        if model_path is None:
            print("[STT] Vosk model not found. Place 'vosk-model-small-en-us-0.15' in the Model/ folder.")
            return

        try:
            model = vosk.Model(model_path)
            self.recognizer = vosk.KaldiRecognizer(model, self.sample_rate)
            self.loaded = True
            print(f"[STT] Vosk STT loaded — model: {model_path}")
        except Exception as e:
            print(f"[STT] Failed to load Vosk model: {e}")
            self.loaded = False

    def _convert_to_wav(self, audio_data: bytes) -> bytes:
        """
        Convert raw audio bytes to WAV format at 16kHz mono 16-bit.
        Assumes input is 16-bit PCM.
        """
        buffer = BytesIO()
        with wave.open(buffer, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)
        return buffer.getvalue()

    def recognize(self, audio_data: bytes) -> str:
        """
        Recognize speech from audio bytes.
        Returns the recognized text or empty string on failure.
        """
        if not self.loaded or not audio_data:
            return ""

        try:
            # Try to accept the audio data
            # If it's already WAV, use it directly; otherwise convert
            wav_data = audio_data
            if not audio_data.startswith(b"RIFF"):
                wav_data = self._convert_to_wav(audio_data)

            if self.recognizer.AcceptWaveform(wav_data):
                result = self.recognizer.Result()
                try:
                    data = json.loads(result)
                    return data.get("text", "")
                except json.JSONDecodeError:
                    return result
            else:
                # Partial result
                partial = self.recognizer.PartialResult()
                try:
                    data = json.loads(partial)
                    return data.get("partial", "")
                except json.JSONDecodeError:
                    return ""
        except Exception as e:
            print(f"[STT] Recognition error: {e}")
            return ""

    def recognize_from_file(self, file_path: str) -> str:
        """Recognize speech from a WAV file."""
        if not self.loaded or not os.path.exists(file_path):
            return ""

        try:
            with open(file_path, "rb") as f:
                audio_data = f.read()
            return self.recognize(audio_data)
        except Exception as e:
            print(f"[STT] File recognition error: {e}")
            return ""
