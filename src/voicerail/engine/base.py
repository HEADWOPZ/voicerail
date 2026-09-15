"""Engine contract. Implementations must stay on-device."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from voicerail.audio.pcm import AudioClip
from voicerail.presets import Preset
from voicerail.voices import VoiceProfile


@dataclass(frozen=True)
class EngineInfo:
    id: str
    label: str
    offline: bool
    gpu_required: bool
    available: bool
    detail: str


class TTSEngine(ABC):
    id: str

    @abstractmethod
    def info(self) -> EngineInfo:
        raise NotImplementedError

    @abstractmethod
    def synthesize(self, text: str, voice: VoiceProfile, preset: Preset) -> AudioClip:
        raise NotImplementedError
