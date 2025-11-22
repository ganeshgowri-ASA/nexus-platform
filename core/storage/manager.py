"""File storage management."""
import os
import boto3
from typing import BinaryIO, Optional, Union
import pandas as pd
from io import BytesIO
from pathlib import Path
from config.settings import settings


class StorageManager:
    """Manage file storage (local or S3)."""

    def __init__(self):
        """Initialize storage manager."""
        self.storage_type = settings.STORAGE_TYPE
        self.base_path = settings.STORAGE_PATH

        if self.storage_type == 's3':
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.bucket_name = settings.S3_BUCKET_NAME
        else:
            # Ensure local storage directory exists
            Path(self.base_path).mkdir(parents=True, exist_ok=True)

    def save_file(self, file_content: Union[bytes, BinaryIO], path: str) -> str:
        """
        Save file to storage.

        Args:
            file_content: File content as bytes or file-like object
            path: Relative path where file should be saved

        Returns:
            str: Storage path of saved file
        """
        if isinstance(file_content, bytes):
            file_content = BytesIO(file_content)

        if self.storage_type == 'local':
            return self._save_local(file_content, path)
        elif self.storage_type == 's3':
            return self._save_s3(file_content, path)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")

    def save_dataframe(self, df: pd.DataFrame, filename: str,
                       file_format: str = 'excel') -> str:
        """
        Save DataFrame to storage.

        Args:
            df: DataFrame to save
            filename: Filename (without extension)
            file_format: Format to save ('excel', 'csv', 'json')

        Returns:
            str: Storage path of saved file
        """
        buffer = BytesIO()

        if file_format == 'excel':
            if not filename.endswith('.xlsx'):
                filename += '.xlsx'
            df.to_excel(buffer, index=False, engine='openpyxl')
        elif file_format == 'csv':
            if not filename.endswith('.csv'):
                filename += '.csv'
            df.to_csv(buffer, index=False)
        elif file_format == 'json':
            if not filename.endswith('.json'):
                filename += '.json'
            df.to_json(buffer, orient='records', indent=2)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

        buffer.seek(0)
        return self.save_file(buffer, filename)

    def load_file(self, path: str) -> bytes:
        """
        Load file from storage.

        Args:
            path: File path in storage

        Returns:
            bytes: File content
        """
        if self.storage_type == 'local':
            return self._load_local(path)
        elif self.storage_type == 's3':
            return self._load_s3(path)
        else:
            raise ValueError(f"Unsupported storage type: {self.storage_type}")

    def load_dataframe(self, path: str, file_format: Optional[str] = None) -> pd.DataFrame:
        """
        Load DataFrame from storage.

        Args:
            path: File path in storage
            file_format: Format hint ('excel', 'csv', 'json'). Auto-detected if None.

        Returns:
            pd.DataFrame: Loaded DataFrame
        """
        file_content = self.load_file(path)

        # Auto-detect format from extension if not specified
        if file_format is None:
            if path.endswith('.xlsx') or path.endswith('.xls'):
                file_format = 'excel'
            elif path.endswith('.csv'):
                file_format = 'csv'
            elif path.endswith('.json'):
                file_format = 'json'
            else:
                raise ValueError(f"Cannot determine file format for: {path}")

        buffer = BytesIO(file_content)

        if file_format == 'excel':
            return pd.read_excel(buffer, engine='openpyxl')
        elif file_format == 'csv':
            return pd.read_csv(buffer)
        elif file_format == 'json':
            return pd.read_json(buffer)
        else:
            raise ValueError(f"Unsupported file format: {file_format}")

    def delete_file(self, path: str) -> bool:
        """
        Delete file from storage.

        Args:
            path: File path in storage

        Returns:
            bool: True if deleted successfully
        """
        try:
            if self.storage_type == 'local':
                full_path = os.path.join(self.base_path, path)
                if os.path.exists(full_path):
                    os.remove(full_path)
                    return True
            elif self.storage_type == 's3':
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=path)
                return True
            return False
        except Exception:
            return False

    def file_exists(self, path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            path: File path in storage

        Returns:
            bool: True if file exists
        """
        try:
            if self.storage_type == 'local':
                full_path = os.path.join(self.base_path, path)
                return os.path.exists(full_path)
            elif self.storage_type == 's3':
                self.s3_client.head_object(Bucket=self.bucket_name, Key=path)
                return True
        except Exception:
            return False

    def list_files(self, prefix: str = '') -> list:
        """
        List files in storage.

        Args:
            prefix: Prefix to filter files

        Returns:
            list: List of file paths
        """
        if self.storage_type == 'local':
            full_path = os.path.join(self.base_path, prefix)
            if not os.path.exists(full_path):
                return []
            files = []
            for root, _, filenames in os.walk(full_path):
                for filename in filenames:
                    file_path = os.path.join(root, filename)
                    rel_path = os.path.relpath(file_path, self.base_path)
                    files.append(rel_path)
            return files
        elif self.storage_type == 's3':
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            return [obj['Key'] for obj in response.get('Contents', [])]
        return []

    def _save_local(self, file: BinaryIO, path: str) -> str:
        """Save file to local storage."""
        full_path = os.path.join(self.base_path, path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)

        with open(full_path, 'wb') as f:
            f.write(file.read())

        return path

    def _save_s3(self, file: BinaryIO, path: str) -> str:
        """Save file to S3."""
        self.s3_client.upload_fileobj(file, self.bucket_name, path)
        return f"s3://{self.bucket_name}/{path}"

    def _load_local(self, path: str) -> bytes:
        """Load file from local storage."""
        full_path = os.path.join(self.base_path, path)

        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found: {path}")

        with open(full_path, 'rb') as f:
            return f.read()

    def _load_s3(self, path: str) -> bytes:
        """Load file from S3."""
        # Remove s3:// prefix if present
        if path.startswith('s3://'):
            path = path.replace(f"s3://{self.bucket_name}/", '')

        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=path)
        return response['Body'].read()
