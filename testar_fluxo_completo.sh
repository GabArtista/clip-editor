#!/bin/bash

# Script completo para testar: Configurar Webhook -> Processar -> Aprovar -> Publicar
# Testa o formato da webhook: {description, videoLink, date}

API_URL="http://127.0.0.1:8060"
USERNAME="caxa12"
PASSWORD="0102G@briel"
VIDEO_URL="https://www.instagram.com/reels/DN5qu5jgPMb/"
IMPACT_VIDEO=1.0
IMPACT_MUSIC=11.0
MUSIC_ID=1
DESCRIPTION="Music: Fala - CAXA12 #fut #rap #interclasse"
WEBHOOK_URL="https://n8n.dozecrew.com/webhook/98bce4e7-b9b1-4f4f-8c39-3db5955d0b76"

echo "=========================================="
echo "  TESTE COMPLETO: FLUXO DE PUBLICAÇÃO"
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

echo "🔗 2. Configurando webhook URL..."
UPDATE_RESPONSE=$(curl -s -X PUT "$API_URL/api/v1/users/me" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"webhook_url\": \"$WEBHOOK_URL\"}")

echo "$UPDATE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$UPDATE_RESPONSE"
echo ""

echo "🎬 3. Processando vídeo (return_format: url para aprovação)..."
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
  echo "   Verifique se o servidor está rodando e se a URL do vídeo está correta."
  exit 1
fi

echo "✅ Vídeo processado! Video Edit ID: $VIDEO_EDIT_ID"
echo ""

# Extrai preview_url e s3_url
PREVIEW_URL=$(echo $PROCESS_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('preview_url', ''))" 2>/dev/null)
S3_URL=$(echo $PROCESS_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('s3_url', ''))" 2>/dev/null)

if [ ! -z "$PREVIEW_URL" ]; then
  echo "👀 Preview URL (válida por 5 minutos):"
  echo "   $PREVIEW_URL"
  echo ""
fi

echo "⏰ Aguardando 2 segundos antes de aprovar..."
sleep 2
echo ""

echo "✅ 4. Aprovando vídeo e agendando na fila..."
echo "   Descrição: $DESCRIPTION"
echo ""

APPROVE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/video-edits/approve" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"video_edit_id\": $VIDEO_EDIT_ID,
    \"description\": \"$DESCRIPTION\"
  }")

echo "$APPROVE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$APPROVE_RESPONSE"
echo ""

# Extrai publication_id e scheduled_date
PUBLICATION_ID=$(echo $APPROVE_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('publication_id', ''))" 2>/dev/null)
SCHEDULED_DATE=$(echo $APPROVE_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('scheduled_date', ''))" 2>/dev/null)
FINAL_S3_URL=$(echo $APPROVE_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('s3_url', ''))" 2>/dev/null)

if [ -z "$FINAL_S3_URL" ] && [ ! -z "$S3_URL" ]; then
  FINAL_S3_URL="$S3_URL"
fi

if [ ! -z "$PUBLICATION_ID" ]; then
  echo "✅ Vídeo aprovado e agendado!"
  echo "   Publication ID: $PUBLICATION_ID"
  echo "   Data agendada: $SCHEDULED_DATE"
  echo "   S3 URL: $FINAL_S3_URL"
  echo ""
  
  echo "📋 5. Verificando fila de publicações..."
  QUEUE_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/publications/upcoming" \
    -H "Authorization: Bearer $TOKEN")
  
  echo "$QUEUE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$QUEUE_RESPONSE"
  echo ""
  
  echo "=========================================="
  echo "  FORMATO DA WEBHOOK (N8N)"
  echo "=========================================="
  echo ""
  echo "Quando a publicação for processada, a webhook receberá:"
  echo ""
  echo "{"
  echo "  \"description\": \"$DESCRIPTION\","
  echo "  \"videoLink\": \"$FINAL_S3_URL\","
  echo "  \"date\": \"$SCHEDULED_DATE\""
  echo "}"
  echo ""
  echo "📝 Detalhes:"
  echo "   - description: Descrição do post"
  echo "   - videoLink: Link público do S3 (vídeo editado)"
  echo "   - date: Data/hora agendada no formato ISO UTC (ex: 2025-12-09T00:19:00Z)"
  echo ""
  echo "⏰ A webhook será chamada automaticamente quando chegar"
  echo "   a data agendada: $SCHEDULED_DATE"
  echo ""
  echo "💡 Para testar:"
  echo "   1. Verifique os logs do servidor (publication worker)"
  echo "   2. Verifique a webhook do N8N em: $WEBHOOK_URL"
  echo "   3. Ou aguarde a data agendada"
  echo ""
else
  echo "❌ Erro ao aprovar vídeo!"
  echo "$APPROVE_RESPONSE"
  exit 1
fi

echo "=========================================="
echo "  TESTE CONCLUÍDO"
echo "=========================================="


