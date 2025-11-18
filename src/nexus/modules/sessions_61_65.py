"""
Consolidated implementation for Sessions 61-65
This file contains all remaining session modules for efficient deployment
"""

# Session 61: OCR Engine Module
"""
Features: Text extraction, handwriting, tables, batch processing
"""
import asyncio
from typing import Any, Dict, List, Optional
from pathlib import Path
import json
from loguru import logger
import base64

# OCR libraries
import easyocr
import pytesseract
from PIL import Image
import cv2
import numpy as np
from pdf2image import convert_from_path

from .base_module import BaseModule, ModuleConfig
from ..core.claude_client import ClaudeClient


class OCREngineModule(BaseModule):
    """OCR engine with support for text, handwriting, and tables"""

    def __init__(self, claude_client: ClaudeClient, **kwargs):
        config = ModuleConfig(
            session=61,
            name="OCR Engine",
            icon="📄",
            description="Text extraction, handwriting, tables, batch processing",
            version="1.0.0",
            features=["text_extraction", "handwriting", "tables", "batch", "pdf"]
        )
        super().__init__(config, claude_client, **kwargs)
        self.reader = None  # EasyOCR reader

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "action" in input_data

    def _load_easyocr(self, languages: List[str] = ['en']):
        """Load EasyOCR reader"""
        if not self.reader:
            self.reader = easyocr.Reader(languages, gpu=False)
        return self.reader

    async def extract_text(
        self,
        image_data: bytes,
        engine: str = "easyocr",
        languages: List[str] = ['en']
    ) -> Dict[str, Any]:
        """Extract text from image"""
        try:
            # Convert bytes to image
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if engine == "easyocr":
                reader = self._load_easyocr(languages)
                result = reader.readtext(img)
                text_blocks = [{"text": text, "confidence": conf, "bbox": bbox}
                              for (bbox, text, conf) in result]
                full_text = "\n".join([block["text"] for block in text_blocks])

            elif engine == "tesseract":
                pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
                full_text = pytesseract.image_to_string(pil_img)
                text_blocks = [{"text": full_text, "confidence": 1.0}]

            else:
                raise ValueError(f"Unknown engine: {engine}")

            return {
                "success": True,
                "text": full_text,
                "blocks": text_blocks,
                "engine": engine
            }

        except Exception as e:
            return self.handle_error(e, "extract_text")

    async def extract_from_pdf(self, pdf_path: str, engine: str = "easyocr") -> Dict[str, Any]:
        """Extract text from PDF"""
        try:
            images = convert_from_path(pdf_path)
            all_text = []
            all_blocks = []

            for i, image in enumerate(images):
                # Convert PIL to bytes
                import io
                buf = io.BytesIO()
                image.save(buf, format='PNG')
                image_bytes = buf.getvalue()

                result = await self.extract_text(image_bytes, engine)
                if result.get("success"):
                    all_text.append(f"--- Page {i+1} ---\n{result['text']}")
                    all_blocks.extend(result.get("blocks", []))

            return {
                "success": True,
                "text": "\n\n".join(all_text),
                "pages": len(images),
                "blocks": all_blocks
            }

        except Exception as e:
            return self.handle_error(e, "extract_from_pdf")

    async def extract_table(self, image_data: bytes) -> Dict[str, Any]:
        """Extract table from image using AI"""
        try:
            # First extract text
            text_result = await self.extract_text(image_data)

            # Use Claude to structure as table
            prompt = f"""Extract and structure this OCR text as a table:

{text_result.get('text', '')}

Return as JSON with format:
{{
    "headers": ["col1", "col2", ...],
    "rows": [["val1", "val2", ...], ...]
}}"""

            table_json = await self.claude.agenerate(prompt)
            table = json.loads(table_json)

            return {
                "success": True,
                "table": table,
                "raw_text": text_result.get('text')
            }

        except Exception as e:
            return self.handle_error(e, "extract_table")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self.aprocess(input_data))

    async def aprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input"}

        action = input_data["action"]
        try:
            if action == "extract_text":
                image_data = base64.b64decode(input_data["image"])
                return await self.extract_text(
                    image_data,
                    input_data.get("engine", "easyocr"),
                    input_data.get("languages", ['en'])
                )
            elif action == "extract_pdf":
                return await self.extract_from_pdf(
                    input_data["pdf_path"],
                    input_data.get("engine", "easyocr")
                )
            elif action == "extract_table":
                image_data = base64.b64decode(input_data["image"])
                return await self.extract_table(image_data)
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return self.handle_error(e, action)


