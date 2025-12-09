from typing import Optional, List
from sqlalchemy.orm import Session
from app.domain.entities.music import Music
from app.domain.repositories.music_repository import IMusicRepository
from app.Models.music_model import Music


class MusicRepository(IMusicRepository):
    """Implementação do repositório de músicas"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, music: Music) -> Music:
        """Cria uma nova música"""
        db_music = Music(
            user_id=music.user_id,
            name=music.name,
            filename=music.filename,
            file_path=music.file_path,
            duration=music.duration,
            file_size=music.file_size
        )
        self.db.add(db_music)
        self.db.commit()
        self.db.refresh(db_music)
        return db_music.to_domain()
    
    def get_by_id(self, music_id: int) -> Optional[Music]:
        """Busca música por ID"""
        db_music = self.db.query(Music).filter(Music.id == music_id).first()
        return db_music.to_domain() if db_music else None
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Music]:
        """Lista músicas de um usuário"""
        db_musics = self.db.query(Music).filter(
            Music.user_id == user_id
        ).offset(skip).limit(limit).all()
        return [music.to_domain() for music in db_musics]
    
    def get_all(self, skip: int = 0, limit: int = 100) -> List[Music]:
        """Lista todas as músicas"""
        db_musics = self.db.query(Music).offset(skip).limit(limit).all()
        return [music.to_domain() for music in db_musics]
    
    def update(self, music: Music) -> Music:
        """Atualiza uma música"""
        db_music = self.db.query(Music).filter(Music.id == music.id).first()
        if not db_music:
            raise ValueError(f"Música com ID {music.id} não encontrada")
        
        db_music.name = music.name
        db_music.filename = music.filename
        db_music.file_path = music.file_path
        db_music.duration = music.duration
        db_music.file_size = music.file_size
        
        self.db.commit()
        self.db.refresh(db_music)
        return db_music.to_domain()
    
    def delete(self, music_id: int) -> bool:
        """Deleta uma música"""
        db_music = self.db.query(Music).filter(Music.id == music_id).first()
        if not db_music:
            return False
        
        self.db.delete(db_music)
        self.db.commit()
        return True
    
    def get_by_name_and_user(self, name: str, user_id: int) -> Optional[Music]:
        """Busca música por nome e usuário"""
        db_music = self.db.query(Music).filter(
            Music.name == name,
            Music.user_id == user_id
        ).first()
        return db_music.to_domain() if db_music else None

