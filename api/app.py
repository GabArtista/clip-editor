import http.cookiejar
import json
import os
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_session
from app.models import LearningCenter, MusicAsset, MusicFeedback, VideoClipModel, VideoIngest
from app.schemas.feedback import (
    ArtistFeedbackRequest,
    FeedbackResponse,
    LearningCenterCreateRequest,
    LearningCenterResponse,
    LearningCenterUpdateRequest,
    MusicFeedbackRequest,
)
from app.schemas.music import MusicDetailResponse, MusicUploadResponse
from app.schemas.video import VideoDetailResponse, VideoSubmissionResponse
from app.services import FeedbackService, LearningCenterService
from app.services.music_service import MusicMetadata, MusicService
from app.services.video_pipeline import VideoPipeline, VideoRequest
from metrics import get_registry
from metrics.middleware import MetricsMiddleware
from jobs.cleanup import CleanupScheduler
from jobs.config import get_env_float, get_env_int
from jobs.manager import JobManager
from jobs.rate_limit import RateLimiter

tags_metadata = [
    {"name": "Health", "description": "Verificação rápida do serviço."},
    {"name": "Sessions", "description": "Configuração de cookies e sessões externas."},
    {"name": "Video Jobs", "description": "Download, edição e renderização de vídeos."},
    {"name": "Maintenance", "description": "Limpeza de arquivos temporários e utilitários."},
    {"name": "Video Ingestion", "description": "Ingestão de links e geração de modelos de clipe."},
    {"name": "Music Library", "description": "Uploads de músicas e acesso aos metadados."},
    {"name": "Feedback", "description": "Feedbacks e centros de aprendizado personalizados."},
    {"name": "Learning Centers", "description": "Criação e versionamento dos centros de aprendizado."},
    {"name": "Observability", "description": "Métricas para monitoramento da plataforma."},
]

app = FastAPI(title="FALA Editor API", openapi_tags=tags_metadata)

SESSION_FILE_PATH = "cookies/session.netscape"

os.makedirs("processed", exist_ok=True)
os.makedirs("videos", exist_ok=True)
os.makedirs("cookies", exist_ok=True)

app.mount("/videos", StaticFiles(directory="processed"), name="videos")


job_manager = JobManager()
rate_limiter = RateLimiter(
    max_requests=get_env_int("RATE_LIMIT_REQUESTS", 3),
    window_seconds=get_env_float("RATE_LIMIT_WINDOW_SECONDS", 60.0),
)

app.add_middleware(MetricsMiddleware)

cleanup_scheduler = CleanupScheduler(
    directories=[Path("videos"), Path("processed")],
    older_than_seconds=get_env_float("JOB_CLEANUP_TTL_SECONDS", 3600.0),
    interval_seconds=get_env_float("JOB_CLEANUP_INTERVAL_SECONDS", 900.0),
)
cleanup_scheduler.start()

music_service = MusicService()
video_pipeline = VideoPipeline()
feedback_service = FeedbackService()
learning_center_service = LearningCenterService()

class UpdateSessionRequest(BaseModel):
    cookie_string: str


class EditRequest(BaseModel):
    url: str
    music: str
    impact_music: float
    impact_video: float
    return_format: str = "url"


class VideoSubmissionRequest(BaseModel):
    user_id: str
    url: str
    music_id: str | None = None


class VideoRenderRequest(BaseModel):
    clip_ids: list[str]
    return_format: str = "url"


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.post("/update-session", tags=["Sessions"])
def update_session(data: UpdateSessionRequest):
    try:
        cookies_json = json.loads(data.cookie_string)
        cj = http.cookiejar.MozillaCookieJar(SESSION_FILE_PATH)
        
        for cookie_data in cookies_json:
            c = http.cookiejar.Cookie(
                version=0,
                name=cookie_data['name'],
                value=cookie_data['value'],
                port=None,
                port_specified=False,
                domain=cookie_data['domain'],
                domain_specified=True,
                domain_initial_dot=cookie_data['domain'].startswith('.'),
                path=cookie_data['path'],
                path_specified=True,
                secure=cookie_data['secure'],
                expires=int(cookie_data.get('expirationDate', 0)),
                discard=False,
                comment=None,
                comment_url=None,
                rest={'HttpOnly': cookie_data.get('httpOnly', False)},
                rfc2109=False
            )
            cj.set_cookie(c)
        
        cj.save(ignore_discard=True, ignore_expires=True)
        
        return {"status": "ok", "message": "Sessão de cookies atualizada com sucesso e salva em formato Netscape!"}
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="A string de cookies fornecida não é um JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar a sessão: {str(e)}")


