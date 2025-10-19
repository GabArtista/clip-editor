import pytest

pytest.skip("Teste manual legado; ignorado na suíte automatizada.", allow_module_level=True)

import os
import sys
from scripts.edit import adicionar_musica
from scripts.download import baixar_reel

# O mesmo link que você estava usando
video_url = "https://www.instagram.com/reels/DKciWlhRFRE/"
music_name = "fala"  # Substitua pelo nome da sua música
impact_music_sec = 51.0
impact_video_sec = 10.10

print("Iniciando o teste...")
try:
    video_path = baixar_reel(video_url)
    if not video_path:
        raise Exception("Falha ao baixar o vídeo.")

    musica_path = os.path.join("music", f"{music_name}.mp3")
    if not os.path.exists(musica_path):
        raise FileNotFoundError(f"Música não encontrada: {musica_path}")

    output_path = os.path.join("processed", "test_output.mp4")

    print("Chamando a função adicionar_musica...")
    adicionar_musica(
        video_path=video_path,
        musica_path=musica_path,
        segundo_video=impact_video_sec,
        output_path=output_path,
        music_impact=impact_music_sec
    )

    print("✅ Sucesso! O vídeo foi processado.")

except Exception as e:
    print("❌ Ocorreu um erro.")
    print(f"Detalhes do erro: {e}")
    sys.exit(1)
