from __future__ import annotations

import shutil
import uuid
from pathlib import Path
from uuid import UUID
from typing import List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.models import MusicTranscription, User, UserMusic
from app.services.ai import AIClient
from app.services.costs import CostCalculator
from app.services.wallet import WalletManager
from app.settings import music_storage_dir


class MusicLibrary:
    def __init__(self, db: Session, ai_client: AIClient, cost_calculator: CostCalculator):
        self.db = db
        self.ai_client = ai_client
        self.cost_calculator = cost_calculator

    def get_music_for_user(self, user: User, music_id: str | UUID) -> UserMusic:
        music_uuid = music_id if isinstance(music_id, UUID) else UUID(str(music_id))
        music = (
            self.db.query(UserMusic)
            .filter(UserMusic.id == music_uuid, UserMusic.user_id == user.id)
            .first()
        )
        if not music:
            raise ValueError("Música não encontrada.")
        return music

    def list_music(self, user: User) -> List[UserMusic]:
        return (
            self.db.query(UserMusic)
            .filter(UserMusic.user_id == user.id)
            .order_by(UserMusic.created_at.desc())
            .all()
        )

    def upload_music(
        self,
        user: User,
        file: UploadFile,
        title: str,
        description: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        bpm: Optional[int] = None,
    ) -> UserMusic:
        storage_root = music_storage_dir()
        storage_root.mkdir(parents=True, exist_ok=True)
        suffix = Path(file.filename or "").suffix or ".mp3"
        file_name = f"{uuid.uuid4()}{suffix}"
        target_path = storage_root / file_name
        target_path.parent.mkdir(parents=True, exist_ok=True)
        file.file.seek(0)
        with target_path.open("wb") as dest:
            shutil.copyfileobj(file.file, dest)

        music = UserMusic(
            user_id=user.id,
            title=title.strip(),
            description=description,
            audio_storage_path=str(target_path),
            duration_seconds=duration_seconds,
            bpm=bpm,
        )
        self.db.add(music)
        self.db.flush()
        self.db.refresh(music)
        return music

    def transcribe_music(self, user: User, music_id: str, language: str, wallet: WalletManager) -> MusicTranscription:
        music = self.get_music_for_user(user, music_id)
        if not music.duration_seconds:
            raise ValueError("duration_seconds precisa estar preenchido para estimar custo de transcrição.")

        estimate = self.cost_calculator.estimate_music_transcription(float(music.duration_seconds))
        wallet.spend(user, estimate.total_cost_brl, f"[IA] {estimate.operation} {music.title}")

        result = self.ai_client.transcribe_music(Path(music.audio_storage_path), language or "pt")

        transcription = music.transcription or MusicTranscription(user_music_id=music.id)
        transcription.language = result.language
        transcription.transcript_text = result.text
        transcription.transcript_json = result.raw_response
        transcription.generated_by = result.generated_by
        transcription.confidence = result.confidence

        self.db.add(transcription)
        self.db.flush()
        self.db.refresh(transcription)
        return transcription
