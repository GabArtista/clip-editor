# 🎬 Comandos para Processar Vídeo

## 📋 Informações do Vídeo

- **URL:** https://www.instagram.com/reel/DN3xbyf2Fro/?igsh=MWVhZ3dwMmpqYXdvNQ==
- **Impacto Vídeo:** 1.0
- **Impacto Música:** 51.0

---

## 🔐 Passo 1: Login

```bash
# Login como usuário (substitua USERNAME e PASSWORD)
curl -X POST http://127.0.0.1:8060/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "caxa12",
    "password": "0102G@briel"
  }'
```

**Salve o token retornado!** Exemplo:
```bash
export TOKEN="seu_token_aqui"
```

---

## 🎵 Passo 2: Listar Músicas (Obter ID da Música)

```bash
curl -X GET http://127.0.0.1:8060/api/v1/musics \
  -H "Authorization: Bearer $TOKEN"
```

**Anote o ID da música!** Exemplo:
```bash
export MUSIC_ID=1
```

---

## 🎬 Passo 3: Processar Vídeo

```bash
curl -X POST http://127.0.0.1:8060/api/v1/videos/process \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/reel/DN3xbyf2Fro/?igsh=MWVhZ3dwMmpqYXdvNQ==",
    "music_id": 1,
    "impact_music": 51.0,
    "impact_video": 1.0,
    "return_format": "url"
  }'
```

**Anote o video_edit_id retornado!** Exemplo:
```bash
export VIDEO_EDIT_ID=123
```

---

## 👀 Passo 4: Ver Vídeo Editado (Preview)

```bash
curl -X GET http://127.0.0.1:8060/api/v1/video-edits/$VIDEO_EDIT_ID \
  -H "Authorization: Bearer $TOKEN"
```

**Copie o preview_url** para visualizar no navegador!

---

## ✅ Passo 5: Aprovar Vídeo (Dentro de 5 minutos)

```bash
curl -X POST http://127.0.0.1:8060/api/v1/video-edits/approve \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_edit_id": 123,
    "description": "Vídeo editado com Mix Guia V1 🚀"
  }'
```

---

## 📋 Script Completo (Copie e Cole)

```bash
#!/bin/bash

# Configurações
API_URL="http://127.0.0.1:8060"
USERNAME="caxa12"
PASSWORD="0102G@briel"
VIDEO_URL="https://www.instagram.com/reel/DN3xbyf2Fro/?igsh=MWVhZ3dwMmpqYXdvNQ=="
IMPACT_VIDEO=1.0
IMPACT_MUSIC=51.0

echo "🔐 1. Fazendo login..."
LOGIN_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\": \"$USERNAME\", \"password\": \"$PASSWORD\"}")

TOKEN=$(echo $LOGIN_RESPONSE | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo "❌ Erro no login!"
  echo $LOGIN_RESPONSE
  exit 1
fi

echo "✅ Login realizado! Token: ${TOKEN:0:50}..."
echo ""

echo "🎵 2. Listando músicas..."
MUSICS_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/musics" \
  -H "Authorization: Bearer $TOKEN")

echo $MUSICS_RESPONSE | python3 -m json.tool
echo ""

# Extrai o primeiro ID de música (ajuste se necessário)
MUSIC_ID=$(echo $MUSICS_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '1')")

echo "📝 Usando música ID: $MUSIC_ID"
echo ""

echo "🎬 3. Processando vídeo..."
echo "   URL: $VIDEO_URL"
echo "   Impacto Vídeo: $IMPACT_VIDEO"
echo "   Impacto Música: $IMPACT_MUSIC"
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

echo $PROCESS_RESPONSE | python3 -m json.tool
echo ""

# Extrai video_edit_id
VIDEO_EDIT_ID=$(echo $PROCESS_RESPONSE | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('video_edit_id', ''))")

if [ -z "$VIDEO_EDIT_ID" ]; then
  echo "❌ Erro ao processar vídeo!"
  exit 1
fi

echo "✅ Vídeo processado! Video Edit ID: $VIDEO_EDIT_ID"
echo ""

echo "👀 4. Informações do vídeo editado:"
curl -s -X GET "$API_URL/api/v1/video-edits/$VIDEO_EDIT_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "📋 5. Para aprovar o vídeo, execute:"
echo "curl -X POST $API_URL/api/v1/video-edits/approve \\"
echo "  -H \"Authorization: Bearer $TOKEN\" \\"
echo "  -H \"Content-Type: application/json\" \\"
echo "  -d '{\"video_edit_id\": $VIDEO_EDIT_ID, \"description\": \"Sua descrição aqui\"}'"
echo ""
echo "⏰ Lembre-se: Você tem 5 minutos para aprovar!"
```

---

## 🚀 Executar Script

```bash
# Salve o script acima em um arquivo
nano processar_video.sh

# Dê permissão de execução
chmod +x processar_video.sh

# Execute
./processar_video.sh
```

---

## 📝 Comandos Individuais (Se Preferir)

### 1. Login
```bash
curl -X POST http://127.0.0.1:8060/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "caxa12", "password": "0102G@briel"}'
```

### 2. Listar Músicas
```bash
curl -X GET http://127.0.0.1:8060/api/v1/musics \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 3. Processar Vídeo
```bash
curl -X POST http://127.0.0.1:8060/api/v1/videos/process \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/reel/DN3xbyf2Fro/?igsh=MWVhZ3dwMmpqYXdvNQ==",
    "music_id": 1,
    "impact_music": 51.0,
    "impact_video": 1.0,
    "return_format": "url"
  }'
```

### 4. Ver Vídeo Editado
```bash
curl -X GET http://127.0.0.1:8060/api/v1/video-edits/VIDEO_EDIT_ID \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

### 5. Aprovar Vídeo
```bash
curl -X POST http://127.0.0.1:8060/api/v1/video-edits/approve \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "video_edit_id": VIDEO_EDIT_ID,
    "description": "Vídeo editado com Mix Guia V1 🚀"
  }'
```

---

## ⚠️ Importante

- ⏰ **Aprove o vídeo dentro de 5 minutos** após o processamento
- 🎵 **Substitua `music_id`** pelo ID real da sua música
- 🔑 **Use o token** retornado no login em todas as requisições
- 📹 **O processamento pode levar alguns minutos**


