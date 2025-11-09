import sys
import types
from pathlib import Path

import numpy as np

try:
    from metrics import reset_registry as _reset_metrics_registry
except Exception:  # pragma: no cover - fallback when metrics not available
    _reset_metrics_registry = None


def reset_app_modules() -> None:
    """
    Remove módulos 'app' e 'jobs' do cache do Python para que possam ser importados
    novamente com o ambiente configurado para cada teste.
    """
    if _reset_metrics_registry is not None:
        _reset_metrics_registry()

    db_module = sys.modules.get("app.database")
    if db_module is not None:
        base = getattr(db_module, "Base", None)
        if base is not None:
            base.metadata.clear()
            if hasattr(base, "registry"):
                base.registry.dispose()

    prefixes = ("app", "jobs", "api")
    for name in list(sys.modules.keys()):
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in prefixes):
            sys.modules.pop(name, None)


def ensure_multipart_stub() -> None:
    if "multipart" in sys.modules and "multipart.multipart" in sys.modules:
        return

    multipart_module = types.ModuleType("multipart")
    multipart_module.__version__ = "0.0-test"
    submodule = types.ModuleType("multipart.multipart")

    def parse_options_header(value):  # noqa: ANN001,D401 - comportamento mínimo para testes
        """Stub que imita a assinatura esperada."""
        return {}

    submodule.parse_options_header = parse_options_header
    sys.modules.setdefault("multipart", multipart_module)
    sys.modules.setdefault("multipart.multipart", submodule)


class _FakeVideoAnalyzer:
    def analyze(self, video_path: str) -> dict:
        return {
            "scenes": [
                {"order": 1, "start": 0.0, "end": 10.0, "duration": 10.0},
                {"order": 2, "start": 10.0, "end": 20.0, "duration": 10.0},
            ],
            "motion_peaks": [2.0, 9.5, 15.0],
            "motion_stats": {"mean": 0.6, "std": 0.15, "peaks": [2.0, 9.5, 15.0]},
            "keywords": ["movimento", "energia"],
            "energy": {"profile": [0.5, 0.6, 0.55], "sample_rate": 2.0},
            "duration": 25.0,
        }


class _FakeAudioAnalyzer:
    def __init__(self, fixed_bpm: int = 110) -> None:
        self.fixed_bpm = fixed_bpm

    def analyze(self, audio_path: str) -> dict:
        beats = np.linspace(0, 30, num=30).tolist()
        return {
            "bpm": self.fixed_bpm,
            "beats": beats,
            "transcription": "",
            "language": "pt",
            "key": "C",
            "energy": {"mean": 0.5, "std": 0.1},
        }


def install_ai_stubs(monkeypatch) -> None:
    """
    Monkeypatches heavy AI analyzers to cheap fakes for tests.
    """
    import app.services.video_pipeline as pipeline_module
    import app.services.music_service as music_service_module

    monkeypatch.setattr(pipeline_module, "get_video_analyzer", lambda: _FakeVideoAnalyzer(), raising=True)
    monkeypatch.setattr(music_service_module, "get_audio_analyzer", lambda: _FakeAudioAnalyzer(), raising=True)
