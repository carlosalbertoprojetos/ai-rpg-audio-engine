"""Psychoacoustic feature extraction in pure Python."""
from __future__ import annotations

import math
from typing import Dict, List, Sequence


class PsychoacousticFeatureExtractor:
    """Extracts psychoacoustic descriptors used by the emotional pipeline."""

    def __init__(self, frame_size: int = 256, hop_size: int = 128, mel_bins: int = 24, mfcc_bins: int = 13) -> None:
        self.frame_size = frame_size
        self.hop_size = hop_size
        self.mel_bins = mel_bins
        self.mfcc_bins = mfcc_bins

    def _hann(self, n: int, length: int) -> float:
        return 0.5 - 0.5 * math.cos((2.0 * math.pi * n) / max(length - 1, 1))

    def _frames(self, signal: Sequence[float]) -> List[List[float]]:
        if not signal:
            return [[0.0] * self.frame_size]
        frames: List[List[float]] = []
        index = 0
        while index < len(signal):
            frame = list(signal[index : index + self.frame_size])
            if len(frame) < self.frame_size:
                frame.extend([0.0] * (self.frame_size - len(frame)))
            windowed = [frame[i] * self._hann(i, self.frame_size) for i in range(self.frame_size)]
            frames.append(windowed)
            index += self.hop_size
        return frames

    def _dft_magnitude(self, frame: Sequence[float]) -> List[float]:
        half = len(frame) // 2 + 1
        spectrum: List[float] = []
        for k in range(half):
            real = 0.0
            imag = 0.0
            for n, sample in enumerate(frame):
                angle = 2.0 * math.pi * k * n / len(frame)
                real += sample * math.cos(angle)
                imag -= sample * math.sin(angle)
            spectrum.append(math.sqrt(real * real + imag * imag))
        return spectrum

    def _hz_to_mel(self, hz: float) -> float:
        return 2595.0 * math.log10(1.0 + hz / 700.0)

    def _mel_to_hz(self, mel: float) -> float:
        return 700.0 * (10 ** (mel / 2595.0) - 1.0)

    def _mel_filterbank(self, n_fft: int, sample_rate: int) -> List[List[float]]:
        n_bins = n_fft // 2 + 1
        mel_low = self._hz_to_mel(0.0)
        mel_high = self._hz_to_mel(sample_rate / 2.0)
        mel_points = [mel_low + i * (mel_high - mel_low) / (self.mel_bins + 1) for i in range(self.mel_bins + 2)]
        hz_points = [self._mel_to_hz(m) for m in mel_points]
        bin_points = [min(n_bins - 1, int((n_fft + 1) * hz / sample_rate)) for hz in hz_points]

        filters: List[List[float]] = [[0.0 for _ in range(n_bins)] for _ in range(self.mel_bins)]
        for m in range(1, self.mel_bins + 1):
            left = bin_points[m - 1]
            center = bin_points[m]
            right = bin_points[m + 1]
            if center == left:
                center += 1
            if right == center:
                right += 1
            for k in range(left, min(center, n_bins)):
                filters[m - 1][k] = (k - left) / max(center - left, 1)
            for k in range(center, min(right, n_bins)):
                filters[m - 1][k] = (right - k) / max(right - center, 1)
        return filters

    def log_mel_spectrogram(self, signal: Sequence[float], sample_rate: int = 16000) -> List[List[float]]:
        frames = self._frames(signal)
        spectra = [self._dft_magnitude(frame) for frame in frames]
        filters = self._mel_filterbank(self.frame_size, sample_rate)

        mel_spec: List[List[float]] = []
        for spec in spectra:
            mel_row: List[float] = []
            for mel_filter in filters:
                energy = sum(spec[k] * mel_filter[k] for k in range(len(spec)))
                mel_row.append(math.log(max(energy, 1e-8)))
            mel_spec.append(mel_row)
        return mel_spec

    def mfcc(self, log_mel: Sequence[Sequence[float]]) -> List[List[float]]:
        coeffs: List[List[float]] = []
        for row in log_mel:
            c_row: List[float] = []
            for k in range(self.mfcc_bins):
                value = 0.0
                for n, x in enumerate(row):
                    value += x * math.cos(math.pi * k * (2 * n + 1) / (2 * len(row)))
                c_row.append(value)
            coeffs.append(c_row)
        return coeffs

    def spectral_flux(self, spectra: Sequence[Sequence[float]]) -> List[float]:
        if not spectra:
            return [0.0]
        flux = [0.0]
        for t in range(1, len(spectra)):
            diff = 0.0
            prev = spectra[t - 1]
            curr = spectra[t]
            for k in range(min(len(prev), len(curr))):
                delta = curr[k] - prev[k]
                diff += max(0.0, delta)
            flux.append(diff / max(len(curr), 1))
        return flux

    def roughness(self, spectra: Sequence[Sequence[float]]) -> List[float]:
        rough: List[float] = []
        for spec in spectra:
            if len(spec) < 2:
                rough.append(0.0)
                continue
            acc = 0.0
            for i in range(len(spec) - 1):
                acc += abs(spec[i + 1] - spec[i])
            rough.append(acc / (len(spec) - 1))
        return rough

    def tonnetz(self, spectra: Sequence[Sequence[float]]) -> List[List[float]]:
        tonnetz_frames: List[List[float]] = []
        for spec in spectra:
            chroma = [0.0] * 12
            for bin_idx, mag in enumerate(spec):
                chroma[bin_idx % 12] += mag
            total = sum(chroma) or 1.0
            chroma = [c / total for c in chroma]

            # Project chroma to a 6D tonal centroid style representation.
            frame = [
                sum(chroma[i] * math.cos(2 * math.pi * i / 12.0) for i in range(12)),
                sum(chroma[i] * math.sin(2 * math.pi * i / 12.0) for i in range(12)),
                sum(chroma[i] * math.cos(3 * math.pi * i / 12.0) for i in range(12)),
                sum(chroma[i] * math.sin(3 * math.pi * i / 12.0) for i in range(12)),
                sum(chroma[i] * math.cos(4 * math.pi * i / 12.0) for i in range(12)),
                sum(chroma[i] * math.sin(4 * math.pi * i / 12.0) for i in range(12)),
            ]
            tonnetz_frames.append(frame)
        return tonnetz_frames

    def extract(self, signal: Sequence[float], sample_rate: int = 16000) -> Dict[str, List]:
        """Extract full psychoacoustic feature set for one signal."""

        frames = self._frames(signal)
        spectra = [self._dft_magnitude(frame) for frame in frames]
        log_mel = self.log_mel_spectrogram(signal, sample_rate=sample_rate)
        return {
            "log_mel": log_mel,
            "mfcc": self.mfcc(log_mel),
            "spectral_flux": self.spectral_flux(spectra),
            "roughness": self.roughness(spectra),
            "tonnetz": self.tonnetz(spectra),
        }
