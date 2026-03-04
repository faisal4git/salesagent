# app/services/stt.py
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from typing import Any, Dict, List, Optional

import speech_recognition as sr
from pydub import AudioSegment


class GoogleWebSpeechSTT:
    """
    STT using SpeechRecognition + Google Web Speech API (unofficial).
    - Converts audio to WAV 16kHz mono
    - Splits into chunks
    - Auto-detects language per chunk (EN, TA, HI, KN)
    """

    # Priority order matters
    LANGUAGE_PRIORITY = [
        "en-IN",
        "ta-IN",
        "hi-IN",
        "kn-IN"
    ]

    def __init__(
        self,
        language: str = "auto",  # ignored now (auto mode)
        chunk_seconds: int = 10,
        energy_threshold: int = 300,
        pause_threshold: float = 1.2,
        dynamic_energy_threshold: bool = True,
    ):
        self.chunk_seconds = chunk_seconds

        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = energy_threshold
        self.recognizer.pause_threshold = pause_threshold
        self.recognizer.dynamic_energy_threshold = dynamic_energy_threshold

    # ---------------------------------------------------------

    def transcribe_upload(self, upload_file) -> Dict[str, Any]:

        with tempfile.TemporaryDirectory() as td:
            raw_path = os.path.join(td, "input_audio")
            with open(raw_path, "wb") as f:
                shutil.copyfileobj(upload_file.file, f)

            wav_path = os.path.join(td, "audio.wav")
            self._ffmpeg_convert_to_wav_16k_mono(raw_path, wav_path)

            return self.transcribe_file(wav_path)

    # ---------------------------------------------------------

    def transcribe_file(self, wav_path: str) -> Dict[str, Any]:

        audio = AudioSegment.from_wav(wav_path)

        chunk_ms = self.chunk_seconds * 1000
        segments: List[Dict[str, Any]] = []
        transcript_parts: List[str] = []
        detected_languages: List[str] = []

        for i, start_ms in enumerate(range(0, len(audio), chunk_ms)):
            end_ms = min(start_ms + chunk_ms, len(audio))
            chunk_audio = audio[start_ms:end_ms]

            chunk_path = os.path.join(
                tempfile.gettempdir(),
                f"gws_{os.getpid()}_{i}.wav"
            )
            chunk_audio.export(chunk_path, format="wav")

            try:
                text, lang = self._transcribe_chunk_auto(chunk_path)

                if text:
                    seg = {
                        "start": round(start_ms / 1000.0, 2),
                        "end": round(end_ms / 1000.0, 2),
                        "text": text.strip(),
                    }
                    segments.append(seg)
                    transcript_parts.append(text.strip())
                    detected_languages.append(lang)

            finally:
                try:
                    os.remove(chunk_path)
                except Exception:
                    pass

        transcript = " ".join(transcript_parts).strip()

        # Determine most frequent language
        final_language = None
        if detected_languages:
            final_language = max(
                set(detected_languages),
                key=detected_languages.count
            )

        meta = {
            "backend": "speech_recognition_google_web_speech",
            "language": final_language,
            "chunk_seconds": self.chunk_seconds,
            "segments_count": len(segments),
            "duration_seconds": round(len(audio) / 1000.0, 2),
        }

        return {
            "segments": segments,
            "transcript": transcript,
            "meta": meta
        }

    # ---------------------------------------------------------

    def _transcribe_chunk_auto(self, wav_chunk_path: str) -> (Optional[str], Optional[str]):

        with sr.AudioFile(wav_chunk_path) as source:
            audio_data = self.recognizer.record(source)

        # Try multiple languages
        for lang in self.LANGUAGE_PRIORITY:
            try:
                text = self.recognizer.recognize_google(
                    audio_data,
                    language=lang
                )

                if text and len(text.strip()) > 2:
                    return text, lang

            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                raise RuntimeError(f"Google Web Speech API error: {e}")

        return None, None

    # ---------------------------------------------------------

    def _ffmpeg_convert_to_wav_16k_mono(self, input_path: str, out_wav_path: str) -> None:

        cmd = [
            "ffmpeg", "-y",
            "-i", input_path,
            "-ac", "1",
            "-ar", "16000",
            "-vn",
            out_wav_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
        except FileNotFoundError:
            raise RuntimeError("ffmpeg not found. Install ffmpeg and add to PATH.")
        except subprocess.CalledProcessError as e:
            err = e.stderr.decode(errors="ignore")
            raise RuntimeError(f"ffmpeg conversion failed: {err[:2000]}")