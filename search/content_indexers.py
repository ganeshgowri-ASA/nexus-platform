"""Specialized indexers for different content types."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .indexer import DocumentIndexer
from .models import (
    ChatDocument,
    DocumentDocument,
    DocumentType,
    EmailDocument,
    FileDocument,
)

logger = logging.getLogger(__name__)


class DocumentContentIndexer:
    """Indexer for document content (Word, PDF, etc.)."""

    def __init__(self):
        """Initialize document content indexer."""
        self.indexer = DocumentIndexer()

    async def index_document(
        self,
        doc_id: str,
        title: str,
        content: str,
        owner_id: str,
        owner_name: str,
        file_type: Optional[str] = None,
        file_size: Optional[int] = None,
        page_count: Optional[int] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index a document."""
        try:
            document = DocumentDocument(
                id=doc_id,
                title=title,
                content=content,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                owner_id=owner_id,
                owner_name=owner_name,
                file_type=file_type,
                file_size=file_size,
                page_count=page_count,
                tags=tags or [],
                metadata=metadata or {},
            )

            await self.indexer.index_document(document)
            logger.info(f"Indexed document: {doc_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index document {doc_id}: {e}")
            return False

    async def index_documents_from_directory(
        self,
        directory: str,
        owner_id: str,
        owner_name: str,
        recursive: bool = True,
    ) -> Dict[str, int]:
        """Index all documents from a directory."""
        path = Path(directory)
        if not path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        pattern = "**/*" if recursive else "*"
        files = list(path.glob(pattern))

        indexed = 0
        failed = 0

        for file_path in files:
            if not file_path.is_file():
                continue

            try:
                # Read file content (simplified - in production use proper extractors)
                content = self._extract_content(file_path)

                success = await self.index_document(
                    doc_id=str(file_path),
                    title=file_path.name,
                    content=content,
                    owner_id=owner_id,
                    owner_name=owner_name,
                    file_type=file_path.suffix,
                    file_size=file_path.stat().st_size,
                )

                if success:
                    indexed += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                failed += 1

        return {"success": indexed, "failed": failed}

    def _extract_content(self, file_path: Path) -> str:
        """Extract text content from file (placeholder)."""
        # In production, use libraries like:
        # - python-docx for Word
        # - PyPDF2 or pdfplumber for PDF
        # - openpyxl for Excel
        # - python-pptx for PowerPoint

        try:
            if file_path.suffix in [".txt", ".md", ".py", ".json"]:
                return file_path.read_text(encoding="utf-8", errors="ignore")
            else:
                return f"Binary file: {file_path.name}"
        except Exception as e:
            logger.error(f"Content extraction failed for {file_path}: {e}")
            return ""


