import os
from typing import Optional

# Limites de tamanho (em bytes)
MAX_MUSIC_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
MAX_VIDEO_FILE_SIZE = 500 * 1024 * 1024  # 500 MB

ALLOWED_AUDIO_EXTENSIONS = {'.mp3', '.wav', '.m4a', '.aac'}
ALLOWED_VIDEO_EXTENSIONS = {'.mp4', '.mov', '.avi', '.mkv'}


def validate_file_size(file_path: str, max_size: int, file_type: str = "arquivo") -> None:
    """
    Valida tamanho do arquivo
    
    Args:
        file_path: Caminho do arquivo
        max_size: Tamanho máximo em bytes
        file_type: Tipo do arquivo para mensagem de erro
    
    Raises:
        ValueError: Se o arquivo exceder o tamanho máximo
    """
    if not os.path.exists(file_path):
        raise ValueError(f"{file_type} não encontrado")
    
    file_size = os.path.getsize(file_path)
    if file_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        file_size_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"{file_type} muito grande. "
            f"Tamanho: {file_size_mb:.2f} MB. "
            f"Máximo permitido: {max_size_mb:.2f} MB"
        )


def validate_audio_file(filename: str, file_size: Optional[int] = None) -> None:
    """
    Valida arquivo de áudio
    
    Args:
        filename: Nome do arquivo
        file_size: Tamanho do arquivo em bytes (opcional)
    
    Raises:
        ValueError: Se o arquivo for inválido
    """
    # Valida extensão
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise ValueError(
            f"Formato de áudio não suportado. "
            f"Formatos permitidos: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
        )
    
    # Valida tamanho se fornecido
    if file_size is not None and file_size > MAX_MUSIC_FILE_SIZE:
        max_size_mb = MAX_MUSIC_FILE_SIZE / (1024 * 1024)
        file_size_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"Arquivo de música muito grande. "
            f"Tamanho: {file_size_mb:.2f} MB. "
            f"Máximo permitido: {max_size_mb:.2f} MB"
        )


def validate_video_file(filename: str, file_size: Optional[int] = None) -> None:
    """
    Valida arquivo de vídeo
    
    Args:
        filename: Nome do arquivo
        file_size: Tamanho do arquivo em bytes (opcional)
    
    Raises:
        ValueError: Se o arquivo for inválido
    """
    # Valida extensão
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        raise ValueError(
            f"Formato de vídeo não suportado. "
            f"Formatos permitidos: {', '.join(ALLOWED_VIDEO_EXTENSIONS)}"
        )
    
    # Valida tamanho se fornecido
    if file_size is not None and file_size > MAX_VIDEO_FILE_SIZE:
        max_size_mb = MAX_VIDEO_FILE_SIZE / (1024 * 1024)
        file_size_mb = file_size / (1024 * 1024)
        raise ValueError(
            f"Arquivo de vídeo muito grande. "
            f"Tamanho: {file_size_mb:.2f} MB. "
            f"Máximo permitido: {max_size_mb:.2f} MB"
        )