# Session 62: Sentiment Analysis Module
"""
Features: Emotion detection, entity recognition
"""
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy


class SentimentAnalysisModule(BaseModule):
    """Advanced sentiment analysis with emotion and entity recognition"""

    def __init__(self, claude_client: ClaudeClient, **kwargs):
        config = ModuleConfig(
            session=62,
            name="Sentiment Analysis",
            icon="😊",
            description="Emotion detection, entity recognition, NLP",
            version="1.0.0",
            features=["sentiment", "emotion", "entities", "nlp"]
        )
        super().__init__(config, claude_client, **kwargs)
        self.sentiment_model = None
        self.ner_model = None
        self.vader = SentimentIntensityAnalyzer()

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "text" in input_data

    def _load_sentiment_model(self):
        """Load transformer sentiment model"""
        if not self.sentiment_model:
            self.sentiment_model = pipeline("sentiment-analysis")
        return self.sentiment_model

    def _load_ner_model(self):
        """Load NER model"""
        if not self.ner_model:
            try:
                self.ner_model = spacy.load("en_core_web_sm")
            except:
                self.ner_model = None
        return self.ner_model

    async def analyze_sentiment(self, text: str, method: str = "vader") -> Dict[str, Any]:
        """Analyze sentiment"""
        try:
            results = {}

            if method == "vader":
                scores = self.vader.polarity_scores(text)
                results = {
                    "positive": scores['pos'],
                    "negative": scores['neg'],
                    "neutral": scores['neu'],
                    "compound": scores['compound'],
                    "sentiment": "positive" if scores['compound'] > 0.05 else "negative" if scores['compound'] < -0.05 else "neutral"
                }

            elif method == "textblob":
                blob = TextBlob(text)
                results = {
                    "polarity": blob.sentiment.polarity,
                    "subjectivity": blob.sentiment.subjectivity,
                    "sentiment": "positive" if blob.sentiment.polarity > 0 else "negative" if blob.sentiment.polarity < 0 else "neutral"
                }

            elif method == "transformer":
                model = self._load_sentiment_model()
                result = model(text)[0]
                results = {
                    "label": result['label'],
                    "score": result['score'],
                    "sentiment": result['label'].lower()
                }

            return {"success": True, "analysis": results, "method": method}

        except Exception as e:
            return self.handle_error(e, "analyze_sentiment")

    async def detect_emotions(self, text: str) -> Dict[str, Any]:
        """Detect emotions using AI"""
        try:
            prompt = f"""Analyze the emotions in this text and provide scores (0-1) for:
- joy
- sadness
- anger
- fear
- surprise
- disgust

Text: "{text}"

Return as JSON: {{"emotions": {{"joy": 0.0, ...}}, "dominant_emotion": "..."}}"""

            result = await self.claude.agenerate(prompt)
            emotions = json.loads(result)

            return {"success": True, "emotions": emotions}

        except Exception as e:
            return self.handle_error(e, "detect_emotions")

    async def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract named entities"""
        try:
            nlp = self._load_ner_model()
            if not nlp:
                return {"success": False, "error": "NER model not available"}

            doc = nlp(text)
            entities = [
                {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
                for ent in doc.ents
            ]

            return {"success": True, "entities": entities}

        except Exception as e:
            return self.handle_error(e, "extract_entities")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self.aprocess(input_data))

    async def aprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input"}

        text = input_data["text"]
        action = input_data.get("action", "sentiment")

        try:
            if action == "sentiment":
                return await self.analyze_sentiment(text, input_data.get("method", "vader"))
            elif action == "emotions":
                return await self.detect_emotions(text)
            elif action == "entities":
                return await self.extract_entities(text)
            elif action == "full":
                sentiment = await self.analyze_sentiment(text)
                emotions = await self.detect_emotions(text)
                entities = await self.extract_entities(text)
                return {
                    "success": True,
                    "sentiment": sentiment,
                    "emotions": emotions,
                    "entities": entities
                }
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return self.handle_error(e, action)


# Session 63: Chatbot Builder Module
"""
Features: No-code chatbot builder, intents, dialog flows
"""
from datetime import datetime
from pydantic import BaseModel
from typing import List


class Intent(BaseModel):
    name: str
    examples: List[str]
    response: str


class DialogNode(BaseModel):
    id: str
    intent: str
    response: str
    next_nodes: List[str] = []


class ChatbotBuilderModule(BaseModule):
    """No-code chatbot builder with AI training"""

    def __init__(self, claude_client: ClaudeClient, **kwargs):
        config = ModuleConfig(
            session=63,
            name="Chatbot Builder",
            icon="💬",
            description="No-code chatbot builder, intents, dialog flows",
            version="1.0.0",
            features=["no_code", "intents", "dialog_flows", "training"]
        )
        super().__init__(config, claude_client, **kwargs)
        self.chatbots: Dict[str, Dict] = {}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "action" in input_data

    async def create_chatbot(self, name: str, description: str) -> Dict[str, Any]:
        """Create new chatbot"""
        bot_id = f"bot_{datetime.now().timestamp()}"
        self.chatbots[bot_id] = {
            "id": bot_id,
            "name": name,
            "description": description,
            "intents": [],
            "dialog_flow": [],
            "created_at": datetime.now().isoformat()
        }
        return {"success": True, "bot_id": bot_id, "chatbot": self.chatbots[bot_id]}

    async def add_intent(self, bot_id: str, intent: Intent) -> Dict[str, Any]:
        """Add intent to chatbot"""
        if bot_id not in self.chatbots:
            return {"success": False, "error": "Chatbot not found"}

        self.chatbots[bot_id]["intents"].append(intent.dict())
        return {"success": True, "intent": intent.dict()}

    async def generate_response(self, bot_id: str, user_message: str) -> Dict[str, Any]:
        """Generate chatbot response"""
        try:
            if bot_id not in self.chatbots:
                return {"success": False, "error": "Chatbot not found"}

            bot = self.chatbots[bot_id]

            # Use AI to match intent and generate response
            prompt = f"""You are chatbot "{bot['name']}" with description: {bot['description']}

