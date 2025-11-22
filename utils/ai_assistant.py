"""
AI Assistant utility for NEXUS Platform
Provides Claude AI integration for all modules
"""
import os
from anthropic import Anthropic
from typing import Optional, Dict, Any
import streamlit as st


class AIAssistant:
    """Claude AI Assistant for NEXUS modules"""

    def __init__(self):
        """Initialize AI Assistant with API key"""
        api_key = os.getenv('ANTHROPIC_API_KEY') or st.secrets.get('ANTHROPIC_API_KEY', '')
        if api_key:
            self.client = Anthropic(api_key=api_key)
            self.available = True
        else:
            self.available = False

    def generate(self, prompt: str, context: str = "", max_tokens: int = 4096) -> str:
        """
        Generate AI response

        Args:
            prompt: User prompt
            context: Additional context
            max_tokens: Maximum tokens to generate

        Returns:
            Generated response
        """
        if not self.available:
            return "AI Assistant is not available. Please configure your ANTHROPIC_API_KEY."

        try:
            full_prompt = f"{context}\n\n{prompt}" if context else prompt

            message = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                messages=[
                    {"role": "user", "content": full_prompt}
                ]
            )

            return message.content[0].text
        except Exception as e:
            return f"Error generating AI response: {str(e)}"

    def analyze_code(self, code: str, language: str = "") -> str:
        """Analyze code and provide insights"""
        prompt = f"Analyze this {language} code and provide insights:\n\n```{language}\n{code}\n```"
        return self.generate(prompt)

    def generate_flowchart(self, description: str) -> str:
        """Generate Mermaid flowchart from description"""
        prompt = f"""Generate a Mermaid flowchart diagram based on this description:
{description}

Provide only the Mermaid syntax, starting with 'graph TD' or similar."""
        return self.generate(prompt)

    def generate_mindmap(self, topic: str) -> Dict[str, Any]:
        """Generate mind map structure from topic"""
        prompt = f"""Create a mind map structure for the topic: {topic}

Provide a JSON structure with nodes and connections. Format:
{{
    "root": "topic name",
    "branches": [
        {{
            "name": "branch name",
            "children": ["child1", "child2"]
        }}
    ]
}}"""
        response = self.generate(prompt)
        try:
            import json
            # Extract JSON from response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"root": topic, "branches": []}

    def suggest_infographic_layout(self, data_type: str, content: str) -> str:
        """Suggest infographic layout and design"""
        prompt = f"""Suggest an effective infographic layout for:
Data Type: {data_type}
Content: {content}

Provide design recommendations including layout, colors, and visual elements."""
        return self.generate(prompt)

    def optimize_gantt_schedule(self, tasks: list) -> str:
        """Optimize Gantt chart schedule"""
        prompt = f"""Analyze this project schedule and suggest optimizations:
{tasks}

Focus on:
1. Critical path identification
2. Resource leveling opportunities
3. Schedule optimization
4. Risk areas"""
        return self.generate(prompt)

    def generate_sql_query(self, natural_language: str, schema: str = "") -> str:
        """Generate SQL query from natural language"""
        context = f"Database Schema:\n{schema}\n\n" if schema else ""
        prompt = f"Convert this to a SQL query: {natural_language}"
        return self.generate(prompt, context)

    def generate_api_test(self, endpoint: str, method: str, description: str) -> Dict[str, Any]:
        """Generate API test cases"""
        prompt = f"""Generate test cases for this API endpoint:
Endpoint: {endpoint}
Method: {method}
Description: {description}

Provide JSON format with test cases including headers, body, and assertions."""
        response = self.generate(prompt)
        try:
            import json
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"tests": []}

    def suggest_code_improvements(self, code: str, language: str) -> str:
        """Suggest code improvements"""
        prompt = f"""Review this {language} code and suggest improvements:

```{language}
{code}
```

Focus on:
1. Code quality
2. Performance
3. Best practices
4. Security"""
        return self.generate(prompt)

    def generate_website_content(self, purpose: str, style: str) -> Dict[str, Any]:
        """Generate website content and structure"""
        prompt = f"""Generate website content for:
Purpose: {purpose}
Style: {style}

Provide JSON with:
- page structure
- content sections
- suggested copy
- SEO recommendations"""
        response = self.generate(prompt)
        try:
            import json
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except:
            pass
        return {"pages": [], "content": {}}

    def generate_blog_post(self, topic: str, keywords: list, tone: str = "professional") -> str:
        """Generate blog post content"""
        prompt = f"""Write a blog post about: {topic}
Keywords: {', '.join(keywords)}
Tone: {tone}

Include:
- Engaging title
- Introduction
- Main content with subheadings
- Conclusion
- Meta description for SEO"""
        return self.generate(prompt, max_tokens=8000)


# Global AI assistant instance
ai_assistant = AIAssistant()
