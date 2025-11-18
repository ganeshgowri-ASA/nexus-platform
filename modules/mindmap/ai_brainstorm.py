"""
AI-Powered Brainstorming and Mind Map Generation

This module provides AI capabilities for generating mind maps from text,
suggesting ideas, organizing thoughts, and extracting structure.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Any, TYPE_CHECKING, Tuple
from enum import Enum
import re
import uuid

if TYPE_CHECKING:
    from .nodes import MindMapNode


class AIFeature(Enum):
    """Available AI features."""
    GENERATE_FROM_TEXT = "generate_from_text"
    SUGGEST_IDEAS = "suggest_ideas"
    ORGANIZE_THOUGHTS = "organize_thoughts"
    EXTRACT_STRUCTURE = "extract_structure"
    EXPAND_NODE = "expand_node"
    SUMMARIZE = "summarize"
    FIND_CONNECTIONS = "find_connections"
    CATEGORIZE = "categorize"


class AIBrainstormEngine:
    """
    AI-powered brainstorming engine.

    Features:
    - Generate mind maps from text
    - Suggest related ideas
    - Auto-organize nodes
    - Extract hierarchical structure
    - Find connections between ideas
    - Expand nodes with related content
    """

    def __init__(self, ai_provider: Optional[Any] = None):
        """
        Initialize the AI engine.

        Args:
            ai_provider: Optional AI provider (Claude, GPT, etc.)
                        If None, uses rule-based fallbacks
        """
        self.ai_provider = ai_provider
        self.cache: Dict[str, Any] = {}

    def generate_mindmap_from_text(
        self, text: str, root_text: Optional[str] = None
    ) -> tuple[Dict[str, MindMapNode], str]:
        """
        Generate a complete mind map from input text.

        Args:
            text: Input text to analyze
            root_text: Optional custom root node text

        Returns:
            Tuple of (nodes_dict, root_id)
        """
        from .nodes import MindMapNode, Position

        nodes: Dict[str, MindMapNode] = {}

        # Extract main topics and structure
        structure = self._extract_structure_from_text(text)

        # Create root node
        root_text = root_text or structure.get("title", "Main Topic")
        root_id = str(uuid.uuid4())
        root = MindMapNode(
            text=root_text,
            node_id=root_id,
            position=Position(0, 0)
        )
        nodes[root_id] = root

        # Create child nodes
        for topic in structure.get("topics", []):
            self._add_topic_as_branch(nodes, root_id, topic)

        return nodes, root_id

    def _extract_structure_from_text(self, text: str) -> Dict[str, Any]:
        """
        Extract hierarchical structure from text.

        This is a rule-based implementation. With AI provider,
        this would use NLP to understand context better.
        """
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        structure = {
            "title": "Mind Map",
            "topics": [],
        }

        # Try to detect title (first line or marked with #)
        if lines:
            first_line = lines[0]
            if first_line.startswith("#"):
                structure["title"] = first_line.lstrip("#").strip()
                lines = lines[1:]
            else:
                structure["title"] = first_line
                lines = lines[1:]

        # Extract topics (lines starting with bullet points or numbers)
        current_topic = None

        for line in lines:
            # Detect main topics (-, *, or numbers)
            if line.startswith(("-", "*", "•")) or re.match(r"^\d+\.", line):
                topic_text = re.sub(r"^[-*•]\s*|\d+\.\s*", "", line)
                current_topic = {
                    "text": topic_text,
                    "subtopics": [],
                }
                structure["topics"].append(current_topic)

            # Detect subtopics (indented)
            elif line.startswith(("  ", "\t")) and current_topic:
                subtopic_text = re.sub(r"^[-*•]\s*|\d+\.\s*", "", line.strip())
                current_topic["subtopics"].append({
                    "text": subtopic_text,
                    "subtopics": [],
                })

            # Regular line - add as topic if we don't have many yet
            elif len(structure["topics"]) < 10:
                structure["topics"].append({
                    "text": line,
                    "subtopics": [],
                })

        return structure

    def _add_topic_as_branch(
        self,
        nodes: Dict[str, MindMapNode],
        parent_id: str,
        topic: Dict[str, Any],
    ) -> str:
        """Add a topic and its subtopics as nodes."""
        from .nodes import MindMapNode, Position

        # Create node for this topic
        node_id = str(uuid.uuid4())
        node = MindMapNode(
            text=topic["text"],
            node_id=node_id,
            parent_id=parent_id,
            position=Position(0, 0)
        )
        nodes[node_id] = node

        # Add to parent's children
        if parent_id in nodes:
            nodes[parent_id].add_child(node_id)

        # Recursively add subtopics
        for subtopic in topic.get("subtopics", []):
            self._add_topic_as_branch(nodes, node_id, subtopic)

        return node_id

    def suggest_related_ideas(
        self, node_text: str, context: Optional[List[str]] = None, count: int = 5
    ) -> List[str]:
        """
        Suggest related ideas for a node.

        Args:
            node_text: Text of the current node
            context: Optional context from other nodes
            count: Number of suggestions to generate

        Returns:
            List of suggested idea texts
        """
        if self.ai_provider:
            return self._ai_suggest_ideas(node_text, context, count)

        # Fallback: rule-based suggestions
        return self._rule_based_suggestions(node_text, count)

    def _rule_based_suggestions(self, node_text: str, count: int) -> List[str]:
        """Generate suggestions using rules (fallback)."""
        suggestions = []

        # Common brainstorming prompts
        prompts = [
            f"What are the benefits of {node_text}?",
            f"What are the challenges with {node_text}?",
            f"How can we improve {node_text}?",
            f"What alternatives exist to {node_text}?",
            f"What are examples of {node_text}?",
            f"Why is {node_text} important?",
            f"Who is involved in {node_text}?",
            f"When should we consider {node_text}?",
        ]

        return prompts[:count]

    def _ai_suggest_ideas(
        self, node_text: str, context: Optional[List[str]], count: int
    ) -> List[str]:
        """Use AI provider to suggest ideas."""
        # Placeholder for AI integration
        # In production, this would call Claude API
        prompt = f"""Given the topic: "{node_text}"

