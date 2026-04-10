# 🧪 Teste Completo de Ponta a Ponta - Edição de Vídeos

## 📋 Objetivo

Validar todo o fluxo de edição de vídeos, incluindo:
1. ✅ Processamento de vídeo
2. ✅ Criação de registro com expiração de 5 minutos
3. ✅ Validação de expiração na aprovação
4. ✅ Aprovação e agendamento na fila
5. ✅ Verificação de status após aprovação

## 🚀 Como Executar

### Opção 1: Servidor já está rodando

```bash
python3 test_video_edit_complete.py
```

### Opção 2: Iniciar servidor automaticamente

```bash
./run_test_with_server.sh
```

Este script:
- Verifica se o servidor está rodando
- Se não estiver, inicia automaticamente
- Executa o teste completo
- Para o servidor ao finalizar

## 📝 Pré-requisitos

1. **Servidor rodando** na porta `8060`
   ```bash
   uvicorn bootstrap.app:app --host 0.0.0.0 --port 8060
   ```

2. **Banco de dados configurado** e migrado
   ```bash
   alembic upgrade head
   ```

3. **Música cadastrada** no sistema (o teste usa uma música existente)

4. **Variáveis de ambiente** configuradas (`.env`)
   - Database configurado
   - S3/MinIO configurado (opcional, mas recomendado)

## 🔍 O que o teste valida

### 1. Autenticação
- ✅ Login como admin
- ✅ Criar usuário de teste
- ✅ Login como usuário

### 2. Música
- ✅ Listar músicas do usuário
- ✅ Usar música existente para processamento

### 3. Processamento de Vídeo
- ✅ Download de vídeo do Instagram
- ✅ Processamento com música
- ✅ Upload para S3 (se configurado)
- ✅ Criação de registro `VideoEdit`
- ✅ Geração de preview URL (5 minutos)
- ✅ Verificação de `expires_at`

### 4. Validação de Expiração
- ✅ Verificar se vídeo não expirou
- ✅ Calcular tempo restante
- ✅ Validar expiração na aprovação

### 5. Aprovação
- ✅ Aprovar vídeo dentro do prazo
- ✅ Atualizar status para `APPROVED`
- ✅ Agendar na fila de publicação
- ✅ Marcar como `PUBLISHED`

### 6. Verificação Final
- ✅ Verificar status após aprovação
- ✅ Verificar fila de publicações
- ✅ Validar dados retornados

## 📊 Saída Esperada

```
============================================================
  TESTE COMPLETO - FLUXO DE EDIÇÃO DE VÍDEOS
============================================================

============================================================
  1. Login Admin
============================================================
Status: 200
✓ Login admin: OK

============================================================
  2. Criar/Obter Usuário
============================================================
Status: 201
✓ Usuário criado: OK

...

============================================================
  RESUMO DO TESTE
============================================================
✓ Login admin: OK
✓ Criar/obter usuário: OK
✓ Login usuário: OK
✓ Upload/obter música: OK
✓ Processar vídeo: OK
✓ Verificar vídeo editado: OK
✓ Listar pendentes: OK
✓ Aprovar vídeo: OK
✓ Verificar status após aprovação: OK
✓ Verificar fila de publicação: OK

🎉 TESTE COMPLETO EXECUTADO COM SUCESSO!
```

## ⚠️ Possíveis Problemas

### Servidor não está rodando
```bash
# Inicie o servidor primeiro
uvicorn bootstrap.app:app --host 0.0.0.0 --port 8060
```

### Nenhuma música encontrada
```bash
# Faça upload de uma música primeiro
curl -X POST http://127.0.0.1:8060/api/v1/musics \
  -H "Authorization: Bearer SEU_TOKEN" \
  -F "file=@/caminho/para/musica.mp3" \
  -F "name=Nome da Música"
```

### Vídeo expirou antes da aprovação
- O teste valida a expiração de 5 minutos
- Se demorar mais de 5 minutos, o vídeo expira e não pode ser aprovado
- Isso é comportamento esperado e valida a lógica de expiração

### Erro de conexão S3
- Se S3 não estiver configurado, o sistema usa armazenamento local
- O teste continua funcionando, mas sem upload para S3

## 🔧 Personalização

Para testar com diferentes URLs de vídeo, edite `test_video_edit_complete.py`:

```python
"url": "https://www.instagram.com/p/SEU_VIDEO_ID/",
```

Para testar com diferentes músicas, edite o `music_id` ou faça upload de uma nova música antes.

## 📝 Notas

- O teste usa um usuário temporário (`teste_video`)
- O vídeo processado pode ser grande (depende do vídeo original)
- O processamento pode levar alguns minutos
- A aprovação deve ser feita dentro de 5 minutos após o processamento


