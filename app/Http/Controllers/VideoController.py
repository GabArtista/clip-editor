import os
import base64
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from app.Providers.DatabaseServiceProvider import get_db
from app.Repositories.MusicRepository import MusicRepository, VideoEditRepository, UserRepository
from app.domain.entities.user import User
from app.Http.Middleware.AuthMiddleware import get_current_user
from app.Services.VideoEditService import VideoEditService
from app.infrastructure.storage import S3Client
from scripts.download import baixar_reel
from scripts.edit import adicionar_musica
from config import settings

router = APIRouter(prefix="/api/v1/videos", tags=["Videos"])


class EditVideoRequest(BaseModel):
    """Request para edição de vídeo"""
    url: HttpUrl
    music_id: int
    impact_music: float
    impact_video: float
    return_format: str = "url"


@router.post("/process", status_code=status.HTTP_200_OK)
def process_video(
    request: EditVideoRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Processa vídeo adicionando música"""
    try:
        # Verifica se música existe e pertence ao usuário
        music_repo = MusicRepository(db)
        music = music_repo.get_by_id(request.music_id)
        
        if not music:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Música não encontrada"
            )
        
        if not music.is_owned_by(current_user.id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Música não pertence ao usuário"
            )
        
        # Verifica se arquivo de música existe
        if not os.path.exists(music.file_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Arquivo de música não encontrado no sistema de arquivos"
            )
        
        # Baixa vídeo (usa yt-dlp que suporta múltiplas fontes)
        video_path = baixar_reel(str(request.url), cookie_file_path=settings.SESSION_FILE_PATH)
        if not video_path or not os.path.exists(video_path):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao baixar o vídeo. Verifique se a sessão de cookies ainda é válida."
            )
        
        # Gera nome do arquivo de saída (isolado por usuário)
        user_processed_dir = os.path.join(settings.PROCESSED_DIR, str(current_user.id))
        os.makedirs(user_processed_dir, exist_ok=True)
        
        base = os.path.splitext(os.path.basename(video_path))[0]
        out = os.path.join(
            user_processed_dir,
            f"{base}_{music.name}_iv{request.impact_video:.2f}_im{request.impact_music:.2f}.mp4"
        )
        
        # Processa vídeo
        adicionar_musica(
            video_path=video_path,
            musica_path=music.file_path,
            segundo_video=request.impact_video,
            output_path=out,
            music_impact=request.impact_music
        )
        
        if not os.path.exists(out):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Falha ao processar vídeo"
            )
        
        filename = os.path.basename(out)
        
        # NOVO FLUXO: Upload para S3 e cria registro para aprovação
        try:
            s3_client = S3Client()
            video_edit_repo = VideoEditRepository(db)
            video_edit_service = VideoEditService(video_edit_repo, s3_client)
            
            # Cria registro e faz upload para S3
            video_edit = video_edit_service.create_video_edit(
                user_id=current_user.id,
                music_id=request.music_id,
                local_file_path=out
            )
            
            # Retorna dados do vídeo editado
            response_data = {
                "ok": True,
                "video_edit_id": video_edit.id,
                "preview_url": video_edit.preview_url,  # URL temporária (5 min)
                "s3_url": video_edit.s3_url,  # URL pública permanente
                "expires_at": video_edit.expires_at.isoformat() if video_edit.expires_at else None,
                "message": "Vídeo processado e enviado para S3. Use o preview_url para visualizar. Aprove em até 5 minutos."
            }
            
        except Exception as e:
            # Se falhar S3, retorna URL local como fallback
            video_url = f"/api/v1/videos/files/{current_user.id}/{filename}"
            response_data = {
                "ok": True,
                "filename": filename,
                "video_url": video_url,
                "warning": f"Erro ao enviar para S3: {str(e)}. Usando armazenamento local."
            }
        
        if request.return_format == "url":
            return response_data
        elif request.return_format == "base64":
            with open(out, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            response_data["video_base64"] = encoded
            return response_data
        elif request.return_format == "path":
            response_data["video_path"] = out
            return response_data
        elif request.return_format == "file":
            return FileResponse(out, media_type="video/mp4", filename=filename)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar vídeo: {str(e)}"
        )


@router.get("/files/{user_id}/{filename}")
def get_video_file(user_id: int, filename: str, current_user: User = Depends(get_current_user)):
    """Serve arquivo de vídeo processado (isolado por usuário)"""
    # Verifica se o usuário está acessando seu próprio arquivo
    if current_user.id != user_id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar este arquivo"
        )
    
    file_path = os.path.join(settings.PROCESSED_DIR, str(user_id), filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado"
        )
    return FileResponse(file_path, media_type="video/mp4", filename=filename)

