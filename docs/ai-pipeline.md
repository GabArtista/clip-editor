# Pipeline de IA para Análise de Áudio e Vídeo

Este documento descreve o pipeline de Inteligência Artificial implementado para análise real de áudio, vídeo e geração inteligente de sugestões de clipes.

## Visão Geral

O sistema evoluiu de placeholders para análise real usando bibliotecas de IA/ML:

- **Áudio**: Librosa + Whisper para beats, BPM, tonalidade e transcrição
- **Vídeo**: OpenCV + PySceneDetect + CLIP para cenas, movimento e keywords
- **Sugestões**: ClipSuggester inteligente que alinha beats com picos de movimento

## Arquitetura

```
app/services/
├── audio_analyzer.py    # Análise de áudio com librosa + Whisper
├── video_analyzer.py    # Análise de vídeo com OpenCV + CLIP
├── clip_suggester.py    # Motor de sugestões inteligentes
├── music_service.py     # Integra audio_analyzer
└── video_pipeline.py    # Integra video_analyzer e clip_suggester
```

## Análise de Áudio

### AudioAnalyzer (`app/services/audio_analyzer.py`)

**Tecnologias:**
- `librosa`: Beat tracking, BPM detection, chroma features
- `whisper` (OpenAI): Transcrição automática de áudio

