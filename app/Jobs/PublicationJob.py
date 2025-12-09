"""
Worker para processar fila de publicações de forma eficiente
Executa diariamente às 00h e processa apenas publicações do mês atual
"""
import asyncio
import logging
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from datetime import timezone as tz
from sqlalchemy.orm import Session
from app.Providers.DatabaseServiceProvider import SessionLocal
from app.Repositories.PublicationQueueRepository import PublicationQueueRepository
from app.Repositories.UserRepository import UserRepository
from app.Services.PublicationService import PublicationService
from app.Services.PublicationSchedulerService import PublicationSchedulerService
from app.infrastructure.external.n8n_client import N8NClient
from app.domain.entities.publication_queue import PublicationStatus

logger = logging.getLogger(__name__)
SP_TIMEZONE = ZoneInfo("America/Sao_Paulo")


class PublicationWorker:
    """Worker assíncrono para processar publicações"""
    
    def __init__(self):
        self.db: Session = SessionLocal()
        self.publication_repo = PublicationQueueRepository(self.db)
        self.user_repo = UserRepository(self.db)
        self.scheduler_service = PublicationSchedulerService(self.publication_repo)
        self.publication_service = PublicationService(
            self.publication_repo,
            self.scheduler_service
        )
    
    async def process_daily_publications(self):
        """
        Processa publicações agendadas para hoje
        Deve ser chamado diariamente às 00h
        """
        try:
            logger.info("Iniciando processamento diário de publicações...")
            
            # Busca publicações do dia
            publications = self.publication_service.process_due_publications()
            
            if not publications:
                logger.info("Nenhuma publicação agendada para hoje")
                return
            
            logger.info(f"Processando {len(publications)} publicações...")
            
            # Processa em lote (máximo 10 por vez para não sobrecarregar)
            batch_size = 10
            for i in range(0, len(publications), batch_size):
                batch = publications[i:i + batch_size]
                await self._process_batch(batch)
                
                # Pequena pausa entre lotes para não sobrecarregar
                if i + batch_size < len(publications):
                    await asyncio.sleep(2)
            
            logger.info("Processamento diário concluído")
            
        except Exception as e:
            logger.error(f"Erro no processamento diário: {str(e)}", exc_info=True)
        finally:
            self.db.close()
    
    async def _process_batch(self, publications: list):
        """Processa um lote de publicações de forma assíncrona"""
        tasks = [self._publish_single(pub) for pub in publications]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _publish_single(self, publication):
        """Publica uma única publicação"""
        try:
            # Busca usuário para obter webhook_url
            user = self.user_repo.get_by_id(publication.user_id)
            if not user or not user.webhook_url:
                self.publication_service.mark_as_failed(
                    publication.id,
                    "Usuário não encontrado ou webhook não configurado"
                )
                logger.warning(f"Publicação {publication.id}: webhook não configurado")
                return
            
            # Prepara dados para publicação no formato exato do N8N
            scheduled_date = publication.scheduled_date
            if scheduled_date:
                # Converte para UTC e formata com Z no final
                if scheduled_date.tzinfo is None:
                    # Se não tem timezone, assume que é SP e converte para UTC
                    scheduled_date = scheduled_date.replace(tzinfo=SP_TIMEZONE)
                # Converte para UTC
                utc_date = scheduled_date.astimezone(tz.utc)
                # Formata no formato ISO com Z (ex: "2025-12-09T00:19:00Z")
                date_str = utc_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            else:
                # Se não tem data agendada, usa agora em UTC
                now_utc = datetime.now(SP_TIMEZONE).astimezone(tz.utc)
                date_str = now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
            
            # Publica via webhook no formato exato especificado
            # video_url já é o link S3 público
            n8n_client = N8NClient(webhook_url=user.webhook_url)
            await n8n_client.publish_video(
                description=publication.description,
                video_link=publication.video_url,  # Link S3 público
                date=date_str
            )
            
            # Marca como concluída
            self.publication_service.mark_as_completed(publication.id)
            logger.info(f"Publicação {publication.id} concluída com sucesso (S3: {publication.video_url})")
            
        except Exception as e:
            error_msg = str(e)
            self.publication_service.mark_as_failed(publication.id, error_msg)
            logger.error(f"Erro ao publicar {publication.id}: {error_msg}", exc_info=True)
    
    def cleanup_old_publications(self, days: int = 30):
        """
        Limpa publicações antigas (completadas há mais de X dias)
        Para economizar espaço no banco
        """
        try:
            # Esta funcionalidade pode ser implementada se necessário
            # Por enquanto, mantemos todas as publicações para histórico
            pass
        except Exception as e:
            logger.error(f"Erro na limpeza: {str(e)}")


# Instância global do worker
_worker_instance: Optional[PublicationWorker] = None


def get_worker() -> PublicationWorker:
    """Obtém instância do worker (singleton)"""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = PublicationWorker()
    return _worker_instance


async def run_daily_worker():
    """Função para ser chamada pelo scheduler diariamente"""
    worker = get_worker()
    await worker.process_daily_publications()

