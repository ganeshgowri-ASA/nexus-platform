"""
Document Classification Module

Provides AI-powered document classification, content type detection,
and smart filing suggestions.

Features:
- Automatic document classification
- Content type detection
- Smart filing suggestions
- Category management
- Confidence scoring
- Machine learning-based classification
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any, Set
from datetime import datetime
from enum import Enum
import json

logger = logging.getLogger(__name__)


class ClassificationType(Enum):
    """Types of document classification."""
    INVOICE = "invoice"
    CONTRACT = "contract"
    REPORT = "report"
    LETTER = "letter"
    MEMO = "memo"
    FORM = "form"
    RECEIPT = "receipt"
    EMAIL = "email"
    LEGAL = "legal"
    FINANCIAL = "financial"
    TECHNICAL = "technical"
    MARKETING = "marketing"
    HR = "hr"
    OTHER = "other"


class ContentType(Enum):
    """Content types for documents."""
    TEXT = "text"
    IMAGE = "image"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    ARCHIVE = "archive"
    CODE = "code"
    DATA = "data"
    MIXED = "mixed"


class ClassificationResult:
    """
    Result of document classification.
    """

    def __init__(
        self,
        classification: ClassificationType,
        confidence: float,
        content_type: ContentType,
        suggested_category: Optional[str] = None,
        suggested_tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize classification result.

        Args:
            classification: Detected document classification
            confidence: Confidence score (0.0 to 1.0)
            content_type: Detected content type
            suggested_category: Suggested filing category
            suggested_tags: Suggested tags for the document
            metadata: Additional classification metadata
        """
        self.classification = classification
        self.confidence = confidence
        self.content_type = content_type
        self.suggested_category = suggested_category
        self.suggested_tags = suggested_tags or []
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'classification': self.classification.value,
            'confidence': self.confidence,
            'content_type': self.content_type.value,
            'suggested_category': self.suggested_category,
            'suggested_tags': self.suggested_tags,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClassificationResult':
        """Create result from dictionary."""
        result = cls(
            classification=ClassificationType(data['classification']),
            confidence=data['confidence'],
            content_type=ContentType(data['content_type']),
            suggested_category=data.get('suggested_category'),
            suggested_tags=data.get('suggested_tags', []),
            metadata=data.get('metadata', {})
        )
        result.timestamp = datetime.fromisoformat(data['timestamp'])
        return result


class ClassificationRule:
    """
    Rule-based classification pattern.
    """

    def __init__(
        self,
        name: str,
        classification: ClassificationType,
        patterns: List[str],
        keywords: Optional[List[str]] = None,
        min_confidence: float = 0.6,
        weight: float = 1.0
    ):
        """
        Initialize classification rule.

        Args:
            name: Rule name
            classification: Target classification
            patterns: Regular expression patterns to match
            keywords: Keywords that indicate this classification
            min_confidence: Minimum confidence threshold
            weight: Weight of this rule in scoring
        """
        self.name = name
        self.classification = classification
        self.patterns = [re.compile(p, re.IGNORECASE) for p in patterns]
        self.keywords = [k.lower() for k in (keywords or [])]
        self.min_confidence = min_confidence
        self.weight = weight

    def evaluate(self, text: str) -> float:
        """
        Evaluate how well the text matches this rule.

        Args:
            text: Text to evaluate

        Returns:
            Confidence score (0.0 to 1.0)
        """
        score = 0.0
        text_lower = text.lower()

        # Check patterns
        pattern_matches = sum(1 for p in self.patterns if p.search(text))
        if self.patterns:
            pattern_score = (pattern_matches / len(self.patterns)) * 0.6
            score += pattern_score

        # Check keywords
        keyword_matches = sum(1 for k in self.keywords if k in text_lower)
        if self.keywords:
            keyword_score = min(keyword_matches / len(self.keywords), 1.0) * 0.4
            score += keyword_score

        return min(score * self.weight, 1.0)


