#!/bin/bash

# Script para processar vídeo do Instagram
# URL: https://www.instagram.com/reel/DN3xbyf2Fro/?igsh=MWVhZ3dwMmpqYXdvNQ==
# Impacto Vídeo: 1.0
# Impacto Música: 51.0

API_URL="http://127.0.0.1:8060"
USERNAME="caxa12"
PASSWORD="0102G@briel"
VIDEO_URL="https://www.instagram.com/reel/DN3xbyf2Fro/?igsh=MWVhZ3dwMmpqYXdvNQ=="
IMPACT_VIDEO=1.0
IMPACT_MUSIC=51.0

echo "=========================================="
echo "  PROCESSAR VÍDEO DO INSTAGRAM"
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

echo "🎵 2. Listando músicas disponíveis..."
MUSICS_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/musics" \
  -H "Authorization: Bearer $TOKEN")

echo "$MUSICS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$MUSICS_RESPONSE"
echo ""

# Extrai o primeiro ID de música
MUSIC_ID=$(echo $MUSICS_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if isinstance(data, list) and len(data) > 0 else '1')" 2>/dev/null || echo "1")

echo "📝 Usando música ID: $MUSIC_ID"
echo ""

echo "🎬 3. Processando vídeo..."
echo "   URL: $VIDEO_URL"
echo "   Música ID: $MUSIC_ID"
echo "   Impacto Vídeo: $IMPACT_VIDEO"
echo "   Impacto Música: $IMPACT_MUSIC"
echo "   (Isso pode levar alguns minutos...)"
echo ""

PROCESS_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/videos/process" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"url\": \"$VIDEO_URL\",
    \"music_id\": $MUSIC_ID,
    \"impact_music\": $IMPACT_MUSIC,
    \"impact_video\": $IMPACT_VIDEO,
    \"return_format\": \"url\"
  }")

echo "$PROCESS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$PROCESS_RESPONSE"
echo ""

# Extrai video_edit_id
VIDEO_EDIT_ID=$(echo $PROCESS_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('video_edit_id', ''))" 2>/dev/null)

if [ -z "$VIDEO_EDIT_ID" ]; then
  echo "❌ Erro ao processar vídeo!"
  echo "   Verifique se o servidor está rodando e se a música existe."
  exit 1
fi

echo "✅ Vídeo processado com sucesso!"
echo "   Video Edit ID: $VIDEO_EDIT_ID"
echo ""

echo "👀 4. Informações do vídeo editado:"
VIDEO_INFO=$(curl -s -X GET "$API_URL/api/v1/video-edits/$VIDEO_EDIT_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "$VIDEO_INFO" | python3 -m json.tool 2>/dev/null || echo "$VIDEO_INFO"
echo ""

# Extrai preview_url
PREVIEW_URL=$(echo $VIDEO_INFO | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('preview_url', ''))" 2>/dev/null)

if [ ! -z "$PREVIEW_URL" ]; then
  echo "🔗 Preview URL (válida por 5 minutos):"
  echo "   $PREVIEW_URL"
  echo ""
fi

echo "=========================================="
echo "  PRÓXIMOS PASSOS"
echo "=========================================="
echo ""
echo "📋 Para aprovar o vídeo e agendar na fila, execute:"
echo ""
echo "curl -X POST $API_URL/api/v1/video-edits/approve \\"
echo "  -H \"Authorization: Bearer $TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"video_edit_id\": $VIDEO_EDIT_ID, \"description\": \"Vídeo editado com Mix Guia V1 🚀\"}'"
echo ""
echo "⏰ IMPORTANTE: Você tem 5 minutos para aprovar o vídeo!"
echo ""


