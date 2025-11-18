"""Main spreadsheet editor engine."""
from typing import Optional, Dict, Any, List, Tuple
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from .formula_engine import FormulaEngine
from .cell_manager import CellManager, CellStyle
from .data_validator import DataValidator, ValidationRule
from .chart_builder import ChartBuilder, ChartConfig
from .pivot_table import PivotTable, PivotConfig
from .conditional_format import ConditionalFormatManager
from .data_tools import DataTools
from .import_export import ImportExport
from .collaboration import CollaborationManager, Change, ChangeType, Comment
from .ai_assistant import SpreadsheetAIAssistant
from .models import Spreadsheet, SpreadsheetVersion
from core.storage.manager import StorageManager


class SpreadsheetEditor:
    """Main spreadsheet editor with all features integrated."""

    def __init__(self, db_session: Session, user_id: int, spreadsheet_id: Optional[int] = None):
        """
        Initialize spreadsheet editor.

        Args:
            db_session: Database session
            user_id: Current user ID
            spreadsheet_id: Optional spreadsheet ID to load
        """
        self.db = db_session
        self.user_id = user_id
        self.spreadsheet_id = spreadsheet_id
        self.spreadsheet: Optional[Spreadsheet] = None

        # Core components
        self.cell_manager = CellManager()
        self.formula_engine = FormulaEngine()
        self.data_validator = DataValidator()
        self.chart_builder = ChartBuilder()
        self.conditional_format = ConditionalFormatManager()
        self.ai_assistant = SpreadsheetAIAssistant()
        self.storage = StorageManager()

        # Collaboration
        self.collaboration: Optional[CollaborationManager] = None

        # Data
        self.data: pd.DataFrame = pd.DataFrame()

        # Load spreadsheet if ID provided
        if spreadsheet_id:
            self.load_spreadsheet(spreadsheet_id)

    def create_new(self, name: str, rows: int = 100, cols: int = 26,
                  description: Optional[str] = None) -> Spreadsheet:
        """
        Create a new spreadsheet.

        Args:
            name: Spreadsheet name
            rows: Initial number of rows
            cols: Initial number of columns
            description: Optional description

        Returns:
            Created spreadsheet
        """
        # Initialize cell manager with size
        self.cell_manager = CellManager(rows=rows, cols=cols)

        # Create empty DataFrame
        self.data = pd.DataFrame(index=range(rows), columns=range(cols))

        # Create database record
        self.spreadsheet = Spreadsheet(
            user_id=self.user_id,
            name=name,
            description=description,
            metadata={
                'rows': rows,
                'columns': cols,
                'created_by': self.user_id
            },
            settings={}
        )

        self.db.add(self.spreadsheet)
        self.db.commit()
        self.db.refresh(self.spreadsheet)

        self.spreadsheet_id = self.spreadsheet.id

        # Initialize collaboration
        self.collaboration = CollaborationManager(self.spreadsheet_id)

        # Save initial version
        self._save_version("Initial version")

        return self.spreadsheet

    def load_spreadsheet(self, spreadsheet_id: int) -> None:
        """
        Load an existing spreadsheet.

        Args:
            spreadsheet_id: Spreadsheet ID

        Raises:
            ValueError: If spreadsheet not found
        """
        self.spreadsheet = self.db.query(Spreadsheet).filter_by(
            id=spreadsheet_id,
            is_active=True
        ).first()

        if not self.spreadsheet:
            raise ValueError(f"Spreadsheet {spreadsheet_id} not found")

        self.spreadsheet_id = spreadsheet_id

        # Load data
        if self.spreadsheet.file_path:
            self.data = self.storage.load_dataframe(self.spreadsheet.file_path)
        elif self.spreadsheet.data_json:
            self.data = pd.DataFrame(self.spreadsheet.data_json)
        else:
            rows = self.spreadsheet.metadata.get('rows', 100)
            cols = self.spreadsheet.metadata.get('columns', 26)
            self.data = pd.DataFrame(index=range(rows), columns=range(cols))

        # Initialize cell manager from data
        self.cell_manager.from_dataframe(self.data)

        # Initialize collaboration
        self.collaboration = CollaborationManager(self.spreadsheet_id)

        # Update last accessed
        self.spreadsheet.last_accessed = datetime.utcnow()
        self.db.commit()

    def save(self) -> None:
        """Save spreadsheet to storage and database."""
        if not self.spreadsheet:
            raise ValueError("No spreadsheet loaded")

        # Get data from cell manager
        self.data = self.cell_manager.to_dataframe()

        # Save to storage
        filename = f"spreadsheet_{self.spreadsheet_id}_{datetime.utcnow().timestamp()}.xlsx"
        file_path = self.storage.save_dataframe(self.data, filename)

        # Update database record
        self.spreadsheet.file_path = file_path
        self.spreadsheet.data_json = self.data.to_dict()
        self.spreadsheet.metadata['rows'] = self.cell_manager.rows
        self.spreadsheet.metadata['columns'] = self.cell_manager.cols
        self.spreadsheet.updated_at = datetime.utcnow()

        self.db.commit()

    def _save_version(self, change_summary: str) -> SpreadsheetVersion:
        """
        Save a new version.

        Args:
            change_summary: Summary of changes

        Returns:
            Created version
        """
        if not self.spreadsheet:
            raise ValueError("No spreadsheet loaded")

        # Get current version number
        latest_version = self.db.query(SpreadsheetVersion).filter_by(
            spreadsheet_id=self.spreadsheet_id
        ).order_by(SpreadsheetVersion.version_number.desc()).first()

        version_number = (latest_version.version_number + 1) if latest_version else 1

        # Create version
        version = SpreadsheetVersion(
            spreadsheet_id=self.spreadsheet_id,
            version_number=version_number,
            file_path=self.spreadsheet.file_path,
            data_json=self.data.to_dict(),
            change_summary=change_summary,
            created_by=self.user_id
        )

        self.db.add(version)
        self.db.commit()
        self.db.refresh(version)

        return version

    def import_file(self, file_path: str, file_format: Optional[str] = None) -> None:
        """
        Import data from file.

        Args:
            file_path: File path
            file_format: Optional format hint
        """
        if file_format == 'csv' or file_path.endswith('.csv'):
            self.data = ImportExport.import_csv(file_path)
        elif file_format == 'json' or file_path.endswith('.json'):
            self.data = ImportExport.import_json(file_path)
        else:
            self.data = ImportExport.import_excel(file_path)

        # Update cell manager
        self.cell_manager.from_dataframe(self.data)

    def export_file(self, file_path: str, file_format: str = 'excel') -> None:
        """
        Export to file.

        Args:
            file_path: Output file path
            file_format: Export format ('excel', 'csv', 'json', 'html', 'pdf')
        """
        df = self.cell_manager.to_dataframe()

        if file_format == 'excel':
            ImportExport.export_excel(df, file_path)
        elif file_format == 'csv':
            ImportExport.export_csv(df, file_path)
        elif file_format == 'json':
            ImportExport.export_json(df, file_path)
        elif file_format == 'html':
            ImportExport.export_html(df, file_path)
        elif file_format == 'pdf':
            ImportExport.export_pdf(df, file_path)

    def get_cell_value(self, row: int, col: int) -> Any:
        """Get cell value."""
        cell = self.cell_manager.get_cell(row, col)
        return cell.value

    def set_cell_value(self, row: int, col: int, value: Any) -> None:
        """
        Set cell value.

        Args:
            row: Row index
            col: Column index
            value: New value
        """
        # Validate if rule exists
        is_valid, error_msg = self.data_validator.validate_cell(row, col, value)
        if not is_valid:
            raise ValueError(error_msg)

        # Record change for collaboration
        old_value = self.get_cell_value(row, col)
        if self.collaboration:
            change = Change(
                change_id=str(uuid.uuid4()),
                user_id=self.user_id,
                user_name="User",  # Get from session
                change_type=ChangeType.CELL_VALUE,
                timestamp=datetime.now(),
                row=row,
                col=col,
                old_value=old_value,
                new_value=value
            )
            self.collaboration.record_change(change)

        # Set value
        self.cell_manager.set_cell_value(row, col, value)

    def set_cell_formula(self, row: int, col: int, formula: str) -> None:
        """
        Set cell formula.

        Args:
            row: Row index
            col: Column index
            formula: Formula string
        """
        self.cell_manager.set_cell_formula(row, col, formula)

        # Evaluate formula and set value
        result = self.formula_engine.evaluate(formula)
        self.cell_manager.set_cell_value(row, col, result, record_undo=False)

    def apply_style(self, row: int, col: int, style: CellStyle) -> None:
        """Apply style to a cell."""
        self.cell_manager.set_cell_style(row, col, style)

    def merge_cells(self, start_row: int, start_col: int, end_row: int, end_col: int) -> None:
        """Merge cells."""
        self.cell_manager.merge_cells(start_row, start_col, end_row, end_col)

    def add_validation(self, row: int, col: int, rule: ValidationRule) -> None:
        """Add validation rule to cell."""
        self.data_validator.add_rule(row, col, rule)

    def create_chart(self, config: ChartConfig):
        """Create a chart."""
        df = self.cell_manager.to_dataframe()
        return self.chart_builder.create_chart(df, config)

    def create_pivot_table(self, config: PivotConfig) -> pd.DataFrame:
        """Create pivot table."""
        df = self.cell_manager.to_dataframe()
        pivot = PivotTable(df)
        return pivot.create(config)

    def sort_data(self, columns: List[int], ascending: Optional[List[bool]] = None) -> None:
        """Sort data."""
        df = self.cell_manager.to_dataframe()
        col_names = [df.columns[i] for i in columns]
        sorted_df = DataTools.sort_data(df, col_names, ascending)
        self.cell_manager.from_dataframe(sorted_df)

    def filter_data(self, filters: Dict[int, Any]) -> pd.DataFrame:
        """Filter data and return filtered DataFrame."""
        df = self.cell_manager.to_dataframe()
        col_filters = {df.columns[col_idx]: condition for col_idx, condition in filters.items()}
        return DataTools.filter_data(df, col_filters)

    def find_replace(self, find: str, replace: str, **kwargs) -> None:
        """Find and replace values."""
        df = self.cell_manager.to_dataframe()
        result_df = DataTools.replace_values(df, find, replace, **kwargs)
        self.cell_manager.from_dataframe(result_df)

    def add_comment(self, row: int, col: int, comment: Comment) -> None:
        """Add comment to cell."""
        if self.collaboration:
            self.collaboration.add_comment(comment)
        cell = self.cell_manager.get_cell(row, col)
        cell.comment = comment.text

    def undo(self) -> bool:
        """Undo last action."""
        return self.cell_manager.undo()

    def redo(self) -> bool:
        """Redo last undone action."""
        return self.cell_manager.redo()

    def get_ai_insights(self, query: str) -> Dict[str, Any]:
        """Get AI insights about the data."""
        df = self.cell_manager.to_dataframe()
        return self.ai_assistant.analyze_data(df, query)

    def get_ai_formula_suggestion(self, description: str) -> str:
        """Get AI-generated formula suggestion."""
        df = self.cell_manager.to_dataframe()
        return self.ai_assistant.suggest_formula(description, df)

    def get_data_cleaning_suggestions(self) -> List[Dict[str, str]]:
        """Get AI suggestions for data cleaning."""
        df = self.cell_manager.to_dataframe()
        return self.ai_assistant.clean_data_suggestions(df)

    def to_dict(self) -> Dict[str, Any]:
        """Convert spreadsheet to dictionary representation."""
        return {
            'id': self.spreadsheet_id,
            'name': self.spreadsheet.name if self.spreadsheet else None,
            'data': self.cell_manager.to_dataframe().to_dict(),
            'metadata': self.spreadsheet.metadata if self.spreadsheet else {},
            'rows': self.cell_manager.rows,
            'columns': self.cell_manager.cols
        }

    def get_version_history(self) -> List[SpreadsheetVersion]:
        """Get version history."""
        if not self.spreadsheet_id:
            return []

        return self.db.query(SpreadsheetVersion).filter_by(
            spreadsheet_id=self.spreadsheet_id
        ).order_by(SpreadsheetVersion.version_number.desc()).all()

    def restore_version(self, version_id: int) -> None:
        """Restore a previous version."""
        version = self.db.query(SpreadsheetVersion).filter_by(id=version_id).first()

        if not version or version.spreadsheet_id != self.spreadsheet_id:
            raise ValueError("Version not found")

        # Load version data
        if version.data_json:
            self.data = pd.DataFrame(version.data_json)
            self.cell_manager.from_dataframe(self.data)

        # Save as new version
        self._save_version(f"Restored from version {version.version_number}")