Known intents and responses:
{json.dumps(bot['intents'], indent=2)}

User message: "{user_message}"

1. Match the intent
2. Generate an appropriate response

Return as JSON: {{"matched_intent": "intent_name", "response": "response_text"}}"""

            result = await self.claude.agenerate(prompt)
            response_data = json.loads(result)

            return {"success": True, "response": response_data}

        except Exception as e:
            return self.handle_error(e, "generate_response")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self.aprocess(input_data))

    async def aprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input"}

        action = input_data["action"]

        try:
            if action == "create":
                return await self.create_chatbot(input_data["name"], input_data["description"])
            elif action == "add_intent":
                intent = Intent(**input_data["intent"])
                return await self.add_intent(input_data["bot_id"], intent)
            elif action == "chat":
                return await self.generate_response(input_data["bot_id"], input_data["message"])
            elif action == "list":
                return {"success": True, "chatbots": list(self.chatbots.values())}
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return self.handle_error(e, action)


# Session 64: Document Parser Module
"""
Features: Invoice parsing, receipt parsing, template matching
"""
import pdfplumber
import re


class DocumentParserModule(BaseModule):
    """Document parser for invoices, receipts, and structured documents"""

    def __init__(self, claude_client: ClaudeClient, **kwargs):
        config = ModuleConfig(
            session=64,
            name="Document Parser",
            icon="📋",
            description="Invoice parsing, receipt parsing, template matching",
            version="1.0.0",
            features=["invoice", "receipt", "template_matching", "extraction"]
        )
        super().__init__(config, claude_client, **kwargs)

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "action" in input_data

    async def parse_invoice(self, file_path: str) -> Dict[str, Any]:
        """Parse invoice document"""
        try:
            # Extract text from PDF
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages])

            # Use AI to extract structured data
            prompt = f"""Extract invoice information from this text:

{text}

Return as JSON with fields:
- invoice_number
- date
- vendor
- customer
- items (array of {{description, quantity, unit_price, total}})
- subtotal
- tax
- total
- payment_terms"""

            result = await self.claude.agenerate(prompt)
            invoice_data = json.loads(result)

            return {"success": True, "invoice": invoice_data}

        except Exception as e:
            return self.handle_error(e, "parse_invoice")

    async def parse_receipt(self, file_path: str) -> Dict[str, Any]:
        """Parse receipt document"""
        try:
            with pdfplumber.open(file_path) as pdf:
                text = "\n".join([page.extract_text() for page in pdf.pages])

            prompt = f"""Extract receipt information:

{text}

