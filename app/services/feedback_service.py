from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import (
    AILearningEvent,
    ArtistFeedback,
    GlobalGenreProfile,
    LearningCenter,
    LearningCenterHistory,
    MusicAsset,
    MusicFeedback,
)
from metrics import (
    estimate_tokens_from_text,
    increment_counter,
    record_token_usage,
)


class FeedbackService:
    """Registra feedbacks de músicas e artistas alimentando o aprendizado contínuo."""

    def record_music_feedback(
        self,
        session: Session,
        *,
        user_id: str,
        music_asset_id: str,
        message: str,
        mood: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        weight: Optional[float] = None,
    ) -> MusicFeedback:
        asset = (
            session.query(MusicAsset)
            .filter(MusicAsset.id == music_asset_id, MusicAsset.user_id == user_id)
            .first()
        )
        if not asset:
            raise ValueError("music_not_found")

        feedback = MusicFeedback(
            music_asset_id=music_asset_id,
            user_id=user_id,
            message=message,
            mood=mood,
            tags=tags or None,
            source=source or "music_feedback",
            weight=weight,
        )
        session.add(feedback)
        session.flush()

        event_payload = {
            "type": "music_feedback",
            "music_asset_id": music_asset_id,
            "message": message,
            "mood": mood,
            "tags": tags or [],
        }
        if weight is not None:
            event_payload["weight"] = float(weight)

        session.add(
            AILearningEvent(
                user_id=user_id,
                source=source or "music_feedback",
                payload=event_payload,
                weight=weight or 1.0,
            )
        )

        estimated_tokens = estimate_tokens_from_text(message)
        record_token_usage(user_id, estimated_tokens, music_asset_id)
        increment_counter(
            "feedback_events_total",
            labels={"type": "music", "mood": mood or "unknown"},
            help_text="Total de feedbacks registrados",
        )

        genre = asset.genre_inferred or asset.genre
        self._update_global_genre_profile(session, genre, weight)
        # Atualiza perfil do artista para personalização futura
        self._update_artist_profile_from_feedback(
            session,
            user_id=user_id,
            message=message,
            mood=mood,
            tags=tags or [],
            weight=weight or 1.0,
        )
        return feedback

    def record_artist_feedback(
        self,
        session: Session,
        *,
        user_id: str,
        message: str,
        mood: Optional[str] = None,
        tags: Optional[List[str]] = None,
        source: Optional[str] = None,
        weight: Optional[float] = None,
        music_asset_id: Optional[str] = None,
    ) -> ArtistFeedback:
        asset = None
        if music_asset_id:
            asset = (
                session.query(MusicAsset)
                .filter(MusicAsset.id == music_asset_id, MusicAsset.user_id == user_id)
                .first()
            )
            if not asset:
                raise ValueError("music_not_found")

        feedback = ArtistFeedback(
            user_id=user_id,
            music_asset_id=music_asset_id,
            message=message,
            mood=mood,
            tags=tags or None,
            source=source or "artist_feedback",
            weight=weight,
        )
        session.add(feedback)
        session.flush()

        payload = {
            "type": "artist_feedback",
            "message": message,
            "mood": mood,
            "tags": tags or [],
        }
        if music_asset_id:
            payload["music_asset_id"] = music_asset_id
        if weight is not None:
            payload["weight"] = float(weight)

        session.add(
            AILearningEvent(
                user_id=user_id,
                source=source or "artist_feedback",
                payload=payload,
                weight=weight or 1.0,
            )
        )

        genre = asset.genre_inferred or asset.genre if asset else None
        self._update_global_genre_profile(session, genre, weight)
        estimated_tokens = estimate_tokens_from_text(message)
        record_token_usage(user_id, estimated_tokens, music_asset_id)
        increment_counter(
            "feedback_events_total",
            labels={"type": "artist", "mood": mood or "unknown"},
            help_text="Total de feedbacks registrados",
        )
        # Atualiza perfil do artista para personalização futura
        self._update_artist_profile_from_feedback(
            session,
            user_id=user_id,
            message=message,
            mood=mood,
            tags=tags or [],
            weight=weight or 1.0,
        )
        return feedback

    def _update_global_genre_profile(
        self, session: Session, genre: Optional[str], weight: Optional[float]
    ) -> None:
        if not genre:
            return
        profile = (
            session.query(GlobalGenreProfile)
            .filter(GlobalGenreProfile.genre == genre)
            .first()
        )
        if not profile:
            profile = GlobalGenreProfile(genre=genre, metrics={})
            session.add(profile)

        metrics = profile.metrics or {}
        metrics["feedback_count"] = int(metrics.get("feedback_count", 0)) + 1
        if weight is not None:
            metrics["weight_sum"] = float(metrics.get("weight_sum", 0.0)) + float(weight)
        profile.metrics = metrics
        profile.updated_at = datetime.utcnow()
        increment_counter(
            "genre_profiles_updates_total",
            labels={"genre": genre},
            help_text="Atualizações em perfis globais por gênero",
        )

    def _update_artist_profile_from_feedback(
        self,
        session: Session,
        *,
        user_id: str,
        message: str,
        mood: Optional[str],
        tags: List[str],
        weight: float,
    ) -> None:
        """
        Consolida feedbacks em um perfil simples do artista, armazenado em LearningCenter(scope="artist").
        Atualiza contadores de moods/tags e pesos de preferência.
        """
        # Obtém ou cria o centro do artista
        center: LearningCenter | None = (
            session.query(LearningCenter)
            .filter(LearningCenter.scope == "artist", LearningCenter.user_id == user_id)
            .order_by(LearningCenter.created_at.asc())
            .first()
        )
        if center is None:
            center = LearningCenter(
                name="artist-profile",
                scope="artist",
                user_id=user_id,
                status="active",
                parameters={},
            )
            session.add(center)
            session.flush()
            self._record_history(session, center, notes="created-by-feedback")

        params = dict(center.parameters or {})

        # Estrutura básica de perfil
        profile = params.get("profile") or {
            "mood_counts": {},
            "tag_counts": {},
            "weight_sum": 0.0,
            "feedback_count": 0,
        }

        if mood:
            profile["mood_counts"][mood] = int(profile["mood_counts"].get(mood, 0)) + 1

        for tag in (tags or []):
            profile["tag_counts"][tag] = int(profile["tag_counts"].get(tag, 0)) + 1

        profile["feedback_count"] = int(profile.get("feedback_count", 0)) + 1
        profile["weight_sum"] = float(profile.get("weight_sum", 0.0)) + float(weight)

        # Pesos default para rerankeamento, ajustáveis ao longo do tempo
        default_weights = {
            "base_score": 1.0,
            "mood_affinity": 0.5,
            "keyword_match": 0.5,
            "energy_match": 0.3,
        }
        weights = params.get("weights") or default_weights
        # Garante todas as chaves
        for k, v in default_weights.items():
            weights.setdefault(k, v)

        params["profile"] = profile
        params["weights"] = weights
        center.parameters = params
        center.version += 1
        center.updated_at = datetime.utcnow()
        self._record_history(session, center, notes="profile-updated")
        increment_counter(
            "learning_center_events_total",
            labels={"action": "profile_update", "scope": "artist"},
            help_text="Atualizações de perfil do artista",
        )

