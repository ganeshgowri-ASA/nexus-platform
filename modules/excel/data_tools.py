"""Data manipulation tools for spreadsheets."""
from typing import List, Optional, Any, Callable
import pandas as pd
import re


class DataTools:
    """Tools for data manipulation: sort, filter, find/replace."""

    @staticmethod
    def sort_data(df: pd.DataFrame, columns: List[str],
                 ascending: Optional[List[bool]] = None) -> pd.DataFrame:
        """
        Sort data by columns.

        Args:
            df: DataFrame to sort
            columns: Columns to sort by
            ascending: Sort order for each column

        Returns:
            Sorted DataFrame
        """
        if ascending is None:
            ascending = [True] * len(columns)

        return df.sort_values(by=columns, ascending=ascending).reset_index(drop=True)

    @staticmethod
    def filter_data(df: pd.DataFrame, filters: dict) -> pd.DataFrame:
        """
        Filter data based on conditions.

        Args:
            df: DataFrame to filter
            filters: Dictionary of column -> filter condition

        Returns:
            Filtered DataFrame
        """
        filtered = df.copy()

        for column, condition in filters.items():
            if column not in filtered.columns:
                continue

            if callable(condition):
                filtered = filtered[filtered[column].apply(condition)]
            elif isinstance(condition, (list, tuple)):
                filtered = filtered[filtered[column].isin(condition)]
            else:
                filtered = filtered[filtered[column] == condition]

        return filtered

    @staticmethod
    def auto_filter(df: pd.DataFrame, column: str, values: List[Any]) -> pd.DataFrame:
        """
        Apply auto-filter to a column.

        Args:
            df: DataFrame
            column: Column name
            values: Values to include

        Returns:
            Filtered DataFrame
        """
        return df[df[column].isin(values)]

    @staticmethod
    def advanced_filter(df: pd.DataFrame, query: str) -> pd.DataFrame:
        """
        Apply advanced filter using pandas query.

        Args:
            df: DataFrame
            query: Query string (e.g., "age > 30 and city == 'NYC'")

        Returns:
            Filtered DataFrame
        """
        try:
            return df.query(query)
        except Exception as e:
            raise ValueError(f"Invalid query: {str(e)}")

    @staticmethod
    def find_values(df: pd.DataFrame, search_term: str,
                   case_sensitive: bool = False,
                   whole_word: bool = False) -> List[tuple]:
        """
        Find values in DataFrame.

        Args:
            df: DataFrame to search
            search_term: Term to search for
            case_sensitive: Whether search is case sensitive
            whole_word: Whether to match whole word only

        Returns:
            List of (row, col) tuples where value found
        """
        results = []

        for col_idx, column in enumerate(df.columns):
            for row_idx, value in enumerate(df[column]):
                value_str = str(value)

                if not case_sensitive:
                    value_str = value_str.lower()
                    search_term = search_term.lower()

                if whole_word:
                    if value_str == search_term:
                        results.append((row_idx, col_idx))
                else:
                    if search_term in value_str:
                        results.append((row_idx, col_idx))

        return results

    @staticmethod
    def replace_values(df: pd.DataFrame, find: str, replace: str,
                      case_sensitive: bool = False,
                      whole_word: bool = False,
                      columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Find and replace values.

        Args:
            df: DataFrame
            find: Value to find
            replace: Replacement value
            case_sensitive: Whether replacement is case sensitive
            whole_word: Whether to match whole word only
            columns: Specific columns to search (None = all)

        Returns:
            DataFrame with replacements made
        """
        result = df.copy()
        target_columns = columns if columns else result.columns

        for column in target_columns:
            if column not in result.columns:
                continue

            if whole_word:
                if case_sensitive:
                    result[column] = result[column].replace(find, replace)
                else:
                    result[column] = result[column].str.replace(
                        find, replace, case=False, regex=False
                    )
            else:
                if case_sensitive:
                    result[column] = result[column].astype(str).str.replace(
                        find, replace, regex=False
                    )
                else:
                    result[column] = result[column].astype(str).str.replace(
                        find, replace, case=False, regex=False
                    )

        return result

    @staticmethod
    def remove_duplicates(df: pd.DataFrame,
                         columns: Optional[List[str]] = None,
                         keep: str = 'first') -> pd.DataFrame:
        """
        Remove duplicate rows.

        Args:
            df: DataFrame
            columns: Columns to consider for duplicates (None = all)
            keep: Which duplicates to keep ('first', 'last', False)

        Returns:
            DataFrame with duplicates removed
        """
        return df.drop_duplicates(subset=columns, keep=keep).reset_index(drop=True)

    @staticmethod
    def text_to_columns(df: pd.DataFrame, column: str, delimiter: str = ',',
                       new_column_names: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Split text in a column into multiple columns.

        Args:
            df: DataFrame
            column: Column to split
            delimiter: Delimiter to split on
            new_column_names: Names for new columns

        Returns:
            DataFrame with new columns
        """
        result = df.copy()

        # Split the column
        split_data = result[column].str.split(delimiter, expand=True)

        # Assign new column names
        if new_column_names:
            split_data.columns = new_column_names[:split_data.shape[1]]
        else:
            split_data.columns = [f"{column}_{i+1}" for i in range(split_data.shape[1])]

        # Drop original column and add new columns
        result = result.drop(columns=[column])
        result = pd.concat([result, split_data], axis=1)

        return result

    @staticmethod
    def fill_down(df: pd.DataFrame, columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Fill down empty cells with value from above.

        Args:
            df: DataFrame
            columns: Columns to fill (None = all)

        Returns:
            DataFrame with filled values
        """
        result = df.copy()
        target_columns = columns if columns else result.columns

        for column in target_columns:
            if column in result.columns:
                result[column] = result[column].fillna(method='ffill')

        return result

    @staticmethod
    def transpose(df: pd.DataFrame) -> pd.DataFrame:
        """
        Transpose DataFrame (swap rows and columns).

        Args:
            df: DataFrame to transpose

        Returns:
            Transposed DataFrame
        """
        return df.transpose()

    @staticmethod
    def group_by(df: pd.DataFrame, group_columns: List[str],
                agg_dict: dict) -> pd.DataFrame:
        """
        Group data and apply aggregations.

        Args:
            df: DataFrame
            group_columns: Columns to group by
            agg_dict: Dictionary of column -> aggregation function

        Returns:
            Grouped DataFrame
        """
        return df.groupby(group_columns).agg(agg_dict).reset_index()

    @staticmethod
    def merge_data(df1: pd.DataFrame, df2: pd.DataFrame,
                  on: Optional[str] = None,
                  left_on: Optional[str] = None,
                  right_on: Optional[str] = None,
                  how: str = 'inner') -> pd.DataFrame:
        """
        Merge two DataFrames.

        Args:
            df1: First DataFrame
            df2: Second DataFrame
            on: Column to join on (if same in both)
            left_on: Column in df1 to join on
            right_on: Column in df2 to join on
            how: Join type ('inner', 'outer', 'left', 'right')

        Returns:
            Merged DataFrame
        """
        if on:
            return pd.merge(df1, df2, on=on, how=how)
        elif left_on and right_on:
            return pd.merge(df1, df2, left_on=left_on, right_on=right_on, how=how)
        else:
            raise ValueError("Must specify 'on' or both 'left_on' and 'right_on'")

    @staticmethod
    def clean_data(df: pd.DataFrame, operations: List[str]) -> pd.DataFrame:
        """
        Clean data with various operations.

        Args:
            df: DataFrame to clean
            operations: List of operations ('trim', 'remove_empty_rows', etc.)

        Returns:
            Cleaned DataFrame
        """
        result = df.copy()

        for operation in operations:
            if operation == 'trim':
                # Trim whitespace from string columns
                for column in result.select_dtypes(include=['object']):
                    result[column] = result[column].str.strip()

            elif operation == 'remove_empty_rows':
                # Remove rows where all values are NaN
                result = result.dropna(how='all')

            elif operation == 'remove_empty_columns':
                # Remove columns where all values are NaN
                result = result.dropna(axis=1, how='all')

            elif operation == 'fill_na':
                # Fill NaN with empty string
                result = result.fillna('')

            elif operation == 'remove_duplicates':
                result = result.drop_duplicates()

        return result.reset_index(drop=True)

    @staticmethod
    def apply_formula_to_column(df: pd.DataFrame, column: str,
                               formula: Callable[[Any], Any]) -> pd.DataFrame:
        """
        Apply a formula to a column.

        Args:
            df: DataFrame
            column: Column to apply formula to
            formula: Function to apply

        Returns:
            DataFrame with formula applied
        """
        result = df.copy()
        result[column] = result[column].apply(formula)
        return result

    @staticmethod
    def create_calculated_column(df: pd.DataFrame, new_column: str,
                                formula: Callable[[pd.Series], Any]) -> pd.DataFrame:
        """
        Create a new calculated column.

        Args:
            df: DataFrame
            new_column: Name of new column
            formula: Function that takes the row and returns value

        Returns:
            DataFrame with new column
        """
        result = df.copy()
        result[new_column] = result.apply(formula, axis=1)
        return result
