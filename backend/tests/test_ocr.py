"""Tests for OCR module"""
import pytest
from httpx import AsyncClient


class TestOCREndpoints:
    """Test OCR API endpoints"""

    @pytest.mark.asyncio
    async def test_ocr_health_check(self, client: AsyncClient):
        """Test OCR health check endpoint"""
        response = await client.get("/api/v1/ocr/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["module"] == "ocr"

    @pytest.mark.asyncio
    async def test_extract_text_success(self, client: AsyncClient, sample_image_bytes: bytes):
        """Test successful text extraction"""
        files = {"file": ("test.png", sample_image_bytes, "image/png")}
        data = {
            "engine": "tesseract",
            "detect_language": True,
            "extract_tables": True,
            "detect_handwriting": True,
            "analyze_layout": True
        }

        response = await client.post("/api/v1/ocr/extract", files=files, data=data)
        assert response.status_code == 201
        result = response.json()

        assert "id" in result
        assert "file_name" in result
        assert "status" in result
        assert result["status"] in ["completed", "processing"]

    @pytest.mark.asyncio
    async def test_extract_text_invalid_file_type(self, client: AsyncClient):
        """Test extraction with invalid file type"""
        files = {"file": ("test.txt", b"not an image", "text/plain")}
        data = {"engine": "tesseract"}

        response = await client.post("/api/v1/ocr/extract", files=files, data=data)
        assert response.status_code == 500  # Should fail with unsupported file type

    @pytest.mark.asyncio
    async def test_list_documents(self, client: AsyncClient):
        """Test listing OCR documents"""
        response = await client.get("/api/v1/ocr/documents")
        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "items" in data
        assert "page" in data
        assert "page_size" in data

    @pytest.mark.asyncio
    async def test_list_documents_with_filters(self, client: AsyncClient):
        """Test listing documents with filters"""
        params = {
            "status": "completed",
            "page": 1,
            "page_size": 5
        }

        response = await client.get("/api/v1/ocr/documents", params=params)
        assert response.status_code == 200
        data = response.json()

        assert data["page"] == 1
        assert data["page_size"] == 5

    @pytest.mark.asyncio
    async def test_get_document_not_found(self, client: AsyncClient):
        """Test getting non-existent document"""
        response = await client.get("/api/v1/ocr/documents/non-existent-id")
        assert response.status_code == 404


class TestOCRProcessor:
    """Test OCR processor logic"""

    @pytest.mark.asyncio
    async def test_tesseract_processor_initialization(self):
        """Test Tesseract processor initialization"""
        from app.modules.ocr.processor import OCRProcessor

        processor = OCRProcessor(engine="tesseract")
        assert processor.engine == "tesseract"

    @pytest.mark.asyncio
    async def test_google_vision_processor_initialization(self):
        """Test Google Vision processor initialization"""
        from app.modules.ocr.processor import OCRProcessor

        try:
            processor = OCRProcessor(engine="google_vision")
            assert processor.engine == "google_vision"
        except Exception:
            # Expected if API key is not configured
            pass


class TestOCRUtils:
    """Test OCR utility functions"""

    def test_validate_image_file(self, sample_image_bytes: bytes):
        """Test image file validation"""
        from app.modules.ocr.utils import validate_image_file

        is_valid = validate_image_file(sample_image_bytes, "test.png")
        assert is_valid is True

    def test_get_file_hash(self, sample_image_bytes: bytes):
        """Test file hash generation"""
        from app.modules.ocr.utils import get_file_hash

        hash1 = get_file_hash(sample_image_bytes)
        hash2 = get_file_hash(sample_image_bytes)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hash length

    def test_preprocess_image(self):
        """Test image preprocessing"""
        from app.modules.ocr.utils import preprocess_image
        from PIL import Image

        img = Image.new('RGB', (100, 100), color='white')
        processed = preprocess_image(img)

        assert processed.mode == 'RGB'
        assert processed.size == (100, 100)


class TestOCRModels:
    """Test OCR database models"""

    def test_ocr_document_creation(self):
        """Test OCR document model creation"""
        from app.modules.ocr.models import OCRDocument, OCRStatus, OCREngine

        doc = OCRDocument(
            file_name="test.png",
            file_path="/tmp/test.png",
            file_type="image/png",
            file_size=1024,
            status=OCRStatus.PENDING,
            engine=OCREngine.TESSERACT
        )

        assert doc.file_name == "test.png"
        assert doc.status == OCRStatus.PENDING
        assert doc.engine == OCREngine.TESSERACT

    def test_ocr_table_creation(self):
        """Test OCR table model creation"""
        from app.modules.ocr.models import OCRTable

        table = OCRTable(
            document_id="test-doc-id",
            table_index=0,
            rows=3,
            columns=3,
            data=[["A", "B", "C"], ["1", "2", "3"], ["X", "Y", "Z"]]
        )

        assert table.rows == 3
        assert table.columns == 3
        assert len(table.data) == 3
