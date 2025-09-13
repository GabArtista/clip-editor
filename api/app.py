import os
import base64
import json
import http.cookiejar
from fastapi import FastAPI, HTTPException
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

app.mount("/videos", StaticFiles(directory="processed"), name="videos")


class UpdateSessionRequest(BaseModel):
    cookie_string: str


class EditRequest(BaseModel):
    url: str
    music: str
    impact_music: float
    impact_video: float
    return_format: str = "url"


@app.get("/health")
def health():
    return {"status": "ok"}


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