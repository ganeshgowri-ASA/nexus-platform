"""API Key management service."""
from typing import Optional
from shared.security import encrypt_data, decrypt_data
from shared.utils.logger import get_logger
from modules.integration_hub.models import APIKey
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

logger = get_logger(__name__)


class APIKeyService:
    """Service for managing API keys."""

    def __init__(self, db: Session):
        self.db = db
        self.logger = logger

    def create_api_key(
        self,
        integration_id: str,
        name: str,
        api_key: str,
        description: Optional[str] = None,
        additional_fields: Optional[dict] = None,
        rate_limit_per_minute: Optional[str] = None,
        rate_limit_per_hour: Optional[str] = None,
    ) -> APIKey:
        """Create and store an encrypted API key."""
        try:
            # Encrypt the API key
            encrypted_key = encrypt_data(api_key)

            # Encrypt additional fields if provided
            encrypted_additional = None
            if additional_fields:
                import json

                encrypted_additional = encrypt_data(json.dumps(additional_fields))

            # Create API key record
            api_key_record = APIKey(
                id=str(uuid.uuid4()),
                integration_id=integration_id,
                name=name,
                description=description,
                encrypted_key=encrypted_key,
                additional_fields=encrypted_additional,
                is_active=True,
                rate_limit_per_minute=rate_limit_per_minute,
                rate_limit_per_hour=rate_limit_per_hour,
            )

            self.db.add(api_key_record)
            self.db.commit()
            self.db.refresh(api_key_record)

            self.logger.info(f"API key created: {name}")
            return api_key_record

        except Exception as e:
            self.logger.error(f"Error creating API key: {e}")
            self.db.rollback()
            raise

    def get_decrypted_key(self, api_key_id: str) -> str:
        """Get decrypted API key."""
        try:
            api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
            if not api_key:
                raise ValueError(f"API key not found: {api_key_id}")

            if not api_key.is_active:
                raise ValueError("API key is not active")

            # Decrypt the key
            decrypted_key = decrypt_data(api_key.encrypted_key)

            # Update last_used
            api_key.last_used = datetime.utcnow()
            self.db.commit()

            return decrypted_key

        except Exception as e:
            self.logger.error(f"Error getting decrypted key: {e}")
            raise

    def get_additional_fields(self, api_key_id: str) -> Optional[dict]:
        """Get decrypted additional fields."""
        try:
            api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
            if not api_key or not api_key.additional_fields:
                return None

            import json

            decrypted_fields = decrypt_data(api_key.additional_fields)
            return json.loads(decrypted_fields)

        except Exception as e:
            self.logger.error(f"Error getting additional fields: {e}")
            return None

    def rotate_key(self, api_key_id: str, new_key: str) -> APIKey:
        """Rotate an API key."""
        try:
            api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
            if not api_key:
                raise ValueError(f"API key not found: {api_key_id}")

            # Encrypt new key
            api_key.encrypted_key = encrypt_data(new_key)
            self.db.commit()
            self.db.refresh(api_key)

            self.logger.info(f"API key rotated: {api_key.name}")
            return api_key

        except Exception as e:
            self.logger.error(f"Error rotating key: {e}")
            self.db.rollback()
            raise

    def deactivate_key(self, api_key_id: str) -> bool:
        """Deactivate an API key."""
        try:
            api_key = self.db.query(APIKey).filter(APIKey.id == api_key_id).first()
            if not api_key:
                return False

            api_key.is_active = False
            self.db.commit()

            self.logger.info(f"API key deactivated: {api_key.name}")
            return True

        except Exception as e:
            self.logger.error(f"Error deactivating key: {e}")
            return False
