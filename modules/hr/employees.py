"""
NEXUS HR - Employee Management Module
Employee records, profiles, compensation, benefits.
Rival to BambooHR.
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from typing import List, Dict, Optional
from enum import Enum
from decimal import Decimal


class EmploymentStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    TERMINATED = "terminated"
    ON_LEAVE = "on_leave"


class EmploymentType(Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERN = "intern"


@dataclass
class Employee:
    """Employee record"""
    id: str
    employee_number: str

    # Personal info
    first_name: str
    last_name: str
    email: str
    phone: str = ""
    date_of_birth: Optional[date] = None

    # Employment
    department: str = ""
    job_title: str = ""
    manager_id: Optional[str] = None
    employment_type: EmploymentType = EmploymentType.FULL_TIME
    employment_status: EmploymentStatus = EmploymentStatus.ACTIVE

    # Dates
    hire_date: Optional[date] = None
    termination_date: Optional[date] = None

    # Compensation
    salary: Decimal = Decimal("0.00")
    pay_frequency: str = "monthly"  # monthly, biweekly, weekly
    currency: str = "USD"

    # Location
    office_location: str = ""
    remote: bool = False

    # Emergency contact
    emergency_contact_name: str = ""
    emergency_contact_phone: str = ""
    emergency_contact_relation: str = ""

    # Documents
    document_urls: Dict[str, str] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Compensation:
    """Compensation history"""
    id: str
    employee_id: str
    effective_date: date
    salary: Decimal
    currency: str = "USD"
    reason: str = ""
    notes: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Benefit:
    """Employee benefit"""
    id: str
    name: str
    description: str
    benefit_type: str  # health, dental, vision, 401k, pto, etc.
    provider: str = ""
    cost_employee: Decimal = Decimal("0.00")
    cost_employer: Decimal = Decimal("0.00")


@dataclass
class EmployeeBenefit:
    """Benefit enrollment"""
    id: str
    employee_id: str
    benefit_id: str
    enrolled_date: date
    coverage_start: date
    coverage_end: Optional[date] = None
    is_active: bool = True


class EmployeeManager:
    """Employee management"""

    def __init__(self):
        self.employees: Dict[str, Employee] = {}
        self.compensation_history: Dict[str, List[Compensation]] = {}  # key: employee_id
        self.benefits: Dict[str, Benefit] = {}
        self.employee_benefits: Dict[str, List[EmployeeBenefit]] = {}  # key: employee_id
        self.employee_counter = 1000

    def create_employee(
        self,
        first_name: str,
        last_name: str,
        email: str,
        **kwargs
    ) -> Employee:
        """Create employee record"""
        import uuid
        employee_number = f"EMP-{self.employee_counter}"
        self.employee_counter += 1

        employee = Employee(
            id=str(uuid.uuid4()),
            employee_number=employee_number,
            first_name=first_name,
            last_name=last_name,
            email=email,
            **kwargs
        )

        self.employees[employee.id] = employee
        return employee

    def update_employee(self, employee_id: str, **updates) -> Optional[Employee]:
        """Update employee record"""
        employee = self.employees.get(employee_id)
        if not employee:
            return None

        for key, value in updates.items():
            if hasattr(employee, key):
                setattr(employee, key, value)

        employee.updated_at = datetime.now()
        return employee

    def terminate_employee(
        self,
        employee_id: str,
        termination_date: date,
        reason: str = ""
    ) -> bool:
        """Terminate employee"""
        employee = self.employees.get(employee_id)
        if not employee:
            return False

        employee.employment_status = EmploymentStatus.TERMINATED
        employee.termination_date = termination_date
        employee.updated_at = datetime.now()
        return True

    def add_compensation_change(
        self,
        employee_id: str,
        effective_date: date,
        new_salary: Decimal,
        reason: str = ""
    ) -> Optional[Compensation]:
        """Add compensation change"""
        employee = self.employees.get(employee_id)
        if not employee:
            return None

        import uuid
        comp = Compensation(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            effective_date=effective_date,
            salary=new_salary,
            reason=reason
        )

        if employee_id not in self.compensation_history:
            self.compensation_history[employee_id] = []

        self.compensation_history[employee_id].append(comp)

        # Update employee salary if effective
        if effective_date <= date.today():
            employee.salary = new_salary
            employee.updated_at = datetime.now()

        return comp

    def create_benefit(
        self,
        name: str,
        description: str,
        benefit_type: str,
        **kwargs
    ) -> Benefit:
        """Create benefit"""
        import uuid
        benefit = Benefit(
            id=str(uuid.uuid4()),
            name=name,
            description=description,
            benefit_type=benefit_type,
            **kwargs
        )
        self.benefits[benefit.id] = benefit
        return benefit

    def enroll_employee_benefit(
        self,
        employee_id: str,
        benefit_id: str,
        coverage_start: date
    ) -> Optional[EmployeeBenefit]:
        """Enroll employee in benefit"""
        if employee_id not in self.employees or benefit_id not in self.benefits:
            return None

        import uuid
        enrollment = EmployeeBenefit(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            benefit_id=benefit_id,
            enrolled_date=date.today(),
            coverage_start=coverage_start
        )

        if employee_id not in self.employee_benefits:
            self.employee_benefits[employee_id] = []

        self.employee_benefits[employee_id].append(enrollment)
        return enrollment

    def get_employee_benefits(self, employee_id: str) -> List[Dict]:
        """Get employee benefits with details"""
        enrollments = self.employee_benefits.get(employee_id, [])
        benefits = []

        for enrollment in enrollments:
            if enrollment.is_active:
                benefit = self.benefits.get(enrollment.benefit_id)
                if benefit:
                    benefits.append({
                        "benefit": benefit,
                        "enrollment": enrollment
                    })

        return benefits

    def get_department_employees(self, department: str) -> List[Employee]:
        """Get all employees in department"""
        return [
            emp for emp in self.employees.values()
            if emp.department == department and emp.employment_status == EmploymentStatus.ACTIVE
        ]

    def get_direct_reports(self, manager_id: str) -> List[Employee]:
        """Get direct reports"""
        return [
            emp for emp in self.employees.values()
            if emp.manager_id == manager_id and emp.employment_status == EmploymentStatus.ACTIVE
        ]


if __name__ == "__main__":
    manager = EmployeeManager()

    emp = manager.create_employee(
        "John",
        "Doe",
        "john.doe@company.com",
        department="Engineering",
        job_title="Software Engineer",
        employment_type=EmploymentType.FULL_TIME,
        hire_date=date(2023, 1, 15),
        salary=Decimal("85000.00")
    )

    manager.add_compensation_change(
        emp.id,
        date(2024, 1, 1),
        Decimal("95000.00"),
        "Annual raise"
    )

    benefit = manager.create_benefit(
        "Health Insurance",
        "Company health insurance plan",
        "health",
        cost_employee=Decimal("200.00"),
        cost_employer=Decimal("500.00")
    )

    manager.enroll_employee_benefit(emp.id, benefit.id, date.today())

    print(f"Employee: {emp.first_name} {emp.last_name}")
    print(f"Salary: ${emp.salary}")
    print(f"Benefits: {len(manager.get_employee_benefits(emp.id))}")
