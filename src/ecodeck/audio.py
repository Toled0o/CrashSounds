# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
"""Mixer independente de hardware e adaptador PortAudio de duas saídas."""

from __future__ import annotations

import threading
from collections import OrderedDict
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import sounddevice as sd
import soundfile as sf
import soxr

from ecodeck.models import MAX_DURATION, Settings, gain
from ecodeck.storage import validate_audio

RATE = 48_000
BLOCK = 960
MAX_VOICES = 16
CACHE_BYTES = 128 * 1024 * 1024


def decode(path: Path) -> np.ndarray:
    validate_audio(path)
    info = sf.info(path)
    if not 8_000 <= info.samplerate <= 192_000:
        raise ValueError("Taxa de amostragem deve estar entre 8 e 192 kHz.")
    data, rate = sf.read(
        path, dtype="float32", always_2d=True, frames=int(MAX_DURATION * info.samplerate) + 1
    )
    if rate != RATE:
        data = soxr.resample(data, rate, RATE, quality="HQ")
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    if not np.isfinite(data).all():
        raise ValueError("Áudio contém amostras inválidas.")
    data = np.ascontiguousarray(data, dtype=np.float32)
    data.flags.writeable = False
    return data


@dataclass
class Voice:
    ident: str
    samples: np.ndarray
    position: int = 0


class Mixer:
    def __init__(self):
        self.lock = threading.Lock()
        self.voices: list[Voice] = []
        self.volumes: dict[str, float] = {}
        self.master = 0.8

    def play(self, ident: str, samples: np.ndarray):
        with self.lock:
            if len(self.voices) >= MAX_VOICES:
                self.voices.pop(0)
            self.voices.append(Voice(ident, samples))

    def stop(self):
        with self.lock:
            self.voices.clear()

    def active_ids(self) -> set[str]:
        with self.lock:
            return {v.ident for v in self.voices}

    def render(self, frames: int) -> np.ndarray:
        out = np.zeros((frames, 2), dtype=np.float32)
        with self.lock:
            remaining = []
            for voice in self.voices:
                length = min(frames, len(voice.samples) - voice.position)
                out[:length] += voice.samples[
                    voice.position : voice.position + length
                ] * self.volumes.get(voice.ident, 0.8)
                voice.position += length
                if voice.position < len(voice.samples):
                    remaining.append(voice)
            self.voices = remaining
            out *= self.master
        return out


