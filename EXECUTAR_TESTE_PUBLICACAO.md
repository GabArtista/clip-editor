# 🚀 Executar Teste de Aprovação e Publicação

## ✅ URL de Webhook Configurada

A URL de webhook do usuário está configurada no script:
```
https://n8n.dozecrew.com/webhook/98bce4e7-b9b1-4f4f-8c39-3db5955d0b76
```

---

## 🎯 Executar Teste Completo

### Opção 1: Script Automático (Recomendado)

```bash
./testar_fluxo_completo.sh
```

Este script irá:
1. ✅ Fazer login
2. ✅ Configurar webhook URL
3. ✅ Processar vídeo (return_format: "url")
4. ✅ Aprovar vídeo com descrição: "Music: Fala - CAXA12 #fut #rap #interclasse"
5. ✅ Agendar na fila de publicação
6. ✅ Mostrar formato da webhook

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

### 2. Configurar Webhook
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
- **`description`**: "Music: Fala - CAXA12 #fut #rap #interclasse"
- **`videoLink`**: Link público do S3 (vídeo editado)
- **`date`**: Data/hora agendada no formato ISO UTC (ex: "2025-12-09T10:00:00Z")

---

## ⚠️ Importante

1. ⏰ **Aprove dentro de 5 minutos** após processar o vídeo
2. 🔗 **Webhook já está configurada** no script
3. 📅 **A publicação é agendada** automaticamente (10/mês, horários 10h/13h/17h)
4. 🚀 **A webhook é chamada** automaticamente quando chegar a data agendada

---

## 🎬 Pronto para Executar!

Execute o script:
```bash
./testar_fluxo_completo.sh
```

Ou use os comandos manuais acima substituindo `SEU_TOKEN_AQUI` pelo token do login.


