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
from .storage import StorageDriver, get_storage_driver
from .audio_analyzer import get_audio_analyzer


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
    def __init__(self, storage_dir: Optional[Path] = None, storage_driver: Optional[StorageDriver] = None) -> None:
        self.storage_dir = storage_dir or music_storage_dir()
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.storage_driver = storage_driver or get_storage_driver()
        # Inicializa audio analyzer (lazy loading)
        self._audio_analyzer = None

    def _save_upload(self, upload: UploadFile, user_id: str, music_id: str) -> tuple[str, int]:
        """Salva o upload usando o driver de storage configurado."""
        # Extrai a extensão do arquivo
        suffix = os.path.splitext(upload.filename or "")[1].lower() or ".mp3"
        
        # Define a chave do objeto no formato: media/{user_id}/{music_id}/original.{ext}
        object_key = f"media/{user_id}/{music_id}/original{suffix}"
        
        # Lê o conteúdo do arquivo
        file_content = upload.file.read()
        file_size = len(file_content)
        
        # Faz upload usando o driver
        storage_path = self.storage_driver.upload_file(
            file_content=io.BytesIO(file_content),
            object_key=object_key,
            content_type=upload.content_type,
        )
        
        upload.file.seek(0)
        return storage_path, file_size

    def _calculate_checksum(self, file_obj: io.BufferedReader) -> str:
        file_obj.seek(0)
        sha = hashlib.sha256()
        for chunk in iter(lambda: file_obj.read(8192), b""):
            sha.update(chunk)
        file_obj.seek(0)
        return sha.hexdigest()

    @property
    def audio_analyzer(self):
        """Lazy load do audio analyzer."""
        if self._audio_analyzer is None:
            self._audio_analyzer = get_audio_analyzer()
        return self._audio_analyzer

    def _prefill_analysis(self, declared_genre: Optional[str], audio_path: Optional[str] = None) -> AnalysisResult:
        """Realiza análise de áudio. Usa IA se audio_path fornecido, senão retorna placeholders."""
        
        if audio_path and Path(audio_path).exists():
            try:
                # Análise real com IA
                analysis_data = self.audio_analyzer.analyze(audio_path)
                
                beats = [
                    (beat, "beat", 0.8) for beat in analysis_data.get("beats", [])[:50]  # Limita a 50 beats
                ]
                
                # Cria embedding simples baseado em BPM e key
                embedding_vector = [
                    analysis_data.get("bpm", 120) / 200.0,  # Normaliza BPM
                    analysis_data.get("energy", {}).get("mean", 0.5),
                    float(len(analysis_data.get("beats", [])) / 100),  # Densidade de beats
                    0.5,  # Placeholder
                    0.5,  # Placeholder
                ]
                embeddings = [("rhythm", {"vector": embedding_vector})]
                
                summary = {
                    "notes": "Análise realizada com IA usando librosa e Whisper",
                    "created_at": datetime.utcnow().isoformat(),
                    "bpm_detected": analysis_data.get("bpm"),
                    "key_detected": analysis_data.get("key"),
                }
                
                return AnalysisResult(
                    genre_inferred=declared_genre or "desconhecido",
                    genre_confidence=0.7 if declared_genre else 0.3,
                    bpm=analysis_data.get("bpm"),
                    musical_key=analysis_data.get("key"),
                    transcription_text=analysis_data.get("transcription", ""),
                    transcription_language=analysis_data.get("language", "pt"),
                    beats=beats if beats else [(i * 0.5, "beat", 0.8) for i in range(6)],
                    embeddings=embeddings,
                    analysis_summary=summary,
                )
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erro na análise de IA, usando placeholder: {e}")
        
        # Fallback para placeholders
        inferred = declared_genre or "desconhecido"
        beats = [(i * 0.5, "beat", 0.8) for i in range(6)]
        embeddings = [("rhythm", {"vector": [0.1 * i for i in range(5)]})]
        summary = {
            "notes": "Análise placeholder (IA indisponível ou falhou)",
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
        # Importa UUID aqui para evitar import circular
        import uuid as uuid_lib
        
        # Converte user_id para UUID se necessário
        user_id = metadata.user_id
        if isinstance(user_id, str):
            user_id = uuid_lib.UUID(user_id)
        
        # Cria o asset primeiro para obter o ID
        asset = MusicAsset(
            user_id=user_id,
            title=metadata.title,
            description=metadata.description,
            genre=metadata.declared_genre,
            status=AssetStatus.processing,
        )
        db.add(asset)
        db.flush()
        
        # Agora usa o ID do asset para construir o path do storage
        storage_path, size_bytes = self._save_upload(upload, str(user_id), str(asset.id))
        
        checksum = self._calculate_checksum(upload.file)

        audio = AudioFile(
            user_id=user_id,
            storage_path=storage_path,
            original_filename=upload.filename,
            mime_type=upload.content_type,
            size_bytes=size_bytes,
            checksum=checksum,
        )
        db.add(audio)
        db.flush()

        # Atualiza o asset com o audio_file_id
        asset.audio_file_id = audio.id
        db.add(asset)
        db.flush()

        # Pega o caminho do arquivo para análise (temporário, será movido para S3 depois)
        # Se for storage local, usa o path diretamente
        audio_path = storage_path if not storage_path.startswith("s3://") else None
        
        analysis = self._prefill_analysis(metadata.declared_genre, audio_path=audio_path)
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
        # Gera URL presignada se o storage suportar
        download_url = None
        if asset.audio_file and asset.audio_file.storage_path:
            # Tenta extrair a object_key do storage_path
            if asset.audio_file.storage_path.startswith("s3://"):
                # Formato: s3://bucket/media/user_id/music_id/original.mp3
                parts = asset.audio_file.storage_path.split("/")
                if len(parts) >= 4:
                    object_key = "/".join(parts[3:])  # Remove s3://bucket/
                    download_url = self.storage_driver.get_presigned_url(object_key)
            elif self.storage_driver.file_exists(asset.audio_file.storage_path):
                download_url = self.storage_driver.get_presigned_url(asset.audio_file.storage_path)
        
        result = {
            "id": str(asset.id),
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
        
        if download_url:
            result["download_url"] = download_url
        
        return result