class MicBuffer:
    """Fila limitada: descarta voz antiga quando relógios de dispositivos divergem."""

    def __init__(self, capacity: int = RATE // 5):
        self.data = np.zeros((capacity, 2), dtype=np.float32)
        self.read_pos = 0
        self.write_pos = 0
        self.size = 0
        self.lock = threading.Lock()

    def push(self, samples: np.ndarray):
        with self.lock:
            samples = samples[-len(self.data) :]
            count = len(samples)
            overflow = max(0, self.size + count - len(self.data))
            self.read_pos = (self.read_pos + overflow) % len(self.data)
            first = min(count, len(self.data) - self.write_pos)
            self.data[self.write_pos : self.write_pos + first] = samples[:first]
            self.data[: count - first] = samples[first:]
            self.write_pos = (self.write_pos + count) % len(self.data)
            self.size = min(len(self.data), self.size + count)

    def take(self, frames: int) -> np.ndarray:
        out = np.zeros((frames, 2), dtype=np.float32)
        with self.lock:
            count = min(frames, self.size)
            first = min(count, len(self.data) - self.read_pos)
            out[:first] = self.data[self.read_pos : self.read_pos + first]
            out[first:count] = self.data[: count - first]
            self.read_pos = (self.read_pos + count) % len(self.data)
            self.size -= count
        return out


def devices() -> list[dict]:
    hosts = sd.query_hostapis()
    result = []
    for index, device in enumerate(sd.query_devices()):
        host = hosts[device["hostapi"]]["name"]
        # WASAPI compartilhado: nomes sem duplicação MME/DirectSound no Windows.
        import sys

        if sys.platform == "win32" and host != "Windows WASAPI":
            continue
        result.append(
            {
                "index": index,
                "key": f"{host} :: {device['name']}",
                "name": device["name"],
                "inputs": device["max_input_channels"],
                "outputs": device["max_output_channels"],
            }
        )
    return result


class AudioEngine:
    def __init__(self):
        self.monitor = Mixer()
        self.virtual = Mixer()
        self.mic = MicBuffer()
        self.mic_gain = 0.8
        self.streams: list = []
        self.targets: list[Mixer] = []
        self.cache: OrderedDict[str, np.ndarray] = OrderedDict()
        self.cache_lock = threading.Lock()
        self.epoch = 0
        self.routing_epoch = 0
        self.xruns = 0

    @property
    def running(self) -> bool:
        return bool(self.streams) and all(stream.active for stream in self.streams)

    def set_levels(self, master: float, volumes: dict[str, float], mic_gain: float):
        for mixer in (self.monitor, self.virtual):
            with mixer.lock:
                mixer.master = gain(master)
                mixer.volumes = {key: gain(value) for key, value in volumes.items()}
        self.mic_gain = gain(mic_gain)

    def stop_all(self):
        # Invalida também solicitações que ainda estão decodificando no worker.
        self.epoch += 1
        self.monitor.stop()
        self.virtual.stop()

    def close(self):
        self.stop_all()
        self.routing_epoch += 1
        streams, self.streams = self.streams, []
        self.targets = []
        errors = []
        for stream in reversed(streams):
            try:
                stream.abort()
            except Exception as exc:
                errors.append(exc)
            try:
                stream.close()
            except Exception as exc:
                errors.append(exc)
        self.mic = MicBuffer()
        if errors:
            raise OSError(f"Não foi possível encerrar um dispositivo: {errors[0]}")

    def configure(self, settings: Settings):
        self.close()
        choices = devices()

        def resolve(key: str | None, kind: str) -> int | None:
            if key is None:
                return None
            matches = [d for d in choices if d["key"] == key and d[kind] > 0]
            if len(matches) != 1:
                raise ValueError(
                    "Dispositivo ausente ou ambíguo. Selecione novamente nas configurações."
                )
            return matches[0]["index"]

        monitor = resolve(settings.monitor, "outputs")
        virtual = resolve(settings.virtual, "outputs")
        microphone = resolve(settings.microphone, "inputs") if settings.mix_microphone else None
        if monitor is None and virtual is None:
            raise ValueError("Selecione pelo menos uma saída de áudio nas configurações.")
        if monitor is not None and monitor == virtual:
            raise ValueError("Fones e cabo virtual precisam ser dispositivos diferentes.")
        if settings.mix_microphone and (microphone is None or virtual is None):
            raise ValueError("Para misturar voz, selecione o microfone real e a saída virtual.")
        self.mic_gain = settings.mic_gain
        self.xruns = 0

        def output_callback(mixer: Mixer, include_mic: bool):
            def callback(outdata, frames, time, status):
                if status:
                    self.xruns += 1
                result = mixer.render(frames)
                if include_mic and settings.mix_microphone:
                    result += self.mic.take(frames) * self.mic_gain
                np.clip(result, -1, 1, out=outdata)

            return callback

        try:
            for device, mixer, include_mic in (
                (monitor, self.monitor, False),
                (virtual, self.virtual, True),
            ):
                if device is None:
                    continue
                sd.check_output_settings(
                    device=device, channels=2, dtype="float32", samplerate=RATE
                )
                stream = sd.OutputStream(
                    device=device,
                    channels=2,
                    samplerate=RATE,
                    blocksize=BLOCK,
                    dtype="float32",
                    latency="high",
                    callback=output_callback(mixer, include_mic),
                )
                self.streams.append(stream)
                stream.start()
                self.targets.append(mixer)
            if microphone is not None:
                sd.check_input_settings(
                    device=microphone, channels=1, dtype="float32", samplerate=RATE
                )

                def capture(indata, frames, time, status):
                    if status:
                        self.xruns += 1
                    self.mic.push(indata)  # broadcasting mono → estéreo na fila

                stream = sd.InputStream(
                    device=microphone,
                    channels=1,
                    samplerate=RATE,
                    blocksize=BLOCK,
                    dtype="float32",
                    latency="high",
                    callback=capture,
                )
                self.streams.append(stream)
                stream.start()
        except Exception:
            self.close()
            raise

    def load(self, ident: str, path: Path) -> np.ndarray:
        # Worker único; lock também protege eviction contra disparo na UI.
        with self.cache_lock:
            if ident in self.cache:
                self.cache.move_to_end(ident)
                return self.cache[ident]
        samples = decode(path)
        with self.cache_lock:
            active = self.monitor.active_ids() | self.virtual.active_ids()
            while sum(s.nbytes for s in self.cache.values()) + samples.nbytes > CACHE_BYTES:
                victim = next((key for key in self.cache if key not in active), None)
                if victim is None:
                    raise ValueError(
                        "Limite de memória de áudio atingido. Pare alguns sons e tente novamente."
                    )
                del self.cache[victim]
            self.cache[ident] = samples
        return samples

    def play_loaded(self, ident: str, samples: np.ndarray, epoch: int, routing_epoch: int):
        if epoch != self.epoch or routing_epoch != self.routing_epoch or not self.running:
            return
        for mixer in self.targets:
            mixer.play(ident, samples)
