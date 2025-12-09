"""
Cliente S3 para upload e gerenciamento de vídeos
"""
import boto3
from botocore.exceptions import ClientError
from typing import Optional
from datetime import datetime, timedelta
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class S3Client:
    """Cliente para operações S3"""
    
    def __init__(
        self,
        bucket_name: Optional[str] = None,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        region_name: str = "us-east-1"
    ):
        self.bucket_name = bucket_name or getattr(settings, "S3_BUCKET_NAME", None)
        self.region_name = region_name or getattr(settings, "S3_REGION", "us-east-1")
        
        # Inicializa cliente S3
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id or getattr(settings, "AWS_ACCESS_KEY_ID", None),
            aws_secret_access_key=aws_secret_access_key or getattr(settings, "AWS_SECRET_ACCESS_KEY", None),
            region_name=self.region_name
        )
    
    def upload_file(
        self,
        file_path: str,
        s3_key: str,
        content_type: str = "video/mp4",
        public: bool = True
    ) -> str:
        """
        Faz upload de arquivo para S3
        
        Args:
            file_path: Caminho local do arquivo
            s3_key: Chave no S3 (caminho)
            content_type: Tipo MIME do arquivo
            public: Se True, torna o arquivo público
        
        Returns:
            URL pública do arquivo
        """
        try:
            extra_args = {
                'ContentType': content_type
            }
            
            if public:
                extra_args['ACL'] = 'public-read'
            
            self.s3_client.upload_file(
                file_path,
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args
            )
            
            # Retorna URL pública
            if public:
                url = f"https://{self.bucket_name}.s3.{self.region_name}.amazonaws.com/{s3_key}"
            else:
                # Gera URL pré-assinada se não for público
                url = self.s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket_name, 'Key': s3_key},
                    ExpiresIn=3600
                )
            
            logger.info(f"Arquivo enviado para S3: {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Erro ao fazer upload para S3: {str(e)}")
            raise Exception(f"Erro ao fazer upload para S3: {str(e)}")
    
    def generate_presigned_url(
        self,
        s3_key: str,
        expiration: int = 300  # 5 minutos por padrão
    ) -> str:
        """
        Gera URL pré-assinada temporária
        
        Args:
            s3_key: Chave no S3
            expiration: Tempo de expiração em segundos
        
        Returns:
            URL pré-assinada
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            return url
        except ClientError as e:
            logger.error(f"Erro ao gerar URL pré-assinada: {str(e)}")
            raise Exception(f"Erro ao gerar URL pré-assinada: {str(e)}")
    
    def delete_file(self, s3_key: str) -> bool:
        """
        Deleta arquivo do S3
        
        Args:
            s3_key: Chave no S3
        
        Returns:
            True se deletado com sucesso
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            logger.info(f"Arquivo deletado do S3: {s3_key}")
            return True
        except ClientError as e:
            logger.error(f"Erro ao deletar arquivo do S3: {str(e)}")
            return False
    
    def file_exists(self, s3_key: str) -> bool:
        """
        Verifica se arquivo existe no S3
        
        Args:
            s3_key: Chave no S3
        
        Returns:
            True se existe
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=s3_key)
            return True
        except ClientError:
            return False

