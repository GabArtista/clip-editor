# Migração para Object Storage (S3/MinIO)

Este documento descreve a implementação de suporte a object storage para armazenamento de músicas, permitindo que as faixas sejam reutilizáveis e armazenadas de forma escalável.

## Visão Geral

Anteriormente, o sistema armazenava arquivos de música apenas em disco local (`music_storage/`). Agora, o sistema suporta tanto storage local quanto S3/MinIO através de um driver abstrato.

### Benefícios

- **Reutilização**: Arquivos armazenados uma vez podem ser referenciados por múltiplos assets
- **Escalabilidade**: Storage distribuído com MinIO/S3
- **Preservação**: Estrutura organizada por usuário e asset (`media/{user_id}/{music_id}/original.mp3`)
- **URLs Presignadas**: Acesso seguro e temporário aos arquivos

## Arquitetura

### Storage Driver

O sistema implementa um driver de storage abstrato (`app/services/storage.py`) com duas implementações:

1. **LocalStorageDriver**: Armazena arquivos no filesystem local
2. **S3StorageDriver**: Armazena arquivos no MinIO/S3 compatível com S3

### Configuração

A seleção do driver é feita através da variável de ambiente `MUSIC_STORAGE_DRIVER`:

```bash
# Storage local (padrão)
MUSIC_STORAGE_DRIVER=local

# Storage S3/MinIO
MUSIC_STORAGE_DRIVER=s3
```

## Configuração do S3/MinIO

### Variáveis de Ambiente

Adicione estas variáveis ao seu `.env` ou `.env.dev`:

```bash
MUSIC_STORAGE_DRIVER=s3
OBJECT_STORAGE_ENDPOINT=http://127.0.0.1:9000
OBJECT_STORAGE_BUCKET_MEDIA=media
OBJECT_STORAGE_ACCESS_KEY=minioadmin
OBJECT_STORAGE_SECRET_KEY=minioadmin
OBJECT_STORAGE_REGION=us-east-1
```

### Docker Compose

O `docker-compose.dev.yml` já está configurado com MinIO:

```yaml
services:
  minio:
    image: minio/minio:RELEASE.2024-06-04T19-20-08Z
    container_name: fala-minio
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    ports:
      - "9000:9000"  # API
      - "9001:9001"  # Console
    command: server /data --console-address ":9001"
    volumes:
      - fala_object_storage:/data
```

Para iniciar:

```bash
docker-compose -f docker-compose.dev.yml up -d
```

Acesse o console do MinIO em: http://localhost:9001
- Usuário: `minioadmin`
- Senha: `minioadmin`

## Estrutura de Armazenamento

Os arquivos são organizados no formato:

```
media/{user_id}/{music_id}/original.{ext}
```

Exemplo:
```
media/550e8400-e29b-41d4-a716-446655440000/123e4567-e89b-12d3-a456-426614174000/original.mp3
```

## Migração de Arquivos Existentes

Para migrar arquivos já armazenados localmente para S3:

1. Configure as variáveis de ambiente S3
2. Execute o script de migração:

```bash
python scripts/migrate_music_to_s3.py
```

O script:
- Busca todos os arquivos de áudio no banco de dados
- Faz upload para S3 mantendo a estrutura
- Atualiza `storage_path` no banco com URL S3

## API

### Upload de Música

**POST** `/music`

O endpoint continua funcionando da mesma forma, mas agora armazena no driver configurado:

```bash
curl -X POST http://localhost:8000/music \
  -H "Authorization: Bearer {token}" \
  -F "title=Minha Música" \
  -F "genre=trap" \
  -F "file=@music.mp3"
```

Resposta inclui `download_url` (se disponível):

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "title": "Minha Música",
  "status": "ready",
  "download_url": "https://minio:9000/media/...?X-Amz-Signature=..."
}
```

### Listagem e Detalhes

**GET** `/music` e **GET** `/music/{id}` continuam funcionando normalmente.

As URLs presignadas são geradas automaticamente quando:
- O storage é S3/MinIO
- O arquivo existe no storage
- A expiração padrão é de 1 hora

## Testes

Os testes foram atualizados para suportar o novo sistema de storage:

```bash
pytest tests/test_music.py
```

Os testes usam storage local por padrão. Para testar com S3, use mocks:

```python
from unittest.mock import patch

@patch('app.services.storage.boto3.client')
def test_with_s3(mock_s3):
    # Teste com S3 mockado
    pass
```

## Desenvolvimento Local

### Modo Local (Padrão)

Não requer configuração adicional. Os arquivos são salvos em `music_storage/`.

### Modo S3 com MinIO

1. Inicie o MinIO:
```bash
docker-compose -f docker-compose.dev.yml up -d minio
```

2. Configure `.env.dev`:
```bash
MUSIC_STORAGE_DRIVER=s3
OBJECT_STORAGE_ENDPOINT=http://127.0.0.1:9000
OBJECT_STORAGE_ACCESS_KEY=minioadmin
OBJECT_STORAGE_SECRET_KEY=minioadmin
```

3. Reinicie a aplicação

## Produção

Para usar com AWS S3:

```bash
MUSIC_STORAGE_DRIVER=s3
OBJECT_STORAGE_ENDPOINT=https://s3.amazonaws.com
OBJECT_STORAGE_BUCKET_MEDIA=my-bucket-name
OBJECT_STORAGE_ACCESS_KEY=${AWS_ACCESS_KEY_ID}
OBJECT_STORAGE_SECRET_KEY=${AWS_SECRET_ACCESS_KEY}
OBJECT_STORAGE_REGION=us-east-1
```

## Troubleshooting

### Erro ao criar bucket

Se o bucket não existir, o driver tenta criar automaticamente. Certifique-se de que as credenciais têm permissão de criação.

### Arquivo não encontrado

Verifique se o `storage_path` no banco corresponde à chave do objeto no S3. Use o script de migração para corrigir.

### URLs presignadas não funcionam

Verifique:
- As credenciais estão corretas
- O endpoint está acessível
- As permissões do bucket permitem leitura

## Roadmap Futuro

- [ ] Suporte a diferentes formatos de áudio (formato normalizado)
- [ ] Compressão de arquivos
- [ ] Versionamento de assets
- [ ] CDN para distribuição global
- [ ] Lazy loading de metadados


