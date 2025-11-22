"""Tests for Excel module."""
import pytest
import pandas as pd
from modules.excel.formula_engine import FormulaEngine
from modules.excel.cell_manager import CellManager, CellStyle, column_letter, column_index
from modules.excel.data_validator import DataValidator, ValidationRule, ValidationType, ValidationOperator
from modules.excel.data_tools import DataTools
from modules.excel.editor import SpreadsheetEditor


class TestFormulaEngine:
    """Test formula engine."""

    def test_sum_formula(self):
        """Test SUM formula."""
        engine = FormulaEngine()
        result = engine.evaluate("=SUM(1,2,3,4,5)")
        assert result == 15

    def test_average_formula(self):
        """Test AVERAGE formula."""
        engine = FormulaEngine()
        result = engine.evaluate("=AVERAGE(10,20,30)")
        assert result == 20

    def test_if_formula(self):
        """Test IF formula."""
        engine = FormulaEngine()
        result = engine.evaluate("=IF(TRUE,10,20)")
        assert result == 10

    def test_concatenate_formula(self):
        """Test CONCATENATE formula."""
        engine = FormulaEngine()
        result = engine.evaluate('=CONCATENATE("Hello"," ","World")')
        assert result == "Hello World"

    def test_round_formula(self):
        """Test ROUND formula."""
        engine = FormulaEngine()
        result = engine.evaluate("=ROUND(3.14159,2)")
        assert result == 3.14


class TestCellManager:
    """Test cell manager."""

    def test_create_cell_manager(self):
        """Test creating cell manager."""
        manager = CellManager(rows=100, cols=26)
        assert manager.rows == 100
        assert manager.cols == 26

    def test_set_cell_value(self):
        """Test setting cell value."""
        manager = CellManager()
        manager.set_cell_value(0, 0, "Test")
        assert manager.get_cell(0, 0).value == "Test"

    def test_cell_style(self):
        """Test cell styling."""
        manager = CellManager()
        style = CellStyle(bold=True, font_color="#FF0000")
        manager.set_cell_style(0, 0, style)
        assert manager.get_cell(0, 0).style.bold is True
        assert manager.get_cell(0, 0).style.font_color == "#FF0000"

    def test_merge_cells(self):
        """Test merging cells."""
        manager = CellManager()
        manager.merge_cells(0, 0, 0, 2)
        assert (0, 0, 0, 2) in manager.merged_cells

    def test_undo_redo(self):
        """Test undo/redo functionality."""
        manager = CellManager()
        manager.set_cell_value(0, 0, "First")
        manager.set_cell_value(0, 0, "Second")

        manager.undo()
        assert manager.get_cell(0, 0).value == "First"

        manager.redo()
        assert manager.get_cell(0, 0).value == "Second"

    def test_column_letter_conversion(self):
        """Test column letter conversion."""
        assert column_letter(0) == "A"
        assert column_letter(25) == "Z"
        assert column_letter(26) == "AA"

    def test_column_index_conversion(self):
        """Test column index conversion."""
        assert column_index("A") == 0
        assert column_index("Z") == 25
        assert column_index("AA") == 26


class TestDataValidator:
    """Test data validator."""

    def test_number_range_validation(self):
        """Test number range validation."""
        validator = DataValidator()
        rule = validator.create_number_range_rule(1, 10)
        validator.add_rule(0, 0, rule)

        is_valid, _ = validator.validate_cell(0, 0, 5)
        assert is_valid is True

        is_valid, error = validator.validate_cell(0, 0, 15)
        assert is_valid is False
        assert error is not None

    def test_dropdown_validation(self):
        """Test dropdown list validation."""
        validator = DataValidator()
        rule = validator.create_dropdown_rule(["Option 1", "Option 2", "Option 3"])
        validator.add_rule(0, 0, rule)

        is_valid, _ = validator.validate_cell(0, 0, "Option 1")
        assert is_valid is True

        is_valid, error = validator.validate_cell(0, 0, "Invalid")
        assert is_valid is False

    def test_text_length_validation(self):
        """Test text length validation."""
        validator = DataValidator()
        rule = validator.create_text_length_rule(min_length=5, max_length=10)
        validator.add_rule(0, 0, rule)

        is_valid, _ = validator.validate_cell(0, 0, "Hello")
        assert is_valid is True

        is_valid, error = validator.validate_cell(0, 0, "Hi")
        assert is_valid is False


