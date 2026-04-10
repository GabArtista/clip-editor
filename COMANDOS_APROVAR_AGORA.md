# ✅ Comandos para Aprovar Vídeo Agora

## ⚠️ Situação Atual

O vídeo foi processado, mas o upload para S3 falhou (413 - arquivo muito grande).
**AGORA o sistema cria o registro mesmo quando S3 falha**, permitindo aprovação!

---

## 🔄 Processar Novamente (com correção)

Como o vídeo anterior não criou registro, você precisa processar novamente:

### 1. Processar Vídeo (return_format: "url")

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

**Agora retornará `video_edit_id` mesmo se S3 falhar!**

---

### 2. Verificar Vídeos Pendentes

```bash
curl -X GET http://127.0.0.1:8060/api/v1/video-edits/pending \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzY1Mzg2NzM5fQ.2XGCVHr4FhYluGq0DutvTDqeBAP1kyslHcZlnFQPJLs"
```

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

**Substitua `VIDEO_EDIT_ID` pelo ID retornado no passo 1!**

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
  "videoLink": "http://127.0.0.1:8060/api/v1/videos/files/2/filename.mp4",
  "date": "2025-12-09T10:00:00Z"
}
```

**Nota:** Se o S3 falhar, o `videoLink` será a URL local. Se o S3 funcionar, será a URL do MinIO.

---

## ⚠️ Importante

- ⏰ **Aprove dentro de 5 minutos** após processar
- 🔄 **Processe novamente** para criar o registro (com a correção aplicada)
- 📝 **O sistema agora cria registro mesmo quando S3 falha**

---

## 🚀 Pronto!

Execute os comandos acima na ordem. O sistema agora funciona mesmo quando o S3 falha!


