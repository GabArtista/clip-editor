import http.cookiejar
import json
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import parse_qs
from uuid import UUID

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.database import get_session
from app.models import LearningCenter, MusicAsset, MusicFeedback, VideoClipModel, VideoIngest, User
from app.schemas.feedback import (
    ArtistFeedbackRequest,
    FeedbackResponse,
    LearningCenterCreateRequest,
    LearningCenterResponse,
    LearningCenterUpdateRequest,
    MusicFeedbackRequest,
)
from app.schemas.music import MusicDetailResponse, MusicListItem, MusicUploadResponse
from app.schemas.auth import AuthMeResponse, AuthRegisterRequest, TokenResponse, UserSummary
from app.schemas.video import VideoDetailResponse, VideoSubmissionResponse, VideoListItem
from app.schemas.learning import ClipLearningSummary, ClipLearningTrainResponse
from app.services import FeedbackService, LearningCenterService, ClipLearningService
from app.services.music_service import MusicMetadata, MusicService
from app.services.video_pipeline import VideoPipeline, VideoRequest
from metrics import get_registry
from metrics.middleware import MetricsMiddleware
from jobs.cleanup import CleanupScheduler
from jobs.config import get_env_float, get_env_int
from jobs.manager import JobManager
from jobs.rate_limit import RateLimiter
from app.security import (
    PasswordValidationError,
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
)

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

# Inicialização automática do banco em ambiente de testes (evita 'no such table')
if os.getenv("PYTEST_CURRENT_TEST"):
	try:
		from app import database as _db
		from app.models import Base as _Base
		_Base.metadata.create_all(_db.engine)
	except Exception:
		pass

SESSION_DIR = Path("cookies")

os.makedirs("processed", exist_ok=True)
os.makedirs("videos", exist_ok=True)
SESSION_DIR.mkdir(parents=True, exist_ok=True)

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
clip_learning_service = ClipLearningService()


def session_file_for_user(user_id: str) -> Path:
    SESSION_DIR.mkdir(parents=True, exist_ok=True)
    return SESSION_DIR / f"{user_id}.netscape"

class UpdateSessionRequest(BaseModel):
    cookie_string: str


class EditRequest(BaseModel):
    url: str
    music: str
    impact_music: float
    impact_video: float
    return_format: str = "url"


class VideoSubmissionRequest(BaseModel):
    url: str
    music_id: str | None = None


class VideoRenderRequest(BaseModel):
    clip_ids: list[str]
    return_format: str = "url"


def _to_user_summary(user: User) -> UserSummary:
    return UserSummary(id=str(user.id), email=user.email)


@app.post(
    "/auth/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Auth"],
)
def register_user(body: AuthRegisterRequest, db: Session = Depends(get_session)):
    email = body.email.lower().strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado.")
    try:
        password_hash = hash_password(body.password)
    except PasswordValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    user = User(email=email, password_hash=password_hash, last_login_at=datetime.utcnow())
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, token_type="bearer", user=_to_user_summary(user))


async def _extract_login_credentials(request: Request) -> tuple[str, str]:
    """Extract username/email and password from JSON or x-www-form-urlencoded payloads."""
    content_type = (request.headers.get("content-type") or "").lower()
    body_bytes = await request.body()
    if not body_bytes:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Os campos username/email e password são obrigatórios.",
        )

    try:
        if "application/json" in content_type:
            payload = json.loads(body_bytes.decode("utf-8"))
            username = payload.get("username") or payload.get("email")
            password = payload.get("password")
        else:
            charset = "utf-8"
            if "charset=" in content_type:
                charset = content_type.split("charset=")[-1].split(";")[0].strip() or "utf-8"
            form_data = parse_qs(body_bytes.decode(charset))
            username = form_data.get("username", form_data.get("email", [None]))[0]
            password = form_data.get("password", [None])[0]
    except (json.JSONDecodeError, UnicodeDecodeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não foi possível interpretar o corpo da requisição.",
        ) from exc

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Os campos username/email e password são obrigatórios.",
        )
    return username, password


