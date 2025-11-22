"""AI orchestration for NEXUS platform using Claude."""
from anthropic import Anthropic
import json
from typing import Optional, Dict, Any, List
import pandas as pd
from config.settings import settings


class AIOrchestrator:
    """Centralized AI orchestration using Claude."""

    def __init__(self):
        """Initialize AI orchestrator."""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY) if settings.ANTHROPIC_API_KEY else None
        self.model = settings.DEFAULT_MODEL

    def analyze_spreadsheet(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """
        Analyze spreadsheet data with AI.

        Args:
            df: DataFrame to analyze
            query: User query about the data

        Returns:
            dict: Analysis results with answer, insights, patterns, and suggestions

        Raises:
            ValueError: If AI client not configured
        """
        if not self.client:
            raise ValueError("AI client not configured. Please set ANTHROPIC_API_KEY.")

        # Convert DataFrame to a readable format
        data_summary = self._summarize_dataframe(df)

        prompt = f"""You are analyzing a spreadsheet with the following structure:

{data_summary}

User query: {query}

Provide a detailed analysis addressing the query. Include:
1. Direct answer to the query
2. Relevant insights from the data
3. Any patterns or anomalies noticed
4. Suggestions for further analysis

Return your response as JSON with keys: answer, insights, patterns, suggestions.
Make insights, patterns, and suggestions arrays of strings."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=4096,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        result_text = response.content[0].text

        # Try to parse JSON, fallback to structured response
        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            return {
                "answer": result_text,
                "insights": [],
                "patterns": [],
                "suggestions": []
            }

    def generate_formula(self, description: str, columns: List[str],
                        cell_references: Optional[Dict[str, str]] = None) -> str:
        """
        Generate Excel formula from natural language.

        Args:
            description: Natural language description of the formula
            columns: Available column names
            cell_references: Optional dict of cell references

        Returns:
            str: Excel formula

        Raises:
            ValueError: If AI client not configured
        """
        if not self.client:
            raise ValueError("AI client not configured. Please set ANTHROPIC_API_KEY.")

        context = {
            "columns": columns,
            "cell_references": cell_references or {}
        }

        prompt = f"""Generate an Excel formula for: {description}

Available context:
- Columns: {', '.join(columns)}
- Cell references: {json.dumps(cell_references or {}, indent=2)}

Return ONLY the formula in Excel format (e.g., =SUM(A1:A10)), no explanation.
The formula should start with '=' character."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )

        formula = response.content[0].text.strip()

        # Ensure formula starts with =
        if not formula.startswith('='):
            formula = '=' + formula

        return formula

    def suggest_chart(self, df: pd.DataFrame, goal: str) -> Dict[str, Any]:
        """
        Suggest best chart type for data visualization.

        Args:
            df: DataFrame to visualize
            goal: Visualization goal

        Returns:
            dict: Chart suggestion with type, x_axis, y_axis, and reasoning

        Raises:
            ValueError: If AI client not configured
        """
        if not self.client:
            raise ValueError("AI client not configured. Please set ANTHROPIC_API_KEY.")

        data_summary = self._summarize_dataframe(df)

        prompt = f"""Suggest the best chart type for this data:

{data_summary}

Visualization goal: {goal}

Return a JSON response with:
- chart_type: one of [line, bar, column, pie, scatter, area]
- x_axis: column name for x-axis
- y_axis: column name or names for y-axis (can be array)
- reasoning: why this chart type is best

Return only valid JSON."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text

        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            # Fallback suggestion
            return {
                "chart_type": "bar",
                "x_axis": df.columns[0] if len(df.columns) > 0 else None,
                "y_axis": df.columns[1] if len(df.columns) > 1 else None,
                "reasoning": "Default bar chart suggestion"
            }

    def clean_data_suggestions(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Get AI suggestions for data cleaning.

        Args:
            df: DataFrame to analyze

        Returns:
            list: List of cleaning suggestions

        Raises:
            ValueError: If AI client not configured
        """
        if not self.client:
            raise ValueError("AI client not configured. Please set ANTHROPIC_API_KEY.")

        # Analyze data quality
        data_info = {
            "shape": df.shape,
            "columns": list(df.columns),
            "dtypes": df.dtypes.astype(str).to_dict(),
            "null_counts": df.isnull().sum().to_dict(),
            "sample": df.head(5).to_dict()
        }

        prompt = f"""Analyze this data and suggest cleaning operations:

{json.dumps(data_info, indent=2, default=str)}

Provide suggestions as JSON array of objects with:
- issue: description of the problem
- suggestion: how to fix it
- priority: high, medium, or low

Return only valid JSON array."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=3072,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text

        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            return []

    def detect_anomalies(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """
        Detect anomalies in a numeric column.

        Args:
            df: DataFrame containing the data
            column: Column name to analyze

        Returns:
            dict: Anomaly detection results

        Raises:
            ValueError: If AI client not configured
        """
        if not self.client:
            raise ValueError("AI client not configured. Please set ANTHROPIC_API_KEY.")

        if column not in df.columns:
            raise ValueError(f"Column {column} not found in DataFrame")

        # Get basic statistics
        stats = df[column].describe().to_dict()
        values_sample = df[column].dropna().head(20).tolist()

        prompt = f"""Analyze this numeric data for anomalies:

Column: {column}
Statistics: {json.dumps(stats, indent=2, default=str)}
Sample values: {values_sample}

Identify:
1. Outliers (values significantly different from the norm)
2. Unexpected patterns
3. Data quality issues

Return JSON with:
- has_anomalies: boolean
- anomaly_indices: array of row indices with anomalies
- description: explanation of anomalies found
- severity: low, medium, or high

Return only valid JSON."""

        response = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}]
        )

        result_text = response.content[0].text

        try:
            return json.loads(result_text)
        except json.JSONDecodeError:
            return {
                "has_anomalies": False,
                "anomaly_indices": [],
                "description": "Could not analyze",
                "severity": "low"
            }

    @staticmethod
    def _summarize_dataframe(df: pd.DataFrame, max_rows: int = 10) -> str:
        """
        Create a summary of DataFrame for AI context.

        Args:
            df: DataFrame to summarize
            max_rows: Maximum number of sample rows

        Returns:
            str: Formatted summary
        """
        summary = f"Shape: {df.shape[0]} rows × {df.shape[1]} columns\n\n"
        summary += "Columns:\n"

        for col in df.columns:
            dtype = df[col].dtype
            null_count = df[col].isnull().sum()
            sample = df[col].dropna().head(3).tolist()

            summary += f"  - {col} ({dtype})"
            if null_count > 0:
                summary += f" [{null_count} nulls]"
            summary += f": {sample}\n"

        summary += f"\nFirst {min(max_rows, len(df))} rows:\n"
        summary += df.head(max_rows).to_string()

        return summary
