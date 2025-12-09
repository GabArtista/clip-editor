import httpx
from typing import Dict, Any
from app.config import settings


class N8NClient:
    """Cliente para integração com webhook N8N"""
    
    def __init__(self, webhook_url: str = None):
        self.webhook_url = webhook_url or settings.N8N_WEBHOOK_URL
    
    async def publish_video(self, description: str, video_link: str, date: str) -> Dict[str, Any]:
        """
        Publica vídeo via webhook N8N no formato exato:
        {
            "description": "...",
            "videoLink": "...",
            "date": "2025-12-09T00:19:00Z"
        }
        
        Args:
            description: Descrição do vídeo
            video_link: URL do vídeo (será enviado como "videoLink")
            date: Data no formato ISO UTC com Z (ex: "2025-12-09T00:19:00Z")
        
        Returns:
            Resposta do webhook
        """
        payload = {
            "description": description,
            "videoLink": video_link,  # Formato exato: videoLink (camelCase)
            "date": date  # Formato: "2025-12-09T00:19:00Z"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(self.webhook_url, json=payload)
                response.raise_for_status()
                return {
                    "success": True,
                    "status_code": response.status_code,
                    "data": response.json() if response.content else {}
                }
            except httpx.HTTPError as e:
                raise Exception(f"Erro ao publicar vídeo no N8N: {str(e)}")
            except Exception as e:
                raise Exception(f"Erro inesperado ao publicar vídeo: {str(e)}")

