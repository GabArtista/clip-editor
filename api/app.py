import os
import base64
import json
import http.cookiejar
import subprocess
import shlex
from pathlib import Path
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from fastapi.responses import FileResponse
from scripts.download import baixar_reel
from scripts.edit import adicionar_musica

app = FastAPI(title="FALA Editor API")

SESSION_FILE_PATH = "cookies/session.netscape"

os.makedirs("processed", exist_ok=True)
os.makedirs("videos", exist_ok=True)
os.makedirs("cookies", exist_ok=True)
os.makedirs("music", exist_ok=True)

app.mount("/videos", StaticFiles(directory="processed"), name="videos")


class UpdateSessionRequest(BaseModel):
    cookie_string: str


class EditRequest(BaseModel):
    url: str
    music: str
    impact_music: float
    impact_video: float
    return_format: str = "url"


def _validar_audio_com_ffprobe(arquivo_path: str) -> dict:
    """
    Valida um arquivo de áudio usando ffprobe (seguindo padrão do sistema).
    Retorna informações do arquivo ou levanta exceção se inválido.
    """
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration,format_name",
        "-show_entries", "stream=codec_name,codec_type",
        "-of", "json",
        arquivo_path
    ]
    
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            raise RuntimeError(f"ffprobe falhou: {proc.stderr}")
        
        data = json.loads(proc.stdout)
        
        # Verifica se tem stream de áudio
        streams = data.get("streams", [])
        audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
        
        if not audio_streams:
            raise ValueError("Arquivo não contém stream de áudio válido")
        
        format_info = data.get("format", {})
        duration = float(format_info.get("duration", 0))
        
        if duration <= 0:
            raise ValueError("Arquivo de áudio tem duração inválida ou zero")
        
        return {
            "duration": duration,
            "format": format_info.get("format_name", "unknown"),
            "codec": audio_streams[0].get("codec_name", "unknown"),
            "valid": True
        }
    except json.JSONDecodeError as e:
        raise ValueError(f"Erro ao processar resposta do ffprobe: {e}")
    except subprocess.TimeoutExpired:
        raise ValueError("Timeout ao validar arquivo de áudio")
    except Exception as e:
        raise ValueError(f"Erro ao validar áudio: {str(e)}")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload-music")
