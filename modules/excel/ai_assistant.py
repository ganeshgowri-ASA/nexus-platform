"""AI assistant for spreadsheet analysis and automation."""
from typing import List, Optional, Dict, Any
import pandas as pd
from core.ai.orchestrator import AIOrchestrator


class SpreadsheetAIAssistant:
    """AI assistant for intelligent spreadsheet operations."""

    def __init__(self):
        """Initialize AI assistant."""
        self.ai = AIOrchestrator()

    def analyze_data(self, df: pd.DataFrame, query: str) -> Dict[str, Any]:
        """
        Analyze spreadsheet data with natural language query.

        Args:
            df: DataFrame to analyze
            query: Natural language query

        Returns:
            Analysis results

        Example:
            >>> assistant.analyze_data(df, "What are the top 10 sales by region?")
        """
        return self.ai.analyze_spreadsheet(df, query)

    def suggest_formula(self, description: str, df: pd.DataFrame) -> str:
        """
        Generate formula from natural language description.

        Args:
            description: Natural language description
            df: DataFrame context

        Returns:
            Excel formula

        Example:
            >>> assistant.suggest_formula("sum of all sales", df)
            "=SUM(B2:B100)"
        """
        columns = list(df.columns)
        return self.ai.generate_formula(description, columns)

    def suggest_chart(self, df: pd.DataFrame, goal: str) -> Dict[str, Any]:
        """
        Suggest best chart type for visualization.

        Args:
            df: DataFrame to visualize
            goal: Visualization goal

        Returns:
            Chart suggestion

        Example:
            >>> assistant.suggest_chart(df, "show sales trend over time")
            {"chart_type": "line", "x_axis": "date", "y_axis": "sales"}
        """
        return self.ai.suggest_chart(df, goal)

    def clean_data_suggestions(self, df: pd.DataFrame) -> List[Dict[str, str]]:
        """
        Get AI suggestions for data cleaning.

        Args:
            df: DataFrame to analyze

        Returns:
            List of cleaning suggestions

        Example:
            >>> assistant.clean_data_suggestions(df)
            [
                {"issue": "Missing values in column A", "suggestion": "Fill with median", "priority": "high"},
                ...
            ]
        """
        return self.ai.clean_data_suggestions(df)

    def detect_anomalies(self, df: pd.DataFrame, column: str) -> Dict[str, Any]:
        """
        Detect anomalies in data.

        Args:
            df: DataFrame
            column: Column to analyze

        Returns:
            Anomaly detection results

        Example:
            >>> assistant.detect_anomalies(df, "sales")
            {
                "has_anomalies": True,
                "anomaly_indices": [5, 17, 23],
                "description": "Unusually high values detected",
                "severity": "medium"
            }
        """
        return self.ai.detect_anomalies(df, column)

    def auto_format_suggestions(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Suggest formatting for data.

        Args:
            df: DataFrame

        Returns:
            List of formatting suggestions
        """
        suggestions = []

        for col in df.columns:
            # Detect column type and suggest format
            if pd.api.types.is_numeric_dtype(df[col]):
                # Check if looks like currency
                if 'price' in col.lower() or 'cost' in col.lower() or 'amount' in col.lower():
                    suggestions.append({
                        'column': col,
                        'format': 'currency',
                        'reasoning': 'Column name suggests monetary values'
                    })
                # Check if looks like percentage
                elif 'percent' in col.lower() or 'rate' in col.lower():
                    suggestions.append({
                        'column': col,
                        'format': 'percentage',
                        'reasoning': 'Column name suggests percentage values'
                    })
                else:
                    suggestions.append({
                        'column': col,
                        'format': 'number',
                        'reasoning': 'Numeric data'
                    })

            elif pd.api.types.is_datetime64_any_dtype(df[col]):
                suggestions.append({
                    'column': col,
                    'format': 'date',
                    'reasoning': 'Date/time data detected'
                })

        return suggestions

    def generate_pivot_table_suggestion(self, df: pd.DataFrame,
                                       goal: str) -> Dict[str, Any]:
        """
        Suggest pivot table configuration.

        Args:
            df: DataFrame
            goal: Analysis goal

        Returns:
            Pivot table configuration

        Example:
            >>> assistant.generate_pivot_table_suggestion(df, "sales by region and product")
            {
                "rows": ["region"],
                "columns": ["product"],
                "values": {"sales": "sum"},
                "reasoning": "..."
            }
        """
        # Use AI to analyze goal and suggest configuration
        # Simplified implementation
        return {
            "rows": [df.columns[0]],
            "columns": [df.columns[1]] if len(df.columns) > 1 else [],
            "values": {df.columns[-1]: "sum"} if len(df.columns) > 2 else {},
            "reasoning": "Basic pivot configuration based on column structure"
        }

    def auto_complete_data(self, df: pd.DataFrame, column: str,
                          partial_values: List[str]) -> List[str]:
        """
        Auto-complete data values using AI.

        Args:
            df: DataFrame
            column: Column name
            partial_values: Partial values to complete

        Returns:
            List of completed values
        """
        # Use existing column values as context
        existing_values = df[column].dropna().unique().tolist()

        # In production, use AI for smart completion
        # For now, simple matching
        suggestions = []
        for partial in partial_values:
            matches = [v for v in existing_values if str(partial).lower() in str(v).lower()]
            suggestions.extend(matches[:5])  # Top 5 matches

        return suggestions

    def explain_formula(self, formula: str) -> str:
        """
        Explain what a formula does in plain English.

        Args:
            formula: Excel formula

        Returns:
            Plain English explanation

        Example:
            >>> assistant.explain_formula("=VLOOKUP(A2,B:C,2,FALSE)")
            "This formula looks up the value in cell A2 within the range B:C and returns..."
        """
        # Use AI to explain formula
        # Simplified implementation
        if formula.startswith('=SUM'):
            return "This formula calculates the sum of the specified range."
        elif formula.startswith('=AVERAGE'):
            return "This formula calculates the average of the specified range."
        elif formula.startswith('=IF'):
            return "This is a conditional formula that returns different values based on a condition."
        else:
            return f"Formula: {formula}"

    def predict_next_values(self, df: pd.DataFrame, column: str,
                           periods: int = 5) -> List[Any]:
        """
        Predict next values in a series.

        Args:
            df: DataFrame
            column: Column with time series data
            periods: Number of periods to predict

        Returns:
            List of predicted values
        """
        # Simplified prediction - in production use proper forecasting
        values = df[column].dropna().values

        if len(values) < 2:
            return [values[-1]] * periods if len(values) > 0 else [0] * periods

        # Simple linear prediction
        trend = (values[-1] - values[0]) / len(values)
        predictions = [values[-1] + trend * (i + 1) for i in range(periods)]

        return predictions

    def generate_report_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate an AI-powered summary report of the data.

        Args:
            df: DataFrame to summarize

        Returns:
            Summary report

        Example:
            >>> assistant.generate_report_summary(df)
            {
                "overview": "Dataset contains 1000 rows...",
                "key_insights": ["Sales increased by 15%", ...],
                "recommendations": ["Consider adding..."],
                "data_quality": {"completeness": 95, "issues": [...]}
            }
        """
        # Calculate basic statistics
        total_rows = len(df)
        total_cols = len(df.columns)
        missing_values = df.isnull().sum().sum()
        completeness = 100 * (1 - missing_values / (total_rows * total_cols))

        # Identify numeric columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()

        return {
            "overview": f"Dataset contains {total_rows} rows and {total_cols} columns.",
            "numeric_columns": numeric_cols,
            "data_quality": {
                "completeness": round(completeness, 2),
                "missing_values": int(missing_values),
                "duplicate_rows": df.duplicated().sum()
            },
            "key_insights": [
                f"Dataset has {total_rows} records",
                f"Data is {completeness:.1f}% complete",
                f"Contains {len(numeric_cols)} numeric columns"
            ],
            "recommendations": [
                "Consider removing duplicate rows" if df.duplicated().sum() > 0 else None,
                "Fill or remove missing values" if missing_values > 0 else None
            ]
        }

    def smart_search(self, df: pd.DataFrame, query: str) -> pd.DataFrame:
        """
        Smart search across all columns using natural language.

        Args:
            df: DataFrame to search
            query: Natural language search query

        Returns:
            Filtered DataFrame

        Example:
            >>> assistant.smart_search(df, "sales over 1000 in California")
        """
        # Simplified implementation - in production use NLP
        # For now, simple keyword matching
        mask = pd.Series([False] * len(df))

        for col in df.columns:
            mask |= df[col].astype(str).str.contains(query, case=False, na=False)

        return df[mask]