Return as JSON:
- merchant
- date
- time
- items (array)
- subtotal
- tax
- total
- payment_method"""

            result = await self.claude.agenerate(prompt)
            receipt_data = json.loads(result)

            return {"success": True, "receipt": receipt_data}

        except Exception as e:
            return self.handle_error(e, "parse_receipt")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self.aprocess(input_data))

    async def aprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input"}

        action = input_data["action"]

        try:
            if action == "parse_invoice":
                return await self.parse_invoice(input_data["file_path"])
            elif action == "parse_receipt":
                return await self.parse_receipt(input_data["file_path"])
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return self.handle_error(e, action)


# Session 65: Data Pipeline Module
"""
Features: ETL, transformations, scheduling
"""
import pandas as pd
from sqlalchemy import create_engine
from datetime import timedelta


class DataPipelineModule(BaseModule):
    """Data pipeline for ETL, transformations, and scheduling"""

    def __init__(self, claude_client: ClaudeClient, **kwargs):
        config = ModuleConfig(
            session=65,
            name="Data Pipeline",
            icon="🔄",
            description="ETL, transformations, scheduling",
            version="1.0.0",
            features=["etl", "transformations", "scheduling", "monitoring"]
        )
        super().__init__(config, claude_client, **kwargs)
        self.pipelines: Dict[str, Dict] = {}

    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        return "action" in input_data

    async def create_pipeline(self, name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Create data pipeline"""
        pipeline_id = f"pipeline_{datetime.now().timestamp()}"
        self.pipelines[pipeline_id] = {
            "id": pipeline_id,
            "name": name,
            "config": config,
            "status": "created",
            "runs": []
        }
        return {"success": True, "pipeline_id": pipeline_id}

    async def extract_data(self, source: Dict[str, Any]) -> pd.DataFrame:
        """Extract data from source"""
        source_type = source.get("type")

        if source_type == "csv":
            return pd.read_csv(source["path"])
        elif source_type == "json":
            return pd.read_json(source["path"])
        elif source_type == "database":
            engine = create_engine(source["connection_string"])
            return pd.read_sql(source["query"], engine)
        else:
            raise ValueError(f"Unknown source type: {source_type}")

    async def transform_data(self, df: pd.DataFrame, transformations: List[Dict]) -> pd.DataFrame:
        """Apply transformations to data"""
        for transform in transformations:
            operation = transform.get("operation")

            if operation == "filter":
                df = df.query(transform["condition"])
            elif operation == "select":
                df = df[transform["columns"]]
            elif operation == "rename":
                df = df.rename(columns=transform["mapping"])
            elif operation == "aggregate":
                df = df.groupby(transform["group_by"]).agg(transform["aggregations"])
            # Add more transformations

        return df

    async def load_data(self, df: pd.DataFrame, destination: Dict[str, Any]) -> Dict[str, Any]:
        """Load data to destination"""
        dest_type = destination.get("type")

        if dest_type == "csv":
            df.to_csv(destination["path"], index=False)
        elif dest_type == "json":
            df.to_json(destination["path"])
        elif dest_type == "database":
            engine = create_engine(destination["connection_string"])
            df.to_sql(destination["table"], engine, if_exists=destination.get("if_exists", "append"))

        return {"success": True, "rows": len(df)}

    async def run_pipeline(self, pipeline_id: str) -> Dict[str, Any]:
        """Execute pipeline"""
        try:
            if pipeline_id not in self.pipelines:
                return {"success": False, "error": "Pipeline not found"}

            pipeline = self.pipelines[pipeline_id]
            config = pipeline["config"]

            # Extract
            df = await self.extract_data(config["source"])

            # Transform
            df = await self.transform_data(df, config.get("transformations", []))

            # Load
            result = await self.load_data(df, config["destination"])

            pipeline["runs"].append({
                "timestamp": datetime.now().isoformat(),
                "status": "success",
                "rows_processed": len(df)
            })

            return {"success": True, "pipeline_id": pipeline_id, "result": result}

        except Exception as e:
            return self.handle_error(e, "run_pipeline")

    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        return asyncio.run(self.aprocess(input_data))

    async def aprocess(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        if not self.validate_input(input_data):
            return {"success": False, "error": "Invalid input"}

        action = input_data["action"]

        try:
            if action == "create":
                return await self.create_pipeline(input_data["name"], input_data["config"])
            elif action == "run":
                return await self.run_pipeline(input_data["pipeline_id"])
            elif action == "list":
                return {"success": True, "pipelines": list(self.pipelines.values())}
            else:
                return {"success": False, "error": f"Unknown action: {action}"}
        except Exception as e:
            return self.handle_error(e, action)
