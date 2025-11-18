"""
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
        """
        Get all available templates.

        Returns:
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
