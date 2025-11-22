"""
Tests for data_viz module.
"""

import unittest
from modules.infographics.data_viz import (
    DataImporter, DataType, ChartGenerator, DataAnalyzer
)


class TestDataImporter(unittest.TestCase):
    """Tests for DataImporter."""

    def test_import_csv_with_header(self):
        """Test importing CSV with header."""
        csv_data = """Name,Value
A,10
B,20
C,30"""
        table = DataImporter.import_csv(csv_data, has_header=True)

        self.assertEqual(table.get_column_count(), 2)
        self.assertEqual(table.get_row_count(), 3)
        self.assertEqual(table.get_column("Name").values, ["A", "B", "C"])
        self.assertEqual(table.get_column("Value").values, [10.0, 20.0, 30.0])

    def test_import_csv_without_header(self):
        """Test importing CSV without header."""
        csv_data = """10,20
30,40"""
        table = DataImporter.import_csv(csv_data, has_header=False)

        self.assertEqual(table.get_column_count(), 2)
        self.assertEqual(table.get_row_count(), 2)

    def test_import_json_list(self):
        """Test importing JSON list."""
        json_data = '[{"name": "A", "value": 10}, {"name": "B", "value": 20}]'
        table = DataImporter.import_json(json_data)

        self.assertEqual(table.get_column_count(), 2)
        self.assertEqual(table.get_row_count(), 2)

    def test_import_json_object(self):
        """Test importing JSON object."""
        json_data = '{"labels": ["A", "B"], "values": [10, 20]}'
        table = DataImporter.import_json(json_data)

        self.assertEqual(table.get_column_count(), 2)

    def test_infer_data_type_number(self):
        """Test inferring number type."""
        values = ["10", "20", "30"]
        data_type = DataImporter._infer_data_type(values)

        self.assertEqual(data_type, DataType.NUMBER)

    def test_infer_data_type_string(self):
        """Test inferring string type."""
        values = ["apple", "banana", "cherry"]
        data_type = DataImporter._infer_data_type(values)

        self.assertEqual(data_type, DataType.STRING)


class TestChartGenerator(unittest.TestCase):
    """Tests for ChartGenerator."""

    def test_generate_bar_chart(self):
        """Test auto-generating bar chart."""
        csv_data = """Category,Value
A,10
B,20
C,30"""
        table = DataImporter.import_csv(csv_data)
        chart = ChartGenerator.generate_bar_chart(table)

        self.assertIsNotNone(chart)
        self.assertEqual(len(chart.categories), 3)
        self.assertEqual(chart.data_series[0].data, [10.0, 20.0, 30.0])

    def test_generate_pie_chart(self):
        """Test auto-generating pie chart."""
        csv_data = """Label,Value
A,10
B,20
C,30"""
        table = DataImporter.import_csv(csv_data)
        chart = ChartGenerator.generate_pie_chart(table)

        self.assertIsNotNone(chart)
        self.assertEqual(len(chart.data_series[0].data), 3)

    def test_infer_chart_type(self):
        """Test chart type inference."""
        csv_data = """Category,Value
A,10
B,20"""
        table = DataImporter.import_csv(csv_data)
        chart_type = ChartGenerator._infer_chart_type(table)

        # Should infer PIE for 2 rows with category+value
        from modules.infographics.charts import ChartType
        self.assertEqual(chart_type, ChartType.PIE)


class TestDataAnalyzer(unittest.TestCase):
    """Tests for DataAnalyzer."""

    def test_summary_statistics(self):
        """Test calculating summary statistics."""
        from modules.infographics.data_viz import DataColumn
        column = DataColumn(name="values", data_type=DataType.NUMBER, values=[10, 20, 30, 40])
        stats = DataAnalyzer.get_summary_statistics(column)

        self.assertEqual(stats['count'], 4)
        self.assertEqual(stats['min'], 10)
        self.assertEqual(stats['max'], 40)
        self.assertEqual(stats['mean'], 25)

    def test_detect_trends(self):
        """Test trend detection."""
        increasing = [1, 2, 3, 4, 5]
        trend = DataAnalyzer.detect_trends(increasing)
        self.assertEqual(trend, "increasing")

        decreasing = [5, 4, 3, 2, 1]
        trend = DataAnalyzer.detect_trends(decreasing)
        self.assertEqual(trend, "decreasing")

    def test_find_outliers(self):
        """Test outlier detection."""
        values = [10, 12, 11, 13, 100, 12, 11]  # 100 is an outlier
        outliers = DataAnalyzer.find_outliers(values, threshold=2.0)

        self.assertGreater(len(outliers), 0)
        self.assertIn(4, outliers)  # Index of 100


if __name__ == '__main__':
    unittest.main()
