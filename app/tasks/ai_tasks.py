"""
AI Request Tasks for Nexus Platform
Handles Claude AI and OpenAI API requests asynchronously
"""
from typing import Dict, Any, List, Optional
import logging
from celery import Task
from config.celery_config import celery_app
from config.settings import settings

logger = logging.getLogger(__name__)


class AITask(Task):
    """Base class for AI tasks with retry logic and rate limiting"""
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3, 'countdown': 10}
    retry_backoff = True
    rate_limit = '10/m'  # 10 requests per minute


@celery_app.task(base=AITask, bind=True, name='app.tasks.ai_tasks.claude_completion')
def claude_completion(
    self,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate completion using Claude AI

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0 to 1.0)
        model: Model to use (defaults to settings.AI_MODEL_CLAUDE)

    Returns:
        AI response with metadata
    """
    try:
        from anthropic import Anthropic

        client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        model = model or settings.AI_MODEL_CLAUDE

        messages = [{"role": "user", "content": prompt}]

        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        response = client.messages.create(**kwargs)

        result = {
            'status': 'success',
            'model': model,
            'content': response.content[0].text,
            'usage': {
                'input_tokens': response.usage.input_tokens,
                'output_tokens': response.usage.output_tokens
            },
            'stop_reason': response.stop_reason
        }

        logger.info(f"Claude completion successful. Tokens: {response.usage.output_tokens}")
        return result

    except Exception as e:
        logger.error(f"Claude API error: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(base=AITask, bind=True, name='app.tasks.ai_tasks.openai_completion')
def openai_completion(
    self,
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 4096,
    temperature: float = 1.0,
    model: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate completion using OpenAI

    Args:
        prompt: User prompt
        system_prompt: Optional system prompt
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature
        model: Model to use (defaults to settings.AI_MODEL_GPT)

    Returns:
        AI response with metadata
    """
    try:
        from openai import OpenAI

        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        model = model or settings.AI_MODEL_GPT

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature
        )

        result = {
            'status': 'success',
            'model': model,
            'content': response.choices[0].message.content,
            'usage': {
                'prompt_tokens': response.usage.prompt_tokens,
                'completion_tokens': response.usage.completion_tokens,
                'total_tokens': response.usage.total_tokens
            },
            'finish_reason': response.choices[0].finish_reason
        }

        logger.info(f"OpenAI completion successful. Tokens: {response.usage.total_tokens}")
        return result

    except Exception as e:
        logger.error(f"OpenAI API error: {str(e)}")
        raise self.retry(exc=e)


@celery_app.task(base=AITask, bind=True, name='app.tasks.ai_tasks.analyze_document')
def analyze_document(
    self,
    document_text: str,
    analysis_type: str = 'summary',
    custom_instructions: Optional[str] = None
) -> Dict[str, Any]:
    """
    Analyze document content using AI

    Args:
        document_text: Text content to analyze
        analysis_type: Type of analysis (summary, key_points, sentiment, etc.)
        custom_instructions: Optional custom analysis instructions

    Returns:
        Analysis results
    """
    analysis_prompts = {
        'summary': 'Provide a concise summary of the following document:\n\n',
        'key_points': 'Extract the key points from the following document:\n\n',
        'sentiment': 'Analyze the sentiment and tone of the following document:\n\n',
        'action_items': 'Extract action items and tasks from the following document:\n\n',
        'questions': 'Generate relevant questions about the following document:\n\n'
    }

    prompt = analysis_prompts.get(analysis_type, '')
    if custom_instructions:
        prompt = custom_instructions + '\n\n'

    prompt += document_text

    # Use Claude for document analysis
    return claude_completion(
        prompt=prompt,
        system_prompt="You are an expert document analyst. Provide clear, structured analysis."
    )


