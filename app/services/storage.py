"""
Serviço de storage abstrato para suportar filesystem local e S3/MinIO.
"""

from __future__ import annotations

import io
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from datetime import timedelta

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError


class StorageDriver(ABC):
    """Interface abstrata para drivers de storage."""

    @abstractmethod
    def upload_file(
        self,
        file_content: bytes | io.BytesIO,
        object_key: str,
        content_type: Optional[str] = None,
    ) -> str:
        """
        Faz upload de um arquivo e retorna a URL/path.
        
        Args:
            file_content: Conteúdo do arquivo em bytes ou BytesIO
            object_key: Chave do objeto (ex: media/user_id/music_id/original.mp3)
            content_type: Tipo MIME do arquivo
            
        Returns:
            URL ou path do arquivo armazenado
        """
        pass

    @abstractmethod
    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Retorna uma URL presignada para download temporário.
        
        Args:
            object_key: Chave do objeto
            expires_in: Tempo de expiração em segundos (padrão: 1 hora)
            
        Returns:
            URL presignada ou None se não suportado
        """
        pass

    @abstractmethod
    def delete_file(self, object_key: str) -> bool:
        """
        Deleta um arquivo do storage.
        
        Args:
            object_key: Chave do objeto
            
        Returns:
            True se deletado com sucesso, False caso contrário
        """
        pass

    @abstractmethod
    def file_exists(self, object_key: str) -> bool:
        """
        Verifica se um arquivo existe.
        
        Args:
            object_key: Chave do objeto
            
        Returns:
            True se existe, False caso contrário
        """
        pass


class LocalStorageDriver(StorageDriver):
    """Driver de storage local em filesystem."""

    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)

    def upload_file(
        self,
        file_content: bytes | io.BytesIO,
        object_key: str,
        content_type: Optional[str] = None,
    ) -> str:
        file_path = self.base_path / object_key
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if isinstance(file_content, io.BytesIO):
            content = file_content.getvalue()
        else:
            content = file_content
        
        file_path.write_bytes(content)
        return str(file_path)

    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> Optional[str]:
        # Para storage local, retorna o path do arquivo
        file_path = self.base_path / object_key
        if file_path.exists():
            return f"/files/{object_key}"
        return None

    def delete_file(self, object_key: str) -> bool:
        try:
            file_path = self.base_path / object_key
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception:
            return False

    def file_exists(self, object_key: str) -> bool:
        file_path = self.base_path / object_key
        return file_path.exists()


class S3StorageDriver(StorageDriver):
    """Driver de storage S3/MinIO."""

    def __init__(
        self,
        endpoint_url: str,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        region: str = "us-east-1",
    ):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        
        # Configuração do cliente S3
        config = Config(
            region_name=region,
            s3={
                "addressing_style": "path",
            },
            signature_version="s3v4",
        )
        
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            config=config,
        )
        
        # Garante que o bucket existe
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self) -> None:
        """Cria o bucket se não existir."""
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code")
            if error_code == "404":
                # Bucket não existe, cria
                self.s3_client.create_bucket(Bucket=self.bucket_name)
            elif error_code == "403":
                # Bucket existe mas não tem permissão
                pass
            else:
                raise

    def upload_file(
        self,
        file_content: bytes | io.BytesIO,
        object_key: str,
        content_type: Optional[str] = None,
    ) -> str:
        if isinstance(file_content, io.BytesIO):
            file_content.seek(0)
        
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=object_key,
            Body=file_content,
            **extra_args,
        )
        
        # Retorna URL do objeto
        return f"s3://{self.bucket_name}/{object_key}"

    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> Optional[str]:
        try:
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError:
            return None

    def delete_file(self, object_key: str) -> bool:
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError:
            return False

    def file_exists(self, object_key: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except ClientError as e:
            if e.response.get("Error", {}).get("Code") == "404":
                return False
            raise


def get_storage_driver() -> StorageDriver:
    """
    Factory function para criar o driver de storage apropriado.
    
    Usa as variáveis de ambiente:
    - MUSIC_STORAGE_DRIVER: 'local' ou 's3'
    - Para S3: OBJECT_STORAGE_ENDPOINT, OBJECT_STORAGE_ACCESS_KEY, etc.
    """
    driver = os.getenv("MUSIC_STORAGE_DRIVER", "local").lower()
    
    if driver == "s3":
        endpoint = os.getenv("OBJECT_STORAGE_ENDPOINT")
        bucket = os.getenv("OBJECT_STORAGE_BUCKET_MEDIA", "media")
        access_key = os.getenv("OBJECT_STORAGE_ACCESS_KEY")
        secret_key = os.getenv("OBJECT_STORAGE_SECRET_KEY")
        region = os.getenv("OBJECT_STORAGE_REGION", "us-east-1")
        
        if not all([endpoint, access_key, secret_key]):
            raise ValueError(
                "Variáveis de ambiente S3 não configuradas: "
                "OBJECT_STORAGE_ENDPOINT, OBJECT_STORAGE_ACCESS_KEY, OBJECT_STORAGE_SECRET_KEY"
            )
        
        return S3StorageDriver(endpoint, bucket, access_key, secret_key, region)
    
    # Default: storage local
    base_path = Path(os.getenv("MUSIC_STORAGE_DIR", "music_storage"))
    return LocalStorageDriver(base_path)

