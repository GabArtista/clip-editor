import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.infrastructure.database.base import get_db
from app.infrastructure.repositories import MusicRepository
from app.domain.services.music_service import MusicService
from app.domain.entities.user import User
from app.application.auth import get_current_user
from app.application.dto.music_dto import MusicCreateDTO, MusicUpdateDTO, MusicResponseDTO
from app.config import settings
from app.application.utils import get_audio_duration
from app.application.validators import validate_audio_file

router = APIRouter(prefix="/api/v1/musics", tags=["Musics"])


@router.post("", response_model=MusicResponseDTO, status_code=status.HTTP_201_CREATED)
async def upload_music(
    file: UploadFile = File(...),
    name: str = Query(..., min_length=1, max_length=255),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Faz upload de uma música"""
    try:
        # Valida arquivo
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nome do arquivo não fornecido"
            )
        
        # Valida formato e tamanho
        try:
            validate_audio_file(file.filename)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Cria diretório se não existir
        user_music_dir = os.path.join(settings.MUSIC_DIR, str(current_user.id))
        os.makedirs(user_music_dir, exist_ok=True)
        
        # Gera nome único para o arquivo
        file_ext = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = os.path.join(user_music_dir, unique_filename)
        
        # Salva arquivo
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Valida tamanho do arquivo salvo
        file_size = os.path.getsize(file_path)
        try:
            validate_audio_file(file.filename, file_size)
        except ValueError as e:
            # Remove arquivo se inválido
            os.remove(file_path)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        
        # Obtém duração
        try:
            duration = get_audio_duration(file_path)
        except Exception:
            duration = None
        
        # Cria registro no banco
        music_repo = MusicRepository(db)
        music_service = MusicService(music_repo)
        
        music = music_service.create_music(
            user_id=current_user.id,
            name=name,
            filename=unique_filename,
            file_path=file_path,
            duration=duration,
            file_size=file_size
        )
        
        return MusicResponseDTO(
            id=music.id,
            user_id=music.user_id,
            name=music.name,
            filename=music.filename,
            file_path=music.file_path,
            duration=music.duration,
            file_size=music.file_size,
            created_at=music.created_at,
            updated_at=music.updated_at
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Remove arquivo se houve erro
        if 'file_path' in locals() and os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao fazer upload da música: {str(e)}"
        )


@router.get("", response_model=List[MusicResponseDTO])
def list_musics(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lista músicas do usuário atual"""
    try:
        music_repo = MusicRepository(db)
        music_service = MusicService(music_repo)
        
        musics = music_service.get_user_musics(current_user.id, skip=skip, limit=limit)
        
        return [
            MusicResponseDTO(
                id=music.id,
                user_id=music.user_id,
                name=music.name,
                filename=music.filename,
                file_path=music.file_path,
                duration=music.duration,
                file_size=music.file_size,
                created_at=music.created_at,
                updated_at=music.updated_at
            )
            for music in musics
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao listar músicas: {str(e)}"
        )


@router.get("/{music_id}", response_model=MusicResponseDTO)
def get_music(
    music_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Obtém uma música por ID"""
    try:
        music_repo = MusicRepository(db)
        music_service = MusicService(music_repo)
        
        music = music_service.get_music(music_id, current_user.id)
        
        if not music:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Música não encontrada"
            )
        
        return MusicResponseDTO(
            id=music.id,
            user_id=music.user_id,
            name=music.name,
            filename=music.filename,
            file_path=music.file_path,
            duration=music.duration,
            file_size=music.file_size,
            created_at=music.created_at,
            updated_at=music.updated_at
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao buscar música: {str(e)}"
        )


@router.put("/{music_id}", response_model=MusicResponseDTO)
def update_music(
    music_id: int,
    music_data: MusicUpdateDTO,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Atualiza uma música"""
    try:
        music_repo = MusicRepository(db)
        music_service = MusicService(music_repo)
        
        update_data = music_data.dict(exclude_unset=True)
        music = music_service.update_music(music_id, current_user.id, **update_data)
        
        return MusicResponseDTO(
            id=music.id,
            user_id=music.user_id,
            name=music.name,
            filename=music.filename,
            file_path=music.file_path,
            duration=music.duration,
            file_size=music.file_size,
            created_at=music.created_at,
            updated_at=music.updated_at
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao atualizar música: {str(e)}"
        )


@router.delete("/{music_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_music(
    music_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Deleta uma música"""
    try:
        music_repo = MusicRepository(db)
        music_service = MusicService(music_repo)
        
        # Busca música para obter caminho do arquivo
        music = music_service.get_music(music_id, current_user.id)
        if not music:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Música não encontrada"
            )
        
        # Deleta do banco
        success = music_service.delete_music(music_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Música não encontrada"
            )
        
        # Deleta arquivo físico
        if os.path.exists(music.file_path):
            try:
                os.remove(music.file_path)
            except Exception as e:
                # Log erro mas não falha a requisição
                print(f"Erro ao deletar arquivo {music.file_path}: {e}")
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao deletar música: {str(e)}"
        )

