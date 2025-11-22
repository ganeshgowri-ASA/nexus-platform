"""
Security Testing Module

Provides SecurityScanner, VulnerabilityDetector, and PenetrationTester for security testing.
"""

import logging
import re
import hashlib
from typing import Dict, Any, List, Optional
import httpx

logger = logging.getLogger(__name__)


class VulnerabilityDetector:
    """
    Vulnerability detector for common security issues.

    Scans for OWASP Top 10 and other vulnerabilities.
    """

    def __init__(self):
        """Initialize vulnerability detector."""
        self.logger = logging.getLogger(__name__)
        self.vulnerabilities: List[Dict[str, Any]] = []

    def detect_sql_injection(self, code: str) -> List[Dict[str, Any]]:
        """
        Detect potential SQL injection vulnerabilities.

        Args:
            code: Code to analyze

        Returns:
            List of detected vulnerabilities
        """
        vulns = []

        # Patterns that might indicate SQL injection
        patterns = [
            r"execute\(['\"].*\%s.*['\"]",
            r"cursor\.execute\(['\"].*\+.*['\"]",
            r"SELECT.*WHERE.*\+",
            r"\.format\(.*SELECT",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                vulns.append({
                    "type": "SQL_INJECTION",
                    "severity": "HIGH",
                    "line": code[:match.start()].count('\n') + 1,
                    "description": "Potential SQL injection vulnerability detected",
                    "code_snippet": match.group(),
                })

        return vulns

    def detect_xss(self, code: str) -> List[Dict[str, Any]]:
        """
        Detect potential XSS vulnerabilities.

        Args:
            code: Code to analyze

        Returns:
            List of detected vulnerabilities
        """
        vulns = []

        # Patterns for XSS
        patterns = [
            r"innerHTML\s*=",
            r"document\.write\(",
            r"\.html\([^)]*\+",
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                vulns.append({
                    "type": "XSS",
                    "severity": "HIGH",
                    "line": code[:match.start()].count('\n') + 1,
                    "description": "Potential XSS vulnerability detected",
                    "code_snippet": match.group(),
                })

        return vulns

    def detect_hardcoded_secrets(self, code: str) -> List[Dict[str, Any]]:
        """
        Detect hardcoded secrets and credentials.

        Args:
            code: Code to analyze

        Returns:
            List of detected secrets
        """
        vulns = []

        # Patterns for secrets
        patterns = [
            (r"password\s*=\s*['\"][^'\"]+['\"]", "HARDCODED_PASSWORD"),
            (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "HARDCODED_API_KEY"),
            (r"secret\s*=\s*['\"][^'\"]+['\"]", "HARDCODED_SECRET"),
            (r"token\s*=\s*['\"][^'\"]+['\"]", "HARDCODED_TOKEN"),
            (r"aws_access_key_id\s*=\s*['\"][^'\"]+['\"]", "AWS_CREDENTIALS"),
        ]

        for pattern, vuln_type in patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                vulns.append({
                    "type": vuln_type,
                    "severity": "CRITICAL",
                    "line": code[:match.start()].count('\n') + 1,
                    "description": f"Hardcoded {vuln_type.lower().replace('_', ' ')} detected",
                    "code_snippet": match.group()[:50] + "...",
                })

        return vulns

    def detect_weak_crypto(self, code: str) -> List[Dict[str, Any]]:
        """
        Detect weak cryptographic implementations.

        Args:
            code: Code to analyze

        Returns:
            List of detected weaknesses
        """
        vulns = []

        # Patterns for weak crypto
        patterns = [
            (r"md5\(", "WEAK_HASH_MD5"),
            (r"sha1\(", "WEAK_HASH_SHA1"),
            (r"DES\.new\(", "WEAK_CIPHER_DES"),
            (r"random\.random\(", "WEAK_RANDOM"),
        ]

        for pattern, vuln_type in patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                vulns.append({
                    "type": vuln_type,
                    "severity": "MEDIUM",
                    "line": code[:match.start()].count('\n') + 1,
                    "description": f"Weak cryptographic function detected: {vuln_type}",
                    "code_snippet": match.group(),
                })

        return vulns


class PenetrationTester:
    """
    Penetration tester for active security testing.

    Tests for authentication, authorization, and input validation issues.
    """

    def __init__(self, base_url: str):
        """
        Initialize penetration tester.

        Args:
            base_url: Base URL to test
        """
        self.base_url = base_url.rstrip("/")
        self.logger = logging.getLogger(__name__)
        self.client = httpx.Client(timeout=30)

    async def test_authentication_bypass(
        self,
        endpoint: str,
    ) -> Dict[str, Any]:
        """
        Test for authentication bypass vulnerabilities.

        Args:
            endpoint: Protected endpoint to test

        Returns:
            Test results
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        vulnerabilities = []

        # Test 1: Access without credentials
        try:
            response = self.client.get(url)
            if response.status_code == 200:
                vulnerabilities.append({
                    "type": "AUTH_BYPASS",
                    "severity": "CRITICAL",
                    "description": "Endpoint accessible without authentication",
                    "endpoint": endpoint,
                })
        except:
            pass

        # Test 2: SQL injection in auth
        sql_payloads = [
            "' OR '1'='1",
            "admin' --",
            "' OR 1=1--",
        ]

        for payload in sql_payloads:
            try:
                response = self.client.post(
                    url,
                    json={"username": payload, "password": payload}
                )
                if response.status_code == 200:
                    vulnerabilities.append({
                        "type": "SQL_INJECTION_AUTH",
                        "severity": "CRITICAL",
                        "description": "SQL injection in authentication",
                        "payload": payload,
                    })
            except:
                pass

        return {
            "endpoint": endpoint,
            "vulnerabilities_found": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
        }

    async def test_authorization(
        self,
        endpoint: str,
        valid_token: str,
    ) -> Dict[str, Any]:
        """
        Test for authorization issues.

        Args:
            endpoint: Endpoint to test
            valid_token: Valid authorization token

        Returns:
            Test results
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        vulnerabilities = []

        # Test 1: Privilege escalation
        headers = {"Authorization": f"Bearer {valid_token}"}

        try:
            # Try admin endpoints with regular user token
            admin_paths = ["/admin", "/users/all", "/config"]

            for path in admin_paths:
                response = self.client.get(f"{self.base_url}{path}", headers=headers)
                if response.status_code == 200:
                    vulnerabilities.append({
                        "type": "PRIVILEGE_ESCALATION",
                        "severity": "HIGH",
                        "description": f"Unauthorized access to {path}",
                        "endpoint": path,
                    })
        except:
            pass

        # Test 2: Horizontal privilege escalation (IDOR)
        try:
            # Test accessing other users' resources
            user_ids = ["1", "2", "999", "admin"]

            for user_id in user_ids:
                response = self.client.get(
                    f"{url}/{user_id}",
                    headers=headers,
                )
                if response.status_code == 200:
                    vulnerabilities.append({
                        "type": "IDOR",
                        "severity": "HIGH",
                        "description": "Insecure Direct Object Reference detected",
                        "user_id": user_id,
                    })
        except:
            pass

        return {
            "endpoint": endpoint,
            "vulnerabilities_found": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
        }

    async def test_input_validation(
        self,
        endpoint: str,
        method: str = "POST",
    ) -> Dict[str, Any]:
        """
        Test input validation.

        Args:
            endpoint: Endpoint to test
            method: HTTP method

        Returns:
            Test results
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        vulnerabilities = []

        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
        ]

        for payload in xss_payloads:
            try:
                response = self.client.request(
                    method,
                    url,
                    json={"input": payload},
                )
                if payload in response.text:
                    vulnerabilities.append({
                        "type": "XSS",
                        "severity": "HIGH",
                        "description": "Reflected XSS vulnerability",
                        "payload": payload,
                    })
            except:
                pass

        return {
            "endpoint": endpoint,
            "vulnerabilities_found": len(vulnerabilities),
            "vulnerabilities": vulnerabilities,
        }


class SecurityScanner:
    """
    Comprehensive security scanner.

    Orchestrates security testing across multiple dimensions.
    """

    def __init__(self, base_url: str = None):
        """
        Initialize security scanner.

        Args:
            base_url: Base URL for API testing
        """
        self.base_url = base_url
        self.vulnerability_detector = VulnerabilityDetector()
        self.penetration_tester = PenetrationTester(base_url) if base_url else None
        self.logger = logging.getLogger(__name__)

    async def scan_code(self, code: str, file_path: str = None) -> Dict[str, Any]:
        """
        Scan code for vulnerabilities.

        Args:
            code: Source code to scan
            file_path: Optional file path

        Returns:
            Scan results
        """
        self.logger.info(f"Scanning code{f' from {file_path}' if file_path else ''}")

        vulnerabilities = []

        # Run all detectors
        vulnerabilities.extend(self.vulnerability_detector.detect_sql_injection(code))
        vulnerabilities.extend(self.vulnerability_detector.detect_xss(code))
        vulnerabilities.extend(self.vulnerability_detector.detect_hardcoded_secrets(code))
        vulnerabilities.extend(self.vulnerability_detector.detect_weak_crypto(code))

        # Categorize by severity
        by_severity = {
            "CRITICAL": [],
            "HIGH": [],
            "MEDIUM": [],
            "LOW": [],
        }

        for vuln in vulnerabilities:
            by_severity[vuln["severity"]].append(vuln)

        return {
            "file_path": file_path,
            "total_vulnerabilities": len(vulnerabilities),
            "by_severity": {
                "critical": len(by_severity["CRITICAL"]),
                "high": len(by_severity["HIGH"]),
                "medium": len(by_severity["MEDIUM"]),
                "low": len(by_severity["LOW"]),
            },
            "vulnerabilities": vulnerabilities,
        }

    async def scan_api(
        self,
        endpoints: List[str],
        auth_token: str = None,
    ) -> Dict[str, Any]:
        """
        Scan API endpoints for security issues.

        Args:
            endpoints: List of endpoints to test
            auth_token: Optional authentication token

        Returns:
            Scan results
        """
        if not self.penetration_tester:
            raise ValueError("Base URL required for API scanning")

        self.logger.info(f"Scanning {len(endpoints)} API endpoints")

        results = []

        for endpoint in endpoints:
            endpoint_results = {
                "endpoint": endpoint,
                "vulnerabilities": [],
            }

            # Test authentication
            auth_result = await self.penetration_tester.test_authentication_bypass(endpoint)
            endpoint_results["vulnerabilities"].extend(auth_result.get("vulnerabilities", []))

            # Test authorization if token provided
            if auth_token:
                authz_result = await self.penetration_tester.test_authorization(endpoint, auth_token)
                endpoint_results["vulnerabilities"].extend(authz_result.get("vulnerabilities", []))

            # Test input validation
            input_result = await self.penetration_tester.test_input_validation(endpoint)
            endpoint_results["vulnerabilities"].extend(input_result.get("vulnerabilities", []))

            results.append(endpoint_results)

        total_vulns = sum(len(r["vulnerabilities"]) for r in results)

        return {
            "endpoints_scanned": len(endpoints),
            "total_vulnerabilities": total_vulns,
            "results": results,
        }

    def generate_security_report(
        self,
        scan_results: Dict[str, Any],
    ) -> str:
        """
        Generate security scan report.

        Args:
            scan_results: Scan results

        Returns:
            Report text
        """
        report = "# Security Scan Report\n\n"

        if "file_path" in scan_results:
            report += f"## File: {scan_results['file_path']}\n\n"

        report += f"**Total Vulnerabilities:** {scan_results['total_vulnerabilities']}\n\n"

        if "by_severity" in scan_results:
            report += "### By Severity\n\n"
            for severity, count in scan_results["by_severity"].items():
                report += f"- {severity.upper()}: {count}\n"

        return report
