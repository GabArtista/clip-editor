from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
import base64

from scripts.download import baixar_reel
from scripts.edit import adicionar_musica

app = FastAPI(title="FALA Editor API")

# Garante que as pastas existem
os.makedirs("processed", exist_ok=True)
os.makedirs("videos", exist_ok=True)

# Monta rota estática para servir vídeos processados
app.mount("/videos", StaticFiles(directory="processed"), name="videos")


class EditRequest(BaseModel):
    url: str
    music: str
    impact_music: float
    impact_video: float
    return_format: str = "url"  
    # valores possíveis: "url", "base64", "path", "file"


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/processar")
def processar_video(data: EditRequest):
    try:
        # 1. Baixar vídeo
        video_path = baixar_reel(data.url)
        if not os.path.exists(video_path):
            raise HTTPException(status_code=500, detail="Falha ao baixar o vídeo")

        # 2. Localizar música
        musica_path = os.path.join("music", f"{data.music}.mp3")
        if not os.path.exists(musica_path):
            raise HTTPException(status_code=404, detail=f"Música não encontrada: {musica_path}")

        # 3. Definir saída
        base = os.path.splitext(os.path.basename(video_path))[0]
        safe_music = os.path.splitext(os.path.basename(musica_path))[0]
        filename = f"{base}_{safe_music}_iv{data.impact_video:.2f}_im{data.impact_music:.2f}.mp4"
        out = os.path.join("processed", filename)

        # 4. Editar vídeo
        adicionar_musica(
            video_path=video_path,
            musica_path=musica_path,
            segundo_video=data.impact_video,
            output_path=out,
            music_impact=data.impact_music,
            debug=True,
        )

        # 5. Retornos flexíveis
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

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/cleanup")
def cleanup_videos():
    """
    Limpa todos os vídeos das pastas videos/ e processed/
    """
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
        raise HTTPException(status_code=500, detail=f"Erro ao limpar vídeos: {str(e)}")
