# 📹 Explicação do Processamento de Vídeo

## ✅ O que aconteceu?

Quando você executou o comando com `return_format: "file"`, o servidor:

1. ✅ **Baixou o vídeo** do Instagram
2. ✅ **Processou com a música** (Mix Guia V1)
3. ✅ **Aplicou os impactos:**
   - Impacto Vídeo: 1.0
   - Impacto Música: 11.0
4. ✅ **Retornou o arquivo MP4** diretamente
5. ✅ **Salvou como** `video_editado.mp4` no diretório atual

## 📊 Resultado

- **Arquivo:** `video_editado.mp4`
- **Tamanho:** 2.0 MB
- **Formato:** MP4 válido (ISO Media)
- **Localização:** `/home/acer/Documentos/Projetos/Automacao/edit/video_editado.mp4`

## 🎬 Como Visualizar o Vídeo

### Opção 1: Abrir com player padrão
```bash
xdg-open video_editado.mp4
```

### Opção 2: Abrir com VLC
```bash
vlc video_editado.mp4
```

### Opção 3: Abrir com MPV
```bash
mpv video_editado.mp4
```

### Opção 4: Navegador de arquivos
```bash
nautilus .  # ou nemo, thunar, etc.
```
Depois clique duas vezes no arquivo `video_editado.mp4`

## 📝 Diferença entre `return_format`

### `"file"` (o que você usou)
- ✅ Retorna o arquivo MP4 diretamente
- ✅ Baixa automaticamente
- ✅ Não precisa aprovar
- ❌ Não cria registro no banco para aprovação
- ❌ Não vai para S3
- ❌ Não agenda na fila de publicação

### `"url"` (recomendado para produção)
- ✅ Cria registro no banco (`video_edit_id`)
- ✅ Faz upload para S3
- ✅ Gera preview URL (5 minutos)
- ✅ Permite aprovação e agendamento na fila
- ❌ Precisa aprovar em 5 minutos
- ❌ Não baixa o arquivo automaticamente

## 🔄 Para Usar o Fluxo Completo (Aprovação + Fila)

Se quiser usar o fluxo completo com aprovação:

```bash
# 1. Processar com return_format: "url"
curl -X POST http://127.0.0.1:8060/api/v1/videos/process \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.instagram.com/reels/DN5qu5jgPMb/",
    "music_id": 1,
    "impact_music": 11.0,
    "impact_video": 1.0,
    "return_format": "url"
  }'

# 2. Copiar o preview_url retornado e visualizar no navegador

# 3. Aprovar (dentro de 5 minutos)
curl -X POST http://127.0.0.1:8060/api/v1/video-edits/approve \
  -H "Authorization: Bearer SEU_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "video_edit_id": VIDEO_EDIT_ID,
    "description": "Vídeo editado com Mix Guia V1 🚀"
  }'
```

## 📍 Localização do Arquivo

O arquivo está em:
```
/home/acer/Documentos/Projetos/Automacao/edit/video_editado.mp4
```

Ou simplesmente:
```
./video_editado.mp4
```
(no diretório atual)


