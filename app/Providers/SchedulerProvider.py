"""
Scheduler Provider - Laravel Style
Scheduler para executar tarefas periódicas de forma eficiente
Usa APScheduler com execução em background thread
"""
import asyncio
import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from app.Jobs.PublicationJob import run_daily_worker
from app.Jobs.CleanupJob import run_cleanup_worker

logger = logging.getLogger(__name__)

_scheduler: BackgroundScheduler = None


def _run_async_worker():
    """Wrapper para executar função async no scheduler"""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(run_daily_worker())
        loop.close()
    except Exception as e:
        logger.error(f"Erro ao executar worker: {str(e)}", exc_info=True)


def setup_scheduler():
    """Configura o scheduler"""
    global _scheduler
    
    if _scheduler is not None:
        return _scheduler
    
    _scheduler = BackgroundScheduler()
    
    # Agenda execução diária às 00:00 (horário de São Paulo) para publicações
    _scheduler.add_job(
        func=_run_async_worker,
        trigger=CronTrigger(hour=0, minute=0, timezone="America/Sao_Paulo"),
        id="daily_publication_worker",
        name="Processar publicações diárias",
        replace_existing=True,
        max_instances=1
    )
    
    # Agenda limpeza a cada hora para vídeos expirados
    _scheduler.add_job(
        func=run_cleanup_worker,
        trigger=CronTrigger(minute=0),  # Todo minuto 0 (a cada hora)
        id="cleanup_worker",
        name="Limpar vídeos expirados do S3",
        replace_existing=True,
        max_instances=1
    )
    
    logger.info("Scheduler configurado:")
    logger.info("  - Publicações: diariamente às 00:00 (SP)")
    logger.info("  - Limpeza S3: a cada hora")
    return _scheduler


def start_scheduler():
    """Inicia o scheduler"""
    global _scheduler
    if _scheduler is None:
        setup_scheduler()
    
    if not _scheduler.running:
        _scheduler.start()
        logger.info("Scheduler iniciado")


def shutdown_scheduler():
    """Para o scheduler"""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=True)
        logger.info("Scheduler parado")

