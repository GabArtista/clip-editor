# 🚀 Comandos Finais - Aprovar e Testar Publicação

## ✅ Token Atual

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzY1Mzg2NzM5fQ.2XGCVHr4FhYluGq0DutvTDqeBAP1kyslHcZlnFQPJLs
```

---

## 📝 Comandos Sequenciais

### 1. Configurar Webhook

```bash
curl -X PUT http://127.0.0.1:8060/api/v1/users/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzY1Mzg2NzM5fQ.2XGCVHr4FhYluGq0DutvTDqeBAP1kyslHcZlnFQPJLs" \
  -H "Content-Type: application/json" \
  -d '{"webhook_url": "https://n8n.dozecrew.com/webhook/98bce4e7-b9b1-4f4f-8c39-3db5955d0b76"}'
```

---

### 2. Processar Vídeo (return_format: "url")

```bash
curl -X POST http://127.0.0.1:8060/api/v1/videos/process \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzY1Mzg2NzM5fQ.2XGCVHr4FhYluGq0DutvTDqeBAP1kyslHcZlnFQPJLs" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/reels/DN5qu5jgPMb/",
    "music_id": 1,
    "impact_music": 11.0,
    "impact_video": 1.0,
    "return_format": "url"
  }'
```

**Anote o `video_edit_id` retornado!**

---

### 3. Aprovar Vídeo

```bash
curl -X POST http://127.0.0.1:8060/api/v1/video-edits/approve \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzY1Mzg2NzM5fQ.2XGCVHr4FhYluGq0DutvTDqeBAP1kyslHcZlnFQPJLs" \
  -H "Content-Type: application/json" \
  -d '{
    "video_edit_id": VIDEO_EDIT_ID,
    "description": "Music: Fala - CAXA12 #fut #rap #interclasse"
  }'
```

**Substitua `VIDEO_EDIT_ID` pelo ID retornado no passo 2!**

---

### 4. Verificar Fila de Publicações

```bash
curl -X GET http://127.0.0.1:8060/api/v1/publications/upcoming \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzY1Mzg2NzM5fQ.2XGCVHr4FhYluGq0DutvTDqeBAP1kyslHcZlnFQPJLs"
```

---

## 📤 Formato da Webhook (N8N)

Quando a publicação for processada, a webhook receberá:

```json
{
  "description": "Music: Fala - CAXA12 #fut #rap #interclasse",
  "videoLink": "https://minio.dozecrew.com/clip-dev/video-edits/2/uuid_video.mp4",
  "date": "2025-12-09T10:00:00Z"
}
```

**A URL do vídeo será do MinIO da dozecrew**, não do AWS S3 genérico!

---

## ⚠️ Importante

- ⏰ **Aprove dentro de 5 minutos** após processar
- 🔗 **Webhook já configurada** no comando 1
- 📅 **Publicação agendada** automaticamente (10/mês, horários 10h/13h/17h)
- 🚀 **Webhook chamada** automaticamente na data agendada

---

## 🔄 Se o Token Expirar

Faça login novamente:
```bash
curl -X POST http://127.0.0.1:8060/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "caxa12", "password": "0102G@briel"}'
```

E substitua o token nos comandos acima.


