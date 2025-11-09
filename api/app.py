from __future__ import annotations

from decimal import Decimal
from typing import List

from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.database import get_session
from app.models import User
from app.schemas.auth import AuthLoginRequest, AuthMeResponse, AuthRegisterRequest, TokenResponse, UserSummary
from app.schemas.music import (
    MusicDetailResponse,
    MusicListItem,
    MusicTranscriptionRequest,
    MusicTranscriptionResponse,
    MusicUploadResponse,
)
from app.schemas.wallet import WalletBalanceResponse, WalletDepositRequest, WalletTransactionResponse
from app.schemas.video import (
    VideoSuggestionRequest,
    VideoSuggestionResponse,
    VideoSuggestionItem,
    VideoVariationItem,
    VideoVariationRequest,
    VideoVariationResponse,
    VideoVariationSegment,
)
from app.security import (
    PasswordValidationError,
    authenticate_user,
    create_access_token,
    get_current_user,
    hash_password,
)
from app.services.ai import AIClient
from app.services.costs import CostCalculator
from app.services.music import MusicLibrary
from app.services.video import VideoService
from app.services.wallet import InsufficientCreditsError, WalletManager

app = FastAPI(
    title="FALA Viral API",
    description="Backend simplificado para cadastro de músicas, transcrição e geração de sugestões com IA.",
)

ai_client = AIClient()
cost_calculator = CostCalculator()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def _to_user_summary(user: User) -> UserSummary:
    return UserSummary(id=str(user.id), email=user.email, display_name=user.display_name)


@app.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
def register_user(body: AuthRegisterRequest, db: Session = Depends(get_session)):
    email = body.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado.")
    try:
        password_hash = hash_password(body.password)
    except PasswordValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    user = User(email=email, password_hash=password_hash, display_name=body.display_name)
    db.add(user)
    db.flush()
    wallet = WalletManager(db)
    wallet.get_or_create_account(user)
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=_to_user_summary(user))


