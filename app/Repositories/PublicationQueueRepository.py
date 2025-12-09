from typing import Optional, List
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from app.domain.entities.publication_queue import PublicationQueue, PublicationStatus
from app.domain.repositories.publication_queue_repository import IPublicationQueueRepository
from app.Models.publication_queue_model import PublicationQueue


class PublicationQueueRepository(IPublicationQueueRepository):
    """Implementação do repositório de fila de publicações"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, publication: PublicationQueue) -> PublicationQueue:
        """Cria uma nova publicação na fila"""
        db_publication = PublicationQueue(
            user_id=publication.user_id,
            video_path=publication.video_path,
            video_url=publication.video_url,
            description=publication.description,
            scheduled_date=publication.scheduled_date,
            status=publication.status
        )
        self.db.add(db_publication)
        self.db.commit()
        self.db.refresh(db_publication)
        return db_publication.to_domain()
    
    def get_by_id(self, publication_id: int) -> Optional[PublicationQueue]:
        """Busca publicação por ID"""
        db_publication = self.db.query(PublicationQueue).filter(
            PublicationQueue.id == publication_id
        ).first()
        return db_publication.to_domain() if db_publication else None
    
    def get_by_user_id(self, user_id: int, skip: int = 0, limit: int = 100) -> List[PublicationQueue]:
        """Lista publicações de um usuário"""
        db_publications = self.db.query(PublicationQueue).filter(
            PublicationQueue.user_id == user_id
        ).offset(skip).limit(limit).order_by(PublicationQueue.scheduled_date.desc()).all()
        return [pub.to_domain() for pub in db_publications]
    
    def get_pending_for_month(self, user_id: int, year: int, month: int) -> List[PublicationQueue]:
        """Lista publicações pendentes de um mês específico"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        db_publications = self.db.query(PublicationQueue).filter(
            and_(
                PublicationQueue.user_id == user_id,
                PublicationQueue.scheduled_date >= start_date,
                PublicationQueue.scheduled_date < end_date,
                PublicationQueue.status.in_([PublicationStatus.PENDING, PublicationStatus.SCHEDULED])
            )
        ).order_by(PublicationQueue.scheduled_date).all()
        return [pub.to_domain() for pub in db_publications]
    
    def get_scheduled_for_today(self) -> List[PublicationQueue]:
        """Lista publicações agendadas para hoje"""
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_end = datetime.now().replace(hour=23, minute=59, second=59, microsecond=999999)
        
        db_publications = self.db.query(PublicationQueue).filter(
            and_(
                PublicationQueue.scheduled_date >= today_start,
                PublicationQueue.scheduled_date <= today_end,
                PublicationQueue.status == PublicationStatus.SCHEDULED
            )
        ).order_by(PublicationQueue.scheduled_date).all()
        return [pub.to_domain() for pub in db_publications]
    
    def count_by_user_and_month(self, user_id: int, year: int, month: int) -> int:
        """Conta publicações agendadas de um usuário em um mês"""
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)
        
        count = self.db.query(func.count(PublicationQueue.id)).filter(
            and_(
                PublicationQueue.user_id == user_id,
                PublicationQueue.scheduled_date >= start_date,
                PublicationQueue.scheduled_date < end_date,
                PublicationQueue.status.in_([PublicationStatus.PENDING, PublicationStatus.SCHEDULED])
            )
        ).scalar()
        return count or 0
    
    def update(self, publication: PublicationQueue) -> PublicationQueue:
        """Atualiza uma publicação"""
        db_publication = self.db.query(PublicationQueue).filter(
            PublicationQueue.id == publication.id
        ).first()
        if not db_publication:
            raise ValueError(f"Publicação com ID {publication.id} não encontrada")
        
        db_publication.video_path = publication.video_path
        db_publication.video_url = publication.video_url
        db_publication.description = publication.description
        db_publication.scheduled_date = publication.scheduled_date
        db_publication.published_date = publication.published_date
        db_publication.status = publication.status
        db_publication.error_message = publication.error_message
        
        self.db.commit()
        self.db.refresh(db_publication)
        return db_publication.to_domain()
    
    def delete(self, publication_id: int) -> bool:
        """Deleta uma publicação"""
        db_publication = self.db.query(PublicationQueue).filter(
            PublicationQueue.id == publication_id
        ).first()
        if not db_publication:
            return False
        
        self.db.delete(db_publication)
        self.db.commit()
        return True

