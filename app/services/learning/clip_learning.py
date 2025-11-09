"""
Learning helpers to train and apply a clip ranking model based on user feedback.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence, Tuple

import numpy as np
import uuid as uuid_lib
from sqlalchemy.orm import Session, joinedload

from app.models import (
    ClipFeedback,
    LearningCenter,
    MusicAsset,
    VideoAnalysis,
    VideoClipModel,
    VideoIngest,
)
from app.services.feedback_service import LearningCenterService

POSITIVE_MOODS = {"positive", "approved", "like", "liked", "good", "great"}
NEGATIVE_MOODS = {"negative", "rejected", "dislike", "bad", "terrible"}
POSITIVE_HINTS = {"gostei", "aprov", "bom", "perfeito", "legal", "top"}
NEGATIVE_HINTS = {"ruim", "horr", "péssimo", "nao gostei", "não gostei", "negativo", "rejeit"}


@dataclass
class ClipFeatureVector:
    clip_id: uuid_lib.UUID
    video_ingest_id: uuid_lib.UUID
    user_id: uuid_lib.UUID
    features: List[float]
    label: float


@dataclass
class TrainedModelPayload:
    weights: List[float]
    bias: float
    feature_mean: List[float]
    feature_std: List[float]
    metrics: dict
    samples: int
    positives: int
    negatives: int
    trained_at: str


class ClipLearningService:
    """
    Orchestrates extraction of training examples from feedback and stores a simple
    logistic model inside LearningCenter.parameters["learned_model"].
    """

    def __init__(self) -> None:
        self.center_service = LearningCenterService()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def train_for_user(self, session: Session, user_id: str | uuid_lib.UUID) -> Optional[TrainedModelPayload]:
        """Collect feedback for the given user, train a model and persist it."""
        user_uuid = self._to_uuid(user_id)

        examples = self._collect_examples(session, user_uuid)
        if not examples:
            return None

        features_matrix, labels = self._build_training_matrices(examples)
        model_state, metrics = self._train_logistic_regression(features_matrix, labels)

        payload = TrainedModelPayload(
            weights=model_state["weights"].tolist(),
            bias=float(model_state["bias"]),
            feature_mean=model_state["mean"].tolist(),
            feature_std=model_state["std"].tolist(),
            metrics=metrics,
            samples=len(labels),
            positives=int(labels.sum()),
            negatives=int(len(labels) - labels.sum()),
            trained_at=datetime.utcnow().isoformat(),
        )

        center = (
            session.query(LearningCenter)
            .filter(LearningCenter.scope == "artist", LearningCenter.user_id == user_uuid)
            .order_by(LearningCenter.created_at.asc())
            .first()
        )

        if center is None:
            center = self.center_service.create(
                session,
                name="artist-profile",
                scope="artist",
                user_id=str(user_uuid),
                parameters={},
            )

        parameters = dict(center.parameters or {})
        parameters.setdefault("profile", {"mood_counts": {}, "tag_counts": {}})
        parameters["learned_model"] = payload.__dict__
        self.center_service.update(
            session,
            center,
            parameters=parameters,
            notes="model-trained",
        )

        session.flush()
        return payload

    def predict_score(
        self,
        model_payload: dict,
        features: Sequence[float],
    ) -> float:
        """Run inference with a stored model payload."""
        if not model_payload:
            return 0.0

        weights = np.asarray(model_payload.get("weights") or [], dtype=float)
        bias = float(model_payload.get("bias", 0.0))
        feature_mean = np.asarray(model_payload.get("feature_mean") or [], dtype=float)
        feature_std = np.asarray(model_payload.get("feature_std") or [], dtype=float)
        input_vec = np.asarray(list(features), dtype=float)
        if len(weights) != input_vec.shape[0]:
            return 0.0
        normalized = self._safe_normalize(input_vec, feature_mean, feature_std)
        logits = float(np.dot(normalized, weights) + bias)
        return float(self._sigmoid(logits))

    def build_features_for_clip(
        self,
        clip: VideoClipModel,
        analysis: Optional[VideoAnalysis],
        music: Optional[MusicAsset],
        ingest: VideoIngest,
    ) -> List[float]:
        """Expose feature extraction so other services can reuse the same representation."""
        return self._extract_features(clip, analysis, music, ingest)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _collect_examples(self, session: Session, user_id: uuid_lib.UUID) -> List[ClipFeatureVector]:
        """
        Collect clip feedback with associated features. Each feedback is one example.
        """
        query = (
            session.query(VideoClipModel, ClipFeedback, VideoIngest, VideoAnalysis, MusicAsset)
            .join(ClipFeedback, ClipFeedback.clip_id == VideoClipModel.id)
            .join(VideoIngest, VideoIngest.id == VideoClipModel.video_ingest_id)
            .outerjoin(VideoAnalysis, VideoAnalysis.video_ingest_id == VideoIngest.id)
            .outerjoin(MusicAsset, MusicAsset.id == VideoClipModel.music_asset_id)
            .options(joinedload(VideoClipModel.video_ingest))
            .filter(VideoIngest.user_id == user_id)
        )

        examples: List[ClipFeatureVector] = []
        for clip, feedback, ingest, analysis, music in query.all():
            label = self._label_from_feedback(feedback)
            if label is None:
                continue

            features = self._extract_features(clip, analysis, music, ingest)
            if not features:
                continue

            examples.append(
                ClipFeatureVector(
                    clip_id=clip.id,
                    video_ingest_id=clip.video_ingest_id,
                    user_id=ingest.user_id,
                    features=features,
                    label=float(label),
                )
            )
        return examples

    @staticmethod
    def _extract_features(
        clip: VideoClipModel,
        analysis: Optional[VideoAnalysis],
        music: Optional[MusicAsset],
        ingest: VideoIngest,
    ) -> List[float]:
        """
        Create a simple feature vector combining clip stats, motion stats and music metadata.
        """
        segments = clip.video_segments or []
        duration = 0.0
        for segment in segments:
            start = float(segment.get("video_start_seconds") or 0.0)
            end = float(segment.get("video_end_seconds") or start)
            duration += max(0.0, end - start)
        if not segments:
            if clip.music_start_seconds is not None and clip.music_end_seconds is not None:
                duration = float(clip.music_end_seconds) - float(clip.music_start_seconds)
        duration = max(duration, 0.01)

        bpm = float(music.bpm) if (music and music.bpm) else 120.0
        clip_score = float(clip.score or 0.0)

        motion_stats = (analysis.motion_stats or {}) if analysis else {}
        motion_mean = float(
            (motion_stats.get("stats") or {}).get("mean", motion_stats.get("average_motion", 0.5))
        )
        motion_std = float(
            (motion_stats.get("stats") or {}).get("std", 0.1)
        )
        peak_count = len((motion_stats.get("peaks") or [])[:20])
        keywords = analysis.keywords if analysis and analysis.keywords else []
        keyword_count = len(keywords)
        ingest_duration = float(ingest.duration_seconds or duration)

        return [
            duration / 60.0,  # Normalized clip duration (target max 60s)
            clip_score / 100.0,
            bpm / 200.0,
            motion_mean,
            motion_std,
            peak_count / 20.0,
            keyword_count / 10.0,
            ingest_duration / 60.0,
        ]

    @staticmethod
    def _label_from_feedback(feedback: ClipFeedback) -> Optional[int]:
        mood = (feedback.mood or "").strip().lower()
        if mood in POSITIVE_MOODS:
            return 1
        if mood in NEGATIVE_MOODS:
            return 0

        text = (feedback.message or "").strip().lower()
        if any(keyword in text for keyword in POSITIVE_HINTS):
            return 1
        if any(keyword in text for keyword in NEGATIVE_HINTS):
            return 0
        return None

    @staticmethod
    def _build_training_matrices(
        examples: Sequence[ClipFeatureVector],
    ) -> Tuple[np.ndarray, np.ndarray]:
        matrix = np.array([example.features for example in examples], dtype=float)
        labels = np.array([example.label for example in examples], dtype=float)
        return matrix, labels

    def _train_logistic_regression(
        self,
        features: np.ndarray,
        labels: np.ndarray,
        learning_rate: float = 0.1,
        epochs: int = 300,
    ) -> Tuple[dict, dict]:
        normalized, mean, std = self._normalize_matrix(features)
        weights = np.zeros(normalized.shape[1], dtype=float)
        bias = 0.0

        for _ in range(epochs):
            logits = normalized @ weights + bias
            predictions = self._sigmoid(logits)
            error = predictions - labels

            gradient_w = normalized.T @ error / len(labels)
            gradient_b = float(np.mean(error))

            weights -= learning_rate * gradient_w
            bias -= learning_rate * gradient_b

        final_logits = normalized @ weights + bias
        final_preds = self._sigmoid(final_logits)
        binary_preds = (final_preds >= 0.5).astype(float)
        accuracy = float(np.mean(binary_preds == labels))
        positive_rate = float(final_preds.mean())
        metric_payload = {
            "accuracy": accuracy,
            "positive_rate": positive_rate,
        }

        model_state = {
            "weights": weights,
            "bias": bias,
            "mean": mean,
            "std": std,
        }
        return model_state, metric_payload

    @staticmethod
    def _normalize_matrix(matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        mean = matrix.mean(axis=0)
        std = matrix.std(axis=0)
        std = np.where(std < 1e-6, 1.0, std)
        normalized = (matrix - mean) / std
        return normalized, mean, std

    @staticmethod
    def _safe_normalize(vector: np.ndarray, mean: np.ndarray, std: np.ndarray) -> np.ndarray:
        if mean.shape != vector.shape or std.shape != vector.shape:
            return vector
        safe_std = np.where(std < 1e-6, 1.0, std)
        return (vector - mean) / safe_std

    @staticmethod
    def _sigmoid(x: np.ndarray | float) -> np.ndarray | float:
        return 1.0 / (1.0 + np.exp(-x))

    @staticmethod
    def _to_uuid(value: str | uuid_lib.UUID) -> uuid_lib.UUID:
        if isinstance(value, uuid_lib.UUID):
            return value
        return uuid_lib.UUID(str(value))
