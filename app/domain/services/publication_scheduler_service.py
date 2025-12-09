from datetime import datetime, timedelta
from typing import List, Optional
from zoneinfo import ZoneInfo
from app.domain.entities.publication_queue import PublicationQueue, PublicationStatus
from app.domain.repositories.publication_queue_repository import IPublicationQueueRepository

# Timezone de São Paulo
SP_TIMEZONE = ZoneInfo("America/Sao_Paulo")

# Horários permitidos (10h, 13h, 17h)
ALLOWED_HOURS = [10, 13, 17]
MAX_PUBLICATIONS_PER_MONTH = 10


class PublicationSchedulerService:
    """Serviço para agendar publicações respeitando as regras"""
    
    def __init__(self, publication_repo: IPublicationQueueRepository):
        self.publication_repo = publication_repo
    
    def calculate_scheduled_dates(
        self,
        user_id: int,
        count: int,
        start_month: Optional[datetime] = None
    ) -> List[datetime]:
        """
        Calcula datas agendadas para publicações respeitando as regras:
        - Máximo 10 por mês
        - Horários: 10h, 13h, 17h (rotacionando)
        - Distribuir bem ao longo do mês
        
        Args:
            user_id: ID do usuário
            count: Quantidade de publicações a agendar
            start_month: Mês inicial (se None, usa mês atual)
        
        Returns:
            Lista de datas agendadas
        """
        if start_month is None:
            now = datetime.now(SP_TIMEZONE)
            start_month = datetime(now.year, now.month, 1, tzinfo=SP_TIMEZONE)
        else:
            start_month = start_month.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if start_month.tzinfo is None:
                start_month = start_month.replace(tzinfo=SP_TIMEZONE)
        
        scheduled_dates = []
        current_month = start_month
        remaining = count
        hour_index = 0
        
        while remaining > 0:
            # Conta quantas publicações já estão agendadas neste mês
            existing_count = self.publication_repo.count_by_user_and_month(
                user_id, current_month.year, current_month.month
            )
            
            # Calcula quantas podem ser agendadas neste mês
            available_slots = MAX_PUBLICATIONS_PER_MONTH - existing_count
            to_schedule_this_month = min(remaining, available_slots)
            
            if to_schedule_this_month > 0:
                # Calcula datas para este mês
                month_dates = self._distribute_dates_in_month(
                    current_month,
                    to_schedule_this_month,
                    hour_index
                )
                scheduled_dates.extend(month_dates)
                hour_index = (hour_index + to_schedule_this_month) % len(ALLOWED_HOURS)
                remaining -= to_schedule_this_month
            
            # Se ainda há publicações para agendar, vai para o próximo mês
            if remaining > 0:
                if current_month.month == 12:
                    current_month = datetime(current_month.year + 1, 1, 1, tzinfo=SP_TIMEZONE)
                else:
                    current_month = datetime(
                        current_month.year, current_month.month + 1, 1, tzinfo=SP_TIMEZONE
                    )
        
        return scheduled_dates
    
    def _distribute_dates_in_month(
        self,
        month_start: datetime,
        count: int,
        start_hour_index: int
    ) -> List[datetime]:
        """
        Distribui datas ao longo do mês de forma equilibrada
        
        Args:
            month_start: Primeiro dia do mês
            count: Quantidade de datas
            start_hour_index: Índice do horário inicial
        
        Returns:
            Lista de datas distribuídas
        """
        # Calcula último dia do mês
        if month_start.month == 12:
            next_month = datetime(month_start.year + 1, 1, 1, tzinfo=SP_TIMEZONE)
        else:
            next_month = datetime(month_start.year, month_start.month + 1, 1, tzinfo=SP_TIMEZONE)
        
        last_day = (next_month - timedelta(days=1)).day
        
        # Distribui as datas ao longo do mês
        dates = []
        if count == 0:
            return dates
        
        # Calcula intervalo entre datas
        interval = last_day / (count + 1)
        
        hour_index = start_hour_index
        for i in range(count):
            # Calcula dia (distribuído ao longo do mês)
            day = int(1 + (i + 1) * interval)
            day = min(day, last_day)
            
            # Seleciona horário (rotaciona entre 10, 13, 17)
            hour = ALLOWED_HOURS[hour_index % len(ALLOWED_HOURS)]
            hour_index += 1
            
            scheduled_date = datetime(
                month_start.year,
                month_start.month,
                day,
                hour,
                0,
                0,
                tzinfo=SP_TIMEZONE
            )
            dates.append(scheduled_date)
        
        return sorted(dates)
    
    def reschedule_past_due(
        self,
        publication: PublicationQueue,
        current_date: datetime
    ) -> PublicationQueue:
        """
        Realoca uma publicação que está com data vencida
        
        Args:
            publication: Publicação a ser realocada
            current_date: Data atual
        
        Returns:
            Publicação atualizada
        """
        if not publication.scheduled_date:
            return publication
        
        # Se a data é do mês atual, tenta realocar no mesmo mês
        pub_month = publication.scheduled_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month = current_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if pub_month == current_month:
            # Tenta encontrar slot no mesmo mês
            existing_count = self.publication_repo.count_by_user_and_month(
                publication.user_id, current_date.year, current_date.month
            )
            
            if existing_count < MAX_PUBLICATIONS_PER_MONTH:
                # Encontra próxima data disponível no mês
                new_date = self._find_next_available_date(
                    current_date, publication.user_id, current_date.year, current_date.month
                )
                if new_date:
                    publication.scheduled_date = new_date
                    publication.status = PublicationStatus.SCHEDULED
                    return publication
        
        # Se não couber no mês atual, agenda para o próximo mês
        if current_date.month == 12:
            next_month = datetime(current_date.year + 1, 1, 1, tzinfo=SP_TIMEZONE)
        else:
            next_month = datetime(current_date.year, current_date.month + 1, 1, tzinfo=SP_TIMEZONE)
        
        dates = self.calculate_scheduled_dates(publication.user_id, 1, next_month)
        if dates:
            publication.scheduled_date = dates[0]
            publication.status = PublicationStatus.SCHEDULED
        
        return publication
    
    def _find_next_available_date(
        self,
        current_date: datetime,
        user_id: int,
        year: int,
        month: int
    ) -> Optional[datetime]:
        """Encontra próxima data disponível no mês"""
        # Busca todas as datas já agendadas no mês
        existing = self.publication_repo.get_pending_for_month(user_id, year, month)
        scheduled_dates = {pub.scheduled_date for pub in existing if pub.scheduled_date}
        
        # Tenta encontrar próxima data disponível
        for day in range(current_date.day + 1, 32):
            try:
                for hour in ALLOWED_HOURS:
                    candidate = datetime(year, month, day, hour, 0, 0, tzinfo=SP_TIMEZONE)
                    if candidate > current_date and candidate not in scheduled_dates:
                        return candidate
            except ValueError:
                # Dia não existe no mês
                break
        
        return None

