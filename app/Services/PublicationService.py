from typing import List, Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from app.domain.entities.publication_queue import PublicationQueue, PublicationStatus
from app.domain.repositories.publication_queue_repository import IPublicationQueueRepository
from app.Services.PublicationSchedulerService import PublicationSchedulerService

SP_TIMEZONE = ZoneInfo("America/Sao_Paulo")


class PublicationService:
    """Serviço de domínio para publicações"""
    
    def __init__(
        self,
        publication_repo: IPublicationQueueRepository,
        scheduler_service: PublicationSchedulerService
    ):
        self.publication_repo = publication_repo
        self.scheduler_service = scheduler_service
    
    def queue_publication(
        self,
        user_id: int,
        video_path: str,  # Pode ser link S3 ou caminho local
        video_url: str,   # URL pública (S3 ou local)
        description: str
    ) -> PublicationQueue:
        """
        Adiciona publicação na fila e agenda automaticamente
        
        Args:
            user_id: ID do usuário
            video_path: Caminho do vídeo (S3 URL ou caminho local)
            video_url: URL pública do vídeo (S3 URL ou URL local)
            description: Descrição para publicação
        
        Retorna a publicação criada com data agendada
        """
        # Calcula próxima data disponível
        dates = self.scheduler_service.calculate_scheduled_dates(user_id, 1)
        
        if not dates:
            raise ValueError("Não foi possível agendar publicação. Limite mensal atingido.")
        
        scheduled_date = dates[0]
        
        # Cria publicação
        # video_path agora pode ser link S3 (para vídeos aprovados)
        publication = PublicationQueue(
            user_id=user_id,
            video_path=video_path,  # S3 URL ou caminho local
            video_url=video_url,     # URL pública (S3)
            description=description,
            scheduled_date=scheduled_date,
            status=PublicationStatus.SCHEDULED
        )
        
        return self.publication_repo.create(publication)
    
    def get_user_queue(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PublicationQueue]:
        """Lista publicações do usuário"""
        return self.publication_repo.get_by_user_id(user_id, skip, limit)
    
    def cancel_publication(self, publication_id: int, user_id: int) -> bool:
        """Cancela uma publicação"""
        publication = self.publication_repo.get_by_id(publication_id)
        if not publication or publication.user_id != user_id:
            return False
        
        if publication.status in [PublicationStatus.COMPLETED, PublicationStatus.PROCESSING]:
            return False
        
        publication.status = PublicationStatus.CANCELLED
        self.publication_repo.update(publication)
        return True
    
    def process_due_publications(self) -> List[PublicationQueue]:
        """
        Processa publicações que estão agendadas para hoje
        Retorna lista de publicações processadas
        """
        now = datetime.now(SP_TIMEZONE)
        today_publications = self.publication_repo.get_scheduled_for_today()
        
        processed = []
        for pub in today_publications:
            # Verifica se é hora de publicar (com margem de 1 hora)
            if pub.scheduled_date and pub.scheduled_date <= now:
                # Verifica se não está vencida (realoca se necessário)
                if pub.is_past_due(now):
                    pub = self.scheduler_service.reschedule_past_due(pub, now)
                    self.publication_repo.update(pub)
                else:
                    # Marca como processando
                    pub.status = PublicationStatus.PROCESSING
                    self.publication_repo.update(pub)
                    processed.append(pub)
        
        return processed
    
    def mark_as_completed(self, publication_id: int) -> bool:
        """Marca publicação como concluída"""
        publication = self.publication_repo.get_by_id(publication_id)
        if not publication:
            return False
        
        publication.status = PublicationStatus.COMPLETED
        publication.published_date = datetime.now(SP_TIMEZONE)
        self.publication_repo.update(publication)
        return True
    
    def mark_as_failed(self, publication_id: int, error_message: str) -> bool:
        """Marca publicação como falhada"""
        publication = self.publication_repo.get_by_id(publication_id)
        if not publication:
            return False
        
        publication.status = PublicationStatus.FAILED
        publication.error_message = error_message
        self.publication_repo.update(publication)
        return True

