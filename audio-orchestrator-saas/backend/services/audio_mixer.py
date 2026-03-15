"""Audio synthesis and mixing utility for layered scene export."""
from __future__ import annotations

import math
import shutil
import struct
import subprocess
import wave
from pathlib import Path
from random import Random

from backend.models.audio_request import SceneLayer


class AudioMixer:
    """Mixes synthetic layer signals and exports wav/mp3/ogg output."""

    def __init__(self, sample_rate: int = 22050) -> None:
        self.sample_rate = sample_rate
        self._rng = Random(42)

    def mix(self, layers: list[SceneLayer], output_path: Path, output_format: str) -> Path:
        if not layers:
            raise ValueError("Cannot mix an empty layer list")

        max_duration = max(layer.duration_seconds for layer in layers)
        total_samples = int(max_duration * self.sample_rate)
        mixed = [0.0 for _ in range(total_samples)]

        for layer in layers:
            signal = self._synthesize_layer(layer, total_samples)
            for i in range(total_samples):
                mixed[i] += signal[i] * layer.volume

        peak = max(abs(value) for value in mixed) or 1.0
        normalized = [max(-1.0, min(1.0, value / peak * 0.9)) for value in mixed]
        pcm_bytes = b"".join(struct.pack("<h", int(sample * 32767)) for sample in normalized)

        wav_path = output_path.with_suffix(".wav")
        self._write_wav(wav_path, pcm_bytes)
        if output_format == "wav":
            return wav_path

        converted = output_path.with_suffix(f".{output_format}")
        self._convert_with_ffmpeg(wav_path, converted)
        return converted

    def _synthesize_layer(self, layer: SceneLayer, total_samples: int) -> list[float]:
        """Generate deterministic synthetic signal per sound type and semantics."""

        signal = [0.0 for _ in range(total_samples)]
        fade_samples = int(0.8 * self.sample_rate)
        base_freq = 110.0 + (layer.intensity * 180.0)

        for i in range(total_samples):
            t = i / self.sample_rate
            if layer.sound_type == "environment":
                carrier = math.sin(2 * math.pi * (base_freq * 0.4) * t)
                noise = (self._rng.random() * 2 - 1) * 0.2
                sample = 0.5 * carrier + noise
            elif layer.sound_type == "human_voice":
                formant = math.sin(2 * math.pi * (base_freq * 1.2) * t)
                breath = math.sin(2 * math.pi * 3.0 * t) * 0.25
                sample = 0.45 * formant + 0.15 * breath
            elif layer.sound_type in {"cinematic_music", "dynamic_music"}:
                chord = (
                    math.sin(2 * math.pi * base_freq * t)
                    + math.sin(2 * math.pi * (base_freq * 1.25) * t)
                    + math.sin(2 * math.pi * (base_freq * 1.5) * t)
                ) / 3.0
                pulse = 1.0 if math.sin(2 * math.pi * 2.0 * t) > 0 else 0.5
                sample = chord * pulse
            else:
                sample = math.sin(2 * math.pi * base_freq * t)

            # Linear fade-in and fade-out to avoid clicks at boundaries.
            if i < fade_samples:
                sample *= i / max(fade_samples, 1)
            if i > total_samples - fade_samples:
                sample *= max(0.0, (total_samples - i) / max(fade_samples, 1))
            signal[i] = sample
        return signal

    def _write_wav(self, output: Path, pcm_bytes: bytes) -> None:
        output.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(pcm_bytes)

    def _convert_with_ffmpeg(self, input_wav: Path, output_file: Path) -> None:
        ffmpeg = shutil.which("ffmpeg")
        if ffmpeg is None:
            raise RuntimeError("ffmpeg is required to export mp3/ogg")
        command = [ffmpeg, "-y", "-i", str(input_wav), str(output_file)]
        subprocess.run(command, check=True, capture_output=True)