@app.post("/processar", tags=["Video Jobs"])
def processar_video(data: EditRequest, request: Request):
    try:
        client_id = request.client.host if request.client else "anonymous"
        allowed, retry_after = rate_limiter.allow(client_id)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail=f"Limite de processamento excedido. Tente novamente em {int(retry_after)} segundos.",
            )

        if data.return_format == "file":
            raise HTTPException(
                status_code=400,
                detail="Formato 'file' não suportado em jobs assíncronos. Utilize url, base64 ou path.",
            )

        job_id = job_manager.enqueue_video_edit(data.dict())
        job_info = job_manager.get_job(job_id) or {}
        return {"ok": True, "job_id": job_id, "status": job_info.get("status", "queued")}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro inesperado no processamento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado no processamento: {str(e)}")


@app.delete("/cleanup", tags=["Maintenance"])
def cleanup_videos():
    pastas = ["videos", "processed"]
    removidos = []

    try:
        for pasta in pastas:
            if os.path.exists(pasta):
                for arquivo in os.listdir(pasta):
                    caminho = os.path.join(pasta, arquivo)
                    if os.path.isfile(caminho):
                        os.remove(caminho)
                        removidos.append(caminho)

        return {"ok": True, "removidos": removidos}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/jobs/{job_id}", tags=["Video Jobs"])
def get_job_status(job_id: str):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    return job


@app.get("/metrics", tags=["Observability"])
def metrics_endpoint():
    return PlainTextResponse(get_registry().render_prometheus(), media_type="text/plain")


def _serialize_learning_center(center: LearningCenter) -> dict:
    return {
        "id": center.id,
        "name": center.name,
        "description": center.description,
        "scope": center.scope,
        "status": center.status,
        "user_id": center.user_id,
        "music_asset_id": center.music_asset_id,
        "genre": center.genre,
        "is_experimental": center.is_experimental,
        "version": center.version,
        "parameters": center.parameters,
        "baseline_snapshot": center.baseline_snapshot,
        "created_at": center.created_at,
        "updated_at": center.updated_at,
    }


