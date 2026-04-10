# ✅ Comandos para Aprovar e Testar Publicação

## 📋 Fluxo Completo

1. **Configurar Webhook** (se não estiver configurado)
2. **Processar Vídeo** (com `return_format: "url"`)
3. **Aprovar Vídeo** (dentro de 5 minutos)
4. **Verificar Fila** (publicações agendadas)
5. **Testar Webhook** (formato enviado)

---

## 🚀 Opção 1: Script Automático (Recomendado)

```bash
./testar_fluxo_completo.sh
```

O script faz tudo automaticamente!

---

## 📝 Opção 2: Comandos Manuais

### 1. Login

```bash
curl -X POST http://127.0.0.1:8060/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "caxa12", "password": "0102G@briel"}'
```

**Copie o `access_token` retornado.**

---

### 2. Configurar Webhook (se necessário)

```bash
curl -X PUT http://127.0.0.1:8060/api/v1/users/me \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "webhook_url": "https://n8n.dozecrew.com/webhook/98bce4e7-b9b1-4f4f-8c39-3db5955d0b76"
  }'
```

---

### 3. Processar Vídeo (com return_format: "url")

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

**Anote o `video_edit_id` retornado.**

---

### 4. Aprovar Vídeo

```bash
curl -X POST http://127.0.0.1:8060/api/v1/video-edits/approve \
  -H "Authorization: Bearer SEU_TOKEN_AQUI" \
  -H "Content-Type: application/json" \
  -d '{
    "video_edit_id": VIDEO_EDIT_ID,
    "description": "Music: Fala - CAXA12 #fut #rap #interclasse"
  }'
```

**Anote o `publication_id` e `scheduled_date` retornados.**

---

### 5. Verificar Fila de Publicações

```bash
curl -X GET http://127.0.0.1:8060/api/v1/publications/upcoming \
  -H "Authorization: Bearer SEU_TOKEN_AQUI"
```

---

## 📤 Formato da Webhook (N8N)

Quando a publicação for processada (na data agendada), a webhook receberá:

```json
{
  "description": "Music: Fala - CAXA12 #fut #rap #interclasse",
  "videoLink": "https://bucket.s3.amazonaws.com/video-edits/2/uuid_video.mp4",
  "date": "2025-12-09T10:00:00Z"
}
```

### Campos:

- **`description`**: Descrição do post (fornecida na aprovação)
- **`videoLink`**: Link público do S3 (vídeo editado)
- **`date`**: Data/hora agendada no formato ISO UTC (ex: `2025-12-09T10:00:00Z`)

---

## ⚠️ Importante

1. **Aprove dentro de 5 minutos** após processar o vídeo
2. **Webhook deve estar configurado** no perfil do usuário
3. **A publicação é agendada** automaticamente na fila (10/mês, horários 10h/13h/17h)
4. **A webhook é chamada** automaticamente quando chegar a data agendada

---

## 🔍 Verificar Status

### Ver vídeo editado:
```bash
curl -X GET http://127.0.0.1:8060/api/v1/video-edits/VIDEO_EDIT_ID \
  -H "Authorization: Bearer SEU_TOKEN"
```

### Ver publicação:
```bash
curl -X GET http://127.0.0.1:8060/api/v1/publications/PUBLICATION_ID \
  -H "Authorization: Bearer SEU_TOKEN"
```

---

## 🧪 Testar Webhook Manualmente

Se quiser testar a webhook manualmente (sem aguardar a data):

```bash
curl -X POST https://n8n.dozecrew.com/webhook/98bce4e7-b9b1-4f4f-8c39-3db5955d0b76 \
  -H "Content-Type: application/json" \
  -d '{
    "description": "Music: Fala - CAXA12 #fut #rap #interclasse",
    "videoLink": "https://bucket.s3.amazonaws.com/video-edits/2/uuid_video.mp4",
    "date": "2025-12-09T10:00:00Z"
  }'
```

---

## 📋 Resumo

**Para testar o fluxo completo:**
```bash
./testar_fluxo_completo.sh
```

**Ou manualmente:**
1. Login → 2. Configurar Webhook → 3. Processar (url) → 4. Aprovar → 5. Verificar Fila


