from __future__ import annotations

from typing import Dict, Optional

from .registry import MetricsRegistry

REGISTRY = MetricsRegistry()


def get_registry() -> MetricsRegistry:
    return REGISTRY


def reset_registry() -> None:
    global REGISTRY
    REGISTRY = MetricsRegistry()


def increment_counter(name: str, *, amount: float = 1.0, labels: Optional[Dict[str, str]] = None, help_text: str = "") -> None:
    counter = REGISTRY.counter(name, help_text or name)
    counter.inc(amount, labels=labels)


def observe_histogram(
    name: str,
    value: float,
    *,
    labels: Optional[Dict[str, str]] = None,
    help_text: str = "",
    buckets: Optional[list[float]] = None,
) -> None:
    histogram = REGISTRY.histogram(name, help_text or name, buckets)
    histogram.observe(value, labels=labels)


def set_gauge(name: str, value: float, *, labels: Optional[Dict[str, str]] = None, help_text: str = "") -> None:
    gauge = REGISTRY.gauge(name, help_text or name)
    gauge.set(value, labels=labels)


def record_token_usage(user_id: str, tokens: float, music_asset_id: Optional[str] = None) -> None:
    labels = {"user_id": user_id}
    if music_asset_id:
        labels["music_asset_id"] = music_asset_id
    increment_counter(
        "ai_token_usage_total",
        amount=tokens,
        labels=labels,
        help_text="Estimated token usage per user/music",
    )


def estimate_tokens_from_text(message: str) -> float:
    words = message.split()
    return max(1.0, len(words) * 1.3)
