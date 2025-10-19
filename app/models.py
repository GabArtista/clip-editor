from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, Enum, ForeignKey, Numeric, String, Text, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


UUID_STR = String(36)


def _uuid_str() -> str:
    return str(uuid.uuid4())


class AssetStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    ready = "ready"
    failed = "failed"
    archived = "archived"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    password_hash: Mapped[Optional[str]] = mapped_column(String(255))
    status: Mapped[Optional[str]] = mapped_column(String(32), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    music_assets: Mapped[List["MusicAsset"]] = relationship(back_populates="user")
    video_ingests: Mapped[List["VideoIngest"]] = relationship(back_populates="user")
    music_feedback_entries: Mapped[List["MusicFeedback"]] = relationship(back_populates="user")
    artist_feedback_entries: Mapped[List["ArtistFeedback"]] = relationship(back_populates="user")
    learning_centers: Mapped[List["LearningCenter"]] = relationship(back_populates="user")
    learning_events: Mapped[List["AILearningEvent"]] = relationship(back_populates="user")


class AudioFile(Base):
    __tablename__ = "audio_files"

    id: Mapped[str] = mapped_column(
        UUID_STR,
        primary_key=True,
        default=_uuid_str,
    )
    user_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("users.id", ondelete="CASCADE"))
    storage_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    original_filename: Mapped[Optional[str]] = mapped_column(String(255))
    mime_type: Mapped[Optional[str]] = mapped_column(String(128))
    duration_seconds: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    size_bytes: Mapped[Optional[int]] = mapped_column()
    checksum: Mapped[Optional[str]] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="audio_files", viewonly=True)
    music_asset: Mapped["MusicAsset"] = relationship(back_populates="audio_file", uselist=False)


User.audio_files = relationship("AudioFile", back_populates="user", cascade="all, delete")  # type: ignore[attr-defined]


class MusicAsset(Base):
    __tablename__ = "music_assets"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("users.id", ondelete="CASCADE"))
    audio_file_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("audio_files.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text())
    genre: Mapped[Optional[str]] = mapped_column(String(128))
    genre_inferred: Mapped[Optional[str]] = mapped_column(String(128))
    genre_confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    bpm: Mapped[Optional[int]] = mapped_column()
    musical_key: Mapped[Optional[str]] = mapped_column(String(32))
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status", native_enum=False),
        default=AssetStatus.pending,
    )
    analysis_version: Mapped[Optional[str]] = mapped_column(String(32))
    analysis_summary: Mapped[Optional[dict]] = mapped_column(JSON)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(back_populates="music_assets")
    audio_file: Mapped["AudioFile"] = relationship(back_populates="music_asset")
    transcription: Mapped[Optional["MusicTranscription"]] = relationship(back_populates="music_asset", uselist=False)
    beats: Mapped[List["MusicBeat"]] = relationship(back_populates="music_asset", cascade="all, delete-orphan")
    embeddings: Mapped[List["MusicEmbedding"]] = relationship(
        back_populates="music_asset",
        cascade="all, delete-orphan",
    )
    video_clip_models: Mapped[List["VideoClipModel"]] = relationship(back_populates="music_asset")
    preferred_video_ingests: Mapped[List["VideoIngest"]] = relationship(back_populates="music_asset")
    feedback_entries: Mapped[List["MusicFeedback"]] = relationship(back_populates="music_asset")
    artist_feedback_entries: Mapped[List["ArtistFeedback"]] = relationship(back_populates="music_asset")
    learning_centers: Mapped[List["LearningCenter"]] = relationship(back_populates="music_asset")


class MusicTranscription(Base):
    __tablename__ = "music_transcriptions"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    music_asset_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("music_assets.id", ondelete="CASCADE"))
    transcript_text: Mapped[Optional[str]] = mapped_column(Text())
    transcript_json: Mapped[Optional[dict]] = mapped_column(JSON)
    language: Mapped[str] = mapped_column(String(8), default="pt")
    model_version: Mapped[Optional[str]] = mapped_column(String(64))
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    music_asset: Mapped["MusicAsset"] = relationship(back_populates="transcription")


class MusicBeat(Base):
    __tablename__ = "music_beats"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    music_asset_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("music_assets.id", ondelete="CASCADE"))
    timestamp_seconds: Mapped[float] = mapped_column(Numeric(10, 2))
    beat_type: Mapped[str] = mapped_column(String(32), default="beat")
    confidence: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    music_asset: Mapped["MusicAsset"] = relationship(back_populates="beats")


class MusicEmbedding(Base):
    __tablename__ = "music_embeddings"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    music_asset_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("music_assets.id", ondelete="CASCADE"))
    embedding_type: Mapped[str] = mapped_column(String(64))
    vector: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    music_asset: Mapped["MusicAsset"] = relationship(back_populates="embeddings")