class DocumentClassifier:
    """
    Main document classification engine.

    Uses a combination of rule-based and heuristic approaches
    to classify documents and suggest filing locations.
    """

    def __init__(
        self,
        custom_rules: Optional[List[ClassificationRule]] = None,
        enable_ml: bool = False,
        model_path: Optional[str] = None
    ):
        """
        Initialize document classifier.

        Args:
            custom_rules: Custom classification rules
            enable_ml: Enable machine learning classification
            model_path: Path to ML model (if enabled)
        """
        self.custom_rules = custom_rules or []
        self.enable_ml = enable_ml
        self.model_path = model_path

        # Initialize default rules
        self.rules = self._create_default_rules()
        self.rules.extend(self.custom_rules)

        # Category mapping for smart filing
        self.category_mapping: Dict[ClassificationType, str] = {
            ClassificationType.INVOICE: "Finance/Invoices",
            ClassificationType.RECEIPT: "Finance/Receipts",
            ClassificationType.CONTRACT: "Legal/Contracts",
            ClassificationType.LEGAL: "Legal/General",
            ClassificationType.REPORT: "Reports",
            ClassificationType.LETTER: "Correspondence/Letters",
            ClassificationType.EMAIL: "Correspondence/Emails",
            ClassificationType.MEMO: "Internal/Memos",
            ClassificationType.HR: "HR",
            ClassificationType.MARKETING: "Marketing",
            ClassificationType.TECHNICAL: "Technical",
            ClassificationType.FINANCIAL: "Finance/General",
            ClassificationType.FORM: "Forms",
            ClassificationType.OTHER: "Uncategorized"
        }

        logger.info(f"DocumentClassifier initialized with {len(self.rules)} rules")

    def classify(
        self,
        file_path: Union[str, Path],
        text_content: Optional[str] = None
    ) -> ClassificationResult:
        """
        Classify a document.

        Args:
            file_path: Path to the document
            text_content: Optional pre-extracted text content

        Returns:
            ClassificationResult

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Classifying document: {file_path.name}")

        # Extract text if not provided
        if text_content is None:
            text_content = self._extract_text(file_path)

        # Detect content type
        content_type = self._detect_content_type(file_path)

        # Run classification
        if self.enable_ml and self.model_path:
            classification, confidence = self._classify_with_ml(text_content)
        else:
            classification, confidence = self._classify_with_rules(text_content)

        # Generate filing suggestions
        suggested_category = self._suggest_category(classification, file_path)
        suggested_tags = self._suggest_tags(classification, text_content)

        # Extract metadata
        metadata = self._extract_metadata(text_content, classification)

        result = ClassificationResult(
            classification=classification,
            confidence=confidence,
            content_type=content_type,
            suggested_category=suggested_category,
            suggested_tags=suggested_tags,
            metadata=metadata
        )

        logger.info(
            f"Classification: {classification.value} "
            f"(confidence: {confidence:.2%}, content: {content_type.value})"
        )

        return result

    def _classify_with_rules(self, text: str) -> Tuple[ClassificationType, float]:
        """
        Classify using rule-based approach.

        Args:
            text: Document text

        Returns:
            Tuple of (classification, confidence)
        """
        scores: Dict[ClassificationType, float] = {}

        # Evaluate all rules
        for rule in self.rules:
            score = rule.evaluate(text)

            if score >= rule.min_confidence:
                current_score = scores.get(rule.classification, 0.0)
                scores[rule.classification] = max(current_score, score)

        # Get best classification
        if scores:
            best_classification = max(scores.items(), key=lambda x: x[1])
            return best_classification[0], best_classification[1]
        else:
            return ClassificationType.OTHER, 0.3

    def _classify_with_ml(self, text: str) -> Tuple[ClassificationType, float]:
        """
        Classify using machine learning model.

        Args:
            text: Document text

        Returns:
            Tuple of (classification, confidence)
        """
        # This is a placeholder for ML-based classification
        # In production, this would use a trained model (sklearn, transformers, etc.)

        logger.warning("ML classification not fully implemented, using rules")
        return self._classify_with_rules(text)

    def _detect_content_type(self, file_path: Path) -> ContentType:
        """Detect content type based on file extension and characteristics."""
        extension = file_path.suffix.lower()

        # Mapping of extensions to content types
        type_mapping = {
            # Text documents
            '.txt': ContentType.TEXT,
            '.md': ContentType.TEXT,
            '.doc': ContentType.TEXT,
            '.docx': ContentType.TEXT,
            '.odt': ContentType.TEXT,
            '.rtf': ContentType.TEXT,
            '.pdf': ContentType.TEXT,

            # Images
            '.jpg': ContentType.IMAGE,
            '.jpeg': ContentType.IMAGE,
            '.png': ContentType.IMAGE,
            '.gif': ContentType.IMAGE,
            '.bmp': ContentType.IMAGE,
            '.tiff': ContentType.IMAGE,
            '.svg': ContentType.IMAGE,

            # Spreadsheets
            '.xls': ContentType.SPREADSHEET,
            '.xlsx': ContentType.SPREADSHEET,
            '.ods': ContentType.SPREADSHEET,
            '.csv': ContentType.SPREADSHEET,

            # Presentations
            '.ppt': ContentType.PRESENTATION,
            '.pptx': ContentType.PRESENTATION,
            '.odp': ContentType.PRESENTATION,

            # Archives
            '.zip': ContentType.ARCHIVE,
            '.tar': ContentType.ARCHIVE,
            '.gz': ContentType.ARCHIVE,
            '.rar': ContentType.ARCHIVE,
            '.7z': ContentType.ARCHIVE,

            # Code
            '.py': ContentType.CODE,
            '.js': ContentType.CODE,
            '.java': ContentType.CODE,
            '.cpp': ContentType.CODE,
            '.c': ContentType.CODE,
            '.html': ContentType.CODE,
            '.css': ContentType.CODE,

            # Data
            '.json': ContentType.DATA,
            '.xml': ContentType.DATA,
            '.yaml': ContentType.DATA,
            '.sql': ContentType.DATA,
        }

        return type_mapping.get(extension, ContentType.MIXED)

    def _extract_text(self, file_path: Path) -> str:
        """
        Extract text content from document.

        Args:
            file_path: Path to document

        Returns:
            Extracted text
        """
        try:
            # Import text extractor from conversion module
            from .conversion import TextExtractor

            extractor = TextExtractor()
            return extractor.extract(file_path, use_ocr=False)

        except Exception as e:
            logger.warning(f"Text extraction failed: {e}")

            # Fallback: try simple text read
            try:
                return file_path.read_text(encoding='utf-8', errors='ignore')
            except:
                return ""

    def _suggest_category(
        self,
        classification: ClassificationType,
        file_path: Path
    ) -> str:
        """Suggest filing category based on classification."""
        base_category = self.category_mapping.get(classification, "Uncategorized")

        # Enhance with date-based organization for certain types
        if classification in [ClassificationType.INVOICE, ClassificationType.RECEIPT]:
            year = datetime.now().year
            month = datetime.now().month
            return f"{base_category}/{year}/{month:02d}"

        return base_category

    def _suggest_tags(
        self,
        classification: ClassificationType,
        text: str
    ) -> List[str]:
        """Suggest tags based on classification and content."""
        tags = [classification.value]

        # Add tags based on classification type
        if classification == ClassificationType.INVOICE:
            tags.extend(self._extract_invoice_tags(text))
        elif classification == ClassificationType.CONTRACT:
            tags.extend(self._extract_contract_tags(text))
        elif classification == ClassificationType.FINANCIAL:
            tags.extend(self._extract_financial_tags(text))

        # Add general tags
        if 'urgent' in text.lower() or 'priority' in text.lower():
            tags.append('urgent')

        if 'confidential' in text.lower() or 'private' in text.lower():
            tags.append('confidential')

        return list(set(tags))  # Remove duplicates

    def _extract_invoice_tags(self, text: str) -> List[str]:
        """Extract tags from invoice content."""
        tags = []

        # Look for payment status
        if re.search(r'\bpaid\b', text, re.IGNORECASE):
            tags.append('paid')
        elif re.search(r'\bunpaid\b|\bdue\b', text, re.IGNORECASE):
            tags.append('unpaid')

        # Look for amount patterns
        if re.search(r'\$[\d,]+\.?\d*', text):
            tags.append('has-amount')

        return tags

    def _extract_contract_tags(self, text: str) -> List[str]:
        """Extract tags from contract content."""
        tags = []

        # Look for contract types
        contract_types = [
            'employment', 'service', 'lease', 'purchase',
            'nda', 'confidentiality', 'partnership'
        ]

        for ctype in contract_types:
            if ctype in text.lower():
                tags.append(ctype)

        return tags

    def _extract_financial_tags(self, text: str) -> List[str]:
        """Extract tags from financial content."""
        tags = []

        financial_terms = [
            'budget', 'forecast', 'statement', 'balance',
            'revenue', 'expense', 'profit', 'loss'
        ]

        for term in financial_terms:
            if term in text.lower():
                tags.append(term)

        return tags

    def _extract_metadata(
        self,
        text: str,
        classification: ClassificationType
    ) -> Dict[str, Any]:
        """Extract relevant metadata from document content."""
        metadata = {}

        # Extract dates
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}-\d{1,2}-\d{4}',  # MM-DD-YYYY
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                metadata['dates_found'] = matches[:5]  # First 5 dates
                break

        # Extract email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        if emails:
            metadata['emails'] = emails[:3]  # First 3 emails

        # Extract phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        phones = re.findall(phone_pattern, text)
        if phones:
            metadata['phone_numbers'] = phones[:3]

        # Extract amounts (for financial documents)
        if classification in [ClassificationType.INVOICE, ClassificationType.FINANCIAL, ClassificationType.RECEIPT]:
            amount_pattern = r'\$\s*[\d,]+\.?\d{0,2}'
            amounts = re.findall(amount_pattern, text)
            if amounts:
                metadata['amounts'] = amounts[:5]

        # Extract invoice numbers (for invoices)
        if classification == ClassificationType.INVOICE:
            invoice_pattern = r'invoice\s*#?\s*(\w+)'
            matches = re.findall(invoice_pattern, text, re.IGNORECASE)
            if matches:
                metadata['invoice_number'] = matches[0]

        # Extract document numbers
        doc_pattern = r'(?:document|ref|reference)\s*#?\s*(\w+)'
        matches = re.findall(doc_pattern, text, re.IGNORECASE)
        if matches:
            metadata['reference_number'] = matches[0]

        return metadata

    def _create_default_rules(self) -> List[ClassificationRule]:
        """Create default classification rules."""
        return [
            # Invoice rules
            ClassificationRule(
                name="invoice_pattern",
                classification=ClassificationType.INVOICE,
                patterns=[
                    r'invoice\s+#?\d+',
                    r'total\s+amount\s+due',
                    r'payment\s+terms',
                ],
                keywords=['invoice', 'bill', 'amount due', 'payment'],
                weight=1.2
            ),

            # Receipt rules
            ClassificationRule(
                name="receipt_pattern",
                classification=ClassificationType.RECEIPT,
                patterns=[
                    r'receipt\s+#?\d+',
                    r'thank\s+you\s+for\s+your\s+purchase',
                ],
                keywords=['receipt', 'purchase', 'transaction', 'paid'],
                weight=1.1
            ),

            # Contract rules
            ClassificationRule(
                name="contract_pattern",
                classification=ClassificationType.CONTRACT,
                patterns=[
                    r'this\s+agreement',
                    r'whereas',
                    r'parties\s+agree',
                    r'terms\s+and\s+conditions',
                ],
                keywords=['agreement', 'contract', 'party', 'whereas', 'hereby'],
                weight=1.3
            ),

            # Legal document rules
            ClassificationRule(
                name="legal_pattern",
                classification=ClassificationType.LEGAL,
                patterns=[
                    r'pursuant\s+to',
                    r'aforementioned',
                    r'legal\s+notice',
                ],
                keywords=['legal', 'law', 'court', 'attorney', 'plaintiff', 'defendant'],
                weight=1.2
            ),

            # Report rules
            ClassificationRule(
                name="report_pattern",
                classification=ClassificationType.REPORT,
                patterns=[
                    r'executive\s+summary',
                    r'quarterly\s+report',
                    r'annual\s+report',
                ],
                keywords=['report', 'analysis', 'findings', 'conclusion', 'summary'],
                weight=1.0
            ),

            # Letter rules
            ClassificationRule(
                name="letter_pattern",
                classification=ClassificationType.LETTER,
                patterns=[
                    r'dear\s+[A-Z]',
                    r'sincerely',
                    r'yours\s+truly',
                ],
                keywords=['dear', 'sincerely', 'regards', 'yours'],
                weight=1.0
            ),

            # Memo rules
            ClassificationRule(
                name="memo_pattern",
                classification=ClassificationType.MEMO,
                patterns=[
                    r'memorandum',
                    r'to:\s+.+\nfrom:',
                    r'subject:',
                ],
                keywords=['memo', 'memorandum', 'internal'],
                weight=1.1
            ),

            # Financial rules
            ClassificationRule(
                name="financial_pattern",
                classification=ClassificationType.FINANCIAL,
                patterns=[
                    r'balance\s+sheet',
                    r'profit\s+and\s+loss',
                    r'financial\s+statement',
                ],
                keywords=['financial', 'revenue', 'expense', 'budget', 'forecast'],
                weight=1.1
            ),

            # Form rules
            ClassificationRule(
                name="form_pattern",
                classification=ClassificationType.FORM,
                patterns=[
                    r'application\s+form',
                    r'please\s+complete',
                    r'signature\s*:?\s*_+',
                ],
                keywords=['form', 'application', 'please fill', 'signature'],
                weight=1.0
            ),
        ]

    def add_custom_rule(self, rule: ClassificationRule) -> None:
        """
        Add a custom classification rule.

        Args:
            rule: ClassificationRule to add
        """
        self.rules.append(rule)
        logger.info(f"Added custom rule: {rule.name}")

    def set_category_mapping(
        self,
        classification: ClassificationType,
        category: str
    ) -> None:
        """
        Set custom category mapping for a classification type.

        Args:
            classification: Classification type
            category: Target category path
        """
        self.category_mapping[classification] = category
        logger.info(f"Updated category mapping: {classification.value} -> {category}")


class CategoryManager:
    """
    Manages document categories and filing structure.
    """

    def __init__(self, storage_path: Union[str, Path]):
        """
        Initialize category manager.

        Args:
            storage_path: Path to category storage
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.categories_file = self.storage_path / "categories.json"
        self.categories: Dict[str, Dict[str, Any]] = {}

        self._load_categories()

        logger.info(f"CategoryManager initialized with {len(self.categories)} categories")

    def create_category(
        self,
        name: str,
        description: Optional[str] = None,
        parent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a new category.

        Args:
            name: Category name
            description: Category description
            parent: Parent category path
            metadata: Additional metadata

        Returns:
            Created category data
        """
        category = {
            'name': name,
            'description': description,
            'parent': parent,
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'document_count': 0
        }

        self.categories[name] = category
        self._save_categories()

        logger.info(f"Category created: {name}")

        return category

    def get_category(self, name: str) -> Optional[Dict[str, Any]]:
        """Get category by name."""
        return self.categories.get(name)

    def list_categories(self, parent: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List categories, optionally filtered by parent.

        Args:
            parent: Parent category to filter by

        Returns:
            List of categories
        """
        if parent is None:
            return list(self.categories.values())

        return [
            cat for cat in self.categories.values()
            if cat.get('parent') == parent
        ]

    def delete_category(self, name: str) -> bool:
        """
        Delete a category.

        Args:
            name: Category name

        Returns:
            True if deleted, False if not found
        """
        if name not in self.categories:
            return False

        del self.categories[name]
        self._save_categories()

        logger.info(f"Category deleted: {name}")

        return True

    def increment_document_count(self, name: str) -> None:
        """Increment document count for a category."""
        if name in self.categories:
            self.categories[name]['document_count'] += 1
            self._save_categories()

    def _load_categories(self) -> None:
        """Load categories from storage."""
        if not self.categories_file.exists():
            return

        try:
            with open(self.categories_file, 'r') as f:
                self.categories = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load categories: {e}")

    def _save_categories(self) -> None:
        """Save categories to storage."""
        try:
            with open(self.categories_file, 'w') as f:
                json.dump(self.categories, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save categories: {e}")


# Convenience functions
def classify_document(
    file_path: Union[str, Path],
    text_content: Optional[str] = None
) -> ClassificationResult:
    """
    Convenience function to classify a document.

    Args:
        file_path: Path to document
        text_content: Optional pre-extracted text

    Returns:
        ClassificationResult
    """
    classifier = DocumentClassifier()
    return classifier.classify(file_path, text_content)


def detect_content_type(file_path: Union[str, Path]) -> ContentType:
    """
    Convenience function to detect content type.

    Args:
        file_path: Path to document

    Returns:
        ContentType
    """
    classifier = DocumentClassifier()
    return classifier._detect_content_type(Path(file_path))
