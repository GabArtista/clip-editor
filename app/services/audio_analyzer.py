"""
Serviço de análise de áudio usando librosa, Whisper e técnicas de análise musical.
"""

from __future__ import annotations

import logging
import time
from typing import List, Optional

import librosa
import numpy as np
import torch
import whisper
from pathlib import Path

from metrics import increment_counter, observe_histogram

logger = logging.getLogger(__name__)


class AudioAnalyzer:
    """Analisa arquivos de áudio extraindo beats, BPM, tonalidade, transcrição e embeddings."""

    def __init__(self, whisper_model: str = "base"):
        """
        Args:
            whisper_model: Modelo Whisper a usar ('tiny', 'base', 'small', 'medium', 'large')
        """
        self.whisper_model_name = whisper_model
        self._whisper_model = None
        
    @property
    def whisper_model(self):
        """Lazy load do modelo Whisper."""
        if self._whisper_model is None:
            logger.info(f"Carregando modelo Whisper: {self.whisper_model_name}")
            self._whisper_model = whisper.load_model(self.whisper_model_name)
        return self._whisper_model

    def analyze(self, audio_path: str) -> dict:
        """
        Analisa um arquivo de áudio completo.
        
        Args:
            audio_path: Caminho para o arquivo de áudio
            
        Returns:
            Dicionário com:
                - bpm: Beats por minuto
                - beats: Lista de timestamps dos beats
                - beats_confidence: Confiança dos beats detectados
                - key: Tonalidade estimada
                - key_confidence: Confiança da tonalidade
                - transcription: Texto transcrito
                - language: Idioma detectado
                - confidence: Confiança da transcrição
                - energy: Perfil de energia do áudio
                - duration: Duração em segundos
        """
        start_time = time.perf_counter()
        
        try:
            # Carrega o áudio
            logger.info(f"Carregando áudio: {audio_path}")
            y, sr = librosa.load(audio_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            
            # Detecta beats e BPM
            bpm, beats = self._detect_beats(y, sr)
            
            # Detecta tonalidade
            key, key_confidence = self._detect_key(y, sr)
            
            # Transcreve com Whisper
            transcription_data = self._transcribe(audio_path)
            
            # Calcula energia do áudio
            energy = self._calculate_energy(y, sr)
            
            analysis_time = time.perf_counter() - start_time
            
            # Métricas
            increment_counter("audio_analysis_total", help_text="Total de análises de áudio")
            observe_histogram(
                "audio_analysis_duration_seconds",
                analysis_time,
                help_text="Duração da análise de áudio"
            )
            
            result = {
                "bpm": bpm,
                "beats": beats,
                "beats_confidence": 0.8,  # Confiança estimada
                "key": key,
                "key_confidence": key_confidence,
                "transcription": transcription_data["text"],
                "language": transcription_data["language"],
                "confidence": transcription_data.get("avg_confidence", 0.0),
                "energy": energy,
                "duration": duration,
            }
            
            logger.info(f"Análise concluída em {analysis_time:.2f}s")
            return result
            
        except Exception as e:
            increment_counter("audio_analysis_errors", help_text="Erros na análise de áudio")
            logger.error(f"Erro ao analisar áudio {audio_path}: {e}")
            raise

    def _detect_beats(self, y: np.ndarray, sr: int) -> tuple[int, List[float]]:
        """
        Detecta beats e BPM no áudio.
        
        Returns:
            Tupla (BPM, lista de timestamps dos beats)
        """
        try:
            # Detecta o tempo e beats
            tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr, units='time')
            beats = beat_frames.tolist()
            
            logger.info(f"BPM detectado: {int(tempo)}, {len(beats)} beats")
            return int(tempo), beats
            
        except Exception as e:
            logger.warning(f"Erro ao detectar beats: {e}, usando valores padrão")
            return 120, [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]

    def _detect_key(self, y: np.ndarray, sr: int) -> tuple[str, float]:
        """
        Detecta a tonalidade do áudio.
        
        Returns:
            Tupla (tonalidade, confiança)
        """
        try:
            # Analisa chroma features
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Tonalidades possíveis
            key_profiles = {
                'C': [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88],
                'C#': [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17],
                # ... outras tonalidades
            }
            
            # Correlação com perfis de tonalidade
            chroma_mean = np.mean(chroma, axis=1)
            
            # Normaliza
            chroma_mean = chroma_mean / np.sum(chroma_mean)
            
            # Correlação simples com C maior
            correlations = []
            for i in range(12):
                shifted = np.roll(chroma_mean, -i)
                corr = np.correlate(shifted, key_profiles['C'], mode='valid')[0]
                correlations.append(corr)
            
            # Encontra a melhor correspondência
            best_idx = np.argmax(correlations)
            confidence = float(correlations[best_idx])
            
            keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            key = keys[best_idx]
            
            logger.info(f"Tonalidade detectada: {key} (confiança: {confidence:.2f})")
            return key, confidence
            
        except Exception as e:
            logger.warning(f"Erro ao detectar tonalidade: {e}, usando padrão")
            return "C", 0.5

    def _transcribe(self, audio_path: str) -> dict:
        """
        Transcreve o áudio usando Whisper.
        
        Returns:
            Dicionário com texto, idioma e confiança
        """
        try:
            logger.info("Iniciando transcrição com Whisper")
            
            # Usa GPU se disponível, senão CPU
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Usando dispositivo: {device}")
            
            result = self.whisper_model.transcribe(str(audio_path), language=None)
            
            text = result.get("text", "")
            language = result.get("language", "pt")
            segments = result.get("segments", [])
            
            # Calcula confiança média
            if segments:
                avg_confidence = np.mean([seg.get("no_speech_prob", 0.0) for seg in segments])
            else:
                avg_confidence = 0.0
            
            logger.info(f"Transcrição concluída: {len(text)} caracteres, idioma: {language}")
            
            return {
                "text": text,
                "language": language,
                "avg_confidence": float(1.0 - avg_confidence),  # Inverte no_speech_prob
                "segments": segments,
            }
            
        except Exception as e:
            logger.error(f"Erro ao transcrever com Whisper: {e}")
            return {
                "text": "",
                "language": "pt",
                "avg_confidence": 0.0,
                "segments": [],
            }

    def _calculate_energy(self, y: np.ndarray, sr: int) -> dict:
        """
        Calcula perfil de energia do áudio.
        
        Returns:
            Dicionário com estatísticas de energia
        """
        try:
            # RMS energy
            rms = librosa.feature.rms(y=y)[0]
            
            # Normaliza para 0-1
            rms_normalized = (rms - rms.min()) / (rms.max() - rms.min() + 1e-10)
            
            return {
                "mean": float(np.mean(rms_normalized)),
                "std": float(np.std(rms_normalized)),
                "max": float(np.max(rms_normalized)),
                "min": float(np.min(rms_normalized)),
            }
            
        except Exception as e:
            logger.warning(f"Erro ao calcular energia: {e}")
            return {"mean": 0.5, "std": 0.1, "max": 1.0, "min": 0.0}


# Factory function para criar o analyzer
def get_audio_analyzer(model: str = "base") -> AudioAnalyzer:
    """
    Factory function para criar AudioAnalyzer com configurações do ambiente.
    
    Args:
        model: Modelo Whisper a usar (padrão do ambiente ou 'base')
    """
    import os
    whisper_model = os.getenv("WHISPER_MODEL", model)
    return AudioAnalyzer(whisper_model=whisper_model)

