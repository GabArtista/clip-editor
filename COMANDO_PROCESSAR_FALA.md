# 🎬 Comando para Processar Vídeo com Música "Mix Guia V1"

## 📋 Parâmetros

- **URL:** https://www.instagram.com/reels/DN5qu5jgPMb/
- **Música:** Mix Guia V1 (ID: 1)
- **Impacto Vídeo:** 1.0
- **Impacto Música:** 11.0
- **Return Format:** file

---

## 🚀 Opção 1: Script Automático (Recomendado)

```bash
./processar_video_fala.sh
```

O script faz tudo automaticamente e salva o vídeo editado.

---

## 📝 Opção 2: Comando Manual

### 1. Login

```bash
curl -X POST http://127.0.0.1:8060/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "caxa12", "password": "0102G@briel"}'
```

**Copie o `access_token` retornado.**

---

### 2. Processar Vídeo (Return Format: file)

```bash
curl -X POST http://127.0.0.1:8060/api/v1/videos/process \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/reels/DN5qu5jgPMb/",
    "music_id": 1,
    "impact_music": 11.0,
    "impact_video": 1.0,
    "return_format": "file"
  }' --output video_editado.mp4
```

O vídeo será salvo como `video_editado.mp4` no diretório atual.

---

### 3. Processar Vídeo (Return Format: url) - Para Aprovação

Se quiser usar o fluxo de aprovação (5 minutos), use `return_format: "url"`:

```bash
curl -X POST http://127.0.0.1:8060/api/v1/videos/process \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/reels/DN5qu5jgPMb/",
    "music_id": 1,
    "impact_music": 11.0,
    "impact_video": 1.0,
    "return_format": "url"
  }'
```

Depois use o `video_edit_id` retornado para aprovar:

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

## 📋 Comando Completo em Uma Linha

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:8060/api/v1/auth/login -H "Content-Type: application/json" -d '{"username":"caxa12","password":"0102G@briel"}' | python3 -c "import sys,json;print(json.load(sys.stdin)['access_token'])") && curl -X POST http://127.0.0.1:8060/api/v1/videos/process -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" -d '{"url":"https://www.instagram.com/reels/DN5qu5jgPMb/","music_id":1,"impact_music":11.0,"impact_video":1.0,"return_format":"file"}' --output video_editado.mp4
```

---

## ⚠️ Importante

- **Substitua `SEU_TOKEN_AQUI`** pelo token do login
- **O processamento pode levar alguns minutos**
- **Com `return_format: "file"`**, o vídeo é baixado diretamente
- **Com `return_format: "url"`**, você precisa aprovar em 5 minutos

---

## 🎯 Resumo

**Para baixar o vídeo editado diretamente:**
```bash
./processar_video_fala.sh
```

**Ou manualmente:**
```bash
curl -X POST http://127.0.0.1:8060/api/v1/videos/process \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.instagram.com/reels/DN5qu5jgPMb/","music_id":1,"impact_music":11.0,"impact_video":1.0,"return_format":"file"}' \
  --output video_editado.mp4
```


