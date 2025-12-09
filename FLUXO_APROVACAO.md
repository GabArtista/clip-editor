# 🔄 Fluxo de Aprovação e S3 - Documentação Completa

## 📋 Visão Geral

Sistema completo de aprovação de vídeos editados com armazenamento S3 e expiração automática.

---

## 🔄 Fluxo Completo

### 1. **Processamento de Vídeo**
```
POST /api/v1/videos/process
{
  "url": "https://instagram.com/reels/...",
  "music_id": 1,
  "impact_music": 51.0,
  "impact_video": 10.10
}
```

**O que acontece:**
1. ✅ Baixa vídeo da rede social
2. ✅ Processa com música (sincronização)
3. ✅ Faz upload para S3 (público)
4. ✅ Gera URL pré-assinada temporária (5 minutos)
5. ✅ Cria registro `VideoEdit` com status `PENDING_APPROVAL`

**Resposta:**
```json
{
  "ok": true,
  "video_edit_id": 123,
  "preview_url": "https://s3...?X-Amz-Expires=300",
  "s3_url": "https://bucket.s3.amazonaws.com/video-edits/1/abc123.mp4",
  "expires_at": "2025-01-09T14:05:00Z",
  "message": "Vídeo processado e enviado para S3. Use o preview_url para visualizar. Aprove em até 5 minutos."
}
```

---

### 2. **Visualização e Aprovação**

#### Listar vídeos pendentes:
```
GET /api/v1/video-edits/pending
```

#### Aprovar vídeo:
```
POST /api/v1/video-edits/approve
{
  "video_edit_id": 123,
  "description": "Meu vídeo incrível 🚀"
}
```

**O que acontece:**
1. ✅ Valida que vídeo não expirou (5 min)
2. ✅ Atualiza status para `APPROVED`
3. ✅ Salva descrição
4. ✅ Agenda na fila de publicação usando **link S3 público**
5. ✅ Marca como `PUBLISHED` (agendado)
6. ✅ Define `delete_at` = 3 horas após publicação

**Resposta:**
```json
{
  "ok": true,
  "message": "Vídeo aprovado e agendado para publicação",
  "video_edit_id": 123,
  "publication_id": 456,
  "scheduled_date": "2025-01-10T10:00:00Z",
  "s3_url": "https://bucket.s3.amazonaws.com/video-edits/1/abc123.mp4"
}
```

---

### 3. **Rejeição (Opcional)**
```
POST /api/v1/video-edits/{video_edit_id}/reject
```

**O que acontece:**
1. ✅ Deleta arquivo do S3
2. ✅ Remove registro do banco

---

### 4. **Publicação Automática**

Quando chega a hora agendada:
1. ✅ Worker busca publicação
2. ✅ Envia para webhook N8N com link S3:
```json
{
  "description": "Meu vídeo incrível 🚀",
  "videoLink": "https://bucket.s3.amazonaws.com/video-edits/1/abc123.mp4",
  "date": "2025-12-09T00:19:00Z"
}
```
3. ✅ N8N/Getlate publica em todas as redes sociais
4. ✅ Marca publicação como `COMPLETED`

---

### 5. **Limpeza Automática**

Worker executa a cada hora:

#### Preview Expirado (não aprovado em 5 min):
- ✅ Deleta do S3
- ✅ Remove do banco

#### Vídeo Publicado (3h após publicação):
- ✅ Deleta do S3
- ✅ Remove do banco

---

## ⏱️ Regras de Expiração

### Preview (Aprovação)
- **Duração:** 5 minutos
- **Quando:** Após processamento
- **Ação se expirar:** Deleta automaticamente

### Publicação
- **Duração:** 3 horas após publicação
- **Quando:** Após ser publicado via N8N
- **Ação:** Deleta automaticamente do S3

---

## 🔐 Segurança

### Isolamento por Usuário
- ✅ Vídeos isolados por `user_id`
- ✅ S3 keys: `video-edits/{user_id}/{filename}`
- ✅ Validação de propriedade em todos os endpoints

### URLs
- **Preview URL:** Pré-assinada (5 min) - temporária
- **S3 URL:** Pública permanente (até ser deletado)
- **Publicação:** Usa S3 URL pública

---

## 📊 Estados do Vídeo Editado

| Status | Descrição | Ação |
|--------|-----------|------|
| `PENDING_APPROVAL` | Aguardando aprovação | Usuário visualiza e aprova |
| `APPROVED` | Aprovado, aguardando publicação | Agendado na fila |
| `PUBLISHED` | Publicado | Aguardando 3h para deletar |
| `REJECTED` | Rejeitado | Deletado |
| `EXPIRED` | Preview expirado | Deletado automaticamente |

---

## 🛠️ Configuração S3

### Variáveis de Ambiente
```env
S3_BUCKET_NAME=your-bucket-name
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

### Permissões S3 Necessárias
- `s3:PutObject` (upload)
- `s3:GetObject` (download/URLs)
- `s3:DeleteObject` (limpeza)
- `s3:PutObjectAcl` (tornar público)

### Bucket Policy (Exemplo)
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::your-bucket/video-edits/*"
    }
  ]
}
```

---

## 📝 Endpoints

### Vídeos Editados
- `GET /api/v1/video-edits` - Lista vídeos do usuário
- `GET /api/v1/video-edits/pending` - Lista pendentes de aprovação
- `GET /api/v1/video-edits/{id}` - Obtém vídeo específico
- `POST /api/v1/video-edits/approve` - Aprova e agenda
- `POST /api/v1/video-edits/{id}/reject` - Rejeita e deleta

---

## ✅ Vantagens do Novo Fluxo

1. ✅ **Preview antes de publicar** - Usuário vê antes de aprovar
2. ✅ **Armazenamento S3** - Escalável e confiável
3. ✅ **Links públicos** - N8N acessa diretamente
4. ✅ **Limpeza automática** - Não acumula arquivos
5. ✅ **Isolamento** - Cada usuário tem seus vídeos
6. ✅ **Expiração inteligente** - Preview 5min, publicação 3h

---

## 🎯 Resumo do Fluxo

```
Vídeo Editado
    ↓
Upload S3 (público)
    ↓
Preview URL (5 min)
    ↓
Usuário Visualiza
    ↓
Aprova com Descrição
    ↓
Agenda na Fila (link S3)
    ↓
Publica via N8N (link S3)
    ↓
Mantém 3h no S3
    ↓
Deleta Automaticamente
```

Tudo configurado e funcionando! 🚀

