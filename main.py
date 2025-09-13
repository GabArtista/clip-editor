import os
from scripts.download import baixar_reel
from scripts.edit import adicionar_musica

if __name__ == "__main__":
    url = input("Informe o link do Reels: ").strip()
    music = input("Informe o nome da música (sem .mp3, ex.: Fala): ").strip()
    impact_music = float(input("Informe o segundo de impacto na MÚSICA (ex.: 51.0): ").strip())
    impact_video = float(input("Informe o segundo de impacto no VÍDEO (ex.: 10.10): ").strip())

    print("📥 Baixando vídeo...")
    # Aqui, você precisaria ter o arquivo de cookies para testar o download com autenticação
    # Para testes, a lógica abaixo assume que o vídeo é público ou que o cookie já está salvo
    video_path = baixar_reel(url, cookie_file_path="cookies/session.netscape")
    
    if not os.path.exists(video_path):
        raise FileNotFoundError("Falha ao baixar o vídeo. Verifique o link e os cookies.")

    musica_path = os.path.join("music", f"{music}.mp3")
    if not os.path.exists(musica_path):
        raise FileNotFoundError(f"Música não encontrada: {musica_path}")

    base = os.path.splitext(os.path.basename(video_path))[0]
    out = os.path.join("processed", f"{base}_{music}_iv{impact_video:.2f}_im{impact_music:.2f}.mp4")

    print("🎬 Editando vídeo...")
    adicionar_musica(video_path, musica_path, impact_video, out, music_impact=impact_music)
    print(f"✅ Vídeo processado com sucesso: {out}")