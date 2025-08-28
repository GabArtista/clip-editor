import subprocess
import os

def adicionar_musica(video_path, musica_path, segundo_video, output_path, music_impact=51.0, debug=True, gain_db=6.0):
    """
    Substitui o áudio do vídeo pela música.
    Sincroniza para que music_impact (ex.: 51s) da música ocorra no instante segundo_video do vídeo.
    Funciona para qualquer música e qualquer vídeo.
    Pipeline em 2 passos: gera WAV alinhado (debug) e depois muxa para MP4.
    """
    os.makedirs("processed", exist_ok=True)

    # Offset: quanto a música deve "andar" em relação ao vídeo
    offset = float(music_impact) - float(segundo_video)

    # Duração do vídeo
    duracao_video = float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", video_path
    ]).decode().strip())

    # Arquivo temporário para áudio alinhado
    temp_audio = os.path.join("processed", "debug_audio.wav")

    if offset > 0:
        # Caso X < impact → iniciar música já adiantada
        cmd = [
            "ffmpeg", "-y",
            "-ss", f"{offset:.3f}", "-i", musica_path,
            "-t", f"{duracao_video:.3f}",
            "-ac", "2", "-ar", "48000",
            "-af", f"volume={gain_db}dB",
            "-c:a", "pcm_s16le",
            temp_audio
        ]
    else:
        # Caso X > impact → adicionar silêncio antes (concat de silêncio + música)
        silencio = abs(offset)
        fcomplex = (
            f"[0][1:a]concat=n=2:v=0:a=1,aresample=48000,pan=stereo|c0=c0|c1=c1,volume={gain_db}dB[a]"
        )
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", f"anullsrc=r=48000:cl=stereo:d={silencio:.3f}",
            "-i", musica_path,
            "-filter_complex", fcomplex,
            "-map", "[a]",
            "-t", f"{duracao_video:.3f}",
            "-c:a", "pcm_s16le",
            temp_audio
        ]

    print("🎵 Gerando áudio alinhado:", " ".join(cmd))
    subprocess.run(cmd, check=True)

    # Muxar com o vídeo (reencode seguro)
    cmd_final = [
        "ffmpeg", "-y",
        "-i", video_path, "-i", temp_audio,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "192k", "-ar", "48000",
        "-shortest", output_path
    ]

    print("🎬 Renderizando vídeo final:", " ".join(cmd_final))
    subprocess.run(cmd_final, check=True)

    if not debug and os.path.exists(temp_audio):
        os.remove(temp_audio)

    return output_path