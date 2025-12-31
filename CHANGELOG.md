# Changelog

## [Unreleased] - 2025-12-31

### Added
- **API de Upload de Músicas**
  - `POST /upload-music` - Upload de músicas com validação ffprobe
  - `GET /list-music` - Listagem de todas as músicas disponíveis
  - `DELETE /delete-music/{nome}` - Deleção de músicas
  - Validação automática de formato de áudio usando ffprobe
  - Conversão automática para MP3 quando necessário
  - Prevenção de duplicatas e sanitização de nomes

- **Limpeza Automática de Vídeos**
  - Remoção automática do vídeo original após processamento bem-sucedido
  - Otimiza uso de espaço em disco
  - Mantém apenas o vídeo processado final

### Changed
- Adicionado `python-multipart` às dependências (necessário para upload de arquivos)
- Adicionado `pytest` e `httpx` para testes
- Dockerfile garante criação de diretórios necessários

### Security
- Validação rigorosa de arquivos de áudio com ffprobe
- Sanitização de nomes de arquivo
- Prevenção de sobrescrita acidental
- Limite de tamanho de arquivo (100MB)

### Testing
- Testes automatizados com pytest
- Script de teste manual (`test_upload_api.py`)
- Cobertura de casos de sucesso e erro