class EmailContentIndexer:
    """Indexer for email content."""

    def __init__(self):
        """Initialize email content indexer."""
        self.indexer = DocumentIndexer()

    async def index_email(
        self,
        email_id: str,
        subject: str,
        sender: str,
        recipients: List[str],
        content: str,
        owner_id: str,
        owner_name: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        has_attachments: bool = False,
        attachment_names: Optional[List[str]] = None,
        importance: str = "normal",
        folder: str = "inbox",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index an email."""
        try:
            email = EmailDocument(
                id=email_id,
                title=subject,
                subject=subject,
                content=content,
                sender=sender,
                recipients=recipients,
                cc=cc or [],
                bcc=bcc or [],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                owner_id=owner_id,
                owner_name=owner_name,
                has_attachments=has_attachments,
                attachment_names=attachment_names or [],
                importance=importance,
                folder=folder,
                tags=tags or [],
                metadata=metadata or {},
            )

            await self.indexer.index_document(email)
            logger.info(f"Indexed email: {email_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index email {email_id}: {e}")
            return False

    async def index_emails_bulk(
        self,
        emails: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Bulk index emails."""
        email_docs = []

        for email_data in emails:
            try:
                email = EmailDocument(
                    id=email_data["id"],
                    title=email_data.get("subject", ""),
                    subject=email_data.get("subject", ""),
                    content=email_data.get("content", ""),
                    sender=email_data["sender"],
                    recipients=email_data.get("recipients", []),
                    cc=email_data.get("cc", []),
                    bcc=email_data.get("bcc", []),
                    created_at=email_data.get("created_at", datetime.utcnow()),
                    updated_at=email_data.get("updated_at", datetime.utcnow()),
                    owner_id=email_data["owner_id"],
                    owner_name=email_data["owner_name"],
                    has_attachments=email_data.get("has_attachments", False),
                    attachment_names=email_data.get("attachment_names", []),
                    importance=email_data.get("importance", "normal"),
                    folder=email_data.get("folder", "inbox"),
                    tags=email_data.get("tags", []),
                    metadata=email_data.get("metadata", {}),
                )
                email_docs.append(email)

            except Exception as e:
                logger.error(f"Failed to prepare email for indexing: {e}")

        return await self.indexer.index_documents_bulk(email_docs)


class FileContentIndexer:
    """Indexer for file system content."""

    def __init__(self):
        """Initialize file content indexer."""
        self.indexer = DocumentIndexer()

    async def index_file(
        self,
        file_id: str,
        file_name: str,
        file_path: str,
        content: str,
        owner_id: str,
        owner_name: str,
        file_type: str,
        file_size: int,
        mime_type: str,
        extension: str,
        parent_folder: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index a file."""
        try:
            file_doc = FileDocument(
                id=file_id,
                title=file_name,
                content=content,
                file_name=file_name,
                file_path=file_path,
                file_type=file_type,
                file_size=file_size,
                mime_type=mime_type,
                extension=extension,
                parent_folder=parent_folder,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                owner_id=owner_id,
                owner_name=owner_name,
                tags=tags or [],
                metadata=metadata or {},
            )

            await self.indexer.index_document(file_doc)
            logger.info(f"Indexed file: {file_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index file {file_id}: {e}")
            return False

    async def index_directory(
        self,
        directory: str,
        owner_id: str,
        owner_name: str,
        recursive: bool = True,
    ) -> Dict[str, int]:
        """Index all files in a directory."""
        path = Path(directory)
        if not path.exists():
            raise ValueError(f"Directory does not exist: {directory}")

        pattern = "**/*" if recursive else "*"
        files = list(path.glob(pattern))

        indexed = 0
        failed = 0

        for file_path in files:
            if not file_path.is_file():
                continue

            try:
                content = self._extract_content(file_path)

                success = await self.index_file(
                    file_id=str(file_path),
                    file_name=file_path.name,
                    file_path=str(file_path.absolute()),
                    content=content,
                    owner_id=owner_id,
                    owner_name=owner_name,
                    file_type=file_path.suffix[1:] if file_path.suffix else "unknown",
                    file_size=file_path.stat().st_size,
                    mime_type=self._get_mime_type(file_path),
                    extension=file_path.suffix[1:] if file_path.suffix else "",
                    parent_folder=str(file_path.parent),
                )

                if success:
                    indexed += 1
                else:
                    failed += 1

            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                failed += 1

        return {"success": indexed, "failed": failed}

    def _extract_content(self, file_path: Path) -> str:
        """Extract text content from file."""
        try:
            if file_path.suffix in [".txt", ".md", ".py", ".js", ".json", ".xml", ".html"]:
                return file_path.read_text(encoding="utf-8", errors="ignore")
            else:
                return f"Binary file: {file_path.name}"
        except Exception as e:
            logger.error(f"Content extraction failed for {file_path}: {e}")
            return ""

    def _get_mime_type(self, file_path: Path) -> str:
        """Get MIME type for file (simplified)."""
        # In production, use python-magic library
        extension_map = {
            ".txt": "text/plain",
            ".pdf": "application/pdf",
            ".doc": "application/msword",
            ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".jpg": "image/jpeg",
            ".png": "image/png",
            ".json": "application/json",
        }
        return extension_map.get(file_path.suffix, "application/octet-stream")


class ChatContentIndexer:
    """Indexer for chat messages."""

    def __init__(self):
        """Initialize chat content indexer."""
        self.indexer = DocumentIndexer()

    async def index_message(
        self,
        message_id: str,
        channel_id: str,
        channel_name: str,
        sender: str,
        message: str,
        owner_id: str,
        owner_name: str,
        participants: Optional[List[str]] = None,
        thread_id: Optional[str] = None,
        has_attachments: bool = False,
        reactions: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Index a chat message."""
        try:
            chat_doc = ChatDocument(
                id=message_id,
                title=f"Message in {channel_name}",
                content=message,
                channel_id=channel_id,
                channel_name=channel_name,
                sender=sender,
                message=message,
                participants=participants or [],
                thread_id=thread_id,
                has_attachments=has_attachments,
                reactions=reactions or [],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                owner_id=owner_id,
                owner_name=owner_name,
                tags=tags or [],
                metadata=metadata or {},
            )

            await self.indexer.index_document(chat_doc)
            logger.debug(f"Indexed chat message: {message_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to index chat message {message_id}: {e}")
            return False

    async def index_messages_bulk(
        self,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, int]:
        """Bulk index chat messages."""
        chat_docs = []

        for msg_data in messages:
            try:
                chat_doc = ChatDocument(
                    id=msg_data["id"],
                    title=f"Message in {msg_data['channel_name']}",
                    content=msg_data.get("message", ""),
                    channel_id=msg_data["channel_id"],
                    channel_name=msg_data["channel_name"],
                    sender=msg_data["sender"],
                    message=msg_data.get("message", ""),
                    participants=msg_data.get("participants", []),
                    thread_id=msg_data.get("thread_id"),
                    has_attachments=msg_data.get("has_attachments", False),
                    reactions=msg_data.get("reactions", []),
                    created_at=msg_data.get("created_at", datetime.utcnow()),
                    updated_at=msg_data.get("updated_at", datetime.utcnow()),
                    owner_id=msg_data["owner_id"],
                    owner_name=msg_data["owner_name"],
                    tags=msg_data.get("tags", []),
                    metadata=msg_data.get("metadata", {}),
                )
                chat_docs.append(chat_doc)

            except Exception as e:
                logger.error(f"Failed to prepare chat message for indexing: {e}")

        return await self.indexer.index_documents_bulk(chat_docs)