@app.post("/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(body: AuthLoginRequest, db: Session = Depends(get_session)):
    user = authenticate_user(db, body.email.strip().lower(), body.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciais inválidas.")
    token = create_access_token(str(user.id))
    return TokenResponse(access_token=token, user=_to_user_summary(user))


@app.get("/me", response_model=AuthMeResponse, tags=["Auth"])
def whoami(current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    wallet = WalletManager(db)
    snapshot = wallet.get_snapshot(current_user)
    return AuthMeResponse(
        **_to_user_summary(current_user).model_dump(),
        status=current_user.status,
        wallet_balance=snapshot.balance_credits,
        currency=snapshot.currency,
    )


# ---------------------------------------------------------------------------
# Wallet
# ---------------------------------------------------------------------------
@app.post("/wallet/deposit", response_model=WalletBalanceResponse, tags=["Wallet"])
def deposit_credits(
    body: WalletDepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    wallet = WalletManager(db)
    snapshot = wallet.deposit(current_user, body.amount, body.description)
    return WalletBalanceResponse(balance=snapshot.balance_credits, currency=snapshot.currency)


@app.get("/wallet/transactions", response_model=list[WalletTransactionResponse], tags=["Wallet"])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    wallet = WalletManager(db)
    transactions = wallet.list_transactions(current_user)
    return [
        WalletTransactionResponse(
            id=str(tx.id),
            transaction_type=tx.transaction_type,
            amount_credits=Decimal(tx.amount_credits),
            description=tx.description,
            created_at=tx.created_at,
        )
        for tx in transactions
    ]


# ---------------------------------------------------------------------------
# Music
# ---------------------------------------------------------------------------
def _music_to_item(music) -> MusicListItem:
    return MusicListItem(
        id=str(music.id),
        title=music.title,
        description=music.description,
        duration_seconds=float(music.duration_seconds) if music.duration_seconds else None,
        bpm=music.bpm,
        created_at=music.created_at,
        has_transcription=music.transcription is not None,
    )


@app.post("/music", response_model=MusicUploadResponse, status_code=status.HTTP_201_CREATED, tags=["Music"])
async def upload_music(
    title: str = Form(...),
    description: str | None = Form(default=None),
    duration_seconds: float | None = Form(default=None),
    bpm: int | None = Form(default=None),
    audio_file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    library = MusicLibrary(db, ai_client, cost_calculator)
    music = library.upload_music(
        user=current_user,
        file=audio_file,
        title=title,
        description=description,
        duration_seconds=duration_seconds,
        bpm=bpm,
    )
    return MusicUploadResponse(
        id=str(music.id),
        title=music.title,
        duration_seconds=float(music.duration_seconds) if music.duration_seconds else None,
        bpm=music.bpm,
        created_at=music.created_at,
    )


@app.get("/music", response_model=list[MusicListItem], tags=["Music"])
def list_music(current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    library = MusicLibrary(db, ai_client, cost_calculator)
    items = library.list_music(current_user)
    return [_music_to_item(item) for item in items]


@app.get("/music/{music_id}", response_model=MusicDetailResponse, tags=["Music"])
def get_music(music_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_session)):
    library = MusicLibrary(db, ai_client, cost_calculator)
    music = library.get_music_for_user(current_user, music_id)
    item = _music_to_item(music).model_dump()
    item["transcript_text"] = music.transcription.transcript_text if music.transcription else None
    item["language"] = music.transcription.language if music.transcription else None
    return MusicDetailResponse(**item)


@app.post(
    "/music/{music_id}/transcribe",
    response_model=MusicTranscriptionResponse,
    tags=["Music"],
)
def transcribe_music(
    music_id: str,
    body: MusicTranscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    library = MusicLibrary(db, ai_client, cost_calculator)
    wallet = WalletManager(db)
    try:
        transcription = library.transcribe_music(current_user, music_id, body.language, wallet)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except InsufficientCreditsError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Saldo insuficiente. Necessário {exc.required} créditos.",
        ) from exc
    return MusicTranscriptionResponse(
        id=str(transcription.id),
        music_id=str(transcription.user_music_id),
        language=transcription.language,
        transcript_text=transcription.transcript_text,
        confidence=float(transcription.confidence) if transcription.confidence else None,
        generated_by=transcription.generated_by,
        created_at=transcription.created_at,
    )


# ---------------------------------------------------------------------------
# Video IA
# ---------------------------------------------------------------------------
def _handle_wallet_errors(exc: Exception):
    if isinstance(exc, InsufficientCreditsError):
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Saldo insuficiente. Necessário {exc.required} créditos.",
        ) from exc
    raise exc


@app.post("/videos/suggestions", response_model=VideoSuggestionResponse, tags=["Video"])
def generate_suggestions(
    body: VideoSuggestionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    service = VideoService(db, ai_client, cost_calculator)
    wallet = WalletManager(db)
    try:
        results = service.generate_suggestions(
            user=current_user,
            video_url=str(body.video_url),
            duration_seconds=body.video_duration_seconds,
            notes=body.notes,
            music_ids=body.music_ids,
            wallet=wallet,
        )
    except InsufficientCreditsError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Saldo insuficiente. Necessário {exc.required} créditos.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    items = [
        VideoSuggestionItem(
            suggestion_id=result.suggestion_id,
            music_id=result.music_id,
            start_time_seconds=result.start_time_seconds,
            end_time_seconds=result.end_time_seconds,
            reasoning=result.reasoning,
            prompt=result.prompt,
        )
        for result in results
    ]
    return VideoSuggestionResponse(items=items)


@app.post("/videos/variations", response_model=VideoVariationResponse, tags=["Video"])
def generate_variations(
    body: VideoVariationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session),
):
    service = VideoService(db, ai_client, cost_calculator)
    wallet = WalletManager(db)
    try:
        results = service.generate_variations(
            user=current_user,
            video_url=str(body.video_url),
            duration_seconds=body.video_duration_seconds,
            notes=body.notes,
            music_id=body.music_id,
            wallet=wallet,
        )
    except InsufficientCreditsError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=f"Saldo insuficiente. Necessário {exc.required} créditos.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    items = [
        VideoVariationItem(
            variation_id=result.variation_id,
            music_id=result.music_id,
            description=result.description,
            segments=[
                VideoVariationSegment(
                    label=segment.get("label", "segment"),
                    video_start=float(segment.get("video_start", 0)),
                    video_end=float(segment.get("video_end", 0)),
                    music_offset=float(segment.get("music_offset", 0)),
                )
                for segment in result.segments
            ],
        )
        for result in results
    ]
    return VideoVariationResponse(items=items)
