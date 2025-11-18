"""
NEXUS HR - Organizational Chart Module
Organization structure, reporting lines, team hierarchies.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Set


@dataclass
class Department:
    """Department/Division"""
    id: str
    name: str
    description: str = ""

    # Hierarchy
    parent_id: Optional[str] = None

    # Leadership
    head_id: Optional[str] = None  # employee_id of department head

    # Metadata
    cost_center: str = ""
    location: str = ""
    employee_count: int = 0

    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Team:
    """Team within department"""
    id: str
    name: str
    department_id: str

    # Leadership
    team_lead_id: Optional[str] = None

    # Members
    member_ids: List[str] = field(default_factory=list)

    # Metadata
    description: str = ""
    is_active: bool = True


@dataclass
class ReportingRelationship:
    """Reporting relationship"""
    id: str
    employee_id: str
    manager_id: str
    relationship_type: str = "direct"  # "direct", "dotted", "matrix"
    is_primary: bool = True

    effective_date: datetime = field(default_factory=datetime.now)
    end_date: Optional[datetime] = None


class OrgChartManager:
    """Organizational chart management"""

    def __init__(self):
        self.departments: Dict[str, Department] = {}
        self.teams: Dict[str, Team] = {}
        self.reporting_relationships: Dict[str, List[ReportingRelationship]] = {}  # employee_id -> relationships

    def create_department(
        self,
        name: str,
        parent_id: Optional[str] = None,
        **kwargs
    ) -> Department:
        """Create department"""
        import uuid
        dept = Department(
            id=str(uuid.uuid4()),
            name=name,
            parent_id=parent_id,
            **kwargs
        )
        self.departments[dept.id] = dept
        return dept

    def create_team(
        self,
        name: str,
        department_id: str,
        **kwargs
    ) -> Optional[Team]:
        """Create team"""
        if department_id not in self.departments:
            return None

        import uuid
        team = Team(
            id=str(uuid.uuid4()),
            name=name,
            department_id=department_id,
            **kwargs
        )
        self.teams[team.id] = team
        return team

    def add_team_member(self, team_id: str, employee_id: str) -> bool:
        """Add member to team"""
        team = self.teams.get(team_id)
        if not team:
            return False

        if employee_id not in team.member_ids:
            team.member_ids.append(employee_id)

        return True

    def create_reporting_relationship(
        self,
        employee_id: str,
        manager_id: str,
        **kwargs
    ) -> ReportingRelationship:
        """Create reporting relationship"""
        import uuid
        relationship = ReportingRelationship(
            id=str(uuid.uuid4()),
            employee_id=employee_id,
            manager_id=manager_id,
            **kwargs
        )

        if employee_id not in self.reporting_relationships:
            self.reporting_relationships[employee_id] = []

        self.reporting_relationships[employee_id].append(relationship)

        return relationship

    def get_direct_reports(self, manager_id: str) -> List[str]:
        """Get direct reports for manager"""
        reports = []

        for emp_id, relationships in self.reporting_relationships.items():
            for rel in relationships:
                if rel.manager_id == manager_id and rel.is_primary and not rel.end_date:
                    reports.append(emp_id)

        return reports

    def get_manager(self, employee_id: str) -> Optional[str]:
        """Get employee's manager"""
        relationships = self.reporting_relationships.get(employee_id, [])

        for rel in relationships:
            if rel.is_primary and not rel.end_date:
                return rel.manager_id

        return None

    def get_org_hierarchy(self, employee_id: str, levels_up: int = 10) -> List[str]:
        """Get management chain up to N levels"""
        chain = []
        current_id = employee_id

        for _ in range(levels_up):
            manager_id = self.get_manager(current_id)
            if not manager_id:
                break

            chain.append(manager_id)
            current_id = manager_id

        return chain

    def get_all_reports(self, manager_id: str) -> Set[str]:
        """Get all reports (direct and indirect)"""
        all_reports = set()

        def add_reports(mgr_id):
            direct = self.get_direct_reports(mgr_id)
            for emp_id in direct:
                if emp_id not in all_reports:
                    all_reports.add(emp_id)
                    add_reports(emp_id)  # Recursive

        add_reports(manager_id)
        return all_reports

    def get_department_hierarchy(self, department_id: str) -> List[Department]:
        """Get department and all sub-departments"""
        departments = []

        def add_subdepts(dept_id):
            dept = self.departments.get(dept_id)
            if dept:
                departments.append(dept)

                # Find child departments
                for d in self.departments.values():
                    if d.parent_id == dept_id:
                        add_subdepts(d.id)

        add_subdepts(department_id)
        return departments

    def get_team_members(self, team_id: str) -> List[str]:
        """Get team members"""
        team = self.teams.get(team_id)
        return team.member_ids if team else []


if __name__ == "__main__":
    manager = OrgChartManager()

    # Create departments
    engineering = manager.create_department(
        "Engineering",
        head_id="emp_cto"
    )

    backend = manager.create_department(
        "Backend Engineering",
        parent_id=engineering.id,
        head_id="emp_backend_lead"
    )

    # Create team
    api_team = manager.create_team(
        "API Team",
        backend.id,
        team_lead_id="emp_api_lead"
    )

    # Add team members
    manager.add_team_member(api_team.id, "emp_001")
    manager.add_team_member(api_team.id, "emp_002")

    # Create reporting relationships
    manager.create_reporting_relationship("emp_001", "emp_api_lead")
    manager.create_reporting_relationship("emp_api_lead", "emp_backend_lead")

    # Get org structure
    direct_reports = manager.get_direct_reports("emp_api_lead")
    all_reports = manager.get_all_reports("emp_backend_lead")

    print(f"Direct reports: {len(direct_reports)}")
    print(f"All reports: {len(all_reports)}")
    print(f"Team members: {len(manager.get_team_members(api_team.id))}")