async def upload_music(
    file: UploadFile = File(...),
    music_name: str = None
):
    """
    Faz upload de uma música para o sistema.
    
    A música será salva na pasta music/ seguindo o padrão {nome}.mp3.
    O arquivo é validado usando ffprobe para garantir que é um áudio válido.
    
    Parâmetros:
    - file: Arquivo de áudio (MP3, WAV, etc.)
    - music_name: Nome da música (sem extensão). Se não fornecido, usa o nome do arquivo.
    
    Retorna informações sobre a música salva.
    """
    try:
        # Determina o nome da música
        if music_name:
            nome_final = music_name.strip()
        else:
            # Remove extensão do nome original
            nome_final = Path(file.filename).stem.strip()
        
        if not nome_final:
            raise HTTPException(status_code=400, detail="Nome da música não pode ser vazio")
        
        # Sanitiza o nome (remove caracteres inválidos)
        nome_final = "".join(c for c in nome_final if c.isalnum() or c in (' ', '-', '_')).strip()
        nome_final = nome_final.replace(' ', '_')
        
        if not nome_final:
            raise HTTPException(status_code=400, detail="Nome da música inválido após sanitização")
        
        # Caminho final (sempre .mp3, mesmo se upload for outro formato)
        music_dir = "music"
        arquivo_final = os.path.join(music_dir, f"{nome_final}.mp3")
        
        # Verifica se já existe
        if os.path.exists(arquivo_final):
            raise HTTPException(
                status_code=409,
                detail=f"Música '{nome_final}' já existe. Use outro nome ou delete a música existente primeiro."
            )
        
        # Salva arquivo temporário primeiro
        temp_path = os.path.join(music_dir, f"temp_{nome_final}_{os.urandom(4).hex()}")
        
        try:
            # Lê e salva o arquivo
            conteudo = await file.read()
            if len(conteudo) == 0:
                raise HTTPException(status_code=400, detail="Arquivo vazio")
            
            # Limite de tamanho: 100MB
            MAX_SIZE = 100 * 1024 * 1024
            if len(conteudo) > MAX_SIZE:
                raise HTTPException(status_code=400, detail=f"Arquivo muito grande. Máximo: 100MB")
            
            with open(temp_path, "wb") as f:
                f.write(conteudo)
            
            # Valida o arquivo com ffprobe
            info_audio = _validar_audio_com_ffprobe(temp_path)
            
            # Se o arquivo não for MP3, converte para MP3 usando ffmpeg
            if not temp_path.lower().endswith('.mp3'):
                # Converte para MP3
                cmd_convert = [
                    "ffmpeg", "-y", "-i", temp_path,
                    "-acodec", "libmp3lame", "-b:a", "192k",
                    "-ar", "48000", "-ac", "2",
                    arquivo_final
                ]
                proc = subprocess.run(cmd_convert, capture_output=True, text=True, timeout=60)
                if proc.returncode != 0:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Erro ao converter para MP3: {proc.stderr}"
                    )
                # Remove temporário
                os.remove(temp_path)
            else:
                # Se já é MP3, apenas move
                os.rename(temp_path, arquivo_final)
            
            # Valida o arquivo final
            info_final = _validar_audio_com_ffprobe(arquivo_final)
            
            return {
                "ok": True,
                "message": f"Música '{nome_final}' enviada com sucesso",
                "music_name": nome_final,
                "file_path": arquivo_final,
                "duration": info_final["duration"],
                "format": info_final["format"],
                "codec": info_final["codec"],
                "size_bytes": os.path.getsize(arquivo_final)
            }
            
        except HTTPException:
            # Remove temp se houver erro
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
        except Exception as e:
            # Remove temp se houver erro
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise HTTPException(status_code=500, detail=f"Erro ao processar upload: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro inesperado: {str(e)}")


