"""
Responses Module

Handles form submissions, response storage, real-time tracking, and filtering.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import uuid
import json


@dataclass
class FormResponse:
    """Represents a single form response"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    form_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    submitted_at: datetime = field(default_factory=datetime.now)

    # Metadata
    respondent_email: Optional[str] = None
    respondent_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Timing
    time_spent: int = 0  # seconds
    started_at: Optional[datetime] = None

    # Status
    is_complete: bool = True
    is_test: bool = False
    is_spam: bool = False

    # Scoring (for quizzes)
    score: Optional[float] = None
    max_score: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            "id": self.id,
            "form_id": self.form_id,
            "data": self.data,
            "submitted_at": self.submitted_at.isoformat(),
            "respondent_email": self.respondent_email,
            "respondent_id": self.respondent_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "time_spent": self.time_spent,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "is_complete": self.is_complete,
            "is_test": self.is_test,
            "is_spam": self.is_spam,
            "score": self.score,
            "max_score": self.max_score,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FormResponse":
        """Create response from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            form_id=data.get("form_id", ""),
            data=data.get("data", {}),
            submitted_at=datetime.fromisoformat(data["submitted_at"])
                if "submitted_at" in data else datetime.now(),
            respondent_email=data.get("respondent_email"),
            respondent_id=data.get("respondent_id"),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            time_spent=data.get("time_spent", 0),
            started_at=datetime.fromisoformat(data["started_at"])
                if data.get("started_at") else None,
            is_complete=data.get("is_complete", True),
            is_test=data.get("is_test", False),
            is_spam=data.get("is_spam", False),
            score=data.get("score"),
            max_score=data.get("max_score"),
        )

    def get_field_value(self, field_id: str) -> Any:
        """Get value for a specific field"""
        return self.data.get(field_id)

    def calculate_completion_time(self) -> int:
        """Calculate time taken to complete form in seconds"""
        if self.started_at and self.submitted_at:
            return int((self.submitted_at - self.started_at).total_seconds())
        return self.time_spent


class ResponseManager:
    """Manages form responses"""

    def __init__(self):
        self.responses: Dict[str, List[FormResponse]] = {}
        self.real_time_callbacks: List[Callable[[FormResponse], None]] = []

    def submit_response(self, response: FormResponse) -> str:
        """
        Submit a new form response

        Returns:
            Response ID
        """
        if response.form_id not in self.responses:
            self.responses[response.form_id] = []

        self.responses[response.form_id].append(response)

        # Trigger real-time callbacks
        for callback in self.real_time_callbacks:
            callback(response)

        return response.id

    def get_response(self, response_id: str) -> Optional[FormResponse]:
        """Get a specific response by ID"""
        for responses in self.responses.values():
            for response in responses:
                if response.id == response_id:
                    return response
        return None

    def get_form_responses(self, form_id: str,
                          include_test: bool = False,
                          include_spam: bool = False) -> List[FormResponse]:
        """Get all responses for a form"""
        if form_id not in self.responses:
            return []

        responses = self.responses[form_id]

        if not include_test:
            responses = [r for r in responses if not r.is_test]

        if not include_spam:
            responses = [r for r in responses if not r.is_spam]

        return responses

    def get_response_count(self, form_id: str,
                          include_test: bool = False,
                          include_spam: bool = False) -> int:
        """Get count of responses for a form"""
        return len(self.get_form_responses(form_id, include_test, include_spam))

    def delete_response(self, response_id: str) -> bool:
        """Delete a response"""
        for form_id, responses in self.responses.items():
            for i, response in enumerate(responses):
                if response.id == response_id:
                    self.responses[form_id].pop(i)
                    return True
        return False

    def mark_as_spam(self, response_id: str) -> bool:
        """Mark a response as spam"""
        response = self.get_response(response_id)
        if response:
            response.is_spam = True
            return True
        return False

    def filter_responses(self, form_id: str,
                        filters: Dict[str, Any]) -> List[FormResponse]:
        """
        Filter responses based on criteria

        Args:
            form_id: Form ID
            filters: Dictionary of field_id: value pairs

        Returns:
            List of matching responses
        """
        responses = self.get_form_responses(form_id)
        filtered = []

        for response in responses:
            matches = True
            for field_id, filter_value in filters.items():
                response_value = response.data.get(field_id)

                if isinstance(filter_value, list):
                    # Match any of the values
                    if response_value not in filter_value:
                        matches = False
                        break
                elif isinstance(filter_value, dict):
                    # Range filter
                    if "min" in filter_value and response_value < filter_value["min"]:
                        matches = False
                        break
                    if "max" in filter_value and response_value > filter_value["max"]:
                        matches = False
                        break
                else:
                    # Exact match
                    if response_value != filter_value:
                        matches = False
                        break

            if matches:
                filtered.append(response)

        return filtered

    def search_responses(self, form_id: str, search_term: str) -> List[FormResponse]:
        """
        Search responses for a term

        Args:
            form_id: Form ID
            search_term: Search term

        Returns:
            List of matching responses
        """
        responses = self.get_form_responses(form_id)
        search_term = search_term.lower()
        matching = []

        for response in responses:
            for value in response.data.values():
                if search_term in str(value).lower():
                    matching.append(response)
                    break

        return matching

    def get_responses_by_date_range(self, form_id: str,
                                   start_date: datetime,
                                   end_date: datetime) -> List[FormResponse]:
        """Get responses within a date range"""
        responses = self.get_form_responses(form_id)
        return [
            r for r in responses
            if start_date <= r.submitted_at <= end_date
        ]

    def get_latest_responses(self, form_id: str, limit: int = 10) -> List[FormResponse]:
        """Get the most recent responses"""
        responses = self.get_form_responses(form_id)
        responses.sort(key=lambda r: r.submitted_at, reverse=True)
        return responses[:limit]

    def add_real_time_callback(self, callback: Callable[[FormResponse], None]) -> None:
        """Add a callback to be triggered on new submissions"""
        self.real_time_callbacks.append(callback)

    def remove_real_time_callback(self, callback: Callable[[FormResponse], None]) -> None:
        """Remove a real-time callback"""
        if callback in self.real_time_callbacks:
            self.real_time_callbacks.remove(callback)

    def get_spreadsheet_view(self, form_id: str,
                            field_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get responses in spreadsheet format

        Returns:
            Dictionary with headers and rows
        """
        responses = self.get_form_responses(form_id)

        if not responses:
            return {"headers": [], "rows": []}

        # Determine headers
        if field_ids:
            headers = ["Response ID", "Submitted At"] + field_ids
        else:
            # Get all unique field IDs
            all_fields = set()
            for response in responses:
                all_fields.update(response.data.keys())
            headers = ["Response ID", "Submitted At"] + sorted(all_fields)

        # Build rows
        rows = []
        for response in responses:
            row = [
                response.id,
                response.submitted_at.strftime("%Y-%m-%d %H:%M:%S")
            ]

            for header in headers[2:]:  # Skip Response ID and Submitted At
                value = response.data.get(header, "")
                # Convert lists to comma-separated strings
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value)
                row.append(value)

            rows.append(row)

        return {"headers": headers, "rows": rows}

    def get_field_responses(self, form_id: str, field_id: str) -> List[Any]:
        """Get all responses for a specific field"""
        responses = self.get_form_responses(form_id)
        return [r.data.get(field_id) for r in responses if field_id in r.data]

    def save_responses(self, form_id: str, filepath: str) -> None:
        """Save responses to JSON file"""
        responses = self.get_form_responses(form_id, include_test=True, include_spam=True)
        data = [r.to_dict() for r in responses]

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def load_responses(self, form_id: str, filepath: str) -> int:
        """
        Load responses from JSON file

        Returns:
            Number of responses loaded
        """
        with open(filepath, 'r') as f:
            data = json.load(f)

        if form_id not in self.responses:
            self.responses[form_id] = []

        count = 0
        for item in data:
            response = FormResponse.from_dict(item)
            self.responses[form_id].append(response)
            count += 1

        return count

    def clear_responses(self, form_id: str) -> None:
        """Clear all responses for a form"""
        self.responses[form_id] = []

    def get_summary_statistics(self, form_id: str) -> Dict[str, Any]:
        """Get summary statistics for form responses"""
        responses = self.get_form_responses(form_id)

        if not responses:
            return {
                "total_responses": 0,
                "complete_responses": 0,
                "average_time": 0,
                "first_response": None,
                "last_response": None,
            }

        complete_responses = [r for r in responses if r.is_complete]
        times = [r.time_spent for r in responses if r.time_spent > 0]

        return {
            "total_responses": len(responses),
            "complete_responses": len(complete_responses),
            "incomplete_responses": len(responses) - len(complete_responses),
            "test_responses": len([r for r in responses if r.is_test]),
            "spam_responses": len([r for r in responses if r.is_spam]),
            "average_time": sum(times) / len(times) if times else 0,
            "median_time": sorted(times)[len(times) // 2] if times else 0,
            "first_response": min(r.submitted_at for r in responses),
            "last_response": max(r.submitted_at for r in responses),
        }


class ResponseValidator:
    """Validates form responses"""

    @staticmethod
    def detect_spam(response: FormResponse) -> bool:
        """
        Detect potential spam responses

        Returns:
            True if response is likely spam
        """
        # Check for rapid submission
        if response.time_spent < 5:  # Less than 5 seconds
            return True

        # Check for suspicious patterns
        data_str = " ".join(str(v) for v in response.data.values())

        # Check for excessive URLs
        if data_str.count("http://") + data_str.count("https://") > 3:
            return True

        # Check for repeated characters
        import re
        if re.search(r'(.)\1{10,}', data_str):
            return True

        return False

    @staticmethod
    def detect_duplicate(response: FormResponse,
                        existing_responses: List[FormResponse]) -> bool:
        """
        Detect duplicate responses

        Returns:
            True if response is a duplicate
        """
        for existing in existing_responses:
            # Check for same email
            if response.respondent_email and \
               response.respondent_email == existing.respondent_email:
                # Check if data is very similar
                if response.data == existing.data:
                    return True

            # Check for same IP within short time
            if response.ip_address and \
               response.ip_address == existing.ip_address:
                time_diff = abs((response.submitted_at - existing.submitted_at).total_seconds())
                if time_diff < 60:  # Within 1 minute
                    return True

        return False


class ResponseNotifier:
    """Handles notifications for form responses"""

    def __init__(self):
        self.notification_handlers: Dict[str, Callable] = {}

    def add_handler(self, name: str, handler: Callable[[FormResponse], None]) -> None:
        """Add a notification handler"""
        self.notification_handlers[name] = handler

    def notify(self, response: FormResponse) -> None:
        """Send notifications for a response"""
        for handler in self.notification_handlers.values():
            try:
                handler(response)
            except Exception as e:
                print(f"Notification handler error: {e}")

    @staticmethod
    def send_confirmation_email(response: FormResponse, form_title: str) -> None:
        """Send confirmation email to respondent"""
        if not response.respondent_email:
            return

        # In production, this would send an actual email
        print(f"Sending confirmation email to {response.respondent_email}")
        print(f"Subject: Thank you for submitting {form_title}")

    @staticmethod
    def send_admin_notification(response: FormResponse,
                               admin_emails: List[str]) -> None:
        """Send notification to form administrators"""
        # In production, this would send actual emails
        for email in admin_emails:
            print(f"Sending admin notification to {email}")
            print(f"New response received: {response.id}")