class LearningCenterService:
    """Gerencia centros de aprendizado com versionamento e histórico."""

    def create(
        self,
        session: Session,
        *,
        name: str,
        scope: str,
        user_id: Optional[str] = None,
        music_asset_id: Optional[str] = None,
        genre: Optional[str] = None,
        description: Optional[str] = None,
        is_experimental: bool = False,
        parameters: Optional[dict] = None,
    ) -> LearningCenter:
        self._validate_scope(session, scope, user_id, music_asset_id)

        center = LearningCenter(
            name=name,
            description=description,
            scope=scope,
            user_id=user_id,
            music_asset_id=music_asset_id,
            genre=genre,
            is_experimental=is_experimental,
            parameters=parameters,
        )
        session.add(center)
        session.flush()
        self._record_history(session, center, notes="created")
        increment_counter(
            "learning_center_events_total",
            labels={"action": "create", "scope": scope},
            help_text="Eventos de centros de aprendizado",
        )
        return center

    def update(
        self,
        session: Session,
        center: LearningCenter,
        *,
        name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None,
        is_experimental: Optional[bool] = None,
        parameters: Optional[dict] = None,
        notes: Optional[str] = None,
    ) -> LearningCenter:
        changed = False

        if name is not None and center.name != name:
            center.name = name
            changed = True
        if description is not None and center.description != description:
            center.description = description
            changed = True
        if status is not None and center.status != status:
            center.status = status
            changed = True
        if is_experimental is not None and center.is_experimental != is_experimental:
            center.is_experimental = is_experimental
            changed = True
        if parameters is not None:
            center.parameters = parameters
            changed = True

        if changed:
            center.version += 1
            center.updated_at = datetime.utcnow()
            self._record_history(session, center, notes=notes or "updated")
            increment_counter(
                "learning_center_events_total",
                labels={"action": "update", "scope": center.scope},
                help_text="Eventos de centros de aprendizado",
            )
        return center

    def archive(
        self, session: Session, center: LearningCenter, *, notes: Optional[str] = None
    ) -> LearningCenter:
        if center.status != "archived":
            center.status = "archived"
            center.version += 1
            center.updated_at = datetime.utcnow()
            self._record_history(session, center, notes=notes or "archived")
            increment_counter(
                "learning_center_events_total",
                labels={"action": "archive", "scope": center.scope},
                help_text="Eventos de centros de aprendizado",
            )
        return center

    def _record_history(
        self,
        session: Session,
        center: LearningCenter,
        *,
        notes: Optional[str] = None,
    ) -> None:
        history = LearningCenterHistory(
            learning_center_id=center.id,
            version=center.version,
            status=center.status,
            payload={
                "name": center.name,
                "description": center.description,
                "scope": center.scope,
                "user_id": center.user_id,
                "music_asset_id": center.music_asset_id,
                "genre": center.genre,
                "is_experimental": center.is_experimental,
                "parameters": center.parameters,
            },
            notes=notes,
        )
        session.add(history)

    def _validate_scope(
        self,
        session: Session,
        scope: str,
        user_id: Optional[str],
        music_asset_id: Optional[str],
    ) -> None:
        normalized = scope.lower()
        if normalized not in {"global", "artist", "music"}:
            raise ValueError("invalid_scope")

        if normalized == "global":
            if user_id or music_asset_id:
                raise ValueError("global_scope_invalid_payload")
        elif normalized == "artist":
            if not user_id:
                raise ValueError("artist_scope_requires_user")
        elif normalized == "music":
            if not music_asset_id:
                raise ValueError("music_scope_requires_music")
            asset_exists = (
                session.query(MusicAsset.id)
                .filter(MusicAsset.id == music_asset_id, MusicAsset.user_id == user_id)
                .first()
            )
            if not asset_exists:
                raise ValueError("music_not_found")
