# Copyright (c) 2026 Murilo Siqueira Toledo. Todos os direitos reservados nos termos da licença MIT.
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

from ecodeck import audio
from ecodeck.audio import MAX_VOICES, AudioEngine, MicBuffer, Mixer, decode
from ecodeck.models import Settings


def test_mixer_volumes_overlap_tail_and_stop():
    mixer = Mixer()
    mixer.master = 0.5
    mixer.volumes = {"a": 0.5, "b": 1}
    mixer.play("a", np.ones((3, 2), dtype="float32"))
    mixer.play("b", np.full((1, 2), 0.5, dtype="float32"))
    np.testing.assert_allclose(mixer.render(2), [[0.5, 0.5], [0.25, 0.25]])
    np.testing.assert_allclose(mixer.render(2), [[0.25, 0.25], [0, 0]])
    assert not mixer.voices
    mixer.play("a", np.ones((5, 2), dtype="float32"))
    mixer.stop()
    assert not mixer.render(3).any()


def test_polyphony_bounded():
    mixer = Mixer()
    for index in range(50):
        mixer.play(str(index), np.ones((2, 2), dtype="float32"))
    assert len(mixer.voices) == MAX_VOICES
    assert mixer.voices[0].ident == "34"


def test_mic_buffer_wrap_drops_old_samples_and_silence():
    ring = MicBuffer(4)
    ring.push(np.array([[1], [2], [3]], dtype="float32"))
    np.testing.assert_array_equal(ring.take(2), [[1, 1], [2, 2]])
    ring.push(np.array([[4], [5], [6], [7], [8]], dtype="float32"))
    np.testing.assert_array_equal(ring.take(6), [[5, 5], [6, 6], [7, 7], [8, 8], [0, 0], [0, 0]])
    assert ring.size == 0


@pytest.mark.parametrize(
    "extension,format_,subtype",
    [
        ("wav", "WAV", "PCM_16"),
        ("flac", "FLAC", "PCM_16"),
        ("ogg", "OGG", "VORBIS"),
        ("mp3", "MP3", None),
    ],
)
def test_decode_formats_and_resample(tmp_path, extension, format_, subtype):
    path = tmp_path / f"synthetic.{extension}"
    samples = np.sin(2 * np.pi * 440 * np.arange(2205) / 22050).astype("float32") * 0.1
    sf.write(path, samples, 22050, format=format_, subtype=subtype)
    decoded = decode(path)
    assert decoded.shape[1] == 2
    assert abs(len(decoded) - 4800) < 10
    assert not decoded.flags.writeable
    assert decoded.dtype == np.float32
    assert np.max(np.abs(decoded)) > 0.05
    np.testing.assert_array_equal(decoded[:, 0], decoded[:, 1])


@pytest.fixture
def fake_audio(monkeypatch):
    opened = []

    class Stream:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.active = False
            self.closed = False
            opened.append(self)

        def start(self):
            self.active = True

        def abort(self):
            self.active = False

        def close(self):
            self.closed = True

    monkeypatch.setattr(
        audio,
        "devices",
        lambda: [
            {"key": "headphones", "index": 1, "outputs": 2, "inputs": 0},
            {"key": "cable", "index": 2, "outputs": 2, "inputs": 0},
            {"key": "mic", "index": 3, "outputs": 0, "inputs": 1},
        ],
    )
    monkeypatch.setattr(audio.sd, "OutputStream", Stream)
    monkeypatch.setattr(audio.sd, "InputStream", Stream)
    monkeypatch.setattr(audio.sd, "check_output_settings", lambda **kw: None)
    monkeypatch.setattr(audio.sd, "check_input_settings", lambda **kw: None)
    return opened


def test_dual_output_and_mic_isolation_clipping_and_shutdown(fake_audio):
    engine = AudioEngine()
    engine.configure(
        Settings(monitor="headphones", virtual="cable", microphone="mic", mix_microphone=True)
    )
    engine.set_levels(1, {"a": 1}, 1)
    engine.play_loaded(
        "a", np.full((10, 2), 0.7, dtype="float32"), engine.epoch, engine.routing_epoch
    )
    fake_audio[2].kwargs["callback"](np.full((4, 1), 0.8, dtype="float32"), 4, None, False)
    monitor = np.zeros((4, 2), dtype="float32")
    virtual = monitor.copy()
    fake_audio[0].kwargs["callback"](monitor, 4, None, False)
    fake_audio[1].kwargs["callback"](virtual, 4, None, False)
    np.testing.assert_allclose(monitor, 0.7)
    np.testing.assert_allclose(virtual, 1.0)
    engine.close()
    assert all(s.closed for s in fake_audio)
    assert not engine.running


def test_stop_invalidates_queued_decode_and_single_output_does_not_pin_ghost_voices(fake_audio):
    engine = AudioEngine()
    engine.configure(Settings(monitor="headphones"))
    old_epoch, old_route = engine.epoch, engine.routing_epoch
    engine.stop_all()
    engine.play_loaded("a", np.ones((4, 2)), old_epoch, old_route)
    assert not engine.monitor.voices
    engine.play_loaded("a", np.ones((4, 2)), engine.epoch, engine.routing_epoch)
    assert engine.monitor.voices
    assert not engine.virtual.voices
    engine.close()


def test_missing_device_never_falls_back(fake_audio):
    engine = AudioEngine()
    with pytest.raises(ValueError, match="ausente"):
        engine.configure(Settings(monitor="missing"))
    assert not fake_audio


def test_failure_second_stream_closes_first(fake_audio, monkeypatch):
    def check(**kwargs):
        if kwargs["device"] == 2:
            raise OSError("unavailable")

    monkeypatch.setattr(audio.sd, "check_output_settings", check)
    engine = AudioEngine()
    with pytest.raises(OSError, match="unavailable"):
        engine.configure(Settings(monitor="headphones", virtual="cable"))
    assert fake_audio[0].closed
    assert not engine.streams


def test_cache_bound_and_active_sound_not_evicted(monkeypatch):
    engine = AudioEngine()
    monkeypatch.setattr(audio, "CACHE_BYTES", 64)
    monkeypatch.setattr(audio, "decode", lambda _: np.zeros((8, 2), dtype="float32"))
    samples = engine.load("a", None)
    engine.monitor.play("a", samples)
    with pytest.raises(ValueError, match="memória"):
        engine.load("b", None)
    engine.stop_all()
    engine.load("b", None)
    assert list(engine.cache) == ["b"]


def test_close_attempts_every_stream_even_on_error():
    closed = []

    def fail():
        raise OSError("unplugged")

    engine = AudioEngine()
    engine.streams = [
        SimpleNamespace(abort=fail, close=lambda: closed.append(1)),
        SimpleNamespace(abort=lambda: None, close=lambda: closed.append(2)),
    ]
    with pytest.raises(OSError):
        engine.close()
    assert closed == [2, 1]
