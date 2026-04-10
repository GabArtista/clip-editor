import os
import base64
import logging
import threading
from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, HttpUrl
from app.Providers.DatabaseServiceProvider import get_db
from app.Repositories.MusicRepository import MusicRepository
from app.Repositories.VideoEditRepository import VideoEditRepository
from app.domain.entities.user import User
from app.Http.Middleware.AuthMiddleware import get_current_user
from app.Services.VideoEditService import VideoEditService
from app.infrastructure.storage import S3Client
from app.Jobs.VideoUploadJob import process_video_upload
from scripts.download import baixar_reel
from scripts.edit import adicionar_musica
from config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/videos", tags=["Videos"])


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
        
        # Busca user_uuid para usar em caminhos
        from app.Models.User import User as UserModel
        db_user = db.query(UserModel).filter(UserModel.id == current_user.id).first()
        user_uuid = str(db_user.uuid) if db_user else str(current_user.id)
        
        # Gera nome do arquivo de saída (isolado por usuário usando UUID)
        user_processed_dir = os.path.join(settings.PROCESSED_DIR, user_uuid)
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
        
        # FLUXO INTELIGENTE: Comportamento diferente baseado em return_format
        if request.return_format == "url":
            # Caso 1: Processar para aprovação/publicação (sempre cria registro)
            s3_client = S3Client()
            video_edit_repo = VideoEditRepository(db)
            video_edit_service = VideoEditService(video_edit_repo, s3_client)
            
            try:
                # Cria registro imediatamente (status: PROCESSING_UPLOAD)
                video_edit = video_edit_service.create_video_edit_without_upload(
                    user_id=current_user.id,
                    music_id=request.music_id,
                    local_file_path=out,
                    base_url=f"http://{settings.APP_HOST}:{settings.APP_PORT}",
                    user_uuid=user_uuid
                )
                
                # Agenda upload S3 em background (thread)
                def upload_in_background():
                    try:
                        process_video_upload(video_edit.id)
                    except Exception as e:
                        logger.error(f"Erro no upload background para vídeo {video_edit.id}: {e}")
                
                upload_thread = threading.Thread(target=upload_in_background, daemon=True)
                upload_thread.start()
                
                # Retorna resposta rápida com video_edit_id
                response_data = {
                    "ok": True,
                    "video_edit_id": video_edit.id,
                    "preview_url": video_edit.preview_url,  # URL local temporária
                    "s3_url": video_edit.s3_url,  # URL local temporária (será atualizada após S3)
                    "expires_at": video_edit.expires_at.isoformat() if video_edit.expires_at else None,
                    "status": video_edit.status.value,
                    "message": "Vídeo processado. Upload S3 em andamento. Use o preview_url para visualizar. Aprove em até 5 minutos."
                }
                
            except Exception as e:
                logger.error(f"Erro ao criar registro de vídeo: {e}", exc_info=True)
                # Fallback: retorna apenas URL local usando user_uuid
                video_url = f"/api/v1/videos/files/{user_uuid}/{filename}"
                response_data = {
                    "ok": True,
                    "filename": filename,
                    "video_url": video_url,
                    "warning": f"Erro ao criar registro: {str(e)}. Processe novamente."
                }
            
            return response_data
        else:
            # Caso 2: Processar livremente (file, base64, path) - NÃO cria registro
            if request.return_format == "base64":
                with open(out, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                return {
                    "ok": True,
                    "filename": filename,
                    "video_base64": encoded
                }
            elif request.return_format == "path":
                return {
                    "ok": True,
                    "filename": filename,
                    "video_path": out
                }
            elif request.return_format == "file":
                return FileResponse(out, media_type="video/mp4", filename=filename)
            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Formato de retorno inválido: {request.return_format}. Use: url, file, base64, path"
                )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao processar vídeo: {str(e)}"
        )


@router.get("/files/{user_uuid}/{filename}")
def get_video_file(user_uuid: str, filename: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Serve arquivo de vídeo processado (isolado por usuário usando UUID)"""
    # Busca usuário pelo UUID para validar acesso
    from app.Repositories.UserRepository import UserRepository
    user_repo = UserRepository(db)
    file_owner = user_repo.get_by_uuid(user_uuid)
    
    if not file_owner:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado"
        )
    
    # Verifica se o usuário está acessando seu próprio arquivo
    if current_user.id != file_owner.id and not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não tem permissão para acessar este arquivo"
        )
    
    file_path = os.path.join(settings.PROCESSED_DIR, user_uuid, filename)
    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo não encontrado"
        )
    return FileResponse(file_path, media_type="video/mp4", filename=filename)

