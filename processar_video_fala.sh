#!/bin/bash

# Script para processar vídeo do Instagram com música "Mix Guia V1"
# URL: https://www.instagram.com/reels/DN5qu5jgPMb/
# Impacto Vídeo: 1.0
# Impacto Música: 11.0
# Return Format: file

API_URL="http://127.0.0.1:8060"
USERNAME="caxa12"
PASSWORD="0102G@briel"
VIDEO_URL="https://www.instagram.com/reels/DN5qu5jgPMb/"
IMPACT_VIDEO=1.0
IMPACT_MUSIC=11.0
MUSIC_ID=1  # Mix Guia V1
RETURN_FORMAT="file"

echo "=========================================="
echo "  PROCESSAR VÍDEO - MÚSICA 'MIX GUIA V1'"
echo "=========================================="
echo ""

echo "🔐 1. Fazendo login..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Erro no login!"
  echo $LOGIN_RESPONSE
  exit 1
fi

echo "✅ Login realizado!"
echo ""

echo "🎵 2. Verificando música (ID: $MUSIC_ID)..."
MUSIC_INFO=$(curl -s -X GET "$API_URL/api/v1/musics/$MUSIC_ID" \
  -H "Authorization: Bearer $TOKEN")

MUSIC_NAME=$(echo $MUSIC_INFO | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('name', ''))" 2>/dev/null)

if [ -z "$MUSIC_NAME" ]; then
  echo "❌ Música ID $MUSIC_ID não encontrada!"
  exit 1
fi

echo "✅ Música encontrada: $MUSIC_NAME"
echo ""

echo "🎬 3. Processando vídeo..."
echo "   URL: $VIDEO_URL"
echo "   Música: $MUSIC_NAME (ID: $MUSIC_ID)"
echo "   Impacto Vídeo: $IMPACT_VIDEO"
echo "   Impacto Música: $IMPACT_MUSIC"
echo "   Return Format: $RETURN_FORMAT"
echo "   (Isso pode levar alguns minutos...)"
echo ""

# Processa vídeo e salva como arquivo
OUTPUT_FILE="video_editado_$(date +%Y%m%d_%H%M%S).mp4"

echo "📥 Baixando vídeo processado..."
curl -X POST "$API_URL/api/v1/videos/process" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"$VIDEO_URL\",
    \"music_id\": $MUSIC_ID,
    \"impact_music\": $IMPACT_MUSIC,
    \"impact_video\": $IMPACT_VIDEO,
    \"return_format\": \"$RETURN_FORMAT\"
  }" --output "$OUTPUT_FILE" --progress-bar

if [ -f "$OUTPUT_FILE" ] && [ -s "$OUTPUT_FILE" ]; then
  FILE_SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
  echo ""
  echo "✅ Vídeo processado e salvo!"
  echo "   Arquivo: $OUTPUT_FILE"
  echo "   Tamanho: $FILE_SIZE"
  echo ""
  echo "📹 Para visualizar:"
  echo "   xdg-open $OUTPUT_FILE"
  echo "   ou"
  echo "   vlc $OUTPUT_FILE"
else
  echo ""
  echo "❌ Erro ao processar vídeo!"
  echo "   Verifique se o servidor está rodando e se a URL do vídeo está correta."
  exit 1
fi

echo ""
echo "=========================================="
echo "  PROCESSAMENTO CONCLUÍDO"
echo "=========================================="
