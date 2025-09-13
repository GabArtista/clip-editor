import yt_dlp
import os
from glob import glob

def baixar_reel(url, cookie_file_path=None, destino="videos/"):
    os.makedirs(destino, exist_ok=True)
    
    # Configurações básicas do yt-dlp
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'merge_output_format': 'mp4',
        'outtmpl': os.path.join(destino, '%(title)s.%(ext)s'),
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.75 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        },
        'compat_opts': ['no-abort-on-error', 'no-check-certificates'],
        'no_warnings': True,
    }
    
    if cookie_file_path:
        ydl_opts['cookiefile'] = cookie_file_path
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            print("Configurações de download:", ydl_opts)
            info = ydl.extract_info(url, download=True)
            
            # Tenta pegar o caminho do arquivo final do info, que é o mais confiável
            filepath = info.get('filepath')
            
            # Se o filepath não for retornado (ex: arquivo já existe), constrói o caminho manualmente
            if not filepath and 'title' in info:
                # Usa o 'glob' para encontrar o arquivo que foi baixado (ou já existia)
                # O yt-dlp pode adicionar o ID do vídeo ao nome, então o glob é mais seguro
                files = glob(os.path.join(destino, f"{info['title']}*.mp4"))
                if files:
                    filepath = files[0]
            
            if filepath and os.path.exists(filepath):
                return filepath
            
            # Se ainda assim não encontramos o arquivo, algo falhou.
            raise Exception("O yt-dlp não conseguiu retornar o caminho do vídeo baixado ou existente.")

        except Exception as e:
            print(f"Erro ao baixar o vídeo: {e}")
            return None