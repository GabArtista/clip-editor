"""
Motor inteligente de sugestão de clipes alinhando análise de áudio e vídeo.
"""

from __future__ import annotations

import logging
import math
from typing import List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class ClipSuggester:
    """Sugere clipes otimizados alinhando beats de áudio com picos de movimento do vídeo."""

    def suggest_clips(
        self,
        audio_beats: List[float],
        audio_bpm: float,
        video_motion_peaks: List[float],
        video_scenes: List[dict],
        duration: float,
        min_clip_duration: float = 5.0,
        max_clip_duration: float = 15.0,
        max_clips: int = 3,
    ) -> List[dict]:
        """
        Gera sugestões de clipes alinhando áudio e vídeo.
        
        Args:
            audio_beats: Timestamps dos beats do áudio
            audio_bpm: BPM do áudio
            video_motion_peaks: Picos de movimento do vídeo
            video_scenes: Cenas detectadas no vídeo
            duration: Duração total do vídeo
            min_clip_duration: Duração mínima de um clipe
            max_clip_duration: Duração máxima de um clipe
            max_clips: Número máximo de clipes a gerar
            
        Returns:
            Lista de sugestões de clipes com:
                - video_start_seconds: Início no vídeo
                - video_end_seconds: Fim no vídeo
                - music_start_seconds: Início na música
                - music_end_seconds: Fim na música
                - score: Score de qualidade do alinhamento
                - rationale: Motivo da sugestão
        """
        if not audio_beats and not video_motion_peaks:
            # Fallback: segmentos fixos
            return self._generate_fallback_segments(duration, max_clips)
        
        logger.info(f"Gerando sugestões: {len(audio_beats)} beats, {len(video_motion_peaks)} picos de movimento")
        
        # Estratégia 1: Alinhar beats com picos de movimento
        beat_aligned = self._align_beats_with_motion(
            audio_beats, video_motion_peaks, duration, min_clip_duration, max_clip_duration
        )
        
        # Estratégia 2: Usar cenas para diversidade
        scene_based = self._create_scene_based_clips(
            video_scenes, audio_beats, duration, min_clip_duration, max_clip_duration
        )
        
        # Combina e rankeia
        all_suggestions = beat_aligned + scene_based
        
        # Remove duplicatas e segmentos muito próximos
        unique_suggestions = self._deduplicate_suggestions(all_suggestions, min_diff=min_clip_duration)
        
        # Rankeia por score
        sorted_suggestions = sorted(unique_suggestions, key=lambda x: x["score"], reverse=True)
        
        # Limita e ajusta durações
        final_suggestions = []
        for i, suggestion in enumerate(sorted_suggestions[:max_clips * 2], start=1):
            # Ajusta para garantir duração mínima
            adjusted = self._adjust_duration(suggestion, min_clip_duration, max_clip_duration, duration)
            if adjusted:
                final_suggestions.append(adjusted)
        
        logger.info(f"Geradas {len(final_suggestions)} sugestões de clipes")
        return final_suggestions[:max_clips]

    def _align_beats_with_motion(
        self,
        audio_beats: List[float],
        video_motion_peaks: List[float],
        duration: float,
        min_duration: float,
        max_duration: float,
    ) -> List[dict]:
        """Alinha beats do áudio com picos de movimento do vídeo."""
        suggestions = []
        
        if not audio_beats or not video_motion_peaks:
            return suggestions
        
        # Busca pontos de alinhamento (beats próximos a picos de movimento)
        alignment_points = []
        for beat in audio_beats:
            if beat > duration:
                break
            # Encontra pico de movimento mais próximo
            closest_peak = min(video_motion_peaks, key=lambda p: abs(p - beat))
            distance = abs(closest_peak - beat)
            
            if distance < 3.0:  # Alinhamento razoável (dentro de 3s)
                score = 100 - (distance * 10)  # Score baseado na proximidade
                alignment_points.append({
                    "beat": beat,
                    "peak": closest_peak,
                    "distance": distance,
                    "score": score,
                })
        
        logger.info(f"Encontrados {len(alignment_points)} pontos de alinhamento")
        
        # Gera sugestões a partir dos pontos de alinhamento
        for point in alignment_points[:5]:  # Top 5 alinhamentos
            start = max(0.0, point["beat"] - min_duration / 2)
            end = min(duration, start + max_duration)
            
            # Ajusta para garantir duração mínima
            if end - start < min_duration:
                end = min(duration, start + min_duration)
            
            suggestions.append({
                "video_start_seconds": round(start, 2),
                "video_end_seconds": round(end, 2),
                "music_start_seconds": round(start, 2),
                "music_end_seconds": round(end, 2),
                "score": point["score"],
                "rationale": f"Alinhamento beat-movimento (distância: {point['distance']:.1f}s)",
            })
        
        return suggestions

    def _create_scene_based_clips(
        self,
        video_scenes: List[dict],
        audio_beats: List[float],
        duration: float,
        min_duration: float,
        max_duration: float,
    ) -> List[dict]:
        """Cria clipes baseados nas cenas detectadas."""
        suggestions = []
        
        if not video_scenes:
            return suggestions
        
        # Seleciona cenas interessantes (mais longas ou no início)
        interesting_scenes = sorted(video_scenes, key=lambda s: s["duration"], reverse=True)[:3]
        
        for i, scene in enumerate(interesting_scenes, start=1):
            start = scene["start"]
            end = scene["end"]
            
            # Se a cena for muito curta, expande
            if end - start < min_duration:
                expand = (min_duration - (end - start)) / 2
                start = max(0.0, start - expand)
                end = min(duration, end + expand)
            
            # Limita duração máxima
            if end - start > max_duration:
                end = start + max_duration
            
            # Acha beat mais próximo do início
            if audio_beats:
                closest_beat = min(audio_beats, key=lambda b: abs(b - start))
                audio_start = closest_beat
            else:
                audio_start = start
            
            suggestions.append({
                "video_start_seconds": round(start, 2),
                "video_end_seconds": round(end, 2),
                "music_start_seconds": round(audio_start, 2),
                "music_end_seconds": round(audio_start + (end - start), 2),
                "score": 70.0 + (scene["duration"] * 2),  # Cenas mais longas têm score maior
                "rationale": f"Cena {i} (duração: {scene['duration']:.1f}s)",
            })
        
        return suggestions

    def _generate_fallback_segments(self, duration: float, max_clips: int) -> List[dict]:
        """Gera segmentos fixos como fallback."""
        suggestions = []
        segment_duration = min(12.0, duration / max_clips)
        
        for i in range(max_clips):
            start = i * segment_duration
            end = min(duration, start + segment_duration)
            
            if end - start < 5.0:  # Mínimo de 5s
                break
            
            suggestions.append({
                "video_start_seconds": round(start, 2),
                "video_end_seconds": round(end, 2),
                "music_start_seconds": round(start, 2),
                "music_end_seconds": round(end, 2),
                "score": 50.0,
                "rationale": "Segmento fixo (análise indisponível)",
            })
        
        return suggestions

    def _deduplicate_suggestions(self, suggestions: List[dict], min_diff: float) -> List[dict]:
        """Remove sugestões duplicadas ou muito próximas."""
        if not suggestions:
            return []
        
        # Ordena por início
        sorted_sugs = sorted(suggestions, key=lambda x: x["video_start_seconds"])
        
        unique = [sorted_sugs[0]]
        for sug in sorted_sugs[1:]:
            # Verifica se está longe o suficiente da última
            last_end = unique[-1]["video_end_seconds"]
            if sug["video_start_seconds"] - last_end >= min_diff:
                unique.append(sug)
            # Se está sobreposto mas tem score melhor, substitui
            elif sug["score"] > unique[-1]["score"]:
                unique[-1] = sug
        
        return unique

    def _adjust_duration(
        self,
        suggestion: dict,
        min_duration: float,
        max_duration: float,
        total_duration: float,
    ) -> Optional[dict]:
        """Ajusta duração de uma sugestão para estar dentro dos limites."""
        start = suggestion["video_start_seconds"]
        end = suggestion["video_end_seconds"]
        
        duration = end - start
        
        # Se muito curta, estende
        if duration < min_duration:
            extend = (min_duration - duration) / 2
            start = max(0.0, start - extend)
            end = min(total_duration, end + extend)
            
            # Se ainda não chegou ao mínimo, ajusta música também
            if end - start < min_duration:
                end = min(total_duration, start + min_duration)
        
        # Se muito longa, corta
        if end - start > max_duration:
            end = start + max_duration
        
        # Recalcula música
        audio_start = suggestion["music_start_seconds"]
        audio_end = audio_start + (end - start)
        
        suggestion["video_start_seconds"] = round(start, 2)
        suggestion["video_end_seconds"] = round(end, 2)
        suggestion["music_start_seconds"] = round(audio_start, 2)
        suggestion["music_end_seconds"] = round(audio_end, 2)
        
        return suggestion


# Factory function
def get_clip_suggester() -> ClipSuggester:
    """Factory function para criar ClipSuggester."""
    return ClipSuggester()


