# 📦 Migração de Dados Antigos

## 📋 Situação Atual

**Arquivos físicos existem**, mas **não estão registrados no banco de dados novo**.

### Arquivos Encontrados:
- ✅ `music/2/2805941bdddc4a6aa378919ad6a5fba9.mp3` - Música do usuário ID 2
- ✅ `processed/2/Video by caxa.doze_Mix Guia V1_iv1.00_im1.00.mp4` - Vídeo processado
- ✅ `videos/Video by caxa.doze.mp4` - Vídeo baixado

### Status do Banco:
- ❌ **Não há migração automática** de dados antigos
- ❌ Os arquivos físicos existem, mas não estão no banco
- ✅ As migrations criam apenas as **estruturas de tabelas**

---

## 🎯 Opções Disponíveis

### Opção 1: Migração Automática (Recomendado) ⭐

Use o script para registrar arquivos existentes no banco:

```bash
python3 scripts/migrate_existing_files.py
```

**O que faz:**
- ✅ Encontra todos os arquivos MP3 em `music/{user_id}/`
- ✅ Registra no banco de dados
- ✅ Obtém duração automaticamente (FFprobe)
- ✅ Preserva arquivos existentes
- ✅ Evita duplicatas

**Vantagens:**
- ✅ Mantém arquivos existentes
- ✅ Não precisa fazer upload novamente
- ✅ Rápido e automático

---

### Opção 2: Upload Manual

Faça upload novamente via API:

```bash
# 1. Login
curl -X POST http://127.0.0.1:8060/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "caxa12", "password": "sua_senha"}'

# 2. Upload música
curl -X POST http://127.0.0.1:8060/api/v1/musics \
  -H "Authorization: Bearer SEU_TOKEN" \
  -F "file=@/home/acer/Músicas/Musicas/guia mix V1.mp3" \
  -F "name=Mix Guia V1"
```

**Vantagens:**
- ✅ Garante que tudo está correto
- ✅ Permite renomear/ajustar
- ✅ Processo mais controlado

**Desvantagens:**
- ❌ Precisa fazer upload novamente
- ❌ Pode demorar se houver muitos arquivos

---

## 🔍 Verificar o que Existe

### Verificar arquivos físicos:
```bash
# Músicas
find music/ -name "*.mp3" -type f

# Vídeos processados
find processed/ -name "*.mp4" -type f
```

### Verificar no banco (via API):
```bash
# Listar músicas do usuário
curl -X GET http://127.0.0.1:8060/api/v1/musics \
  -H "Authorization: Bearer SEU_TOKEN"
```

---

## 📝 Sobre Vídeos Processados

**⚠️ IMPORTANTE:** Vídeos processados **NÃO precisam ser migrados** porque:

1. São gerados automaticamente quando você processa um vídeo
2. O novo sistema usa **S3** para armazenar vídeos editados
3. Vídeos antigos não têm registro de aprovação/expiração
4. É melhor processar novamente para ter o fluxo completo

**Recomendação:** Processe os vídeos novamente quando precisar.

---

## 🚀 Recomendação Final

**Para músicas:**
- ✅ Use o script de migração (`scripts/migrate_existing_files.py`)
- ✅ Rápido e preserva arquivos existentes

**Para vídeos:**
- ✅ Processe novamente quando precisar
- ✅ O novo sistema tem fluxo completo de aprovação/S3

---

## 🔧 Executar Migração

```bash
# 1. Certifique-se que o banco está configurado
# 2. Execute o script
python3 scripts/migrate_existing_files.py
```

O script irá:
1. Buscar todos os arquivos MP3 em `music/{user_id}/`
2. Verificar se já estão no banco
3. Registrar os que faltam
4. Obter duração automaticamente
5. Mostrar resumo

---

## ❓ Dúvidas?

- **Arquivos não encontrados?** Verifique se estão em `music/{user_id}/`
- **Erro ao registrar?** Verifique se o usuário existe no banco
- **Duração não obtida?** Verifique se FFprobe está instalado
- **Duplicatas?** O script evita duplicatas automaticamente


