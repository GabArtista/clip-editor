from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
import math

from app.settings import get_ai_settings, AISettings


@dataclass
class CostEstimate:
    operation: str
    provider_cost_brl: Decimal
    platform_fee_brl: Decimal
    total_cost_brl: Decimal
    metadata: dict[str, str] | None = None


class CostCalculator:
    def __init__(self, settings: AISettings | None = None):
        self.settings = settings or get_ai_settings()

    def _finalize(self, operation: str, provider_cost: Decimal, metadata: dict[str, str] | None = None) -> CostEstimate:
        provider = provider_cost.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        platform_fee = self.settings.platform_fee_brl.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        total = (provider + platform_fee).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return CostEstimate(operation=operation, provider_cost_brl=provider, platform_fee_brl=platform_fee, total_cost_brl=total, metadata=metadata)

    def estimate_music_transcription(self, duration_seconds: float) -> CostEstimate:
        minutes = max(1, math.ceil(float(duration_seconds) / 60))
        provider_cost = Decimal(minutes) * self.settings.audio_cost_per_minute_brl
        meta = {"minutes": str(minutes)}
        return self._finalize("music_transcription", provider_cost, meta)

    def estimate_video_analysis(self, duration_seconds: float) -> CostEstimate:
        minutes = max(1, math.ceil(float(duration_seconds) / 60))
        provider_cost = Decimal(minutes) * self.settings.video_cost_per_minute_brl
        meta = {"minutes": str(minutes)}
        return self._finalize("video_analysis", provider_cost, meta)

    def estimate_reasoning(self, token_estimate: int, label: str) -> CostEstimate:
        chunks = max(1, math.ceil(token_estimate / 1000))
        provider_cost = Decimal(chunks) * self.settings.text_cost_per_1k_tokens_brl
        meta = {"chunks_1k_tokens": str(chunks)}
        return self._finalize(label, provider_cost, meta)
