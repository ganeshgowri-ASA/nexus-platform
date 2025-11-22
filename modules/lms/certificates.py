"""
NEXUS LMS - Certificates Module
Handles certificate generation, templates, verification, and digital badges.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json
import hashlib


class CertificateType(Enum):
    COMPLETION = "completion"
    ACHIEVEMENT = "achievement"
    PARTICIPATION = "participation"
    EXCELLENCE = "excellence"
    CUSTOM = "custom"


class CertificateStatus(Enum):
    PENDING = "pending"
    ISSUED = "issued"
    REVOKED = "revoked"
    EXPIRED = "expired"


@dataclass
class CertificateTemplate:
    """Template for certificates"""
    id: str
    name: str
    certificate_type: CertificateType

    # Design
    template_html: str = ""
    background_image_url: str = ""
    logo_url: str = ""
    signature_urls: List[str] = field(default_factory=list)

    # Layout customization
    title_text: str = "Certificate of Completion"
    subtitle_text: str = ""
    body_template: str = "This is to certify that {student_name} has successfully completed {course_name}"
    footer_text: str = ""

    # Styling
    primary_color: str = "#1a73e8"
    secondary_color: str = "#34a853"
    font_family: str = "Arial, sans-serif"
    border_style: str = "solid"

    # Requirements
    min_grade: float = 70.0
    completion_required: bool = True
    quiz_passing_required: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    is_active: bool = True


@dataclass
class Certificate:
    """Issued certificate"""
    id: str
    certificate_number: str
    template_id: str

    # Recipient
    student_id: str
    student_name: str
    student_email: str

    # Course details
    course_id: str
    course_name: str
    instructor_name: str

    # Achievement details
    completion_date: datetime
    final_grade: Optional[float] = None
    grade_letter: Optional[str] = None
    course_duration: str = ""
    credits: Optional[float] = None

    # Certificate info
    certificate_type: CertificateType = CertificateType.COMPLETION
    status: CertificateStatus = CertificateStatus.ISSUED

    # Digital verification
    verification_code: str = ""
    blockchain_hash: Optional[str] = None
    qr_code_url: str = ""
    verification_url: str = ""

    # Files
    pdf_url: str = ""
    image_url: str = ""

    # Sharing
    linkedin_share_url: str = ""
    twitter_share_url: str = ""
    is_public: bool = True

    # Metadata
    issued_at: datetime = field(default_factory=datetime.now)
    issued_by: str = ""
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    revocation_reason: str = ""


@dataclass
class Badge:
    """Digital badge for achievements"""
    id: str
    name: str
    description: str
    icon_url: str

    # Criteria
    criteria: str = ""
    points_value: int = 0

    # Design
    badge_color: str = "#FFD700"
    rarity: str = "common"  # common, rare, epic, legendary

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True


@dataclass
class StudentBadge:
    """Badge awarded to a student"""
    id: str
    badge_id: str
    student_id: str
    course_id: Optional[str] = None

    # Award details
    awarded_at: datetime = field(default_factory=datetime.now)
    awarded_by: str = ""
    notes: str = ""

    # Display
    is_featured: bool = False
    display_order: int = 0


class CertificateManager:
    """Manages certificates, templates, and badges"""

    def __init__(self):
        self.templates: Dict[str, CertificateTemplate] = {}
        self.certificates: Dict[str, Certificate] = {}
        self.badges: Dict[str, Badge] = {}
        self.student_badges: Dict[str, List[StudentBadge]] = {}  # key: student_id

    # Template management

    def create_template(
        self,
        name: str,
        certificate_type: CertificateType,
        **kwargs
    ) -> CertificateTemplate:
        """Create a certificate template"""
        import uuid
        template_id = kwargs.get('id', str(uuid.uuid4()))

        template = CertificateTemplate(
            id=template_id,
            name=name,
            certificate_type=certificate_type,
            **{k: v for k, v in kwargs.items() if k != 'id'}
        )

        self.templates[template_id] = template
        return template

    def update_template(self, template_id: str, **updates) -> Optional[CertificateTemplate]:
        """Update a certificate template"""
        if template_id not in self.templates:
            return None

        template = self.templates[template_id]
        for key, value in updates.items():
            if hasattr(template, key):
                setattr(template, key, value)

        return template

    def get_template(self, template_id: str) -> Optional[CertificateTemplate]:
        """Get a certificate template"""
        return self.templates.get(template_id)

    # Certificate generation

    def generate_certificate(
        self,
        template_id: str,
        student_id: str,
        student_name: str,
        student_email: str,
        course_id: str,
        course_name: str,
        instructor_name: str,
        completion_date: datetime,
        **kwargs
    ) -> Certificate:
        """Generate a certificate for a student"""
        if template_id not in self.templates:
            raise ValueError("Template not found")

        template = self.templates[template_id]

        # Generate unique certificate number
        cert_number = self._generate_certificate_number()

        # Generate verification code
        verification_code = self._generate_verification_code(
            student_id, course_id, cert_number
        )

        # Generate verification URL
        verification_url = f"https://nexus.edu/verify/{verification_code}"

        import uuid
        certificate = Certificate(
            id=str(uuid.uuid4()),
            certificate_number=cert_number,
            template_id=template_id,
            student_id=student_id,
            student_name=student_name,
            student_email=student_email,
            course_id=course_id,
            course_name=course_name,
            instructor_name=instructor_name,
            completion_date=completion_date,
            certificate_type=template.certificate_type,
            verification_code=verification_code,
            verification_url=verification_url,
            **kwargs
        )

        # Generate PDF and image (placeholder URLs)
        certificate.pdf_url = f"https://nexus.edu/certificates/{certificate.id}.pdf"
        certificate.image_url = f"https://nexus.edu/certificates/{certificate.id}.png"
        certificate.qr_code_url = f"https://nexus.edu/qr/{verification_code}.png"

        # Generate sharing URLs
        certificate.linkedin_share_url = self._generate_linkedin_share_url(certificate)
        certificate.twitter_share_url = self._generate_twitter_share_url(certificate)

        self.certificates[certificate.id] = certificate

        # Auto-award completion badge
        self._award_completion_badge(student_id, course_id, course_name)

        return certificate

    def _generate_certificate_number(self) -> str:
        """Generate unique certificate number"""
        import time
        timestamp = int(time.time() * 1000)
        import random
        random_num = random.randint(1000, 9999)
        return f"NEXUS-{timestamp}-{random_num}"

    def _generate_verification_code(
        self,
        student_id: str,
        course_id: str,
        cert_number: str
    ) -> str:
        """Generate verification code using hash"""
        data = f"{student_id}:{course_id}:{cert_number}:{datetime.now().isoformat()}"
        return hashlib.sha256(data.encode()).hexdigest()[:16].upper()

    def _generate_linkedin_share_url(self, certificate: Certificate) -> str:
        """Generate LinkedIn share URL"""
        return (
            f"https://www.linkedin.com/profile/add?"
            f"startTask=CERTIFICATION_NAME&"
            f"name={certificate.course_name}&"
            f"organizationId=NEXUS&"
            f"issueYear={certificate.completion_date.year}&"
            f"issueMonth={certificate.completion_date.month}&"
            f"certUrl={certificate.verification_url}&"
            f"certId={certificate.certificate_number}"
        )

    def _generate_twitter_share_url(self, certificate: Certificate) -> str:
        """Generate Twitter share URL"""
        text = f"I just earned a certificate in {certificate.course_name} from NEXUS!"
        return f"https://twitter.com/intent/tweet?text={text}&url={certificate.verification_url}"

    # Certificate management

    def verify_certificate(self, verification_code: str) -> Optional[Certificate]:
        """Verify a certificate by its verification code"""
        for certificate in self.certificates.values():
            if certificate.verification_code == verification_code:
                if certificate.status == CertificateStatus.ISSUED:
                    # Check expiration
                    if certificate.expires_at and datetime.now() > certificate.expires_at:
                        certificate.status = CertificateStatus.EXPIRED
                        return None
                    return certificate

        return None

    def revoke_certificate(
        self,
        certificate_id: str,
        reason: str,
        revoked_by: str
    ) -> bool:
        """Revoke a certificate"""
        if certificate_id not in self.certificates:
            return False

        certificate = self.certificates[certificate_id]
        certificate.status = CertificateStatus.REVOKED
        certificate.revoked_at = datetime.now()
        certificate.revocation_reason = reason

        return True

    def get_certificate(self, certificate_id: str) -> Optional[Certificate]:
        """Get a certificate by ID"""
        return self.certificates.get(certificate_id)

    def get_student_certificates(self, student_id: str) -> List[Certificate]:
        """Get all certificates for a student"""
        return [
            cert for cert in self.certificates.values()
            if cert.student_id == student_id and cert.status == CertificateStatus.ISSUED
        ]

    def get_course_certificates(self, course_id: str) -> List[Certificate]:
        """Get all certificates issued for a course"""
        return [
            cert for cert in self.certificates.values()
            if cert.course_id == course_id
        ]

    # Badge management

    def create_badge(
        self,
        name: str,
        description: str,
        icon_url: str,
        **kwargs
    ) -> Badge:
        """Create a new badge"""
        import uuid
        badge_id = kwargs.get('id', str(uuid.uuid4()))

        badge = Badge(
            id=badge_id,
            name=name,
            description=description,
            icon_url=icon_url,
            **{k: v for k, v in kwargs.items() if k != 'id'}
        )

        self.badges[badge_id] = badge
        return badge

    def award_badge(
        self,
        badge_id: str,
        student_id: str,
        awarded_by: str,
        course_id: Optional[str] = None,
        **kwargs
    ) -> StudentBadge:
        """Award a badge to a student"""
        if badge_id not in self.badges:
            raise ValueError("Badge not found")

        import uuid
        student_badge = StudentBadge(
            id=str(uuid.uuid4()),
            badge_id=badge_id,
            student_id=student_id,
            course_id=course_id,
            awarded_by=awarded_by,
            **kwargs
        )

        if student_id not in self.student_badges:
            self.student_badges[student_id] = []

        self.student_badges[student_id].append(student_badge)

        return student_badge

    def _award_completion_badge(
        self,
        student_id: str,
        course_id: str,
        course_name: str
    ) -> None:
        """Auto-award completion badge"""
        # Check if completion badge exists
        completion_badge = next(
            (b for b in self.badges.values() if b.name == "Course Completion"),
            None
        )

        if not completion_badge:
            # Create default completion badge
            completion_badge = self.create_badge(
                name="Course Completion",
                description="Awarded for completing a course",
                icon_url="https://nexus.edu/badges/completion.png",
                badge_color="#4CAF50",
                rarity="common"
            )

        self.award_badge(
            completion_badge.id,
            student_id,
            "system",
            course_id=course_id,
            notes=f"Completed {course_name}"
        )

    def get_student_badges(self, student_id: str) -> List[Dict[str, Any]]:
        """Get all badges for a student with badge details"""
        student_badges_list = self.student_badges.get(student_id, [])

        result = []
        for student_badge in student_badges_list:
            badge = self.badges.get(student_badge.badge_id)
            if badge:
                result.append({
                    "badge": badge,
                    "awarded_at": student_badge.awarded_at,
                    "notes": student_badge.notes,
                    "is_featured": student_badge.is_featured
                })

        return result

    def feature_badge(self, student_id: str, badge_id: str) -> bool:
        """Feature a badge on student profile"""
        if student_id not in self.student_badges:
            return False

        for student_badge in self.student_badges[student_id]:
            if student_badge.badge_id == badge_id:
                student_badge.is_featured = True
                return True

        return False

    # Analytics

    def get_certificate_analytics(self, course_id: str) -> Dict[str, Any]:
        """Get certificate analytics for a course"""
        certificates = self.get_course_certificates(course_id)

        return {
            "total_issued": len(certificates),
            "average_grade": (
                sum(c.final_grade for c in certificates if c.final_grade)
                / len([c for c in certificates if c.final_grade])
                if any(c.final_grade for c in certificates)
                else None
            ),
            "issued_this_month": len([
                c for c in certificates
                if c.issued_at.year == datetime.now().year
                and c.issued_at.month == datetime.now().month
            ]),
            "public_certificates": len([c for c in certificates if c.is_public])
        }

    def get_student_certificate_summary(self, student_id: str) -> Dict[str, Any]:
        """Get certificate summary for a student"""
        certificates = self.get_student_certificates(student_id)
        badges = self.get_student_badges(student_id)

        return {
            "total_certificates": len(certificates),
            "total_badges": len(badges),
            "completion_certificates": len([
                c for c in certificates
                if c.certificate_type == CertificateType.COMPLETION
            ]),
            "excellence_certificates": len([
                c for c in certificates
                if c.certificate_type == CertificateType.EXCELLENCE
            ]),
            "average_grade": (
                sum(c.final_grade for c in certificates if c.final_grade)
                / len([c for c in certificates if c.final_grade])
                if any(c.final_grade for c in certificates)
                else None
            ),
            "recent_certificates": sorted(
                certificates,
                key=lambda c: c.issued_at,
                reverse=True
            )[:5]
        }


# Example usage
if __name__ == "__main__":
    manager = CertificateManager()

    # Create template
    template = manager.create_template(
        name="Standard Completion Certificate",
        certificate_type=CertificateType.COMPLETION,
        title_text="Certificate of Completion",
        body_template="This certifies that {student_name} has successfully completed {course_name}",
        min_grade=70.0,
        primary_color="#1a73e8"
    )

    # Generate certificate
    certificate = manager.generate_certificate(
        template_id=template.id,
        student_id="student_001",
        student_name="John Doe",
        student_email="john@example.com",
        course_id="course_001",
        course_name="Python for Data Science",
        instructor_name="Dr. Smith",
        completion_date=datetime.now(),
        final_grade=95.0,
        grade_letter="A"
    )

    # Verify certificate
    verified = manager.verify_certificate(certificate.verification_code)

    print(f"Certificate Number: {certificate.certificate_number}")
    print(f"Verification Code: {certificate.verification_code}")
    print(f"Verification URL: {certificate.verification_url}")
    print(f"Verified: {verified is not None}")