@app.post("/videos", response_model=VideoSubmissionResponse, status_code=201, tags=["Video Ingestion"])
def submit_video(data: VideoSubmissionRequest, db: Session = Depends(get_session)):
    try:
        ingest, clip_models = video_pipeline.ingest_and_suggest(
            db,
            VideoRequest(user_id=data.user_id, url=data.url, music_asset_id=data.music_id),
        )
        return VideoSubmissionResponse.model_validate(
            {
                "id": ingest.id,
                "status": ingest.status.value if hasattr(ingest.status, "value") else ingest.status,
                "duration_seconds": float(ingest.duration_seconds) if ingest.duration_seconds else None,
                "options": [
                    {
                        "id": clip.id,
                        "option_order": clip.option_order,
                        "variant_label": clip.variant_label,
                        "description": clip.description,
                        "music_asset_id": clip.music_asset_id,
                        "video_segments": clip.video_segments,
                        "music_start_seconds": float(clip.music_start_seconds)
                        if clip.music_start_seconds is not None
                        else None,
                        "music_end_seconds": float(clip.music_end_seconds)
                        if clip.music_end_seconds is not None
                        else None,
                        "diversity_tags": clip.diversity_tags,
                        "score": float(clip.score) if clip.score is not None else None,
                    }
                    for clip in clip_models
                ],
            }
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


def _clip_to_dict(clip):
    return {
        "id": clip.id,
        "option_order": clip.option_order,
        "variant_label": clip.variant_label,
        "description": clip.description,
        "music_asset_id": clip.music_asset_id,
        "video_segments": clip.video_segments,
        "music_start_seconds": float(clip.music_start_seconds) if clip.music_start_seconds is not None else None,
        "music_end_seconds": float(clip.music_end_seconds) if clip.music_end_seconds is not None else None,
        "diversity_tags": clip.diversity_tags,
        "score": float(clip.score) if clip.score is not None else None,
    }


@app.get("/videos/{video_id}", response_model=VideoDetailResponse, tags=["Video Ingestion"])
def get_video_detail(video_id: str, db: Session = Depends(get_session)):
    ingest = (
        db.query(VideoIngest)
        .options(
            joinedload(VideoIngest.clip_models),
            joinedload(VideoIngest.analysis),
        )
        .filter(VideoIngest.id == video_id)
        .first()
    )
    if not ingest:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")

    analysis_payload = None
    if ingest.analysis:
        analysis_payload = {
            "scene_breakdown": ingest.analysis.scene_breakdown,
            "motion_stats": ingest.analysis.motion_stats,
            "keywords": ingest.analysis.keywords,
        }

    return VideoDetailResponse.model_validate(
        {
            "id": ingest.id,
            "status": ingest.status.value if hasattr(ingest.status, "value") else ingest.status,
            "duration_seconds": float(ingest.duration_seconds) if ingest.duration_seconds else None,
            "options": [_clip_to_dict(clip) for clip in sorted(ingest.clip_models, key=lambda c: c.option_order)],
            "source_url": ingest.source_url,
            "created_at": ingest.created_at,
            "analysis": analysis_payload,
        }
    )


@app.post("/render/{video_id}", tags=["Video Jobs"])
def render_video_variants(video_id: str, data: VideoRenderRequest, db: Session = Depends(get_session)):
    if data.return_format not in {"url"}:
        raise HTTPException(status_code=400, detail="Somente o formato 'url' é suportado.")
    if not data.clip_ids:
        raise HTTPException(status_code=400, detail="Informe ao menos um clip_id para renderização.")

    clips = (
        db.query(VideoClipModel)
        .filter(VideoClipModel.id.in_(data.clip_ids))
        .all()
    )
    if len(clips) != len(data.clip_ids):
        found_ids = {clip.id for clip in clips}
        missing = [clip_id for clip_id in data.clip_ids if clip_id not in found_ids]
        raise HTTPException(status_code=404, detail=f"Clipes não encontrados: {', '.join(missing)}")

    ingest_ids = {clip.video_ingest_id for clip in clips}
    if len(ingest_ids) != 1 or video_id not in ingest_ids:
        raise HTTPException(status_code=400, detail="Clipes não pertencem a este vídeo.")

    job_payload = {
        "mode": "clip_render",
        "video_ingest_id": video_id,
        "clip_ids": data.clip_ids,
        "return_format": data.return_format,
    }
    job_id = job_manager.enqueue_video_edit(job_payload)
    job_info = job_manager.get_job(job_id) or {}
    return {"ok": True, "job_id": job_id, "status": job_info.get("status", "queued")}


@app.post(
    "/music",
    response_model=MusicUploadResponse,
    status_code=201,
    tags=["Music Library"],
)
def upload_music(
    user_id: str = Form(...),
    title: str = Form(...),
    description: str | None = Form(None),
    genre: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_session),
):
    try:
        metadata = MusicMetadata(
            user_id=user_id,
            title=title,
            description=description,
            declared_genre=genre,
        )
        asset = music_service.create_music_asset(db, file, metadata)
        return MusicUploadResponse.model_validate(music_service.to_response_dict(asset))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/music/{music_id}", response_model=MusicDetailResponse, tags=["Music Library"])
