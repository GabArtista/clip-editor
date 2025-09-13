# scripts/edit.py
# -*- coding: utf-8 -*-

import os
import uuid
import json
import shlex
import subprocess
from pathlib import Path


# =========================
# Utilidades
# =========================

def _abspath(p: str) -> str:
    return str(Path(p).expanduser().resolve())

def _run(cmd: list[str], *, quiet: bool = False) -> subprocess.CompletedProcess:
    """Executa um comando e retorna o CompletedProcess. Levanta exceção com stderr se falhar."""
    if not quiet:
        print("CMD:", " ".join(shlex.quote(c) for c in cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(
            "Comando falhou:\n"
            + " ".join(shlex.quote(c) for c in cmd)
            + f"\n--- STDERR ---\n{proc.stderr}\n--- STDOUT ---\n{proc.stdout}\n"
        )
    # Loga avisos do ffmpeg/ffprobe quando houver
    if proc.stderr and not quiet:
        # ffmpeg escreve tudo em stderr, inclusive progresso;
        # mantemos só as primeiras linhas para não poluir
        lines = [l for l in proc.stderr.splitlines() if l.strip()]
        if lines:
            print("FFmpeg/ffprobe:", lines[-1])
    return proc

def _ffprobe_duration(path: str) -> float:
    """Obtém a duração (segundos) via ffprobe, como float."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "json",
        path
    ]
    proc = _run(cmd, quiet=True)
    try:
        data = json.loads(proc.stdout)
        return float(data["format"]["duration"])
    except Exception as e:
        raise RuntimeError(f"Não foi possível ler duração de {path}: {e}\nSaída: {proc.stdout}")


# =========================
# Lógica principal (compatível com API existente)
# =========================

def adicionar_musica(
    video_path: str,
    musica_path: str,
    segundo_video: float,             # mantido p/ compat original (impacto no vídeo)
    output_path: str,
    music_impact: float = 51.0,       # mantido p/ compat original (impacto na música)
    debug: bool = True,
    gain_db: float = 6.0
) -> str:
    """
    Substitui o áudio do vídeo por um trecho contínuo da música, SEM adicionar silêncio.
    Alinha para que 'music_impact' (segundo na música) ocorra exatamente em 'segundo_video' (segundo no vídeo).

    Regras:
    - start_music = music_impact - segundo_video
    - Trecho usado = música[start_music : start_music + duracao_video]
    - Clampeia para nunca sair dos limites da música.
    - Saída pronta para Reels (H.264 yuv420p + AAC).

    Parâmetros mantidos para compatibilidade com a API atual:
    - 'segundo_video' = impacto no vídeo (antes você já usava esse nome)
    - 'music_impact'  = impacto na música (antes você já usava esse nome)
    """

    print("🎬 Iniciando a edição (sem silêncio artificial)…")

    # Pastas/paths
    os.makedirs("processed", exist_ok=True)
    video_path = _abspath(video_path)
    musica_path = _abspath(musica_path)
    output_path = _abspath(output_path)

    # Validações básicas
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Vídeo não encontrado: {video_path}")
    if not os.path.exists(musica_path):
        raise FileNotFoundError(f"Música não encontrada: {musica_path}")

    # Durações
    duracao_video = _ffprobe_duration(video_path)
    duracao_musica = _ffprobe_duration(musica_path)
    print(f"✅ Duração vídeo: {duracao_video:.3f}s | ✅ Duração música: {duracao_musica:.3f}s")

    # Cálculo de alinhamento (sem silêncio)
    # Queremos: music_impact no t=segundo_video do vídeo
    # Logo, o início do trecho da música que usaremos é:
    start_music = float(music_impact) - float(segundo_video)

    # Clampeia para os limites da música (sem sair do range)
    # 1) Não pode começar antes do 0
    if start_music < 0:
        print(f"⚠️ Impacto da música cairia antes do início. Ajustando início de {start_music:.3f}s → 0.000s")
        start_music = 0.0

    # 2) Não pode ultrapassar o final (precisamos de 'duracao_video' de música)
    max_start = max(0.0, duracao_musica - duracao_video)
    if start_music > max_start:
        print(f"⚠️ Ajuste no início para caber o vídeo: {start_music:.3f}s → {max_start:.3f}s")
        start_music = max_start

    print(f"🎯 Início do trecho da música: {start_music:.3f}s (music_impact={music_impact:.3f}s ↔ segundo_video={float(segundo_video):.3f}s)")

    # Áudio temporário (único p/ evitar corrida)
    temp_audio = os.path.join("processed", f"audio_{uuid.uuid4().hex}.wav")

    # Gerar o áudio alinhado (sem silêncio, só corte)
    # Observação: usamos -ss APÓS o -i para busca precisa (ainda que um pouco mais lenta).
    cmd_audio = [
        "ffmpeg", "-y",
        "-i", musica_path,
        "-ss", f"{start_music:.3f}",
        "-t", f"{duracao_video:.3f}",
        "-ac", "2", "-ar", "48000",
        "-af", f"volume={gain_db}dB",
        "-c:a", "pcm_s16le",
        temp_audio
    ]
    print("🎵 Gerando áudio alinhado…")
    _run(cmd_audio)

    # Sanidade do áudio gerado
    if not os.path.exists(temp_audio) or os.path.getsize(temp_audio) < 1024:
        raise RuntimeError(f"Áudio temporário inválido/pequeno: {temp_audio}")
    dur_temp = _ffprobe_duration(temp_audio)
    if dur_temp <= 0.0:
        raise RuntimeError(f"Áudio temporário com duração zero: {temp_audio}")
    print(f"✅ Áudio OK ({dur_temp:.3f}s): {temp_audio}")

    # Mux final (força compatibilidade ampla p/ Reels: H.264 + yuv420p + AAC)
    cmd_final = [
        "ffmpeg", "-y",
        "-i", video_path, "-i", temp_audio,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest",  # Garante término no menor fluxo (evita arrasto se algo sair fora)
        output_path
    ]
    print("🎥 Renderizando vídeo final…")
    _run(cmd_final)

    # Limpeza
    try:
        if not debug and os.path.exists(temp_audio):
            os.remove(temp_audio)
    except Exception as e:
        print("⚠️ Não foi possível remover temporário:", e)

    print(f"✅ Finalizado com sucesso!\n📄 Saída: {output_path}")
    return output_path
