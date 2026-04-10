import httpx
import logging

logger = logging.getLogger(__name__)


class N8NClient:
    """Cliente simples para envio de vídeos ao N8N via webhook."""

    def __init__(self, webhook_url: str):
        if not webhook_url:
            raise ValueError("Webhook URL é obrigatório")
        self.webhook_url = webhook_url

    async def publish_video(self, description: str, video_link: str, date: str) -> None:
        """
        Envia payload no formato exigido pelo Getlate via N8N.
        
        O N8N espera receber o payload dentro de "body" e transforma para o formato do Getlate:
        {
            "body": {
                "content": "...",  // Descrição do vídeo
                "scheduledFor": "2025-12-09T00:19:00Z",
                "timezone": "America/Sao_Paulo",
                "platforms": [
                    {
                        "platform": "tiktok",
                        "accountId": "69378604f43160a0bc99a841"
                    }
                ],
                "mediaItems": [
                    {
                        "type": "video",
                        "url": "<url>"
                    }
                ]
            }
        }
        """
        payload = {
            "body": {
                "content": description,  # Getlate espera "content" em vez de "description"
                "scheduledFor": date,     # Getlate espera "scheduledFor" em vez de "date"
                "timezone": "America/Sao_Paulo",
                "platforms": [
                    {
                        "platform": "tiktok",
                        "accountId": "69378604f43160a0bc99a841"
                    }
                ],
                "mediaItems": [
                    {
                        "type": "video",
                        "url": video_link
                    }
                ]
            }
        }
        
        logger.info(f"Enviando publicação para N8N: {self.webhook_url}")
        logger.debug(f"Payload: {payload}")
        
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
                logger.info(f"Publicação enviada com sucesso para N8N. Status: {resp.status_code}")
        except httpx.HTTPError as e:
            logger.error(f"Erro HTTP ao enviar para N8N: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Erro ao enviar para N8N: {str(e)}")
            raise