def get_music_asset(music_id: str, db: Session = Depends(get_session)):
    asset = (
        db.query(MusicAsset)
        .options(
            joinedload(MusicAsset.beats),
            joinedload(MusicAsset.embeddings),
            joinedload(MusicAsset.transcription),
        )
        .filter(MusicAsset.id == music_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Música não encontrada")
    return MusicDetailResponse.model_validate(music_service.to_response_dict(asset))


@app.post("/feedback/music/{music_id}", response_model=FeedbackResponse, status_code=201, tags=["Feedback"])
def create_music_feedback(music_id: str, body: MusicFeedbackRequest, db: Session = Depends(get_session)):
    try:
        feedback = feedback_service.record_music_feedback(
            db,
            user_id=body.user_id,
            music_asset_id=music_id,
            message=body.message,
            mood=body.mood,
            tags=body.tags,
            source=body.source,
            weight=body.weight,
        )
        db.commit()
        return FeedbackResponse(id=feedback.id, created_at=feedback.created_at)
    except ValueError as exc:
        db.rollback()
        if str(exc) == "music_not_found":
            raise HTTPException(status_code=404, detail="Música não encontrada") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/feedback/artist", response_model=FeedbackResponse, status_code=201, tags=["Feedback"])
def create_artist_feedback(body: ArtistFeedbackRequest, db: Session = Depends(get_session)):
    try:
        feedback = feedback_service.record_artist_feedback(
            db,
            user_id=body.user_id,
            message=body.message,
            mood=body.mood,
            tags=body.tags,
            source=body.source,
            weight=body.weight,
            music_asset_id=body.music_id,
        )
        db.commit()
        return FeedbackResponse(id=feedback.id, created_at=feedback.created_at)
    except ValueError as exc:
        db.rollback()
        detail = "Música não encontrada" if str(exc) == "music_not_found" else str(exc)
        status = 404 if str(exc) == "music_not_found" else 400
        raise HTTPException(status_code=status, detail=detail) from exc


@app.post("/learning-centers", response_model=LearningCenterResponse, status_code=201, tags=["Learning Centers"])
def create_learning_center(body: LearningCenterCreateRequest, db: Session = Depends(get_session)):
    try:
        center = learning_center_service.create(
            db,
            name=body.name,
            scope=body.scope,
            user_id=body.user_id,
            music_asset_id=body.music_asset_id,
            genre=body.genre,
            description=body.description,
            is_experimental=body.is_experimental,
            parameters=body.parameters,
        )
        db.commit()
        return LearningCenterResponse.model_validate(_serialize_learning_center(center))
    except ValueError as exc:
        db.rollback()
        detail = {
            "invalid_scope": "Escopo inválido. Use global, artist ou music.",
            "global_scope_invalid_payload": "Centros globais não aceitam user_id ou music_asset_id.",
            "artist_scope_requires_user": "Centros de artista exigem o user_id.",
            "music_scope_requires_music": "Centros de música exigem o music_asset_id.",
            "music_not_found": "Música associada não encontrada.",
        }.get(str(exc), str(exc))
        status = 404 if str(exc) == "music_not_found" else 400
        raise HTTPException(status_code=status, detail=detail) from exc


@app.put("/learning-centers/{center_id}", response_model=LearningCenterResponse, tags=["Learning Centers"])
def update_learning_center(center_id: str, body: LearningCenterUpdateRequest, db: Session = Depends(get_session)):
    center = db.query(LearningCenter).filter(LearningCenter.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Centro de aprendizado não encontrado")

    learning_center_service.update(
        db,
        center,
        name=body.name,
        description=body.description,
        status=body.status,
        is_experimental=body.is_experimental,
        parameters=body.parameters,
        notes=body.notes,
    )
    db.commit()
    db.refresh(center)
    return LearningCenterResponse.model_validate(_serialize_learning_center(center))


@app.delete("/learning-centers/{center_id}", response_model=LearningCenterResponse, tags=["Learning Centers"])
def archive_learning_center(center_id: str, db: Session = Depends(get_session)):
    center = db.query(LearningCenter).filter(LearningCenter.id == center_id).first()
    if not center:
        raise HTTPException(status_code=404, detail="Centro de aprendizado não encontrado")

    learning_center_service.archive(db, center)
    db.commit()
    db.refresh(center)
    return LearningCenterResponse.model_validate(_serialize_learning_center(center))
