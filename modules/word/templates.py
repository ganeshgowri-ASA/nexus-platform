"""
<<<<<<< HEAD
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
=======
Document templates for Word Editor module.
"""
from typing import Dict
from datetime import datetime


class DocumentTemplates:
    """Pre-defined document templates."""

    @staticmethod
    def get_template(template_name: str, **kwargs) -> str:
        """
        Get a document template.

        Args:
            template_name: Name of the template
            **kwargs: Template variables

        Returns:
            Template content
        """
        templates = {
            "blank": DocumentTemplates.blank_document,
            "business_letter": DocumentTemplates.business_letter,
            "resume": DocumentTemplates.resume,
            "report": DocumentTemplates.report,
            "meeting_notes": DocumentTemplates.meeting_notes,
            "project_proposal": DocumentTemplates.project_proposal,
            "essay": DocumentTemplates.essay,
            "cover_letter": DocumentTemplates.cover_letter,
        }

        template_func = templates.get(template_name.lower().replace(" ", "_"))
        if template_func:
            return template_func(**kwargs)
        return DocumentTemplates.blank_document()

    @staticmethod
    def blank_document(**kwargs) -> str:
        """Blank document template."""
        return ""

    @staticmethod
    def business_letter(**kwargs) -> str:
        """Business letter template."""
        today = datetime.now().strftime("%B %d, %Y")
        sender_name = kwargs.get("sender_name", "[Your Name]")
        sender_title = kwargs.get("sender_title", "[Your Title]")
        sender_company = kwargs.get("sender_company", "[Your Company]")
        sender_address = kwargs.get("sender_address", "[Your Address]")
        recipient_name = kwargs.get("recipient_name", "[Recipient Name]")
        recipient_title = kwargs.get("recipient_title", "[Recipient Title]")
        recipient_company = kwargs.get("recipient_company", "[Recipient Company]")
        recipient_address = kwargs.get("recipient_address", "[Recipient Address]")

        return f"""{sender_name}
{sender_title}
{sender_company}
{sender_address}

{today}

{recipient_name}
{recipient_title}
{recipient_company}
{recipient_address}

Dear {recipient_name},

[Opening paragraph: State the purpose of your letter]

[Body paragraph 1: Provide relevant details and information]

[Body paragraph 2: Continue with additional points or elaboration]

[Closing paragraph: Summarize and include a call to action]

Sincerely,

{sender_name}
{sender_title}"""

    @staticmethod
    def resume(**kwargs) -> str:
        """Resume template."""
        name = kwargs.get("name", "[Your Name]")
        email = kwargs.get("email", "[your.email@example.com]")
        phone = kwargs.get("phone", "[Your Phone Number]")
        location = kwargs.get("location", "[City, State]")

        return f"""# {name}

{email} | {phone} | {location}

## Professional Summary

[2-3 sentences highlighting your key qualifications, experience, and career objectives]

## Experience

### [Job Title] | [Company Name]
*[Start Date] - [End Date]*

- [Key achievement or responsibility]
- [Key achievement or responsibility]
- [Key achievement or responsibility]

### [Job Title] | [Company Name]
*[Start Date] - [End Date]*

- [Key achievement or responsibility]
- [Key achievement or responsibility]
- [Key achievement or responsibility]

## Education

### [Degree] in [Field of Study]
**[University Name]** | [Graduation Year]

- [Honors, GPA, or relevant coursework]

## Skills

- **Technical Skills:** [List relevant technical skills]
- **Languages:** [List languages and proficiency levels]
- **Certifications:** [List relevant certifications]

## Projects

### [Project Name]
[Brief description of the project and your role]

### [Project Name]
[Brief description of the project and your role]"""

    @staticmethod
    def report(**kwargs) -> str:
        """Report template."""
        title = kwargs.get("title", "[Report Title]")
        author = kwargs.get("author", "[Author Name]")
        today = datetime.now().strftime("%B %d, %Y")

        return f"""# {title}

**Author:** {author}
**Date:** {today}

---

## Executive Summary

[Provide a brief overview of the report's purpose, key findings, and recommendations]

## Table of Contents

1. Introduction
2. Background
3. Methodology
4. Findings
5. Analysis
6. Recommendations
7. Conclusion

---

## 1. Introduction

[Introduce the topic, purpose, and scope of the report]

## 2. Background

[Provide context and relevant background information]

## 3. Methodology

[Describe the methods used to gather and analyze information]

## 4. Findings

[Present the key findings from your research or analysis]

### 4.1 Finding One

[Details about the first finding]

### 4.2 Finding Two

[Details about the second finding]

## 5. Analysis

[Analyze and interpret the findings]

## 6. Recommendations

[Provide actionable recommendations based on the findings]

1. [Recommendation 1]
2. [Recommendation 2]
3. [Recommendation 3]

## 7. Conclusion

[Summarize the report and reiterate key points]

---

## Appendices

### Appendix A: [Title]

[Additional supporting information]"""

    @staticmethod
    def meeting_notes(**kwargs) -> str:
        """Meeting notes template."""
        meeting_title = kwargs.get("title", "[Meeting Title]")
        today = datetime.now().strftime("%B %d, %Y")
        time = kwargs.get("time", "[Meeting Time]")

        return f"""# {meeting_title}

**Date:** {today}
**Time:** {time}
**Location:** [Meeting Location/Platform]
**Attendees:** [List of attendees]

---

## Agenda

1. [Agenda item 1]
2. [Agenda item 2]
3. [Agenda item 3]

---

## Discussion Points

### [Topic 1]

- [Key point discussed]
- [Key point discussed]

### [Topic 2]

- [Key point discussed]
- [Key point discussed]

---

## Decisions Made

1. [Decision 1]
2. [Decision 2]

---

## Action Items

| Task | Assigned To | Due Date | Status |
|------|-------------|----------|--------|
| [Task description] | [Name] | [Date] | [Status] |
| [Task description] | [Name] | [Date] | [Status] |

---

## Next Meeting

**Date:** [Next meeting date]
**Agenda:** [Brief description of next meeting topics]"""

    @staticmethod
    def project_proposal(**kwargs) -> str:
        """Project proposal template."""
        project_title = kwargs.get("title", "[Project Title]")
        author = kwargs.get("author", "[Author Name]")
        today = datetime.now().strftime("%B %d, %Y")

        return f"""# {project_title}

**Prepared by:** {author}
**Date:** {today}

---

## Executive Summary

[Provide a concise overview of the project, its objectives, and expected outcomes]

## Problem Statement

[Describe the problem or opportunity this project addresses]

## Objectives

1. [Objective 1]
2. [Objective 2]
3. [Objective 3]

## Scope

### In Scope
- [Item 1]
- [Item 2]

### Out of Scope
- [Item 1]
- [Item 2]

## Methodology

[Describe the approach and methods to be used]

## Timeline

| Phase | Activities | Duration | Completion Date |
|-------|-----------|----------|-----------------|
| Phase 1 | [Activities] | [Duration] | [Date] |
| Phase 2 | [Activities] | [Duration] | [Date] |
| Phase 3 | [Activities] | [Duration] | [Date] |

## Budget

| Category | Cost | Notes |
|----------|------|-------|
| [Category 1] | $[Amount] | [Notes] |
| [Category 2] | $[Amount] | [Notes] |
| **Total** | **$[Total]** | |

## Team

- **Project Manager:** [Name]
- **Team Members:** [Names]
- **Stakeholders:** [Names]

## Risk Assessment

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| [Risk 1] | [High/Medium/Low] | [High/Medium/Low] | [Strategy] |
| [Risk 2] | [High/Medium/Low] | [High/Medium/Low] | [Strategy] |

## Success Criteria

[Define how success will be measured]

## Conclusion

[Summarize the proposal and call to action]"""

    @staticmethod
    def essay(**kwargs) -> str:
        """Essay template."""
        title = kwargs.get("title", "[Essay Title]")
        author = kwargs.get("author", "[Author Name]")
        today = datetime.now().strftime("%B %d, %Y")

        return f"""# {title}

**Author:** {author}
**Date:** {today}

---

## Introduction

[Hook: Start with an engaging opening sentence or question]

[Background: Provide context for your topic]

[Thesis Statement: Clearly state your main argument or position]

## Body Paragraph 1

[Topic Sentence: Introduce the first main point]

[Evidence: Provide supporting evidence, examples, or data]

[Analysis: Explain how the evidence supports your thesis]

[Transition: Connect to the next paragraph]

## Body Paragraph 2

[Topic Sentence: Introduce the second main point]

[Evidence: Provide supporting evidence, examples, or data]

[Analysis: Explain how the evidence supports your thesis]

[Transition: Connect to the next paragraph]

## Body Paragraph 3

[Topic Sentence: Introduce the third main point]

[Evidence: Provide supporting evidence, examples, or data]

[Analysis: Explain how the evidence supports your thesis]

[Transition: Lead into the conclusion]

## Conclusion

[Restate Thesis: Reaffirm your main argument]

[Summarize: Briefly recap your main points]

[Final Thought: End with a memorable closing statement or call to action]

---

## References

[List your sources in the appropriate citation format]"""

    @staticmethod
    def cover_letter(**kwargs) -> str:
        """Cover letter template."""
        today = datetime.now().strftime("%B %d, %Y")
        your_name = kwargs.get("name", "[Your Name]")
        your_address = kwargs.get("address", "[Your Address]")
        your_email = kwargs.get("email", "[Your Email]")
        your_phone = kwargs.get("phone", "[Your Phone]")
        company = kwargs.get("company", "[Company Name]")
        position = kwargs.get("position", "[Position Title]")

        return f"""{your_name}
{your_address}
{your_email}
{your_phone}

{today}

Hiring Manager
{company}
[Company Address]

Dear Hiring Manager,

I am writing to express my strong interest in the {position} position at {company}. [Explain where you found the job posting or how you learned about the opportunity].

[First body paragraph: Explain why you're interested in this specific role and company. Show that you've researched the company and understand their mission, values, or recent achievements.]

[Second body paragraph: Highlight your relevant qualifications, experiences, and skills. Provide specific examples of your achievements that demonstrate why you're a strong fit for the position.]

[Third body paragraph: Emphasize what you can bring to the company. Connect your skills and experiences to the company's needs and goals.]

I would welcome the opportunity to discuss how my background and skills would be an asset to {company}. Thank you for considering my application. I look forward to hearing from you.

Sincerely,

{your_name}"""

    @staticmethod
    def get_all_templates() -> Dict[str, str]:
>>>>>>> origin/claude/word-editor-module-01PPyUEeNUgZmU4swtfxgoCB
        """
        Get all available templates.

        Returns:
<<<<<<< HEAD
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
=======
            Dictionary of template names and descriptions
        """
        return {
            "Blank Document": "Start with a blank document",
            "Business Letter": "Professional business letter format",
            "Resume": "Professional resume template",
            "Report": "Structured report template",
            "Meeting Notes": "Meeting notes with agenda and action items",
            "Project Proposal": "Comprehensive project proposal",
            "Essay": "Academic essay structure",
            "Cover Letter": "Job application cover letter",
        }
>>>>>>> origin/claude/word-editor-module-01PPyUEeNUgZmU4swtfxgoCB
