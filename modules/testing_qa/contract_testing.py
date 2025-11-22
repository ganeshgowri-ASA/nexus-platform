"""
Contract Testing Module

Provides ContractValidator, SchemaTester, and APIContractVerifier for contract testing.
"""

import logging
import json
from typing import Dict, Any, List, Optional
from jsonschema import validate, ValidationError, Draft7Validator

logger = logging.getLogger(__name__)


class SchemaTester:
    """
    JSON Schema tester.

    Tests data against JSON schemas.
    """

    def __init__(self):
        """Initialize schema tester."""
        self.logger = logging.getLogger(__name__)

    def validate_against_schema(
        self,
        data: Dict[str, Any],
        schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate data against JSON schema.

        Args:
            data: Data to validate
            schema: JSON schema

        Returns:
            Validation result
        """
        try:
            validate(instance=data, schema=schema)

            return {
                "valid": True,
                "message": "Data matches schema",
            }

        except ValidationError as e:
            return {
                "valid": False,
                "error": str(e.message),
                "path": list(e.path),
                "schema_path": list(e.schema_path),
            }

    def generate_schema_from_example(
        self,
        example_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Generate JSON schema from example data.

        Args:
            example_data: Example data

        Returns:
            Generated schema
        """
        def get_type(value: Any) -> str:
            """Get JSON schema type for value."""
            if isinstance(value, bool):
                return "boolean"
            elif isinstance(value, int):
                return "integer"
            elif isinstance(value, float):
                return "number"
            elif isinstance(value, str):
                return "string"
            elif isinstance(value, list):
                return "array"
            elif isinstance(value, dict):
                return "object"
            elif value is None:
                return "null"
            return "string"

        def build_schema(data: Any) -> Dict[str, Any]:
            """Recursively build schema."""
            if isinstance(data, dict):
                properties = {}
                required = []

                for key, value in data.items():
                    properties[key] = build_schema(value)
                    required.append(key)

                return {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                }

            elif isinstance(data, list):
                if data:
                    items_schema = build_schema(data[0])
                else:
                    items_schema = {}

                return {
                    "type": "array",
                    "items": items_schema,
                }

            else:
                return {"type": get_type(data)}

        schema = build_schema(example_data)
        schema["$schema"] = "http://json-schema.org/draft-07/schema#"

        return schema


class APIContractVerifier:
    """
    API contract verifier.

    Verifies API contracts between producer and consumer.
    """

    def __init__(self):
        """Initialize API contract verifier."""
        self.logger = logging.getLogger(__name__)
        self.schema_tester = SchemaTester()

    def verify_request_contract(
        self,
        request: Dict[str, Any],
        contract: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Verify request against contract.

        Args:
            request: API request
            contract: Request contract

        Returns:
            Verification result
        """
        issues = []

        # Verify HTTP method
        if request.get("method") != contract.get("method"):
            issues.append({
                "type": "method_mismatch",
                "expected": contract.get("method"),
                "actual": request.get("method"),
            })

        # Verify path
        if request.get("path") != contract.get("path"):
            issues.append({
                "type": "path_mismatch",
                "expected": contract.get("path"),
                "actual": request.get("path"),
            })

        # Verify body schema if present
        if contract.get("body_schema"):
            schema_result = self.schema_tester.validate_against_schema(
                request.get("body", {}),
                contract["body_schema"],
            )

            if not schema_result["valid"]:
                issues.append({
                    "type": "body_schema_violation",
                    "error": schema_result.get("error"),
                })

        return {
            "valid": len(issues) == 0,
            "issues": issues,
        }

    def verify_response_contract(
        self,
        response: Dict[str, Any],
        contract: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Verify response against contract.

        Args:
            response: API response
            contract: Response contract

        Returns:
            Verification result
        """
        issues = []

        # Verify status code
        expected_status = contract.get("status_code")
        actual_status = response.get("status_code")

        if expected_status and actual_status != expected_status:
            issues.append({
                "type": "status_code_mismatch",
                "expected": expected_status,
                "actual": actual_status,
            })

        # Verify response schema
        if contract.get("response_schema"):
            schema_result = self.schema_tester.validate_against_schema(
                response.get("body", {}),
                contract["response_schema"],
            )

            if not schema_result["valid"]:
                issues.append({
                    "type": "response_schema_violation",
                    "error": schema_result.get("error"),
                })

        # Verify required headers
        if contract.get("required_headers"):
            response_headers = response.get("headers", {})

            for header in contract["required_headers"]:
                if header not in response_headers:
                    issues.append({
                        "type": "missing_header",
                        "header": header,
                    })

        return {
            "valid": len(issues) == 0,
            "issues": issues,
        }


class ContractValidator:
    """
    Comprehensive contract validator.

    Validates API contracts for both consumer and producer.
    """

    def __init__(self):
        """Initialize contract validator."""
        self.logger = logging.getLogger(__name__)
        self.api_verifier = APIContractVerifier()
        self.schema_tester = SchemaTester()

    def load_contract(self, contract_file: str) -> Dict[str, Any]:
        """
        Load contract from file.

        Args:
            contract_file: Path to contract file

        Returns:
            Contract data
        """
        try:
            with open(contract_file, 'r') as f:
                contract = json.load(f)

            self.logger.info(f"Loaded contract: {contract_file}")
            return contract

        except Exception as e:
            self.logger.error(f"Failed to load contract: {e}")
            return {}

    def save_contract(
        self,
        contract: Dict[str, Any],
        output_file: str,
    ) -> str:
        """
        Save contract to file.

        Args:
            contract: Contract data
            output_file: Output file path

        Returns:
            Output file path
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(contract, f, indent=2)

            self.logger.info(f"Saved contract: {output_file}")
            return output_file

        except Exception as e:
            self.logger.error(f"Failed to save contract: {e}")
            return None

    def validate_interaction(
        self,
        interaction: Dict[str, Any],
        contract: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate API interaction against contract.

        Args:
            interaction: API interaction (request + response)
            contract: Contract specification

        Returns:
            Validation result
        """
        request_result = self.api_verifier.verify_request_contract(
            interaction.get("request", {}),
            contract.get("request", {}),
        )

        response_result = self.api_verifier.verify_response_contract(
            interaction.get("response", {}),
            contract.get("response", {}),
        )

        all_issues = (
            request_result.get("issues", []) +
            response_result.get("issues", [])
        )

        return {
            "valid": len(all_issues) == 0,
            "request_valid": request_result["valid"],
            "response_valid": response_result["valid"],
            "total_issues": len(all_issues),
            "issues": all_issues,
        }

    def validate_multiple_interactions(
        self,
        interactions: List[Dict[str, Any]],
        contract: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate multiple interactions.

        Args:
            interactions: List of interactions
            contract: Contract specification

        Returns:
            Aggregated validation results
        """
        results = []

        for interaction in interactions:
            result = self.validate_interaction(interaction, contract)
            results.append(result)

        total_valid = sum(1 for r in results if r["valid"])

        return {
            "total_interactions": len(interactions),
            "valid_interactions": total_valid,
            "invalid_interactions": len(interactions) - total_valid,
            "pass_rate": (total_valid / len(interactions) * 100) if interactions else 0,
            "results": results,
        }

    def generate_contract_from_traffic(
        self,
        interactions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Generate contract from observed API traffic.

        Args:
            interactions: List of API interactions

        Returns:
            Generated contract
        """
        if not interactions:
            return {}

        # Use first interaction as template
        first_interaction = interactions[0]
        request = first_interaction.get("request", {})
        response = first_interaction.get("response", {})

        # Generate schemas from examples
        request_schema = None
        if request.get("body"):
            request_schema = self.schema_tester.generate_schema_from_example(
                request["body"]
            )

        response_schema = None
        if response.get("body"):
            response_schema = self.schema_tester.generate_schema_from_example(
                response["body"]
            )

        contract = {
            "description": "Auto-generated contract",
            "request": {
                "method": request.get("method"),
                "path": request.get("path"),
                "body_schema": request_schema,
            },
            "response": {
                "status_code": response.get("status_code"),
                "response_schema": response_schema,
                "required_headers": list(response.get("headers", {}).keys()),
            }
        }

        return contract
