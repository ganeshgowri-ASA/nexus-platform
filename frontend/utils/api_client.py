"""
API Client for NEXUS Platform frontend.

This module provides a client for interacting with the backend API.
"""

from typing import Dict, Any, Optional, List
import requests
import streamlit as st

from frontend.config import config


class APIClient:
    """Client for NEXUS Platform API."""

    @staticmethod
    def _get_headers() -> Dict[str, str]:
        """Get request headers with authentication token."""
        headers = {"Content-Type": "application/json"}

        if "access_token" in st.session_state:
            headers["Authorization"] = f"Bearer {st.session_state.access_token}"

        return headers

    @staticmethod
    def _handle_response(response: requests.Response) -> Any:
        """Handle API response."""
        if response.status_code == 401:
            st.session_state.clear()
            st.error("Session expired. Please login again.")
            st.rerun()

        if not response.ok:
            error_data = response.json() if response.content else {}
            error_msg = error_data.get("error", f"HTTP {response.status_code}")
            raise Exception(f"API Error: {error_msg}")

        return response.json() if response.content else None

    # ==================== Authentication ====================

    @staticmethod
    def login(username: str, password: str) -> Dict[str, Any]:
        """Login to the platform."""
        url = f"{config.api_url}/auth/login"
        response = requests.post(
            url,
            json={"username": username, "password": password}
        )
        return APIClient._handle_response(response)

    @staticmethod
    def register(
        email: str,
        username: str,
        password: str,
        full_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Register a new user."""
        url = f"{config.api_url}/auth/register"
        response = requests.post(
            url,
            json={
                "email": email,
                "username": username,
                "password": password,
                "full_name": full_name
            }
        )
        return APIClient._handle_response(response)

    @staticmethod
    def get_current_user() -> Dict[str, Any]:
        """Get current user information."""
        url = f"{config.api_url}/auth/me"
        response = requests.get(url, headers=APIClient._get_headers())
        return APIClient._handle_response(response)

    # ==================== Campaigns ====================

    @staticmethod
    def create_campaign(data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new campaign."""
        url = f"{config.api_url}/campaigns/"
        response = requests.post(
            url,
            json=data,
            headers=APIClient._get_headers()
        )
        return APIClient._handle_response(response)

    @staticmethod
    def list_campaigns(
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> Dict[str, Any]:
        """List campaigns."""
        url = f"{config.api_url}/campaigns/"
        params = {"skip": skip, "limit": limit}
        if status:
            params["status"] = status

        response = requests.get(
            url,
            params=params,
            headers=APIClient._get_headers()
        )
        return APIClient._handle_response(response)

    @staticmethod
    def get_campaign(campaign_id: int) -> Dict[str, Any]:
        """Get campaign by ID."""
        url = f"{config.api_url}/campaigns/{campaign_id}"
        response = requests.get(url, headers=APIClient._get_headers())
        return APIClient._handle_response(response)

    @staticmethod
    def update_campaign(campaign_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update campaign."""
        url = f"{config.api_url}/campaigns/{campaign_id}"
        response = requests.put(
            url,
            json=data,
            headers=APIClient._get_headers()
        )
        return APIClient._handle_response(response)

    @staticmethod
    def delete_campaign(campaign_id: int) -> None:
        """Delete campaign."""
        url = f"{config.api_url}/campaigns/{campaign_id}"
        response = requests.delete(url, headers=APIClient._get_headers())
        APIClient._handle_response(response)

    @staticmethod
    def update_campaign_status(campaign_id: int, status: str) -> Dict[str, Any]:
        """Update campaign status."""
        url = f"{config.api_url}/campaigns/{campaign_id}/status/{status}"
        response = requests.post(url, headers=APIClient._get_headers())
        return APIClient._handle_response(response)

    # ==================== Channels ====================

    @staticmethod
    def add_channel(campaign_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add channel to campaign."""
        url = f"{config.api_url}/campaigns/{campaign_id}/channels"
        response = requests.post(
            url,
            json=data,
            headers=APIClient._get_headers()
        )
        return APIClient._handle_response(response)

    @staticmethod
    def list_channels(campaign_id: int) -> List[Dict[str, Any]]:
        """List campaign channels."""
        url = f"{config.api_url}/campaigns/{campaign_id}/channels"
        response = requests.get(url, headers=APIClient._get_headers())
        return APIClient._handle_response(response)

    # ==================== Team ====================

    @staticmethod
    def add_team_member(campaign_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add team member to campaign."""
        url = f"{config.api_url}/campaigns/{campaign_id}/team"
        response = requests.post(
            url,
            json=data,
            headers=APIClient._get_headers()
        )
        return APIClient._handle_response(response)

    @staticmethod
    def list_team_members(campaign_id: int) -> List[Dict[str, Any]]:
        """List campaign team members."""
        url = f"{config.api_url}/campaigns/{campaign_id}/team"
        response = requests.get(url, headers=APIClient._get_headers())
        return APIClient._handle_response(response)

    # ==================== Milestones ====================

    @staticmethod
    def create_milestone(campaign_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create campaign milestone."""
        url = f"{config.api_url}/campaigns/{campaign_id}/milestones"
        response = requests.post(
            url,
            json=data,
            headers=APIClient._get_headers()
        )
        return APIClient._handle_response(response)

    @staticmethod
    def list_milestones(campaign_id: int) -> List[Dict[str, Any]]:
        """List campaign milestones."""
        url = f"{config.api_url}/campaigns/{campaign_id}/milestones"
        response = requests.get(url, headers=APIClient._get_headers())
        return APIClient._handle_response(response)

    # ==================== Analytics ====================

    @staticmethod
    def get_campaign_analytics(campaign_id: int) -> Dict[str, Any]:
        """Get campaign analytics."""
        url = f"{config.api_url}/campaigns/{campaign_id}/analytics"
        response = requests.get(url, headers=APIClient._get_headers())
        return APIClient._handle_response(response)

    @staticmethod
    def get_dashboard_stats() -> Dict[str, Any]:
        """Get dashboard statistics."""
        url = f"{config.api_url}/campaigns/dashboard/stats"
        response = requests.get(url, headers=APIClient._get_headers())
        return APIClient._handle_response(response)

    # ==================== AI & Optimization ====================

    @staticmethod
    def optimize_campaign(campaign_id: int) -> Dict[str, Any]:
        """Request campaign optimization."""
        url = f"{config.api_url}/campaigns/{campaign_id}/optimize"
        response = requests.post(
            url,
            json={"campaign_id": campaign_id},
            headers=APIClient._get_headers()
        )
        return APIClient._handle_response(response)

    @staticmethod
    def generate_report(campaign_id: int, report_type: str = "weekly") -> Dict[str, Any]:
        """Generate campaign report."""
        url = f"{config.api_url}/campaigns/{campaign_id}/reports/generate"
        response = requests.post(
            url,
            params={"report_type": report_type},
            headers=APIClient._get_headers()
        )
        return APIClient._handle_response(response)
