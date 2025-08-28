from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import os
from scripts.download import baixar_reel
from scripts.edit import adicionar_musica

app = FastAPI(title="FALA Editor API")

class EditRequest(BaseModel):
    url: str
    music: str
    impact_music: float
    impact_video: float

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/processar")
def processar_video(data: EditRequest):
    try:
        os.makedirs("processed", exist_ok=True)
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
        out = os.path.join(
            "processed",
            f"{base}_{safe_music}_iv{data.impact_video:.2f}_im{data.impact_music:.2f}.mp4"
        )
        # 4. Editar
        adicionar_musica(
            video_path=video_path,
            musica_path=musica_path,
            segundo_video=data.impact_video,
            output_path=out,
            music_impact=data.impact_music,
            debug=True,
        )
        return {"ok": True, "output": out, "video": video_path, "music": musica_path}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))