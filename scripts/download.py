import yt_dlp
import os

def baixar_reel(url, destino="videos/"):
    os.makedirs(destino, exist_ok=True)
    ydl_opts = {
        'outtmpl': os.path.join(destino, '%(title)s.%(ext)s'),
        'format': 'mp4',
        'quiet': True
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return os.path.join(destino, f"{info['title']}.mp4")