**Features extraídas:**
- BPM (Beats Per Minute)
- Lista de timestamps dos beats
- Tonalidade musical (C, C#, D, etc.)
- Texto transcrito com idioma
- Perfil de energia (RMS)

**Uso:**
```python
from app.services.audio_analyzer import get_audio_analyzer

analyzer = get_audio_analyzer(model="base")  # tiny, base, small, medium, large
result = analyzer.analyze("/path/to/audio.mp3")

# Resultado contém:
# - bpm: 120
# - beats: [0.0, 0.5, 1.0, ...]
# - key: "C"
# - transcription: "texto transcrito..."
# - language: "pt"
# - energy: {...}
```

**Configuração:**
```bash
# Escolhe modelo Whisper (maior = mais preciso, mais lento)
WHISPER_MODEL=base  # Opções: tiny, base, small, medium, large
```

## Análise de Vídeo

### VideoAnalyzer (`app/services/video_analyzer.py`)

**Tecnologias:**
- `opencv`: Extração de frames e análise de movimento
- `scenedetect`: Detecção automática de cenas
- `CLIP` (Hugging Face): Extração de keywords e conceitos

**Features extraídas:**
- Cenas detectadas (start, end, duration)
- Picos de movimento (timestamps)
- Keywords relevantes
- Perfil de energia visual

**Uso:**
```python
from app.services.video_analyzer import get_video_analyzer

analyzer = get_video_analyzer()
result = analyzer.analyze("/path/to/video.mp4")

# Resultado contém:
# - scenes: [{order: 1, start: 0.0, end: 5.2, duration: 5.2}, ...]
# - motion_peaks: [0.5, 10.3, 20.1, ...]
# - keywords: ["energia", "movimento", "impacto"]
# - energy: {profile: [...], sample_rate: 2.0}
```

## Geração Inteligente de Sugestões

### ClipSuggester (`app/services/clip_suggester.py`)

Motor que alinha análise de áudio e vídeo para gerar sugestões otimizadas.

**Estratégias:**
1. **Alinhamento Beat-Movimento**: Alinha beats do áudio com picos de movimento do vídeo
2. **Baseado em Cenas**: Usa cenas detectadas para garantir diversidade
3. **Fallback**: Segmentos fixos quando análise indisponível

**Exemplo:**
```python
suggestions = suggester.suggest_clips(
    audio_beats=[0.0, 0.5, 1.0, 1.5],
    audio_bpm=120,
    video_motion_peaks=[0.6, 10.5, 20.3],
    video_scenes=[{start: 0, end: 10}],
    duration=30.0
)

# Retorna:
# - video_start_seconds, video_end_seconds
# - music_start_seconds, music_end_seconds
# - score (qualidade do alinhamento)
# - rationale (motivo da sugestão)
```

## Integração com Services

### MusicService

Agora usa `AudioAnalyzer` para análise real:

```python
# Antes: placeholders fixos
analysis = self._prefill_analysis(genre)

# Agora: análise real com IA
analysis = self._prefill_analysis(genre, audio_path="/path/to/audio.mp3")
```

Se `audio_path` for fornecido e existir, realiza análise completa. Se não, usa placeholders (backward compatible).

### VideoPipeline

Agora usa `VideoAnalyzer` e `ClipSuggester`:

```python
# Análise real de vídeo
video_analysis_data = self.video_analyzer.analyze(ingest.storage_path)

# Gera sugestões inteligentes
suggestions = self.clip_suggester.suggest_clips(...)
```

## Dependências

Adicionadas ao `requirements.txt`:

```txt
# AI/ML Dependencies
librosa>=0.10.0          # Análise de áudio
openai-whisper>=20231117 # Transcrição
opencv-python>=4.8.0     # Vídeo
scenedetect>=0.6.2       # Detecção de cenas
torch>=2.0.0             # ML framework
transformers>=4.30.0     # CLIP
numpy>=1.24.0            # Computação numérica
soundfile>=0.12.0        # Leitura de áudio
```

## Instalação

```bash
# Instalar dependências (pode demorar pela primeira vez)
pip install -r requirements.txt

# Download dos modelos Whisper (automático na primeira execução)
# Modelos: tiny (39MB), base (74MB), small (244MB), medium (769MB), large (1550MB)
# Recomendado para produção: base ou small
```

## Performance e Custos

### Modelos Whisper

| Modelo | Tamanho | Velocidade (CPU) | Velocidade (GPU) | Precisão |
|--------|---------|------------------|------------------|----------|
| tiny   | 39MB    | ~4x real-time    | ~150x real-time  | Baixa    |
| base   | 74MB    | ~2x real-time    | ~100x real-time  | Média    |
| small  | 244MB   | ~0.8x real-time  | ~50x real-time   | Alta     |
| medium | 769MB   | ~0.4x real-time  | ~20x real-time   | Muito Alta |
| large  | 1550MB  | ~0.2x real-time  | ~10x real-time   | Máxima   |

**Recomendação:** `base` para dev/test, `small` para produção.

### Métricas Implementadas

O sistema rastreia:
- `audio_analysis_total`: Total de análises de áudio
- `audio_analysis_duration_seconds`: Tempo de análise
- `video_analysis_total`: Total de análises de vídeo
- `video_analysis_duration_seconds`: Tempo de análise
- `audio_analysis_errors`: Erros na análise de áudio
- `video_analysis_errors`: Erros na análise de vídeo

Acesse via `GET /metrics`.

## GPU (Opcional)

Para acelerar processamento:

```bash
# Verifica GPU disponível
python -c "import torch; print(torch.cuda.is_available())"

# Configura variáveis de ambiente
export CUDA_VISIBLE_DEVICES=0  # GPU 0
```

Modelos Whisper e CLIP automaticamente usam GPU se disponível.

## Fallbacks e Compatibilidade

O sistema é robusto:
- Se IA falhar, usa placeholders
- Compatível com versão anterior
- Funciona sem GPU (apenas mais lento)

## Troubleshooting

### Erro: "No module named 'librosa'"
```bash
pip install librosa soundfile
```

### Erro: Whisper modelo não encontrado
```bash
# Baixa manualmente
python -m whisper download base
```

### Performance lenta
- Use GPU se disponível
- Reduza modelo Whisper (tiny ou base)
- Aumente sampling rate do vídeo (em video_analyzer)

### Memory Error com CLIP
- Reduza número de frames amostrados
- Use CPU apenas (sem GPU)

## Próximos Passos

- [ ] Cache de análises para evitar reprocessamento
- [ ] Worker assíncrono dedicado para análise
- [ ] Suporte a mais formatos de áudio
- [ ] Análise de sentimento em cenas
- [ ] Detecção automática de gênero musical
- [ ] Thumbnails automáticos