@celery_app.task(base=AITask, bind=True, name='app.tasks.ai_tasks.generate_content')
def generate_content(
    self,
    content_type: str,
    topic: str,
    additional_context: Optional[Dict[str, Any]] = None,
    length: str = 'medium'
) -> Dict[str, Any]:
    """
    Generate content using AI

    Args:
        content_type: Type of content (email, blog, presentation, report, etc.)
        topic: Topic or subject
        additional_context: Additional context or requirements
        length: Desired length (short, medium, long)

    Returns:
        Generated content
    """
    length_specs = {
        'short': '1-2 paragraphs',
        'medium': '3-5 paragraphs',
        'long': '6-10 paragraphs'
    }

    content_templates = {
        'email': f'Write a professional email about: {topic}. Length: {length_specs.get(length, "medium")}.',
        'blog': f'Write a blog post about: {topic}. Length: {length_specs.get(length, "medium")}.',
        'presentation': f'Create an outline for a presentation about: {topic}.',
        'report': f'Write a detailed report about: {topic}.',
        'social_media': f'Write engaging social media content about: {topic}. Keep it concise.'
    }

    prompt = content_templates.get(content_type, f'Generate content about: {topic}')

    if additional_context:
        prompt += f'\n\nAdditional context: {additional_context}'

    return claude_completion(
        prompt=prompt,
        system_prompt=f"You are an expert content creator specializing in {content_type}."
    )


@celery_app.task(base=AITask, bind=True, name='app.tasks.ai_tasks.translate_text')
def translate_text(
    self,
    text: str,
    target_language: str,
    source_language: Optional[str] = None
) -> Dict[str, Any]:
    """
    Translate text to target language using AI

    Args:
        text: Text to translate
        target_language: Target language
        source_language: Source language (optional, will auto-detect)

    Returns:
        Translation result
    """
    if source_language:
        prompt = f'Translate the following text from {source_language} to {target_language}:\n\n{text}'
    else:
        prompt = f'Translate the following text to {target_language}:\n\n{text}'

    return claude_completion(
        prompt=prompt,
        system_prompt="You are an expert translator. Provide accurate, natural-sounding translations."
    )


@celery_app.task(base=AITask, bind=True, name='app.tasks.ai_tasks.chat_completion')
def chat_completion(
    self,
    messages: List[Dict[str, str]],
    model: str = 'claude',
    max_tokens: int = 4096
) -> Dict[str, Any]:
    """
    Multi-turn chat completion

    Args:
        messages: List of message dicts with 'role' and 'content'
        model: AI model to use ('claude' or 'openai')
        max_tokens: Maximum tokens to generate

    Returns:
        Chat response
    """
    # Extract last user message
    user_messages = [m for m in messages if m['role'] == 'user']
    if not user_messages:
        raise ValueError("No user messages found")

    last_message = user_messages[-1]['content']

    # Build context from previous messages
    context = '\n'.join([
        f"{m['role'].upper()}: {m['content']}"
        for m in messages[:-1]
    ])

    system_prompt = "You are a helpful AI assistant in the Nexus productivity platform."
    if context:
        system_prompt += f"\n\nPrevious conversation:\n{context}"

    if model == 'claude':
        return claude_completion(
            prompt=last_message,
            system_prompt=system_prompt,
            max_tokens=max_tokens
        )
    else:
        return openai_completion(
            prompt=last_message,
            system_prompt=system_prompt,
            max_tokens=max_tokens
        )


@celery_app.task(base=AITask, bind=True, name='app.tasks.ai_tasks.batch_ai_requests')
def batch_ai_requests(self, requests: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process multiple AI requests in batch

    Args:
        requests: List of AI request configurations

    Returns:
        Batch processing results
    """
    from celery import group

    task_group = []
    for req in requests:
        task_type = req.get('task_type')
        params = req.get('params', {})

        if task_type == 'completion':
            task_group.append(claude_completion.s(**params))
        elif task_type == 'analyze':
            task_group.append(analyze_document.s(**params))
        elif task_type == 'generate':
            task_group.append(generate_content.s(**params))
        elif task_type == 'translate':
            task_group.append(translate_text.s(**params))

    if task_group:
        job = group(task_group)
        result = job.apply_async()

        return {
            'status': 'processing',
            'total_requests': len(requests),
            'group_id': result.id
        }

    return {
        'status': 'error',
        'message': 'No valid requests provided'
    }