@app.post(
    "/auth/login",
    response_model=TokenResponse,
    tags=["Auth"],
)
async def login_user(
    request: Request,
    db: Session = Depends(get_session),
):
    username, password = await _extract_login_credentials(request)

    user = authenticate_user(db, username.strip().lower(), password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user.last_login_at = datetime.utcnow()
    user.updated_at = datetime.utcnow()
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, token_type="bearer", user=_to_user_summary(user))


@app.post(
    "/learning/train",
    response_model=ClipLearningTrainResponse,
    tags=["Learning Centers"],
)
def train_learning_model(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Treina o modelo de ranking de clipes para o artista atual."""

    payload = clip_learning_service.train_for_user(db, current_user.id)
    if not payload:
        summary = ClipLearningSummary(
            samples=0,
            positives=0,
            negatives=0,
            metrics={},
            trained_at=datetime.utcnow(),
        )
        return ClipLearningTrainResponse(result=summary, message="no_training_data")

    db.commit()

    summary = ClipLearningSummary(
        samples=payload.samples,
        positives=payload.positives,
        negatives=payload.negatives,
        metrics=payload.metrics,
        trained_at=datetime.fromisoformat(payload.trained_at),
    )
    return ClipLearningTrainResponse(result=summary, message="trained")


@app.get("/auth/me", response_model=AuthMeResponse, tags=["Auth"])
def get_me(current_user: User = Depends(get_current_user)):
    return AuthMeResponse(id=str(current_user.id), email=current_user.email)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok"}


@app.post("/update-session", tags=["Sessions"])
def update_session(
    data: UpdateSessionRequest,
    current_user: User = Depends(get_current_user),
):
    try:
        cookies_json = json.loads(data.cookie_string)
        session_path = session_file_for_user(current_user.id)
        cj = http.cookiejar.MozillaCookieJar(str(session_path))
        
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
        
        return {
            "status": "ok",
            "message": "Sessão de cookies atualizada com sucesso e salva em formato Netscape!",
            "session_file": str(session_path),
        }
    
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="A string de cookies fornecida não é um JSON válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar a sessão: {str(e)}")


@app.post("/processar", tags=["Video Jobs"])
def processar_video(
    data: EditRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
):
    try:
        client_id = current_user.id
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

        session_path = session_file_for_user(current_user.id)
        if not session_path.exists():
            raise HTTPException(
                status_code=400,
                detail="Sessão de cookies não encontrada. Utilize /update-session antes de processar vídeos.",
            )

        payload = data.dict()
        payload["user_id"] = current_user.id
        payload["session_file_path"] = str(session_path)
        job_id = job_manager.enqueue_video_edit(payload)
        job_info = job_manager.get_job(job_id) or {}
        return {"ok": True, "job_id": job_id, "status": job_info.get("status", "queued")}
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Erro inesperado no processamento: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro inesperado no processamento: {str(e)}")


@app.delete("/cleanup", tags=["Maintenance"])
def cleanup_videos(current_user: User = Depends(get_current_user)):
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
def get_job_status(job_id: str, current_user: User = Depends(get_current_user)):
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job não encontrado")
    owner_id = job.get("request", {}).get("user_id")
    if owner_id is None or owner_id != str(current_user.id):
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
def submit_video(
    data: VideoSubmissionRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        ingest, clip_models = video_pipeline.ingest_and_suggest(
            db,
            VideoRequest(user_id=current_user.id, url=data.url, music_asset_id=data.music_id),
        )
        return VideoSubmissionResponse.model_validate(
            {
                "id": str(ingest.id),
                "status": ingest.status.value if hasattr(ingest.status, "value") else ingest.status,
                "duration_seconds": float(ingest.duration_seconds) if ingest.duration_seconds else None,
                "options": [
                    {
                        "id": str(clip.id),
                        "option_order": clip.option_order,
                        "variant_label": clip.variant_label,
                        "description": clip.description,
                        "music_asset_id": str(clip.music_asset_id) if clip.music_asset_id else None,
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


@app.get("/videos", response_model=list[VideoListItem], tags=["Video Ingestion"])
def list_videos(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ingests = (
        db.query(VideoIngest)
        .options(joinedload(VideoIngest.clip_models))
        .filter(VideoIngest.user_id == current_user.id)
        .order_by(VideoIngest.created_at.desc())
        .all()
    )
    return [
        {
            "id": str(ingest.id),
            "status": ingest.status.value if hasattr(ingest.status, "value") else ingest.status,
            "duration_seconds": float(ingest.duration_seconds) if ingest.duration_seconds else None,
            "options": [_clip_to_dict(clip) for clip in sorted(ingest.clip_models, key=lambda c: c.option_order)],
            "source_url": ingest.source_url,
            "created_at": ingest.created_at,
            "updated_at": ingest.updated_at,
        }
        for ingest in ingests
    ]


def _clip_to_dict(clip):
    return {
        "id": str(clip.id),
        "option_order": clip.option_order,
        "variant_label": clip.variant_label,
        "description": clip.description,
        "music_asset_id": str(clip.music_asset_id) if clip.music_asset_id else None,
        "video_segments": clip.video_segments,
        "music_start_seconds": float(clip.music_start_seconds) if clip.music_start_seconds is not None else None,
        "music_end_seconds": float(clip.music_end_seconds) if clip.music_end_seconds is not None else None,
        "diversity_tags": clip.diversity_tags,
        "score": float(clip.score) if clip.score is not None else None,
    }


@app.get("/videos/{video_id}", response_model=VideoDetailResponse, tags=["Video Ingestion"])
def get_video_detail(
    video_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    ingest = (
        db.query(VideoIngest)
        .options(
            joinedload(VideoIngest.clip_models),
            joinedload(VideoIngest.analysis),
        )
        .filter(VideoIngest.id == video_id, VideoIngest.user_id == current_user.id)
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
            "id": str(ingest.id),
            "status": ingest.status.value if hasattr(ingest.status, "value") else ingest.status,
            "duration_seconds": float(ingest.duration_seconds) if ingest.duration_seconds else None,
            "options": [_clip_to_dict(clip) for clip in sorted(ingest.clip_models, key=lambda c: c.option_order)],
            "source_url": ingest.source_url,
            "created_at": ingest.created_at,
            "updated_at": ingest.updated_at,
            "analysis": analysis_payload,
        }
    )


@app.post("/render/{video_id}", tags=["Video Jobs"])
def render_video_variants(
    video_id: str,
    data: VideoRenderRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if data.return_format not in {"url"}:
        raise HTTPException(status_code=400, detail="Somente o formato 'url' é suportado.")
    if not data.clip_ids:
        raise HTTPException(status_code=400, detail="Informe ao menos um clip_id para renderização.")

    try:
        clip_uuid_ids = [UUID(clip_id) for clip_id in data.clip_ids]
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="clip_id inválido.") from exc

    clips = (
        db.query(VideoClipModel)
        .filter(VideoClipModel.id.in_(clip_uuid_ids))
        .all()
    )
    if len(clips) != len(clip_uuid_ids):
        found_ids = {clip.id for clip in clips}
        missing = [str(clip_id) for clip_id in clip_uuid_ids if clip_id not in found_ids]
        raise HTTPException(status_code=404, detail=f"Clipes não encontrados: {', '.join(missing)}")

    ingest_ids = {clip.video_ingest_id for clip in clips}
    try:
        video_uuid = UUID(video_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="video_id inválido.") from exc

    if len(ingest_ids) != 1 or video_uuid not in ingest_ids:
        raise HTTPException(status_code=400, detail="Clipes não pertencem a este vídeo.")

    job_payload = {
        "mode": "clip_render",
        "video_ingest_id": str(video_uuid),
        "clip_ids": [str(cid) for cid in clip_uuid_ids],
        "return_format": data.return_format,
    }
    ingest = db.query(VideoIngest).filter(VideoIngest.id == video_uuid, VideoIngest.user_id == current_user.id).first()
    if not ingest:
        raise HTTPException(status_code=404, detail="Vídeo não encontrado")
    job_payload["user_id"] = str(current_user.id)
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
    title: str = Form(...),
    description: str | None = Form(None),
    genre: str | None = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    try:
        metadata = MusicMetadata(
            user_id=current_user.id,
            title=title,
            description=description,
            declared_genre=genre,
        )
        asset = music_service.create_music_asset(db, file, metadata)
        return MusicUploadResponse.model_validate(music_service.to_response_dict(asset))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.get("/music", response_model=list[MusicListItem], tags=["Music Library"])
def list_music_assets(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    assets = (
        db.query(MusicAsset)
        .filter(MusicAsset.user_id == current_user.id)
        .order_by(MusicAsset.uploaded_at.desc())
        .all()
    )
    return [
        MusicListItem(
            id=str(asset.id),
            title=asset.title,
            status=asset.status.value if hasattr(asset.status, "value") else asset.status,
            genre=asset.genre,
            uploaded_at=asset.uploaded_at,
        )
        for asset in assets
    ]


@app.get("/music/{music_id}", response_model=MusicDetailResponse, tags=["Music Library"])
def get_music_asset(
    music_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        music_uuid = UUID(music_id)
    except Exception:
        raise HTTPException(status_code=400, detail="music_id inválido")
    asset = (
        db.query(MusicAsset)
        .options(
            joinedload(MusicAsset.beats),
            joinedload(MusicAsset.embeddings),
            joinedload(MusicAsset.transcription),
        )
        .filter(MusicAsset.id == music_uuid, MusicAsset.user_id == current_user.id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=404, detail="Música não encontrada")
    return MusicDetailResponse.model_validate(music_service.to_response_dict(asset))


@app.post("/feedback/music/{music_id}", response_model=FeedbackResponse, status_code=201, tags=["Feedback"])
def create_music_feedback(
    music_id: str,
    body: MusicFeedbackRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        music_uuid = UUID(music_id)
    except Exception:
        raise HTTPException(status_code=400, detail="music_id inválido")
    try:
        feedback = feedback_service.record_music_feedback(
            db,
            user_id=current_user.id,
            music_asset_id=str(music_uuid),
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
def create_artist_feedback(
    body: ArtistFeedbackRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        feedback = feedback_service.record_artist_feedback(
            db,
            user_id=current_user.id,
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
def create_learning_center(
    body: LearningCenterCreateRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    try:
        scope = body.scope.lower()
        owner_id = None if scope == "global" else current_user.id
        center = learning_center_service.create(
            db,
            name=body.name,
            scope=body.scope,
            user_id=owner_id,
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
def update_learning_center(
    center_id: str,
    body: LearningCenterUpdateRequest,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    center = (
        db.query(LearningCenter)
        .filter(LearningCenter.id == center_id)
        .first()
    )
    if not center:
        raise HTTPException(status_code=404, detail="Centro de aprendizado não encontrado")
    if center.user_id and center.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Centro de aprendizado não encontrado")
    if center.user_id is None and center.scope != "global":
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
def archive_learning_center(
    center_id: str,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    center = (
        db.query(LearningCenter)
        .filter(LearningCenter.id == center_id)
        .first()
    )
    if not center:
        raise HTTPException(status_code=404, detail="Centro de aprendizado não encontrado")
    if center.user_id and center.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Centro de aprendizado não encontrado")
    if center.user_id is None and center.scope != "global":
        raise HTTPException(status_code=404, detail="Centro de aprendizado não encontrado")

    learning_center_service.archive(db, center)
    db.commit()
    db.refresh(center)
    return LearningCenterResponse.model_validate(_serialize_learning_center(center))
