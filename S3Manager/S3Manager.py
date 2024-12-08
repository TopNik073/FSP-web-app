import logging
import os
import tempfile
from typing import BinaryIO
import boto3
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logger = logging.getLogger(__name__)


class S3Manager:
    def __init__(self):
        self.bucket = os.getenv("S3_BUCKET")
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=os.environ.get("S3_ENDPOINT"),
            region_name=os.environ.get("S3_REGION"),
            aws_access_key_id=os.environ.get("S3_ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("S3_SECRET_KEY")
        )

    def upload_file(self, file: BinaryIO, file_path: str, content_type: str | None = None) -> dict:
        """
        Загружает файл в S3 хранилище
        """
        try:
            # Создаем временный файл
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                # Копируем содержимое во временный файл
                file.save(temp_file.name)
                
                # Загружаем файл в S3
                extra_args = {'ContentType': content_type} if content_type else {}
                self.s3_client.upload_file(
                    temp_file.name,
                    self.bucket,
                    file_path,
                    ExtraArgs=extra_args
                )

            # Получаем размер файла
            size = os.path.getsize(temp_file.name)
            
            # Удаляем временный файл
            os.unlink(temp_file.name)

            # Формируем публичный URL
            file_url = f"{os.getenv('S3_ENDPOINT')}/{self.bucket}/{file_path}"
            return {
                "name": file_path.split('/')[-1],
                "url": file_url,
                "path": file_path,
                "size": size,
                "mime_type": content_type,
                "uploaded_at": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error uploading file to S3: {e}")
            # Убеждаемся, что временный файл удален
            if 'temp_file' in locals():
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
            return None

    def upload_files(self, files: list[BinaryIO], base_path: str) -> list[dict]:
        """
        Загружает несколько файлов в S3
        """
        uploaded_files = []
        for file in files:
            if file.filename:
                file_path = f"{base_path}/{file.filename}"
                result = self.upload_file(file, file_path, file.content_type)
                if result:
                    uploaded_files.append(result)
        return uploaded_files

    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str | None:
        """
        Генерирует временный URL для доступа к файлу
        
        Args:
            file_path: Путь к файлу в бакете
            expires_in: Время жизни URL в секундах
            
        Returns:
            URL для доступа к файлу или None при ошибке
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket,
                    'Key': file_path
                },
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None

    def delete_file(self, file_path: str) -> bool:
        """
        Удаляет файл из S3
        
        Args:
            file_path: Путь к файлу в бакете
            
        Returns:
            True если удаление успешно, False при ошибке
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket,
                Key=file_path
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting file from S3: {e}")
            return False

    def delete_files(self, file_paths: list[str]) -> bool:
        """
        Удаляет несколько файлов из S3
        
        Args:
            file_paths: Список путей к файлам
            
        Returns:
            True если все файлы удалены успешно
        """
        try:
            objects = [{'Key': path} for path in file_paths]
            self.s3_client.delete_objects(
                Bucket=self.bucket,
                Delete={'Objects': objects}
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting files from S3: {e}")
            return False

    def get_list_files(self, base_path: str) -> list[str]:
        return self.s3_client.list_objects_v2(Bucket=self.bucket, Prefix=base_path)["Contents"]


if __name__ == "__main__":
    s3_manager = S3Manager()
    print(s3_manager.get_list_files("fsp_events/1"))
