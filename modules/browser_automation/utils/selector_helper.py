"""Element selector helper utilities"""
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


class SelectorHelper:
    """Helper class for working with element selectors"""

    @staticmethod
    def generate_css_selector(element_info: Dict[str, Any]) -> str:
        """Generate CSS selector from element info"""
        selectors = []

        # ID selector (highest priority)
        if element_info.get("id"):
            return f"#{element_info['id']}"

        # Class selector
        if element_info.get("classes"):
            classes = ".".join(element_info["classes"])
            selectors.append(f"{element_info.get('tag', '')}.{classes}")

        # Name selector
        if element_info.get("name"):
            selectors.append(f"[name='{element_info['name']}']")

        # Type selector
        if element_info.get("type"):
            selectors.append(f"[type='{element_info['type']}']")

        return selectors[0] if selectors else element_info.get("tag", "*")

    @staticmethod
    def generate_xpath_selector(element_info: Dict[str, Any]) -> str:
        """Generate XPath selector from element info"""
        # ID selector
        if element_info.get("id"):
            return f"//*[@id='{element_info['id']}']"

        # Build XPath parts
        parts = [element_info.get("tag", "*")]

        if element_info.get("classes"):
            class_conditions = [
                f"contains(@class, '{cls}')" for cls in element_info["classes"]
            ]
            parts.append(f"[{' and '.join(class_conditions)}]")

        if element_info.get("name"):
            parts.append(f"[@name='{element_info['name']}']")

        if element_info.get("type"):
            parts.append(f"[@type='{element_info['type']}']")

        return f"//{(''.join(parts))}"

    @staticmethod
    def extract_element_info_from_html(html: str, index: int = 0) -> Dict[str, Any]:
        """Extract element information from HTML"""
        soup = BeautifulSoup(html, "lxml")
        elements = soup.find_all()

        if index >= len(elements):
            return {}

        element = elements[index]

        return {
            "tag": element.name,
            "id": element.get("id"),
            "classes": element.get("class", []),
            "name": element.get("name"),
            "type": element.get("type"),
            "text": element.get_text(strip=True)[:100],
            "attributes": dict(element.attrs)
        }

    @staticmethod
    def validate_selector(selector: str, selector_type: str = "css") -> bool:
        """Validate if a selector is properly formatted"""
        if not selector or not selector.strip():
            return False

        if selector_type == "css":
            # Basic CSS selector validation
            invalid_chars = ["{", "}", ";"]
            return not any(char in selector for char in invalid_chars)

        elif selector_type == "xpath":
            # Basic XPath validation
            return selector.startswith("/") or selector.startswith("(")

        return True

    @staticmethod
    def suggest_selectors(html: str, text_content: Optional[str] = None) -> List[Dict[str, str]]:
        """Suggest multiple selector options for an element"""
        soup = BeautifulSoup(html, "lxml")
        suggestions = []

        # Find elements matching text content
        if text_content:
            elements = soup.find_all(string=lambda s: text_content in s if s else False)
            for elem in elements[:5]:  # Limit to 5 suggestions
                parent = elem.parent
                if parent:
                    info = {
                        "tag": parent.name,
                        "id": parent.get("id"),
                        "classes": parent.get("class", []),
                        "name": parent.get("name"),
                        "type": parent.get("type"),
                    }

                    css_selector = SelectorHelper.generate_css_selector(info)
                    xpath_selector = SelectorHelper.generate_xpath_selector(info)

                    suggestions.append({
                        "css": css_selector,
                        "xpath": xpath_selector,
                        "confidence": "high" if info.get("id") else "medium"
                    })

        return suggestions

    @staticmethod
    def optimize_selector(selector: str, selector_type: str = "css") -> str:
        """Optimize selector for better performance"""
        if selector_type == "css":
            # Remove redundant parts
            parts = selector.split()
            if len(parts) > 3:
                # Keep only the last 3 parts for specificity
                return " ".join(parts[-3:])

        return selector