class VideoIngest(Base):
    __tablename__ = "video_ingests"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("users.id", ondelete="CASCADE"))
    music_asset_id: Mapped[Optional[str]] = mapped_column(
        UUID_STR,
        ForeignKey("music_assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_url: Mapped[str] = mapped_column(String(1024))
    storage_path: Mapped[Optional[str]] = mapped_column(String(1024))
    duration_seconds: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    status: Mapped[AssetStatus] = mapped_column(
        Enum(AssetStatus, name="asset_status", native_enum=False),
        default=AssetStatus.pending,
    )
    metadata_json: Mapped[Optional[dict]] = mapped_column("metadata", JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="video_ingests")
    music_asset: Mapped[Optional["MusicAsset"]] = relationship(back_populates="preferred_video_ingests")
    analysis: Mapped[Optional["VideoAnalysis"]] = relationship(
        back_populates="video_ingest",
        cascade="all, delete-orphan",
        uselist=False,
    )
    clip_models: Mapped[List["VideoClipModel"]] = relationship(
        back_populates="video_ingest",
        cascade="all, delete-orphan",
    )


class VideoAnalysis(Base):
    __tablename__ = "video_analysis"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    video_ingest_id: Mapped[str] = mapped_column(
        UUID_STR,
        ForeignKey("video_ingests.id", ondelete="CASCADE"),
        nullable=False,
    )
    scene_breakdown: Mapped[Optional[dict]] = mapped_column(JSON)
    motion_stats: Mapped[Optional[dict]] = mapped_column(JSON)
    keywords: Mapped[Optional[List[str]]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    video_ingest: Mapped["VideoIngest"] = relationship(back_populates="analysis")


class VideoClipModel(Base):
    __tablename__ = "video_clip_models"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    video_ingest_id: Mapped[str] = mapped_column(
        UUID_STR,
        ForeignKey("video_ingests.id", ondelete="CASCADE"),
        nullable=False,
    )
    music_asset_id: Mapped[Optional[str]] = mapped_column(
        UUID_STR,
        ForeignKey("music_assets.id", ondelete="SET NULL"),
        nullable=True,
    )
    option_order: Mapped[int] = mapped_column()
    variant_label: Mapped[str] = mapped_column(String(64))
    description: Mapped[Optional[str]] = mapped_column(Text())
    video_segments: Mapped[List[dict]] = mapped_column(JSON)
    music_start_seconds: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    music_end_seconds: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    diversity_tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    score: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    video_ingest: Mapped["VideoIngest"] = relationship(back_populates="clip_models")
    music_asset: Mapped[Optional["MusicAsset"]] = relationship(back_populates="video_clip_models")


class AILearningEvent(Base):
    __tablename__ = "ai_learning_events"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("users.id", ondelete="CASCADE"))
    source: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
    weight: Mapped[float] = mapped_column(Numeric(5, 2), default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="learning_events")


class MusicFeedback(Base):
    __tablename__ = "music_feedback"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    music_asset_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("music_assets.id", ondelete="CASCADE"))
    user_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("users.id", ondelete="CASCADE"))
    message: Mapped[str] = mapped_column(Text())
    mood: Mapped[Optional[str]] = mapped_column(String(32))
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    source: Mapped[Optional[str]] = mapped_column(String(64))
    weight: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    music_asset: Mapped["MusicAsset"] = relationship(back_populates="feedback_entries")
    user: Mapped["User"] = relationship(back_populates="music_feedback_entries")


class ArtistFeedback(Base):
    __tablename__ = "artist_feedback"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    user_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("users.id", ondelete="CASCADE"))
    music_asset_id: Mapped[Optional[str]] = mapped_column(UUID_STR, ForeignKey("music_assets.id", ondelete="SET NULL"))
    message: Mapped[str] = mapped_column(Text())
    mood: Mapped[Optional[str]] = mapped_column(String(32))
    tags: Mapped[Optional[List[str]]] = mapped_column(JSON)
    source: Mapped[Optional[str]] = mapped_column(String(64))
    weight: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped["User"] = relationship(back_populates="artist_feedback_entries")
    music_asset: Mapped[Optional["MusicAsset"]] = relationship()


class GlobalGenreProfile(Base):
    __tablename__ = "global_genre_profiles"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    genre: Mapped[str] = mapped_column(String(128), unique=True)
    metrics: Mapped[Optional[dict]] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LearningCenter(Base):
    __tablename__ = "learning_centers"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text())
    scope: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="active")
    user_id: Mapped[Optional[str]] = mapped_column(UUID_STR, ForeignKey("users.id", ondelete="CASCADE"))
    music_asset_id: Mapped[Optional[str]] = mapped_column(UUID_STR, ForeignKey("music_assets.id", ondelete="SET NULL"))
    genre: Mapped[Optional[str]] = mapped_column(String(128))
    is_experimental: Mapped[bool] = mapped_column(Boolean, default=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON)
    baseline_snapshot: Mapped[Optional[dict]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user: Mapped[Optional["User"]] = relationship(back_populates="learning_centers")
    music_asset: Mapped[Optional["MusicAsset"]] = relationship(back_populates="learning_centers")
    history: Mapped[List["LearningCenterHistory"]] = relationship(
        back_populates="learning_center",
        cascade="all, delete-orphan",
        order_by="LearningCenterHistory.version",
    )


class LearningCenterHistory(Base):
    __tablename__ = "learning_center_history"

    id: Mapped[str] = mapped_column(UUID_STR, primary_key=True, default=_uuid_str)
    learning_center_id: Mapped[str] = mapped_column(UUID_STR, ForeignKey("learning_centers.id", ondelete="CASCADE"))
    version: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32))
    payload: Mapped[Optional[dict]] = mapped_column(JSON)
    notes: Mapped[Optional[str]] = mapped_column(Text())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    learning_center: Mapped["LearningCenter"] = relationship(back_populates="history")
