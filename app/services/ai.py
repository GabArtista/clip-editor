from __future__ import annotations

import json
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependência opcional
    OpenAI = None  # type: ignore

from app.settings import get_ai_settings


@dataclass
class TranscriptionResult:
    text: str
    language: str
    confidence: float | None
    generated_by: str
    raw_response: dict | None


@dataclass
class VideoSuggestionResult:
    suggestion_id: str
    music_id: str
    start_time_seconds: float
    end_time_seconds: float
    reasoning: str
    prompt: str


@dataclass
class VideoVariationResult:
    variation_id: str
    music_id: str
    description: str
    segments: list[dict[str, float | str]]


class AIClient:
    def __init__(self):
        self.settings = get_ai_settings()
        self._text_client = None
        if self.settings.api_key and OpenAI:
            self._text_client = OpenAI(api_key=self.settings.api_key)

    # -------------------- Music transcription --------------------
    def transcribe_music(self, audio_path: Path, language: str = "pt") -> TranscriptionResult:
        if self._text_client:
            try:
                with audio_path.open("rb") as source:
                    response = self._text_client.audio.transcriptions.create(
                        model=self.settings.audio_model,
                        file=source,
                        language=language,
                    )
                return TranscriptionResult(
                    text=response.text,
                    language=language,
                    confidence=getattr(response, "confidence", None),
                    generated_by=self.settings.audio_model,
                    raw_response=response.dict() if hasattr(response, "dict") else dict(response),
                )
            except Exception:
                pass  # fallback para modo determinístico

        # fallback determinístico
        sample = audio_path.stem.replace("_", " ").title()
        text = f"Transcrição aproximada da faixa '{sample}' em {language}."
        return TranscriptionResult(
            text=text,
            language=language,
            confidence=0.75,
            generated_by="offline-stub",
            raw_response={"text": text},
        )

    # -------------------- Video reasoning helpers --------------------
    def generate_video_suggestions(self, payload: dict[str, Any]) -> list[VideoSuggestionResult]:
        structured = self._run_reasoning(payload, mode="suggestions")
        return [
            VideoSuggestionResult(
                suggestion_id=item["id"],
                music_id=item["music_id"],
                start_time_seconds=float(item["start"]),
                end_time_seconds=float(item["end"]),
                reasoning=item["reasoning"],
                prompt=item["prompt"],
            )
            for item in structured
        ]

    def generate_variations(self, payload: dict[str, Any]) -> list[VideoVariationResult]:
        structured = self._run_reasoning(payload, mode="variations")
        return [
            VideoVariationResult(
                variation_id=item["id"],
                music_id=item["music_id"],
                description=item["description"],
                segments=item["segments"],
            )
            for item in structured
        ]

    def _run_reasoning(self, payload: dict[str, Any], mode: str) -> list[dict[str, Any]]:
        if self._text_client:
            try:
                prompt = json.dumps({"mode": mode, "input": payload}, ensure_ascii=False)
                response = self._text_client.responses.create(
                    model=self.settings.text_model,
                    input=[
                        {
                            "role": "system",
                            "content": (
                                "Você é uma IA especialista em viralização musical. "
                                "Responda SEMPRE em JSON válido com o campo 'items', contendo exatamente 3 objetos."
                            ),
                        },
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                )
                content = response.output[0].content[0].text  # type: ignore[attr-defined]
                parsed = json.loads(content)
                items = parsed.get("items")
                if isinstance(items, list) and len(items) >= 3:
                    return items[:3]
            except Exception:
                pass

        # fallback determinístico
        return self._fallback_items(payload, mode=mode)

    def _fallback_items(self, payload: dict[str, Any], mode: str) -> list[dict[str, Any]]:
        seed_source = json.dumps(payload, sort_keys=True)
        rng = random.Random(seed_source)
        items: list[dict[str, Any]] = []
        music_field = payload.get("music") or []
        if isinstance(music_field, dict):
            music_ids = [music_field.get("id", payload.get("music_id", "music"))]
        else:
            music_ids = [m.get("id", payload.get("music_id", "music")) for m in music_field] or [
                payload.get("music_id", "music")
            ]
        video_duration = float(payload.get("video", {}).get("duration_seconds", 120))
        for idx in range(3):
            music_id = music_ids[idx % len(music_ids)]
            start = round(rng.uniform(0, max(5.0, video_duration - 10)), 2)
            end = round(min(video_duration, start + rng.uniform(5, 15)), 2)
            if mode == "suggestions":
                items.append(
                    {
                        "id": f"suggestion-{idx+1}",
                        "music_id": music_id,
                        "start": start,
                        "end": end,
                        "reasoning": "Sugestão gerada em modo offline.",
                        "prompt": "Sincronizar clima animado com transição enérgica.",
                    }
                )
            else:
                segments = [
                    {
                        "label": "Intro",
                        "video_start": start,
                        "video_end": round(start + 4, 2),
                        "music_offset": rng.uniform(0, 30),
                    },
                    {
                        "label": "Drop",
                        "video_start": round(start + 4, 2),
                        "video_end": end,
                        "music_offset": rng.uniform(30, 90),
                    },
                ]
                items.append(
                    {
                        "id": f"variation-{idx+1}",
                        "music_id": payload.get("music_id", music_id),
                        "description": "Variação criada em modo offline.",
                        "segments": segments,
                    }
                )
        return items


def describe_video_payload(video_url: str, duration_seconds: float, notes: str | None = None) -> dict[str, Any]:
    base_description = (
        f"Vídeo {video_url} com duração aproximada de {duration_seconds:.0f} segundos."
    )
    if notes:
        base_description += f" Notas do artista: {notes.strip()}."
    return {"url": video_url, "duration_seconds": duration_seconds, "notes": notes or "", "summary": base_description}