Context: {', '.join(context) if context else 'None'}

Suggest {count} related ideas or subtopics that would make good branches in a mind map.
Return only the ideas, one per line."""

        # Would integrate with AI provider here
        return self._rule_based_suggestions(node_text, count)

    def expand_node_with_ai(
        self, node: MindMapNode, expansion_type: str = "general"
    ) -> List[str]:
        """
        Expand a node with AI-generated content.

        Args:
            node: Node to expand
            expansion_type: Type of expansion (general, detailed, creative, analytical)

        Returns:
            List of suggested child node texts
        """
        expansion_prompts = {
            "general": f"What are key aspects of {node.text}?",
            "detailed": f"Break down {node.text} into detailed components",
            "creative": f"What creative ideas relate to {node.text}?",
            "analytical": f"Analyze {node.text} from different perspectives",
        }

        prompt = expansion_prompts.get(expansion_type, expansion_prompts["general"])

        # Generate suggestions
        suggestions = self.suggest_related_ideas(node.text, count=6)
        return suggestions

    def organize_nodes_by_category(
        self, nodes: Dict[str, MindMapNode]
    ) -> Dict[str, List[str]]:
        """
        Automatically categorize nodes by topic/theme.

        Returns:
            Dictionary mapping category names to lists of node IDs
        """
        categories: Dict[str, List[str]] = {
            "Action Items": [],
            "Ideas": [],
            "Questions": [],
            "Resources": [],
            "Other": [],
        }

        for node_id, node in nodes.items():
            text = node.text.lower()

            # Categorize based on keywords and patterns
            if any(word in text for word in ["todo", "task", "action", "need to"]):
                categories["Action Items"].append(node_id)
            elif "?" in text or text.startswith(("how", "what", "why", "when", "where")):
                categories["Questions"].append(node_id)
            elif any(word in text for word in ["link", "resource", "reference", "doc"]):
                categories["Resources"].append(node_id)
            elif any(word in text for word in ["idea", "concept", "thought"]):
                categories["Ideas"].append(node_id)
            else:
                categories["Other"].append(node_id)

        # Remove empty categories
        return {k: v for k, v in categories.items() if v}

    def find_connections(
        self, nodes: Dict[str, MindMapNode]
    ) -> List[Tuple[str, str, str]]:
        """
        Find potential connections between nodes.

        Returns:
            List of tuples (source_id, target_id, reason)
        """
        connections = []

        node_list = list(nodes.items())

        # Simple keyword-based connection detection
        for i, (id1, node1) in enumerate(node_list):
            for id2, node2 in node_list[i + 1 :]:
                # Skip if already connected
                if id2 in node1.children_ids or id1 in node2.children_ids:
                    continue

                # Find common keywords
                words1 = set(node1.text.lower().split())
                words2 = set(node2.text.lower().split())
                common = words1 & words2

                # Remove common words
                common = common - {
                    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"
                }

                if common:
                    reason = f"Shared keywords: {', '.join(common)}"
                    connections.append((id1, id2, reason))

                # Check for question-answer patterns
                if "?" in node1.text and len(node2.text) > 20:
                    connections.append((id1, id2, "Potential answer"))

        return connections

    def summarize_branch(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> str:
        """
        Generate a summary of a branch and its children.

        Args:
            nodes: All nodes
            root_id: Root of the branch to summarize

        Returns:
            Summary text
        """
        root = nodes.get(root_id)
        if not root:
            return ""

        # Collect all texts in this branch
        texts = [root.text]

        def collect_texts(node_id: str):
            if node_id in nodes:
                node = nodes[node_id]
                for child_id in node.children_ids:
                    if child_id in nodes:
                        texts.append(nodes[child_id].text)
                        collect_texts(child_id)

        collect_texts(root_id)

        # Create summary
        if len(texts) == 1:
            return texts[0]

        summary = f"{root.text} encompasses {len(texts)-1} subtopics including: "
        summary += ", ".join(texts[1:min(4, len(texts))])

        if len(texts) > 4:
            summary += f", and {len(texts)-4} more"

        return summary

    def extract_key_concepts(self, text: str) -> List[str]:
        """
        Extract key concepts from text.

        Returns:
            List of key concepts/phrases
        """
        # Simple extraction - would be more sophisticated with NLP
        lines = [line.strip() for line in text.split("\n") if line.strip()]

        concepts = []

        for line in lines:
            # Remove common prefixes
            cleaned = re.sub(r"^[-*•\d\.]+\s*", "", line)

            # Extract capitalized words or phrases
            capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", cleaned)
            concepts.extend(capitalized)

            # Extract quoted text
            quoted = re.findall(r'"([^"]+)"', cleaned)
            concepts.extend(quoted)

        return list(set(concepts))[:10]  # Return unique, limited

    def generate_outline(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> str:
        """
        Generate a text outline from the mind map.

        Args:
            nodes: All nodes
            root_id: Root node

        Returns:
            Formatted outline text
        """
        lines = []

        def add_node_to_outline(node_id: str, level: int = 0):
            if node_id not in nodes:
                return

            node = nodes[node_id]
            indent = "  " * level
            marker = "•" if level > 0 else "■"

            lines.append(f"{indent}{marker} {node.text}")

            # Add notes if present
            if node.notes:
                lines.append(f"{indent}  → {node.notes}")

            # Add children
            for child_id in node.children_ids:
                add_node_to_outline(child_id, level + 1)

        add_node_to_outline(root_id)
        return "\n".join(lines)

    def suggest_reorganization(
        self, nodes: Dict[str, MindMapNode], root_id: str
    ) -> Dict[str, Any]:
        """
        Suggest a better organization for the mind map.

        Returns:
            Dictionary with reorganization suggestions
        """
        suggestions = {
            "categories": self.organize_nodes_by_category(nodes),
            "connections": self.find_connections(nodes),
            "summary": self.summarize_branch(nodes, root_id),
        }

        # Analyze depth and breadth
        max_depth = 0
        max_breadth = 0

        def analyze_tree(node_id: str, depth: int = 0):
            nonlocal max_depth, max_breadth
            if node_id not in nodes:
                return

            max_depth = max(max_depth, depth)
            node = nodes[node_id]
            max_breadth = max(max_breadth, len(node.children_ids))

            for child_id in node.children_ids:
                analyze_tree(child_id, depth + 1)

        analyze_tree(root_id)

        suggestions["analysis"] = {
            "max_depth": max_depth,
            "max_breadth": max_breadth,
            "total_nodes": len(nodes),
        }

        # Provide recommendations
        recommendations = []
        if max_depth > 5:
            recommendations.append("Consider flattening deep branches")
        if max_breadth > 8:
            recommendations.append("Consider grouping related nodes into categories")
        if len(nodes) < 3:
            recommendations.append("Expand with more details and subtopics")

        suggestions["recommendations"] = recommendations

        return suggestions

    def smart_auto_complete(self, partial_text: str, context: List[str]) -> List[str]:
        """
        Provide smart auto-completion suggestions.

        Args:
            partial_text: Partial text being typed
            context: Context from nearby nodes

        Returns:
            List of completion suggestions
        """
        suggestions = []

        # Complete common phrases
        common_completions = {
            "what": ["What are the benefits?", "What are the challenges?", "What is the goal?"],
            "how": ["How can we improve?", "How does it work?", "How to implement?"],
            "why": ["Why is this important?", "Why should we consider this?"],
        }

        partial_lower = partial_text.lower()
        for key, completions in common_completions.items():
            if partial_lower.startswith(key):
                suggestions.extend(completions)

        # Add context-based suggestions
        if context:
            for ctx in context[:3]:
                suggestions.append(f"{partial_text} related to {ctx}")

        return suggestions[:5]
