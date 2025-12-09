from typing import List, Optional
from app.domain.entities.music import Music
from app.domain.repositories.music_repository import IMusicRepository


class MusicService:
    """Serviço de domínio para músicas"""
    
    def __init__(self, music_repository: IMusicRepository):
        self.music_repository = music_repository
    
    def create_music(
        self,
        user_id: int,
        name: str,
        filename: str,
        file_path: str,
        duration: Optional[float] = None,
        file_size: Optional[int] = None
    ) -> Music:
        """Cria uma nova música"""
        # Verifica se já existe música com mesmo nome para o usuário
        existing = self.music_repository.get_by_name_and_user(name, user_id)
        if existing:
            raise ValueError("Já existe uma música com este nome para este usuário")
        
        music = Music(
            user_id=user_id,
            name=name,
            filename=filename,
            file_path=file_path,
            duration=duration,
            file_size=file_size
        )
        
        return self.music_repository.create(music)
    
    def get_user_musics(self, user_id: int, skip: int = 0, limit: int = 100) -> List[Music]:
        """Lista músicas de um usuário"""
        return self.music_repository.get_by_user_id(user_id, skip, limit)
    
    def get_music(self, music_id: int, user_id: Optional[int] = None) -> Optional[Music]:
        """Busca uma música"""
        music = self.music_repository.get_by_id(music_id)
        if not music:
            return None
        
        # Se user_id fornecido, verifica se pertence ao usuário
        if user_id and not music.is_owned_by(user_id):
            return None
        
        return music
    
    def update_music(self, music_id: int, user_id: int, name: Optional[str] = None) -> Music:
        """Atualiza uma música"""
        music = self.music_repository.get_by_id(music_id)
        if not music:
            raise ValueError("Música não encontrada")
        
        if not music.is_owned_by(user_id):
            raise ValueError("Música não pertence ao usuário")
        
        if name:
            # Verifica se novo nome já existe
            existing = self.music_repository.get_by_name_and_user(name, user_id)
            if existing and existing.id != music_id:
                raise ValueError("Já existe uma música com este nome")
            music.name = name
        
        return self.music_repository.update(music)
    
    def delete_music(self, music_id: int, user_id: int) -> bool:
        """Deleta uma música"""
        music = self.music_repository.get_by_id(music_id)
        if not music:
            return False
        
        if not music.is_owned_by(user_id):
            raise ValueError("Música não pertence ao usuário")
        
        return self.music_repository.delete(music_id)

