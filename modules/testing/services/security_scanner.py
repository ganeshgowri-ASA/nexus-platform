"""
Security testing and vulnerability scanning
"""
import logging
import requests
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class SecurityScanner:
    """Security vulnerability scanner"""

    def __init__(self):
        self.vulnerabilities = []

    def run_scan(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Run security scan"""
        try:
            test_data = test_case.get("test_data", {})
            scan_type = test_data.get("scan_type", "basic")

            results = []

            if scan_type == "basic":
                results.extend(self._basic_security_checks(test_data))
            elif scan_type == "owasp":
                results.extend(self._owasp_top10_scan(test_data))
            elif scan_type == "full":
                results.extend(self._basic_security_checks(test_data))
                results.extend(self._owasp_top10_scan(test_data))

            # Count vulnerabilities by severity
            critical = len([v for v in results if v.get("severity") == "critical"])
            high = len([v for v in results if v.get("severity") == "high"])
            medium = len([v for v in results if v.get("severity") == "medium"])
            low = len([v for v in results if v.get("severity") == "low"])

            # Determine status
            if critical > 0 or high > 0:
                status = "failed"
            elif medium > 0:
                status = "warning"
            else:
                status = "passed"

            return {
                "status": status,
                "output": f"Security scan completed: {len(results)} issues found",
                "vulnerabilities": results,
                "summary": {
                    "total": len(results),
                    "critical": critical,
                    "high": high,
                    "medium": medium,
                    "low": low
                }
            }

        except Exception as e:
            logger.error(f"Security scan error: {e}")
            return {
                "status": "error",
                "error_message": str(e)
            }

    def _basic_security_checks(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Basic security checks"""
        vulnerabilities = []
        url = config.get("url")

        if not url:
            return vulnerabilities

        try:
            # Check security headers
            response = requests.get(url, timeout=10)
            headers = response.headers

            # Check for missing security headers
            security_headers = {
                "X-Content-Type-Options": "nosniff",
                "X-Frame-Options": "DENY or SAMEORIGIN",
                "X-XSS-Protection": "1; mode=block",
                "Strict-Transport-Security": "max-age=31536000",
                "Content-Security-Policy": "Defined CSP"
            }

            for header, expected in security_headers.items():
                if header not in headers:
                    vulnerabilities.append({
                        "type": "missing_security_header",
                        "severity": "medium",
                        "description": f"Missing security header: {header}",
                        "recommendation": f"Add header: {header}: {expected}"
                    })

            # Check for sensitive information disclosure
            if "server" in headers:
                vulnerabilities.append({
                    "type": "information_disclosure",
                    "severity": "low",
                    "description": f"Server header exposes server information: {headers['server']}",
                    "recommendation": "Remove or obfuscate server header"
                })

            # Check for insecure protocols
            if url.startswith("http://"):
                vulnerabilities.append({
                    "type": "insecure_protocol",
                    "severity": "high",
                    "description": "Using insecure HTTP protocol",
                    "recommendation": "Use HTTPS instead of HTTP"
                })

        except Exception as e:
            logger.error(f"Basic security check error: {e}")

        return vulnerabilities

    def _owasp_top10_scan(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """OWASP Top 10 vulnerability scan"""
        vulnerabilities = []
        url = config.get("url")

        if not url:
            return vulnerabilities

        try:
            # SQL Injection test
            sql_payloads = ["' OR '1'='1", "1' OR '1'='1' --", "' OR 1=1--"]
            for payload in sql_payloads:
                test_url = f"{url}?id={payload}"
                try:
                    response = requests.get(test_url, timeout=5)
                    if "sql" in response.text.lower() or "syntax" in response.text.lower():
                        vulnerabilities.append({
                            "type": "sql_injection",
                            "severity": "critical",
                            "description": "Potential SQL injection vulnerability detected",
                            "recommendation": "Use parameterized queries and input validation"
                        })
                        break
                except:
                    pass

            # XSS test
            xss_payloads = ["<script>alert('XSS')</script>", "<img src=x onerror=alert('XSS')>"]
            for payload in xss_payloads:
                test_url = f"{url}?q={payload}"
                try:
                    response = requests.get(test_url, timeout=5)
                    if payload in response.text:
                        vulnerabilities.append({
                            "type": "xss",
                            "severity": "high",
                            "description": "Potential Cross-Site Scripting (XSS) vulnerability detected",
                            "recommendation": "Implement proper input sanitization and output encoding"
                        })
                        break
                except:
                    pass

            # Open redirect test
            redirect_payload = "http://evil.com"
            test_url = f"{url}?redirect={redirect_payload}"
            try:
                response = requests.get(test_url, timeout=5, allow_redirects=False)
                if response.status_code in [301, 302] and redirect_payload in response.headers.get("Location", ""):
                    vulnerabilities.append({
                        "type": "open_redirect",
                        "severity": "medium",
                        "description": "Potential open redirect vulnerability detected",
                        "recommendation": "Validate and whitelist redirect URLs"
                    })
            except:
                pass

        except Exception as e:
            logger.error(f"OWASP scan error: {e}")

        return vulnerabilities
