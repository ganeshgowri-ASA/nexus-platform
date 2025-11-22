"""Elasticsearch index schemas and mappings."""

from typing import Dict, Any
from .models import DocumentType


def get_base_mapping() -> Dict[str, Any]:
    """Get base mapping fields common to all document types."""
    return {
        "id": {"type": "keyword"},
        "type": {"type": "keyword"},
        "title": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "autocomplete": {
                    "type": "text",
                    "analyzer": "autocomplete",
                    "search_analyzer": "autocomplete_search",
                },
            },
        },
        "content": {
            "type": "text",
            "analyzer": "standard",
            "fields": {
                "english": {
                    "type": "text",
                    "analyzer": "english",
                }
            },
        },
        "created_at": {"type": "date"},
        "updated_at": {"type": "date"},
        "owner_id": {"type": "keyword"},
        "owner_name": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "tags": {"type": "keyword"},
        "metadata": {"type": "object", "enabled": False},
    }


def get_document_mapping() -> Dict[str, Any]:
    """Get mapping for document type."""
    mapping = get_base_mapping()
    mapping.update({
        "file_type": {"type": "keyword"},
        "file_size": {"type": "long"},
        "page_count": {"type": "integer"},
        "language": {"type": "keyword"},
    })
    return {"properties": mapping}


def get_email_mapping() -> Dict[str, Any]:
    """Get mapping for email type."""
    mapping = get_base_mapping()
    mapping.update({
        "sender": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "recipients": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "cc": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "bcc": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "subject": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "autocomplete": {
                    "type": "text",
                    "analyzer": "autocomplete",
                    "search_analyzer": "autocomplete_search",
                },
            },
        },
        "has_attachments": {"type": "boolean"},
        "attachment_names": {"type": "text"},
        "importance": {"type": "keyword"},
        "folder": {"type": "keyword"},
    })
    return {"properties": mapping}


def get_file_mapping() -> Dict[str, Any]:
    """Get mapping for file type."""
    mapping = get_base_mapping()
    mapping.update({
        "file_name": {
            "type": "text",
            "fields": {
                "keyword": {"type": "keyword"},
                "autocomplete": {
                    "type": "text",
                    "analyzer": "autocomplete",
                    "search_analyzer": "autocomplete_search",
                },
            },
        },
        "file_path": {"type": "keyword"},
        "file_type": {"type": "keyword"},
        "file_size": {"type": "long"},
        "mime_type": {"type": "keyword"},
        "extension": {"type": "keyword"},
        "parent_folder": {"type": "keyword"},
    })
    return {"properties": mapping}


def get_chat_mapping() -> Dict[str, Any]:
    """Get mapping for chat type."""
    mapping = get_base_mapping()
    mapping.update({
        "channel_id": {"type": "keyword"},
        "channel_name": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "sender": {
            "type": "text",
            "fields": {"keyword": {"type": "keyword"}},
        },
        "message": {
            "type": "text",
            "analyzer": "standard",
        },
        "participants": {"type": "keyword"},
        "thread_id": {"type": "keyword"},
        "has_attachments": {"type": "boolean"},
        "reactions": {"type": "keyword"},
    })
    return {"properties": mapping}


class SchemaManager:
    """Manage Elasticsearch schemas for different document types."""

    SCHEMA_MAPPING = {
        DocumentType.DOCUMENT: get_document_mapping,
        DocumentType.EMAIL: get_email_mapping,
        DocumentType.FILE: get_file_mapping,
        DocumentType.CHAT: get_chat_mapping,
        DocumentType.SPREADSHEET: get_document_mapping,
        DocumentType.PRESENTATION: get_document_mapping,
        DocumentType.PROJECT: get_document_mapping,
        DocumentType.NOTE: get_document_mapping,
    }

    @classmethod
    def get_mapping(cls, doc_type: DocumentType) -> Dict[str, Any]:
        """Get mapping for a document type."""
        mapper = cls.SCHEMA_MAPPING.get(doc_type)
        if not mapper:
            raise ValueError(f"No mapping defined for document type: {doc_type}")
        return mapper()

    @classmethod
    def get_all_mappings(cls) -> Dict[DocumentType, Dict[str, Any]]:
        """Get all mappings."""
        return {
            doc_type: mapper()
            for doc_type, mapper in cls.SCHEMA_MAPPING.items()
        }