@app.get("/list-music")
def list_music():
    """
    Lista todas as músicas disponíveis no sistema.
    """
    try:
        music_dir = "music"
        if not os.path.exists(music_dir):
            return {"ok": True, "musics": []}
        
        musicas = []
        for arquivo in os.listdir(music_dir):
            if arquivo.lower().endswith(('.mp3', '.wav', '.m4a', '.flac', '.ogg')):
                caminho_completo = os.path.join(music_dir, arquivo)
                if os.path.isfile(caminho_completo):
                    nome_sem_ext = Path(arquivo).stem
                    tamanho = os.path.getsize(caminho_completo)
                    
                    # Tenta obter duração
                    try:
                        info = _validar_audio_com_ffprobe(caminho_completo)
                        duracao = info["duration"]
                    except:
                        duracao = None
                    
                    musicas.append({
                        "name": nome_sem_ext,
                        "filename": arquivo,
                        "size_bytes": tamanho,
                        "duration": duracao
                    })
        
        return {"ok": True, "musics": musicas, "count": len(musicas)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao listar músicas: {str(e)}")


@app.delete("/delete-music/{music_name}")
def delete_music(music_name: str):
    """
    Deleta uma música do sistema.
    """
    try:
        # Sanitiza o nome
        music_name = "".join(c for c in music_name if c.isalnum() or c in (' ', '-', '_')).strip()
        music_name = music_name.replace(' ', '_')
        
        if not music_name:
            raise HTTPException(status_code=400, detail="Nome da música inválido")
        
        arquivo = os.path.join("music", f"{music_name}.mp3")
        
        if not os.path.exists(arquivo):
            raise HTTPException(status_code=404, detail=f"Música '{music_name}' não encontrada")
        
        os.remove(arquivo)
        
        return {"ok": True, "message": f"Música '{music_name}' deletada com sucesso"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao deletar música: {str(e)}")


@app.post("/update-session")
def update_session(data: UpdateSessionRequest):
    try:
        cookies_json = json.loads(data.cookie_string)
        cj = http.cookiejar.MozillaCookieJar(SESSION_FILE_PATH)
        
        for cookie_data in cookies_json:
            c = http.cookiejar.Cookie(
                version=0,
                name=cookie_data['name'],
                value=cookie_data['value'],
                port=None,
                port_specified=False,
                domain=cookie_data['domain'],
                domain_specified=True,
                domain_initial_dot=cookie_data['domain'].startswith('.'),
                path=cookie_data['path'],
                path_specified=True,
                secure=cookie_data['secure'],
                expires=int(cookie_data.get('expirationDate', 0)),
                discard=False,
                comment=None,
                comment_url=None,
                rest={'HttpOnly': cookie_data.get('httpOnly', False)},
                rfc2109=False
            )
            cj.set_cookie(c)
        
        cj.save(ignore_discard=True, ignore_expires=True)
        
        return {"status": "ok", "message": "Sessão de cookies atualizada com sucesso e salva em formato Netscape!"}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="A string de cookies fornecida não é um JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar a sessão: {str(e)}")


@app.post("/processar")
def processar_video(data: EditRequest):
    try:
        if not os.path.exists(SESSION_FILE_PATH):
            raise HTTPException(status_code=400, detail="Arquivo de sessão de cookies não encontrado. Por favor, use o endpoint /update-session primeiro.")

        video_path = baixar_reel(data.url, cookie_file_path=SESSION_FILE_PATH)
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(status_code=500, detail="Falha ao baixar o vídeo. Verifique se a sessão de cookies ainda é válida.")

        musica_path = os.path.join("music", f"{data.music}.mp3")
        if not os.path.exists(musica_path):
            raise HTTPException(status_code=404, detail=f"Música não encontrada: {musica_path}")

        filename = f"{os.path.basename(video_path).split('.')[0]}_{data.music}.mp4"
        out = os.path.join("processed", filename)
        
        adicionar_musica(
            video_path=video_path,
            musica_path=musica_path,
            segundo_video=data.impact_video,
            output_path=out,
            music_impact=data.impact_music
        )

        # Remove vídeo original após processamento bem-sucedido
        # Seguindo padrão do sistema: não persistir vídeos baixados
        try:
            if os.path.exists(video_path):
                os.remove(video_path)
                print(f"✅ Vídeo original removido: {video_path}")
        except Exception as e:
            # Não falha o processamento se não conseguir remover
            print(f"⚠️ Aviso: Não foi possível remover vídeo original {video_path}: {e}")

        if data.return_format == "url":
            return {"ok": True, "filename": filename, "video_url": f"/videos/{filename}"}
        elif data.return_format == "base64":
            with open(out, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            return {"ok": True, "filename": filename, "video_base64": encoded}
        elif data.return_format == "path":
            return {"ok": True, "filename": filename, "video_path": out}
        elif data.return_format == "file":
            return FileResponse(out, media_type="video/mp4", filename=filename)
        else:
            raise HTTPException(
                status_code=400,
                detail="Formato inválido. Use: url, base64, path ou file."
            )

    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro inesperado no processamento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado no processamento: {str(e)}")


@app.delete("/cleanup")
def cleanup_videos():
    pastas = ["videos", "processed"]
    removidos = []

    try:
        for pasta in pastas:
            if os.path.exists(pasta):
                for arquivo in os.listdir(pasta):
                    caminho = os.path.join(pasta, arquivo)
                    if os.path.isfile(caminho):
                        os.remove(caminho)
                        removidos.append(caminho)

        return {"ok": True, "removidos": removidos}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))