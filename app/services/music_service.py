from __future__ import annotations

import hashlib
import io
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional

from fastapi import UploadFile
from sqlalchemy.orm import Session

from ..models import (
    AssetStatus,
    AudioFile,
    MusicAsset,
    MusicBeat,
    MusicEmbedding,
    MusicTranscription,
)
from ..settings import music_storage_dir


@dataclass
class MusicMetadata:
    user_id: str
    title: str
    description: Optional[str] = None
    declared_genre: Optional[str] = None


@dataclass
class AnalysisResult:
    genre_inferred: Optional[str]
    genre_confidence: Optional[float]
    bpm: Optional[int]
    musical_key: Optional[str]
    transcription_text: str
    transcription_language: str
    beats: List[tuple[float, str, float]]
    embeddings: List[tuple[str, dict]]
    analysis_summary: dict


class MusicService:
    def __init__(self, storage_dir: Optional[Path] = None) -> None:
        self.storage_dir = storage_dir or music_storage_dir()
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _save_upload(self, upload: UploadFile) -> tuple[str, int]:
        suffix = os.path.splitext(upload.filename or "")[1].lower()
        filename = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}_{hashlib.sha1(os.urandom(16)).hexdigest()}{suffix or '.mp3'}"
        destination = self.storage_dir / filename
        with destination.open("wb") as output:
            data = upload.file.read()
            output.write(data)
        size = destination.stat().st_size
        upload.file.seek(0)
        return filename, size

    def _calculate_checksum(self, file_obj: io.BufferedReader) -> str:
        file_obj.seek(0)
        sha = hashlib.sha256()
        for chunk in iter(lambda: file_obj.read(8192), b""):
            sha.update(chunk)
        file_obj.seek(0)
        return sha.hexdigest()

    def _prefill_analysis(self, declared_genre: Optional[str]) -> AnalysisResult:
        inferred = declared_genre or "desconhecido"
        beats = [(i * 0.5, "beat", 0.8) for i in range(6)]
        embeddings = [("rhythm", {"vector": [0.1 * i for i in range(5)]})]
        summary = {
            "notes": "Análise prévia placeholder. Substituir por pipeline IA.",
            "created_at": datetime.utcnow().isoformat(),
        }
        return AnalysisResult(
            genre_inferred=inferred,
            genre_confidence=0.5 if declared_genre else 0.3,
            bpm=96,
            musical_key="C",
            transcription_text="Transcrição automática indisponível no ambiente local.",
            transcription_language="pt",
            beats=beats,
            embeddings=embeddings,
            analysis_summary=summary,
        )

    def create_music_asset(self, db: Session, upload: UploadFile, metadata: MusicMetadata) -> MusicAsset:
        stored_name, size_bytes = self._save_upload(upload)
        storage_path = str(self.storage_dir / stored_name)

        checksum = self._calculate_checksum(upload.file)

        audio = AudioFile(
            user_id=metadata.user_id,
            storage_path=storage_path,
            original_filename=upload.filename,
            mime_type=upload.content_type,
            size_bytes=size_bytes,
            checksum=checksum,
        )
        db.add(audio)
        db.flush()

        asset = MusicAsset(
            user_id=metadata.user_id,
            audio_file_id=audio.id,
            title=metadata.title,
            description=metadata.description,
            genre=metadata.declared_genre,
            status=AssetStatus.processing,
        )
        db.add(asset)
        db.flush()

        analysis = self._prefill_analysis(metadata.declared_genre)
        self._apply_analysis(db, asset, analysis)

        asset.status = AssetStatus.ready
        asset.processed_at = datetime.utcnow()
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    def _apply_analysis(self, db: Session, asset: MusicAsset, analysis: AnalysisResult) -> None:
        asset.genre_inferred = analysis.genre_inferred
        asset.genre_confidence = analysis.genre_confidence
        asset.bpm = analysis.bpm
        asset.musical_key = analysis.musical_key
        asset.analysis_version = "placeholder-1"
        asset.analysis_summary = analysis.analysis_summary

        transcription = MusicTranscription(
            music_asset_id=asset.id,
            transcript_text=analysis.transcription_text,
            transcript_json={"text": analysis.transcription_text},
            language=analysis.transcription_language,
            model_version="placeholder",
            confidence=0.0,
            started_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(transcription)

        beats = [
            MusicBeat(
                music_asset_id=asset.id,
                timestamp_seconds=timestamp,
                beat_type=beat_type,
                confidence=confidence,
            )
            for (timestamp, beat_type, confidence) in analysis.beats
        ]
        db.add_all(beats)

        embedding_records: Iterable[MusicEmbedding] = [
            MusicEmbedding(
                music_asset_id=asset.id,
                embedding_type=embedding_type,
                vector=payload,
            )
            for embedding_type, payload in analysis.embeddings
        ]
        db.add_all(list(embedding_records))

    def to_response_dict(self, asset: MusicAsset) -> dict:
        return {
            "id": asset.id,
            "title": asset.title,
            "status": asset.status.value if isinstance(asset.status, AssetStatus) else asset.status,
            "genre": asset.genre,
            "genre_inferred": asset.genre_inferred,
            "bpm": asset.bpm,
            "musical_key": asset.musical_key,
            "analysis_version": asset.analysis_version,
            "uploaded_at": asset.uploaded_at,
            "processed_at": asset.processed_at,
            "description": asset.description,
            "genre_confidence": float(asset.genre_confidence) if asset.genre_confidence is not None else None,
            "analysis_summary": asset.analysis_summary,
            "beats": [
                {
                    "timestamp_seconds": float(beat.timestamp_seconds),
                    "beat_type": beat.beat_type,
                    "confidence": float(beat.confidence) if beat.confidence is not None else None,
                }
                for beat in sorted(asset.beats, key=lambda b: float(b.timestamp_seconds))
            ],
            "embeddings": [
                {
                    "embedding_type": embedding.embedding_type,
                    "vector": embedding.vector,
                }
                for embedding in asset.embeddings
            ],
            "transcription": None
            if not asset.transcription
            else {
                "transcript_text": asset.transcription.transcript_text,
                "language": asset.transcription.language,
                "model_version": asset.transcription.model_version,
                "confidence": float(asset.transcription.confidence) if asset.transcription.confidence is not None else None,
            },
        }
