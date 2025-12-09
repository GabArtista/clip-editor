from pydantic import HttpUrl, ValidationError
from typing import Optional


def validate_webhook_url(url: Optional[str]) -> Optional[str]:
    """
    Valida se a URL do webhook é válida
    
    Args:
        url: URL a ser validada
    
    Returns:
        URL validada ou None
    
    Raises:
        ValueError: Se a URL for inválida
    """
    if not url:
        return None
    
    url = url.strip()
    if not url:
        return None
    
    try:
        # Usa Pydantic para validar URL
        validated = HttpUrl(url)
        return str(validated)
    except ValidationError:
        raise ValueError("URL do webhook inválida. Deve ser uma URL HTTP/HTTPS válida.")

