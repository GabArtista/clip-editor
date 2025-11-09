from __future__ import annotations

import math
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from sqlalchemy.orm import Session
import uuid as _uuid

from app.models import AssetStatus, MusicAsset, VideoAnalysis, VideoClipModel, VideoIngest, LearningCenter
from app.settings import processed_storage_dir, video_storage_dir
from scripts.download import baixar_reel
from .video_analyzer import get_video_analyzer
from .clip_suggester import get_clip_suggester
from .learning import ClipLearningService


@dataclass
class VideoRequest:
    user_id: str
    url: str
    music_asset_id: Optional[str] = None


class VideoPipeline:
    def __init__(self, downloader=baixar_reel) -> None:
        self.downloader = downloader
        self.video_dir = video_storage_dir()
        self.processed_dir = processed_storage_dir()
        # Inicializa analyzers (lazy loading)
        self._video_analyzer = None
        self._clip_suggester = None
        self._clip_learning_service = None
        
    @property
    def video_analyzer(self):
        """Lazy load do video analyzer."""
        if self._video_analyzer is None:
            self._video_analyzer = get_video_analyzer()
        return self._video_analyzer
    
    @property
    def clip_suggester(self):
        """Lazy load do clip suggester."""
        if self._clip_suggester is None:
            self._clip_suggester = get_clip_suggester()
        return self._clip_suggester

    @property
    def clip_learning_service(self):
        """Lazy load do serviço de aprendizado."""
        if self._clip_learning_service is None:
            self._clip_learning_service = ClipLearningService()
        return self._clip_learning_service

    def ingest_and_suggest(self, db: Session, request: VideoRequest) -> tuple[VideoIngest, List[VideoClipModel]]:
        ingest = self._create_ingest(db, request)
        analysis = self._analyze(db, ingest)
        clip_models = self._generate_suggestions(db, ingest, analysis, request.music_asset_id)

        ingest.status = AssetStatus.ready
        ingest.updated_at = datetime.utcnow()
        db.add(ingest)
        db.commit()
        db.refresh(ingest)
        return ingest, clip_models

    def _create_ingest(self, db: Session, request: VideoRequest) -> VideoIngest:
        storage_path = self._download_video(request.url)
        duration = min(60.0, self._estimate_duration(storage_path))
        ingest = VideoIngest(
            user_id=request.user_id,
            music_asset_id=_uuid.UUID(str(request.music_asset_id)) if request.music_asset_id else None,
            source_url=request.url,
            storage_path=storage_path,
            status=AssetStatus.processing,
            metadata_json={"notes": "placeholder analysis"},
            duration_seconds=duration,
        )
        db.add(ingest)
        db.flush()
        return ingest

    def _download_video(self, url: str) -> str:
        path = self.downloader(url, destino=str(self.video_dir))
        if not path:
            raise RuntimeError("Falha ao baixar o vídeo para análise")
        final_path = Path(path)
        if not final_path.exists():
            raise FileNotFoundError(f"Arquivo de vídeo não encontrado: {final_path}")
        destination = self.video_dir / final_path.name
        if final_path != destination:
            shutil.copyfile(final_path, destination)
        return str(destination)

    def _estimate_duration(self, path: Optional[str]) -> float:
        if not path:
            return 30.0
        try:
            from scripts.edit import _ffprobe_duration

            return float(_ffprobe_duration(path))
        except Exception:
            return 30.0

    def _analyze(self, db: Session, ingest: VideoIngest) -> VideoAnalysis:
        """Analisa vídeo usando IA. Usa placeholders se falhar."""
        
        # Tenta análise real primeiro
        if ingest.storage_path and Path(ingest.storage_path).exists():
            try:
                video_analysis_data = self.video_analyzer.analyze(ingest.storage_path)
                
                analysis = VideoAnalysis(
                    video_ingest_id=ingest.id,
                    scene_breakdown={"scenes": video_analysis_data.get("scenes", [])},
                    motion_stats={
                        "peaks": video_analysis_data.get("motion_peaks", []),
                        "stats": video_analysis_data.get("motion_stats", {}),
                        "energy": video_analysis_data.get("energy", {}),
                    },
                    keywords=video_analysis_data.get("keywords", ["movimento", "energia"]),
                )
                db.add(analysis)
                db.flush()
                return analysis
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Erro na análise de vídeo com IA, usando placeholder: {e}")
        
        # Fallback para placeholders
        duration = float(ingest.duration_seconds or 30.0)
        segments = self._split_segments(duration)
        analysis = VideoAnalysis(
            video_ingest_id=ingest.id,
            scene_breakdown={"segments": segments},
            motion_stats={"average_motion": 0.55, "peaks": [seg["start"] for seg in segments]},
            keywords=["energia", "impacto", "movimento"],
        )
        db.add(analysis)
        db.flush()
        return analysis

    def _split_segments(self, duration: float) -> List[dict]:
        window = max(5.0, min(10.0, duration / 3))
        segments = []
        start = 0.0
        order = 1
        while start < duration:
            end = min(duration, start + window)
            segments.append({"order": order, "start": round(start, 2), "end": round(end, 2)})
            start = end
            order += 1
        return segments

    def _generate_suggestions(
        self,
        db: Session,
        ingest: VideoIngest,
        analysis: VideoAnalysis,
        preferred_music_id: Optional[str],
    ) -> List[VideoClipModel]:
        duration = float(ingest.duration_seconds or 30.0)
        duration = min(duration, 60.0)
        candidate_assets = self._select_music_assets(db, ingest.user_id, preferred_music_id)
        clip_models: List[VideoClipModel] = []
        music_map: Dict[_uuid.UUID, MusicAsset] = {
            asset.id: asset for asset, _ in candidate_assets if asset is not None
        }

        for music_asset, count in candidate_assets:
            offsets = self._compute_offsets(duration, count)
            for idx, offset in enumerate(offsets, start=1):
                segments = [
                    {
                        "segment_order": 1,
                        "video_start_seconds": round(offset, 2),
                        "video_end_seconds": round(min(duration, offset + 12.0), 2),
                        "music_start_seconds": round(offset, 2),
                        "music_end_seconds": round(min(offset + 12.0, offset + duration), 2),
                    }
                ]
                clip = VideoClipModel(
                    video_ingest_id=ingest.id,
                    music_asset_id=music_asset.id if music_asset else None,
                    option_order=len(clip_models) + 1,
                    variant_label=f"{music_asset.title if music_asset else 'auto'} - take {idx}",
                    description="Variação sugerida automaticamente",
                    video_segments=segments,
                    music_start_seconds=segments[0]["music_start_seconds"],
                    music_end_seconds=segments[0]["music_end_seconds"],
                    diversity_tags=["auto" if idx == 1 else "variação"],
                    score=80.0 - (idx * 3),
                )
                db.add(clip)
                clip_models.append(clip)

        # Aplica reranqueamento com base no perfil do artista, se existir
        clip_models = self._rerank_with_artist_profile(db, ingest, analysis, clip_models, music_map)

        # Reatribui option_order após rerank
        for order, clip in enumerate(clip_models, start=1):
            clip.option_order = order

        db.flush()
        return clip_models

    def _rerank_with_artist_profile(
        self,
        db: Session,
        ingest: VideoIngest,
        analysis: VideoAnalysis,
        clips: List[VideoClipModel],
        music_map: Dict[_uuid.UUID, MusicAsset],
    ) -> List[VideoClipModel]:
        # Busca LearningCenter(scope=artist)
        center: LearningCenter | None = (
            db.query(LearningCenter)
            .filter(LearningCenter.scope == "artist", LearningCenter.user_id == ingest.user_id)
            .order_by(LearningCenter.created_at.asc())
            .first()
        )
        if not center or not center.parameters:
            return clips

        params = center.parameters or {}
        profile = params.get("profile") or {}
        weights = params.get("weights") or {
            "base_score": 1.0,
            "mood_affinity": 0.5,
            "keyword_match": 0.5,
            "energy_match": 0.3,
            "ai_model": 0.7,
        }
        learned_model = params.get("learned_model")

        # Extrai keywords do vídeo
        keywords = analysis.keywords or []
        video_keywords = set(keywords if isinstance(keywords, list) else [])
        preferred_tags = set((profile.get("tag_counts") or {}).keys())

        def keyword_affinity() -> float:
            if not video_keywords or not preferred_tags:
                return 0.0
            inter = len(video_keywords.intersection(preferred_tags))
            return min(1.0, inter / max(1, len(preferred_tags)))

        kw_aff = keyword_affinity()

        reranked: List[tuple[float, VideoClipModel]] = []
        for clip in clips:
            base = float(clip.score or 0.0)
            new_score = (
                weights.get("base_score", 1.0) * base
                + weights.get("keyword_match", 0.5) * kw_aff * 100.0
            )

            if learned_model:
                music_asset = None
                if clip.music_asset_id:
                    music_asset = music_map.get(clip.music_asset_id)
                    if music_asset is None and clip.music_asset is not None:
                        music_asset = clip.music_asset
                    if music_asset is None:
                        music_asset = (
                            db.query(MusicAsset)
                            .filter(MusicAsset.id == clip.music_asset_id)
                            .first()
                        )
                        if music_asset:
                            music_map[clip.music_asset_id] = music_asset
                features = self.clip_learning_service.build_features_for_clip(
                    clip,
                    analysis,
                    music_asset,
                    ingest,
                )
                model_score = self.clip_learning_service.predict_score(learned_model, features)
                new_score += weights.get("ai_model", 0.7) * model_score * 100.0

            clip.score = new_score
            reranked.append((new_score, clip))

        reranked.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in reranked]

    def _select_music_assets(
        self, db: Session, user_id: str, preferred_music_id: Optional[str]
    ) -> List[tuple[Optional[MusicAsset], int]]:
        if preferred_music_id:
            asset = (
                db.query(MusicAsset)
                .filter(MusicAsset.id == _uuid.UUID(str(preferred_music_id)), MusicAsset.user_id == user_id)
                .first()
            )
            if not asset:
                raise ValueError("Música selecionada não encontrada")
            return [(asset, 3)]

        assets = (
            db.query(MusicAsset)
            .filter(MusicAsset.user_id == user_id, MusicAsset.status == AssetStatus.ready)
            .order_by(MusicAsset.processed_at.desc())
            .limit(2)
            .all()
        )
        if not assets:
            raise ValueError("Nenhuma música disponível para sugerir")
        return [(asset, 2) for asset in assets]

    def _compute_offsets(self, duration: float, count: int) -> List[float]:
        if count <= 0:
            return []
        base_step = max(5.0, duration / max(count + 1, 2))
        offsets: List[float] = []
        for idx in range(count):
            offset = idx * base_step
            if offset > max(0.0, duration - 5.0):
                offset = max(0.0, duration - 5.0)
            offsets.append(round(offset, 2))
        # Garantir diferença mínima de 5 segundos
        for i in range(1, len(offsets)):
            if offsets[i] - offsets[i - 1] < 5.0:
                offsets[i] = min(duration - 5.0, offsets[i - 1] + 5.0)
        return [max(0.0, value) for value in offsets]
