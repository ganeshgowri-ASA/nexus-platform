"""
Templates Module

Provides pre-built form templates for common use cases including contact forms,
surveys, registrations, applications, and quizzes.
"""

from dataclasses import dataclass
from typing import List, Dict, Any
from .field_types import Field, FieldFactory, FieldType, FieldConfig
from .form_builder import Form, FormSettings


@dataclass
class FormTemplate:
    """Represents a form template"""
    name: str
    description: str
    category: str
    fields: List[Field]
    settings: FormSettings

    def to_form(self) -> Form:
        """Convert template to a Form instance"""
        form = Form()
        form.fields = self.fields
        form.settings = self.settings
        return form


class TemplateLibrary:
    """Library of pre-built form templates"""

    @staticmethod
    def get_contact_form() -> FormTemplate:
        """Simple contact form template"""
        fields = [
            FieldFactory.create_short_text("Name", required=True),
            FieldFactory.create_email("Email Address", required=True),
            FieldFactory.create_phone("Phone Number", required=False),
            FieldFactory.create_short_text("Subject", required=True),
            FieldFactory.create_long_text("Message", required=True, placeholder="Tell us how we can help..."),
        ]

        settings = FormSettings(
            title="Contact Us",
            description="We'd love to hear from you! Fill out the form below and we'll get back to you as soon as possible.",
            theme="modern",
            success_message="Thank you for contacting us! We'll respond within 24 hours.",
        )

        return FormTemplate(
            name="Contact Form",
            description="Simple contact form for inquiries",
            category="Contact",
            fields=fields,
            settings=settings,
        )

    @staticmethod
    def get_customer_satisfaction_survey() -> FormTemplate:
        """Customer satisfaction survey template"""
        fields = [
            FieldFactory.create_email("Email Address", required=False),
            FieldFactory.create_rating(
                "How satisfied are you with our product/service?",
                max_rating=5,
                required=True
            ),
            FieldFactory.create_nps("How likely are you to recommend us to a friend or colleague?"),
            FieldFactory.create_radio(
                "How long have you been using our service?",
                options=["Less than 1 month", "1-6 months", "6-12 months", "1-2 years", "More than 2 years"],
                required=True
            ),
            FieldFactory.create_checkbox(
                "Which features do you use most often? (Select all that apply)",
                options=["Dashboard", "Reports", "Analytics", "Integrations", "Mobile App", "API"],
            ),
            FieldFactory.create_long_text(
                "What can we improve?",
                placeholder="Share your suggestions..."
            ),
            FieldFactory.create_long_text(
                "What do you like most about our service?",
                placeholder="Tell us what we're doing well..."
            ),
        ]

        settings = FormSettings(
            title="Customer Satisfaction Survey",
            description="Help us improve by sharing your feedback",
            theme="modern",
            success_message="Thank you for your valuable feedback!",
        )

        return FormTemplate(
            name="Customer Satisfaction Survey",
            description="Comprehensive customer feedback survey",
            category="Survey",
            fields=fields,
            settings=settings,
        )

    @staticmethod
    def get_event_registration() -> FormTemplate:
        """Event registration form template"""
        fields = [
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="First Name",
                config=FieldConfig(required=True)
            ),
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="Last Name",
                config=FieldConfig(required=True)
            ),
            FieldFactory.create_email("Email Address", required=True),
            FieldFactory.create_phone("Phone Number", required=True),
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="Company/Organization",
                config=FieldConfig(required=False)
            ),
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="Job Title",
                config=FieldConfig(required=False)
            ),
            FieldFactory.create_dropdown(
                "Ticket Type",
                options=["General Admission", "VIP", "Student", "Group (5+)"],
                required=True
            ),
            FieldFactory.create_checkbox(
                "Dietary Restrictions",
                options=["Vegetarian", "Vegan", "Gluten-Free", "Nut Allergy", "No Restrictions"],
            ),
            FieldFactory.create_long_text(
                "Special Requirements",
                placeholder="Any accessibility needs or special requests?"
            ),
            Field(
                field_type=FieldType.CHECKBOX,
                label="Communication Preferences",
                config=FieldConfig(
                    options=["Email updates about the event", "Future event notifications", "Newsletter subscription"]
                )
            ),
        ]

        settings = FormSettings(
            title="Event Registration",
            description="Register for our upcoming event",
            theme="modern",
            success_message="Registration successful! You'll receive a confirmation email shortly.",
            send_confirmation_email=True,
        )

        return FormTemplate(
            name="Event Registration",
            description="Complete event registration form",
            category="Registration",
            fields=fields,
            settings=settings,
        )

    @staticmethod
    def get_job_application() -> FormTemplate:
        """Job application form template"""
        fields = [
            # Personal Information
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="Full Name",
                config=FieldConfig(required=True)
            ),
            FieldFactory.create_email("Email Address", required=True),
            FieldFactory.create_phone("Phone Number", required=True),
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="LinkedIn Profile URL",
                config=FieldConfig(required=False, placeholder="https://linkedin.com/in/...")
            ),

            # Position Information
            FieldFactory.create_dropdown(
                "Position Applying For",
                options=["Software Engineer", "Product Manager", "Designer", "Marketing Manager", "Sales Representative"],
                required=True
            ),
            FieldFactory.create_dropdown(
                "How did you hear about this position?",
                options=["Company Website", "LinkedIn", "Job Board", "Referral", "Other"],
                required=True
            ),

            # Experience
            FieldFactory.create_dropdown(
                "Years of Experience",
                options=["0-1 years", "1-3 years", "3-5 years", "5-10 years", "10+ years"],
                required=True
            ),
            Field(
                field_type=FieldType.LONG_TEXT,
                label="Tell us about your relevant experience",
                config=FieldConfig(
                    required=True,
                    min_length=100,
                    placeholder="Describe your relevant work experience, skills, and achievements..."
                )
            ),

            # Availability
            FieldFactory.create_date("Earliest Start Date", required=True),
            FieldFactory.create_dropdown(
                "Work Authorization",
                options=["Authorized to work in this country", "Requires sponsorship"],
                required=True
            ),

            # Additional
            Field(
                field_type=FieldType.FILE_UPLOAD,
                label="Resume/CV",
                config=FieldConfig(
                    required=True,
                    max_files=1,
                    allowed_file_types=["pdf", "doc", "docx"]
                )
            ),
            Field(
                field_type=FieldType.FILE_UPLOAD,
                label="Cover Letter (Optional)",
                config=FieldConfig(
                    required=False,
                    max_files=1,
                    allowed_file_types=["pdf", "doc", "docx"]
                )
            ),
            Field(
                field_type=FieldType.LONG_TEXT,
                label="Why do you want to work with us?",
                config=FieldConfig(
                    required=True,
                    min_length=50,
                    placeholder="Share what attracts you to this opportunity..."
                )
            ),
        ]

        settings = FormSettings(
            title="Job Application",
            description="Apply for a position at our company",
            theme="classic",
            is_multi_page=True,
            success_message="Application submitted successfully! We'll review your application and get back to you soon.",
            send_confirmation_email=True,
        )

        # Assign fields to pages
        for i, field in enumerate(fields):
            if i < 4:
                field.page = 0  # Personal Info
            elif i < 7:
                field.page = 1  # Position Info
            elif i < 9:
                field.page = 2  # Experience
            elif i < 11:
                field.page = 3  # Availability
            else:
                field.page = 4  # Documents & Final

        return FormTemplate(
            name="Job Application",
            description="Comprehensive job application form",
            category="Application",
            fields=fields,
            settings=settings,
        )

    @staticmethod
    def get_product_feedback() -> FormTemplate:
        """Product feedback form template"""
        fields = [
            FieldFactory.create_email("Email Address (Optional)", required=False),
            FieldFactory.create_dropdown(
                "Which product are you providing feedback about?",
                options=["Product A", "Product B", "Product C", "All Products"],
                required=True
            ),
            FieldFactory.create_rating(
                "How would you rate the product overall?",
                max_rating=5,
                required=True
            ),
            Field(
                field_type=FieldType.MATRIX,
                label="Rate the following aspects:",
                config=FieldConfig(
                    rows=["Quality", "Value for Money", "Customer Support", "Ease of Use"],
                    columns=["Poor", "Fair", "Good", "Very Good", "Excellent"]
                )
            ),
            FieldFactory.create_long_text(
                "What do you like most about the product?",
                required=False
            ),
            FieldFactory.create_long_text(
                "What could be improved?",
                required=False
            ),
            FieldFactory.create_radio(
                "Would you purchase this product again?",
                options=["Definitely", "Probably", "Not Sure", "Probably Not", "Definitely Not"],
                required=True
            ),
        ]

        settings = FormSettings(
            title="Product Feedback",
            description="Share your thoughts about our products",
            theme="minimal",
            success_message="Thank you for your feedback! It helps us improve.",
        )

        return FormTemplate(
            name="Product Feedback",
            description="Collect detailed product feedback",
            category="Feedback",
            fields=fields,
            settings=settings,
        )

    @staticmethod
    def get_quiz_template() -> FormTemplate:
        """Quiz/assessment template"""
        fields = [
            FieldFactory.create_short_text("Name", required=True),
            FieldFactory.create_email("Email Address", required=True),

            # Question 1
            FieldFactory.create_radio(
                "Question 1: What is the capital of France?",
                options=["London", "Berlin", "Paris", "Madrid"],
                required=True
            ),

            # Question 2
            FieldFactory.create_radio(
                "Question 2: Which planet is known as the Red Planet?",
                options=["Venus", "Mars", "Jupiter", "Saturn"],
                required=True
            ),

            # Question 3
            FieldFactory.create_radio(
                "Question 3: What is 15 × 7?",
                options=["95", "105", "115", "125"],
                required=True
            ),

            # Question 4
            FieldFactory.create_checkbox(
                "Question 4: Select all programming languages (multiple answers)",
                options=["Python", "HTML", "Java", "CSS", "C++", "XML"],
            ),

            # Question 5
            FieldFactory.create_short_text(
                "Question 5: What does HTML stand for?",
                required=True
            ),
        ]

        settings = FormSettings(
            title="Knowledge Quiz",
            description="Test your knowledge with this quick quiz",
            theme="modern",
            success_message="Quiz completed! Check your email for results.",
            allow_multiple_submissions=False,
        )

        return FormTemplate(
            name="Quiz Template",
            description="Basic quiz/assessment form",
            category="Quiz",
            fields=fields,
            settings=settings,
        )

    @staticmethod
    def get_lead_generation() -> FormTemplate:
        """Lead generation form template"""
        fields = [
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="Full Name",
                config=FieldConfig(required=True)
            ),
            FieldFactory.create_email("Work Email", required=True),
            FieldFactory.create_phone("Phone Number", required=False),
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="Company Name",
                config=FieldConfig(required=True)
            ),
            FieldFactory.create_dropdown(
                "Company Size",
                options=["1-10", "11-50", "51-200", "201-1000", "1000+"],
                required=True
            ),
            FieldFactory.create_dropdown(
                "Industry",
                options=["Technology", "Healthcare", "Finance", "Education", "Retail", "Manufacturing", "Other"],
                required=True
            ),
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="Job Title",
                config=FieldConfig(required=True)
            ),
            FieldFactory.create_dropdown(
                "What are you interested in?",
                options=["Product Demo", "Pricing Information", "Free Trial", "Speaking to Sales"],
                required=True
            ),
            FieldFactory.create_long_text(
                "Tell us about your needs",
                placeholder="What challenges are you looking to solve?",
                required=False
            ),
        ]

        settings = FormSettings(
            title="Request a Demo",
            description="Learn how our solution can help your business",
            theme="modern",
            success_message="Thank you! Our team will contact you within 24 hours.",
            send_confirmation_email=True,
            notification_emails=["sales@company.com"],
        )

        return FormTemplate(
            name="Lead Generation",
            description="Capture qualified leads",
            category="Lead Generation",
            fields=fields,
            settings=settings,
        )

    @staticmethod
    def get_volunteer_signup() -> FormTemplate:
        """Volunteer signup form template"""
        fields = [
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="First Name",
                config=FieldConfig(required=True)
            ),
            Field(
                field_type=FieldType.SHORT_TEXT,
                label="Last Name",
                config=FieldConfig(required=True)
            ),
            FieldFactory.create_email("Email Address", required=True),
            FieldFactory.create_phone("Phone Number", required=True),
            Field(
                field_type=FieldType.NUMBER,
                label="Age",
                config=FieldConfig(required=True, min_value=13, max_value=100)
            ),
            FieldFactory.create_checkbox(
                "Areas of Interest (Select all that apply)",
                options=[
                    "Event Support",
                    "Community Outreach",
                    "Fundraising",
                    "Social Media",
                    "Teaching/Mentoring",
                    "Administrative Support"
                ],
            ),
            FieldFactory.create_dropdown(
                "Availability",
                options=["Weekdays", "Weekends", "Both", "Flexible"],
                required=True
            ),
            FieldFactory.create_radio(
                "How many hours per week can you commit?",
                options=["1-5 hours", "5-10 hours", "10-15 hours", "15+ hours"],
                required=True
            ),
            FieldFactory.create_long_text(
                "Why do you want to volunteer with us?",
                required=True,
                placeholder="Tell us about your motivation and any relevant experience..."
            ),
        ]

        settings = FormSettings(
            title="Volunteer Signup",
            description="Join our team of volunteers and make a difference!",
            theme="modern",
            success_message="Thank you for signing up! We'll be in touch soon with next steps.",
        )

        return FormTemplate(
            name="Volunteer Signup",
            description="Volunteer registration and interest form",
            category="Registration",
            fields=fields,
            settings=settings,
        )

    @staticmethod
    def get_all_templates() -> List[FormTemplate]:
        """Get all available templates"""
        return [
            TemplateLibrary.get_contact_form(),
            TemplateLibrary.get_customer_satisfaction_survey(),
            TemplateLibrary.get_event_registration(),
            TemplateLibrary.get_job_application(),
            TemplateLibrary.get_product_feedback(),
            TemplateLibrary.get_quiz_template(),
            TemplateLibrary.get_lead_generation(),
            TemplateLibrary.get_volunteer_signup(),
        ]

    @staticmethod
    def get_templates_by_category(category: str) -> List[FormTemplate]:
        """Get templates filtered by category"""
        all_templates = TemplateLibrary.get_all_templates()
        return [t for t in all_templates if t.category.lower() == category.lower()]

    @staticmethod
    def search_templates(query: str) -> List[FormTemplate]:
        """Search templates by name or description"""
        all_templates = TemplateLibrary.get_all_templates()
        query = query.lower()
        return [
            t for t in all_templates
            if query in t.name.lower() or query in t.description.lower()
        ]


class TemplateCustomizer:
    """Customize templates with specific data"""

    @staticmethod
    def customize_field_options(template: FormTemplate,
                               field_label: str,
                               new_options: List[str]) -> FormTemplate:
        """Update options for a specific field"""
        for field in template.fields:
            if field.label == field_label:
                field.config.options = new_options
        return template

    @staticmethod
    def customize_branding(template: FormTemplate,
                          title: str,
                          logo_url: str,
                          primary_color: str) -> FormTemplate:
        """Apply custom branding to template"""
        template.settings.title = title
        template.settings.logo_url = logo_url
        template.settings.primary_color = primary_color
        return template

    @staticmethod
    def add_custom_fields(template: FormTemplate,
                         fields: List[Field],
                         position: int = -1) -> FormTemplate:
        """Add custom fields to template"""
        if position == -1:
            template.fields.extend(fields)
        else:
            for i, field in enumerate(fields):
                template.fields.insert(position + i, field)
        return template

    @staticmethod
    def remove_fields(template: FormTemplate,
                     field_labels: List[str]) -> FormTemplate:
        """Remove fields from template by label"""
        template.fields = [
            f for f in template.fields
            if f.label not in field_labels
        ]
        return template
