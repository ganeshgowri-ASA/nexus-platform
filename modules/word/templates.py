"""
Document Templates

Provides pre-built document templates for various use cases.
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import json


class TemplateCategory(Enum):
    """Template categories"""
    BUSINESS = "business"
    ACADEMIC = "academic"
    PERSONAL = "personal"
    LEGAL = "legal"
    CREATIVE = "creative"
    TECHNICAL = "technical"


@dataclass
class Template:
    """Document template"""
    template_id: str
    name: str
    description: str
    category: TemplateCategory
    content: Dict[str, Any]  # Quill Delta format
    thumbnail_url: Optional[str] = None
    tags: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class TemplateManager:
    """
    Template Manager for document templates.

    Provides a gallery of pre-built templates for various document types.
    """

    def __init__(self):
        """Initialize template manager with built-in templates"""
        self.templates: Dict[str, Template] = {}
        self._load_builtin_templates()

    def _load_builtin_templates(self) -> None:
        """Load built-in templates"""

        # Business Letter Template
        self.templates["business_letter"] = Template(
            template_id="business_letter",
            name="Business Letter",
            description="Professional business letter template",
            category=TemplateCategory.BUSINESS,
            content={"ops": [
                {"insert": "[Your Name]\n"},
                {"insert": "[Your Address]\n"},
                {"insert": "[City, State ZIP]\n"},
                {"insert": "[Email Address]\n"},
                {"insert": "[Phone Number]\n\n"},
                {"insert": "[Date]\n\n"},
                {"insert": "[Recipient Name]\n"},
                {"insert": "[Recipient Title]\n"},
                {"insert": "[Company Name]\n"},
                {"insert": "[Address]\n"},
                {"insert": "[City, State ZIP]\n\n"},
                {"insert": "Dear [Recipient Name],\n\n"},
                {"insert": "[Opening paragraph introducing the purpose of your letter]\n\n"},
                {"insert": "[Body paragraph providing details and context]\n\n"},
                {"insert": "[Closing paragraph with call to action or next steps]\n\n"},
                {"insert": "Sincerely,\n\n"},
                {"insert": "[Your Signature]\n"},
                {"insert": "[Your Typed Name]\n"}
            ]},
            tags=["letter", "business", "professional"]
        )

        # Resume/CV Template
        self.templates["resume"] = Template(
            template_id="resume",
            name="Resume / CV",
            description="Professional resume template",
            category=TemplateCategory.BUSINESS,
            content={"ops": [
                {"insert": "[YOUR NAME]", "attributes": {"header": 1, "bold": True}},
                {"insert": "\n"},
                {"insert": "[Email] | [Phone] | [Location] | [LinkedIn]\n\n"},
                {"insert": "PROFESSIONAL SUMMARY", "attributes": {"header": 2, "bold": True}},
                {"insert": "\n"},
                {"insert": "[2-3 sentences highlighting your experience, skills, and career objectives]\n\n"},
                {"insert": "EXPERIENCE", "attributes": {"header": 2, "bold": True}},
                {"insert": "\n"},
                {"insert": "[Job Title]", "attributes": {"bold": True}},
                {"insert": " | [Company Name] | [Dates]\n"},
                {"insert": "• [Key achievement or responsibility]\n"},
                {"insert": "• [Key achievement or responsibility]\n"},
                {"insert": "• [Key achievement or responsibility]\n\n"},
                {"insert": "EDUCATION", "attributes": {"header": 2, "bold": True}},
                {"insert": "\n"},
                {"insert": "[Degree]", "attributes": {"bold": True}},
                {"insert": " | [University] | [Graduation Date]\n"},
                {"insert": "[Major/Minor]\n\n"},
                {"insert": "SKILLS", "attributes": {"header": 2, "bold": True}},
                {"insert": "\n"},
                {"insert": "• [Skill category]: [Specific skills]\n"},
                {"insert": "• [Skill category]: [Specific skills]\n"}
            ]},
            tags=["resume", "cv", "job", "career"]
        )

        # Report Template
        self.templates["report"] = Template(
            template_id="report",
            name="Report",
            description="Formal report template",
            category=TemplateCategory.BUSINESS,
            content={"ops": [
                {"insert": "[REPORT TITLE]", "attributes": {"header": 1, "align": "center"}},
                {"insert": "\n"},
                {"insert": "[Subtitle or Report Type]", "attributes": {"align": "center"}},
                {"insert": "\n\n"},
                {"insert": "Prepared by: [Your Name]\n"},
                {"insert": "Date: [Date]\n\n"},
                {"insert": "EXECUTIVE SUMMARY", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Brief overview of the report's key findings and recommendations]\n\n"},
                {"insert": "1. INTRODUCTION", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Background and context for the report]\n\n"},
                {"insert": "2. METHODOLOGY", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[How the research/analysis was conducted]\n\n"},
                {"insert": "3. FINDINGS", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Main results and data]\n\n"},
                {"insert": "4. ANALYSIS", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Interpretation of findings]\n\n"},
                {"insert": "5. CONCLUSIONS", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Summary of key insights]\n\n"},
                {"insert": "6. RECOMMENDATIONS", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Actionable suggestions based on findings]\n"}
            ]},
            tags=["report", "business", "analysis"]
        )

        # Proposal Template
        self.templates["proposal"] = Template(
            template_id="proposal",
            name="Business Proposal",
            description="Business proposal template",
            category=TemplateCategory.BUSINESS,
            content={"ops": [
                {"insert": "[PROJECT/PROPOSAL TITLE]", "attributes": {"header": 1, "align": "center"}},
                {"insert": "\n\n"},
                {"insert": "Prepared for: [Client Name]\n"},
                {"insert": "Prepared by: [Your Name/Company]\n"},
                {"insert": "Date: [Date]\n\n"},
                {"insert": "EXECUTIVE SUMMARY", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Brief overview of the proposal and its value proposition]\n\n"},
                {"insert": "PROBLEM STATEMENT", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Description of the challenge or need]\n\n"},
                {"insert": "PROPOSED SOLUTION", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Your solution and approach]\n\n"},
                {"insert": "SCOPE OF WORK", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Detailed breakdown of deliverables and activities]\n\n"},
                {"insert": "TIMELINE", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Project schedule and milestones]\n\n"},
                {"insert": "BUDGET", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Cost breakdown and pricing]\n\n"},
                {"insert": "QUALIFICATIONS", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Your experience and credentials]\n\n"},
                {"insert": "NEXT STEPS", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[How to proceed and contact information]\n"}
            ]},
            tags=["proposal", "business", "project"]
        )

        # Meeting Notes Template
        self.templates["meeting_notes"] = Template(
            template_id="meeting_notes",
            name="Meeting Notes",
            description="Meeting notes and minutes template",
            category=TemplateCategory.BUSINESS,
            content={"ops": [
                {"insert": "MEETING NOTES", "attributes": {"header": 1}},
                {"insert": "\n\n"},
                {"insert": "Date: [Date]\n"},
                {"insert": "Time: [Time]\n"},
                {"insert": "Location: [Location/Platform]\n"},
                {"insert": "Attendees: [Names]\n"},
                {"insert": "Facilitator: [Name]\n"},
                {"insert": "Note-taker: [Name]\n\n"},
                {"insert": "AGENDA", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "1. [Topic]\n"},
                {"insert": "2. [Topic]\n"},
                {"insert": "3. [Topic]\n\n"},
                {"insert": "DISCUSSION POINTS", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Key points discussed during the meeting]\n\n"},
                {"insert": "DECISIONS MADE", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "• [Decision]\n"},
                {"insert": "• [Decision]\n\n"},
                {"insert": "ACTION ITEMS", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[ ] [Task] - Assigned to: [Name] - Due: [Date]\n"},
                {"insert": "[ ] [Task] - Assigned to: [Name] - Due: [Date]\n\n"},
                {"insert": "NEXT MEETING", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "Date: [Date]\n"},
                {"insert": "Topics: [Topics to discuss]\n"}
            ]},
            tags=["meeting", "notes", "minutes", "business"]
        )

        # Essay Template
        self.templates["essay"] = Template(
            template_id="essay",
            name="Academic Essay",
            description="Academic essay template",
            category=TemplateCategory.ACADEMIC,
            content={"ops": [
                {"insert": "[Essay Title]", "attributes": {"header": 1, "align": "center"}},
                {"insert": "\n\n"},
                {"insert": "[Your Name]\n", "attributes": {"align": "center"}},
                {"insert": "[Course Name/Number]\n", "attributes": {"align": "center"}},
                {"insert": "[Instructor Name]\n", "attributes": {"align": "center"}},
                {"insert": "[Date]\n\n", "attributes": {"align": "center"}},
                {"insert": "INTRODUCTION", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Hook or attention-grabber]\n"},
                {"insert": "[Background information]\n"},
                {"insert": "[Thesis statement]\n\n"},
                {"insert": "BODY PARAGRAPH 1", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Topic sentence]\n"},
                {"insert": "[Supporting evidence]\n"},
                {"insert": "[Analysis]\n"},
                {"insert": "[Transition]\n\n"},
                {"insert": "BODY PARAGRAPH 2", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Topic sentence]\n"},
                {"insert": "[Supporting evidence]\n"},
                {"insert": "[Analysis]\n"},
                {"insert": "[Transition]\n\n"},
                {"insert": "CONCLUSION", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Restate thesis]\n"},
                {"insert": "[Summarize main points]\n"},
                {"insert": "[Final thoughts or implications]\n\n"},
                {"insert": "REFERENCES", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Citation 1]\n"},
                {"insert": "[Citation 2]\n"}
            ]},
            tags=["essay", "academic", "writing", "school"]
        )

        # Invoice Template
        self.templates["invoice"] = Template(
            template_id="invoice",
            name="Invoice",
            description="Professional invoice template",
            category=TemplateCategory.BUSINESS,
            content={"ops": [
                {"insert": "INVOICE", "attributes": {"header": 1}},
                {"insert": "\n\n"},
                {"insert": "From:\n", "attributes": {"bold": True}},
                {"insert": "[Your Name/Company]\n"},
                {"insert": "[Address]\n"},
                {"insert": "[City, State ZIP]\n"},
                {"insert": "[Email]\n"},
                {"insert": "[Phone]\n\n"},
                {"insert": "To:\n", "attributes": {"bold": True}},
                {"insert": "[Client Name]\n"},
                {"insert": "[Address]\n"},
                {"insert": "[City, State ZIP]\n\n"},
                {"insert": "Invoice Number: ", "attributes": {"bold": True}},
                {"insert": "[Invoice #]\n"},
                {"insert": "Date: ", "attributes": {"bold": True}},
                {"insert": "[Date]\n"},
                {"insert": "Due Date: ", "attributes": {"bold": True}},
                {"insert": "[Due Date]\n\n"},
                {"insert": "ITEMS", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "Description                  Quantity    Rate        Amount\n"},
                {"insert": "─────────────────────────────────────────────────────────\n"},
                {"insert": "[Service/Product]            [Qty]       [$Rate]     [$Amount]\n"},
                {"insert": "[Service/Product]            [Qty]       [$Rate]     [$Amount]\n\n"},
                {"insert": "Subtotal:     $[Amount]\n", "attributes": {"align": "right"}},
                {"insert": "Tax (X%):     $[Amount]\n", "attributes": {"align": "right"}},
                {"insert": "TOTAL:        $[Amount]\n", "attributes": {"align": "right", "bold": True}},
                {"insert": "\n"},
                {"insert": "Payment Terms: [Terms]\n"},
                {"insert": "Payment Methods: [Methods]\n\n"},
                {"insert": "Thank you for your business!\n", "attributes": {"align": "center", "italic": True}}
            ]},
            tags=["invoice", "billing", "business", "payment"]
        )

        # Blog Post Template
        self.templates["blog_post"] = Template(
            template_id="blog_post",
            name="Blog Post",
            description="Blog post template",
            category=TemplateCategory.CREATIVE,
            content={"ops": [
                {"insert": "[Catchy Blog Title]", "attributes": {"header": 1}},
                {"insert": "\n"},
                {"insert": "[Subtitle or tagline]\n", "attributes": {"italic": True}},
                {"insert": "\n"},
                {"insert": "By [Author Name] | [Date] | [Reading Time] min read\n\n"},
                {"insert": "[Opening paragraph that hooks the reader]\n\n"},
                {"insert": "[Main topic heading]", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Content paragraph with valuable information]\n\n"},
                {"insert": "[Subtopic heading]", "attributes": {"header": 3}},
                {"insert": "\n"},
                {"insert": "[More detailed content]\n\n"},
                {"insert": "Key Takeaways:", "attributes": {"bold": True}},
                {"insert": "\n"},
                {"insert": "• [Point 1]\n"},
                {"insert": "• [Point 2]\n"},
                {"insert": "• [Point 3]\n\n"},
                {"insert": "Conclusion", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[Wrap up with final thoughts and call to action]\n\n"},
                {"insert": "Tags: [tag1] [tag2] [tag3]\n"}
            ]},
            tags=["blog", "content", "writing", "creative"]
        )

        # Technical Documentation Template
        self.templates["technical_doc"] = Template(
            template_id="technical_doc",
            name="Technical Documentation",
            description="Technical documentation template",
            category=TemplateCategory.TECHNICAL,
            content={"ops": [
                {"insert": "[API/Library/Tool Name]", "attributes": {"header": 1}},
                {"insert": "\n"},
                {"insert": "[Brief description]\n\n"},
                {"insert": "Table of Contents", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "1. Overview\n"},
                {"insert": "2. Installation\n"},
                {"insert": "3. Quick Start\n"},
                {"insert": "4. API Reference\n"},
                {"insert": "5. Examples\n"},
                {"insert": "6. Troubleshooting\n\n"},
                {"insert": "Overview", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "[What it does and why it's useful]\n\n"},
                {"insert": "Installation", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "pip install [package-name]\n", "attributes": {"code-block": True}},
                {"insert": "\n"},
                {"insert": "Quick Start", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "from [package] import [module]\n\n# Example code\n", "attributes": {"code-block": True}},
                {"insert": "\n"},
                {"insert": "API Reference", "attributes": {"header": 2}},
                {"insert": "\n"},
                {"insert": "ClassName", "attributes": {"header": 3}},
                {"insert": "\n"},
                {"insert": "[Description]\n\n"},
                {"insert": "Parameters:\n", "attributes": {"bold": True}},
                {"insert": "• param1 (type): description\n"},
                {"insert": "• param2 (type): description\n\n"},
                {"insert": "Returns:\n", "attributes": {"bold": True}},
                {"insert": "• type: description\n"}
            ]},
            tags=["documentation", "technical", "api", "code"]
        )

        # Cover Letter Template
        self.templates["cover_letter"] = Template(
            template_id="cover_letter",
            name="Cover Letter",
            description="Job application cover letter",
            category=TemplateCategory.BUSINESS,
            content={"ops": [
                {"insert": "[Your Name]\n"},
                {"insert": "[Your Address]\n"},
                {"insert": "[City, State ZIP]\n"},
                {"insert": "[Email] | [Phone]\n\n"},
                {"insert": "[Date]\n\n"},
                {"insert": "[Hiring Manager Name]\n"},
                {"insert": "[Company Name]\n"},
                {"insert": "[Company Address]\n\n"},
                {"insert": "Dear [Hiring Manager Name],\n\n"},
                {"insert": "[Opening paragraph: State the position you're applying for and how you heard about it. Include a compelling reason why you're interested.]\n\n"},
                {"insert": "[Second paragraph: Highlight your relevant experience and skills. Provide specific examples of achievements that match the job requirements.]\n\n"},
                {"insert": "[Third paragraph: Explain why you're a great fit for the company culture and values. Show knowledge of the company.]\n\n"},
                {"insert": "[Closing paragraph: Express enthusiasm, indicate your availability for an interview, and thank them for their consideration.]\n\n"},
                {"insert": "Sincerely,\n\n"},
                {"insert": "[Your Name]\n"}
            ]},
            tags=["cover letter", "job application", "career"]
        )

    def get_template(self, template_id: str) -> Optional[Template]:
        """
        Get a template by ID.

        Args:
            template_id: Template ID

        Returns:
            Template or None if not found
        """
        return self.templates.get(template_id)

    def get_all_templates(self) -> List[Template]:
        """
        Get all available templates.

        Returns:
            List of all templates
        """
        return list(self.templates.values())

    def get_templates_by_category(
        self,
        category: TemplateCategory
    ) -> List[Template]:
        """
        Get templates by category.

        Args:
            category: Template category

        Returns:
            List of templates in the category
        """
        return [
            template for template in self.templates.values()
            if template.category == category
        ]

    def search_templates(self, query: str) -> List[Template]:
        """
        Search templates by name, description, or tags.

        Args:
            query: Search query

        Returns:
            List of matching templates
        """
        query = query.lower()
        results = []

        for template in self.templates.values():
            if (query in template.name.lower() or
                query in template.description.lower() or
                any(query in tag.lower() for tag in template.tags)):
                results.append(template)

        return results

    def save_custom_template(
        self,
        name: str,
        description: str,
        category: TemplateCategory,
        content: Dict[str, Any],
        tags: Optional[List[str]] = None
    ) -> Template:
        """
        Save a custom template.

        Args:
            name: Template name
            description: Template description
            category: Template category
            content: Template content in Quill Delta format
            tags: Optional tags

        Returns:
            Created template
        """
        import uuid

        template_id = f"custom_{uuid.uuid4().hex[:8]}"

        template = Template(
            template_id=template_id,
            name=name,
            description=description,
            category=category,
            content=content,
            tags=tags or []
        )

        self.templates[template_id] = template
        return template

    def delete_template(self, template_id: str) -> bool:
        """
        Delete a custom template.

        Args:
            template_id: Template ID to delete

        Returns:
            True if deleted successfully
        """
        # Don't allow deletion of built-in templates
        if not template_id.startswith("custom_"):
            return False

        if template_id in self.templates:
            del self.templates[template_id]
            return True

        return False

    def get_template_categories(self) -> List[str]:
        """
        Get list of all template categories.

        Returns:
            List of category names
        """
        return [category.value for category in TemplateCategory]
