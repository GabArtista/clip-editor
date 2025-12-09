import json
import subprocess
import shlex


def get_audio_duration(path: str) -> float:
    """Obtém a duração (segundos) via ffprobe, como float."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        path
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(proc.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        raise RuntimeError(f"Não foi possível ler duração de {path}: {e}")