class TestDataTools:
    """Test data tools."""

    def test_sort_data(self, sample_dataframe):
        """Test sorting data."""
        sorted_df = DataTools.sort_data(sample_dataframe, ['A'], [False])
        assert sorted_df['A'].iloc[0] == 5
        assert sorted_df['A'].iloc[-1] == 1

    def test_filter_data(self, sample_dataframe):
        """Test filtering data."""
        filtered_df = DataTools.filter_data(sample_dataframe, {'A': lambda x: x > 3})
        assert len(filtered_df) == 2
        assert filtered_df['A'].min() == 4

    def test_find_values(self, sample_dataframe):
        """Test finding values."""
        results = DataTools.find_values(sample_dataframe, 'b')
        assert len(results) > 0

    def test_remove_duplicates(self):
        """Test removing duplicates."""
        df = pd.DataFrame({
            'A': [1, 2, 2, 3, 3, 3],
            'B': ['a', 'b', 'b', 'c', 'c', 'c']
        })
        cleaned_df = DataTools.remove_duplicates(df)
        assert len(cleaned_df) == 3


class TestSpreadsheetEditor:
    """Test spreadsheet editor."""

    def test_create_new_spreadsheet(self, db_session, test_user):
        """Test creating new spreadsheet."""
        editor = SpreadsheetEditor(db_session, test_user.id)
        spreadsheet = editor.create_new("Test Spreadsheet", rows=50, cols=10)

        assert spreadsheet.name == "Test Spreadsheet"
        assert spreadsheet.user_id == test_user.id
        assert editor.cell_manager.rows == 50
        assert editor.cell_manager.cols == 10

    def test_set_and_get_cell_value(self, db_session, test_user):
        """Test setting and getting cell values."""
        editor = SpreadsheetEditor(db_session, test_user.id)
        editor.create_new("Test")

        editor.set_cell_value(0, 0, "Hello")
        assert editor.get_cell_value(0, 0) == "Hello"

    def test_formula_evaluation(self, db_session, test_user):
        """Test formula evaluation in editor."""
        editor = SpreadsheetEditor(db_session, test_user.id)
        editor.create_new("Test")

        # Set some values
        editor.set_cell_value(0, 0, 10)
        editor.set_cell_value(1, 0, 20)

        # Set formula
        editor.set_cell_formula(2, 0, "=SUM(5,10,15)")
        result = editor.get_cell_value(2, 0)

        assert result == 30


def test_integration_workflow(db_session, test_user):
    """Test complete workflow."""
    # Create spreadsheet
    editor = SpreadsheetEditor(db_session, test_user.id)
    spreadsheet = editor.create_new("Sales Data", rows=10, cols=5)

    # Add data
    editor.set_cell_value(0, 0, "Product")
    editor.set_cell_value(0, 1, "Sales")
    editor.set_cell_value(1, 0, "Item A")
    editor.set_cell_value(1, 1, 100)
    editor.set_cell_value(2, 0, "Item B")
    editor.set_cell_value(2, 1, 200)

    # Add formula
    editor.set_cell_formula(3, 1, "=SUM(100,200)")

    # Save
    editor.save()

    assert editor.get_cell_value(3, 1) == 300

    # Test undo
    editor.undo()

    # Load spreadsheet again
    editor2 = SpreadsheetEditor(db_session, test_user.id, spreadsheet.id)
    assert editor2.get_cell_value(0, 0) == "Product"
