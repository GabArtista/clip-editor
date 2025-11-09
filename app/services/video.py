from __future__ import annotations

from dataclasses import dataclass
import math
from typing import List, Sequence
from uuid import UUID

from sqlalchemy.orm import Session, joinedload

from app.models import MusicTranscription, User, UserMusic
from app.services.ai import AIClient, describe_video_payload, VideoSuggestionResult, VideoVariationResult
from app.services.costs import CostCalculator
from app.services.wallet import WalletManager


@dataclass
class MusicContext:
    id: str
    title: str
    bpm: int | None
    transcript_excerpt: str


class VideoService:
    def __init__(self, db: Session, ai_client: AIClient, cost_calculator: CostCalculator):
        self.db = db
        self.ai_client = ai_client
        self.cost_calculator = cost_calculator

    def _query_music(self, user: User, music_ids: Sequence[str | UUID] | None = None) -> List[UserMusic]:
        normalized_ids = None
        if music_ids:
            normalized_ids = [mid if isinstance(mid, UUID) else UUID(str(mid)) for mid in music_ids]
        query = (
            self.db.query(UserMusic)
            .filter(UserMusic.user_id == user.id)
            .options(joinedload(UserMusic.transcription))
            .order_by(UserMusic.created_at.desc())
        )
        if normalized_ids:
            query = query.filter(UserMusic.id.in_(normalized_ids))
        musics = query.all()
        if music_ids and len(musics) != len(set(music_ids)):
            raise ValueError("Alguma das músicas solicitadas não pertence ao usuário.")
        return musics

    def _ensure_transcription(self, music: UserMusic) -> MusicTranscription:
        if not music.transcription:
            raise ValueError(f"A música '{music.title}' ainda não possui transcrição.")
        return music.transcription

    def _estimate_tokens(self, video_summary: str, music_contexts: Sequence[MusicContext]) -> int:
        base = len(video_summary.split())
        music_tokens = sum(len(ctx.transcript_excerpt.split()) for ctx in music_contexts)
        total_words = base + music_tokens
        return max(500, math.ceil(total_words * 1.2))

    def generate_suggestions(
        self,
        user: User,
        video_url: str,
        duration_seconds: float,
        notes: str | None,
        music_ids: Sequence[str] | None,
        wallet: WalletManager,
    ) -> List[VideoSuggestionResult]:
        musics = self._query_music(user, music_ids)
        if not musics:
            raise ValueError("Cadastre e transcreva pelo menos uma música antes de pedir sugestões.")
        contexts: List[MusicContext] = []
        for music in musics:
            transcription = self._ensure_transcription(music)
            excerpt = (transcription.transcript_text or "")[:500] or "Letra não disponível."
            contexts.append(
                MusicContext(
                    id=str(music.id),
                    title=music.title,
                    bpm=music.bpm,
                    transcript_excerpt=excerpt,
                )
            )

        video_payload = describe_video_payload(video_url, duration_seconds, notes)
        analysis_cost = self.cost_calculator.estimate_video_analysis(duration_seconds)
        wallet.spend(user, analysis_cost.total_cost_brl, f"[IA] {analysis_cost.operation} {video_url}")

        reasoning_tokens = self._estimate_tokens(video_payload["summary"], contexts)
        reasoning_cost = self.cost_calculator.estimate_reasoning(reasoning_tokens, "video_suggestions")
        wallet.spend(user, reasoning_cost.total_cost_brl, "[IA] video_suggestions")

        ai_payload = {
            "video": video_payload,
            "music": [
                {
                    "id": ctx.id,
                    "title": ctx.title,
                    "bpm": ctx.bpm,
                    "transcript_excerpt": ctx.transcript_excerpt,
                }
                for ctx in contexts
            ],
        }
        return self.ai_client.generate_video_suggestions(ai_payload)

    def generate_variations(
        self,
        user: User,
        video_url: str,
        duration_seconds: float,
        notes: str | None,
        music_id: str,
        wallet: WalletManager,
    ) -> List[VideoVariationResult]:
        music = self._query_music(user, [music_id])[0]
        transcription = self._ensure_transcription(music)

        video_payload = describe_video_payload(video_url, duration_seconds, notes)
        tokens = self._estimate_tokens(video_payload["summary"], [
            MusicContext(
                id=str(music.id),
                title=music.title,
                bpm=music.bpm,
                transcript_excerpt=(transcription.transcript_text or "")[:800] or "Letra não disponível.",
            )
        ])
        cost = self.cost_calculator.estimate_reasoning(tokens, "video_variations")
        wallet.spend(user, cost.total_cost_brl, "[IA] video_variations")

        ai_payload = {
            "video": video_payload,
            "music_id": str(music.id),
            "music": {
                "title": music.title,
                "bpm": music.bpm,
                "transcript_excerpt": (transcription.transcript_text or "")[:800],
            },
        }
        return self.ai_client.generate_variations(ai_payload)
