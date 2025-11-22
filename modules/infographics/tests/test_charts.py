"""
Tests for charts module.
"""

import unittest
from modules.infographics.charts import (
    ChartFactory, ChartType, DataSeries, ChartStyler, ChartDataTransformer
)


class TestChartFactory(unittest.TestCase):
    """Tests for ChartFactory."""

    def test_create_bar_chart(self):
        """Test creating bar chart."""
        categories = ["A", "B", "C"]
        data = [10, 20, 30]
        chart = ChartFactory.create_bar_chart(categories, data, "Test Chart")

        self.assertEqual(chart.chart_type, ChartType.BAR)
        self.assertEqual(len(chart.data_series), 1)
        self.assertEqual(chart.data_series[0].data, data)
        self.assertEqual(chart.categories, categories)

    def test_create_pie_chart(self):
        """Test creating pie chart."""
        labels = ["A", "B", "C"]
        data = [10, 20, 30]
        chart = ChartFactory.create_pie_chart(labels, data)

        self.assertEqual(chart.chart_type, ChartType.PIE)
        self.assertEqual(chart.data_series[0].labels, labels)

    def test_create_line_chart(self):
        """Test creating line chart."""
        categories = ["Jan", "Feb", "Mar"]
        data = [100, 150, 200]
        chart = ChartFactory.create_line_chart(categories, data)

        self.assertEqual(chart.chart_type, ChartType.LINE)
        self.assertEqual(len(chart.data_series), 1)

    def test_create_comparison_chart(self):
        """Test creating comparison chart with multiple series."""
        categories = ["Q1", "Q2", "Q3"]
        series_data = [("Series1", [10, 20, 30]), ("Series2", [15, 25, 35])]
        chart = ChartFactory.create_comparison_chart(categories, series_data)

        self.assertEqual(len(chart.data_series), 2)
        self.assertEqual(chart.data_series[0].name, "Series1")
        self.assertEqual(chart.data_series[1].name, "Series2")


class TestDataSeries(unittest.TestCase):
    """Tests for DataSeries."""

    def test_data_series_creation(self):
        """Test creating data series."""
        series = DataSeries(name="Test", data=[1, 2, 3], color="#FF0000")

        self.assertEqual(series.name, "Test")
        self.assertEqual(len(series.data), 3)
        self.assertEqual(series.color, "#FF0000")

    def test_data_series_to_dict(self):
        """Test serializing data series."""
        series = DataSeries(name="Test", data=[1, 2, 3])
        data = series.to_dict()

        self.assertIn('name', data)
        self.assertIn('data', data)
        self.assertEqual(data['name'], "Test")


class TestChartStyler(unittest.TestCase):
    """Tests for ChartStyler."""

    def test_apply_color_scheme(self):
        """Test applying color scheme."""
        chart = ChartFactory.create_bar_chart(["A"], [10])
        ChartStyler.apply_color_scheme(chart, 'vibrant')

        self.assertIn('#FF6B6B', chart.config.color_scheme)

    def test_apply_minimal_style(self):
        """Test applying minimal style."""
        chart = ChartFactory.create_bar_chart(["A"], [10])
        ChartStyler.apply_minimal_style(chart)

        self.assertFalse(chart.config.show_grid)


class TestChartDataTransformer(unittest.TestCase):
    """Tests for ChartDataTransformer."""

    def test_normalize_data(self):
        """Test data normalization."""
        data = [10, 20, 30, 40]
        normalized = ChartDataTransformer.normalize_data(data, 0, 100)

        self.assertEqual(normalized[0], 0)
        self.assertEqual(normalized[-1], 100)

    def test_calculate_percentages(self):
        """Test percentage calculation."""
        data = [10, 20, 30, 40]
        percentages = ChartDataTransformer.calculate_percentages(data)

        self.assertAlmostEqual(sum(percentages), 100, places=1)

    def test_aggregate_data(self):
        """Test data aggregation."""
        data = [10, 20, 30, 40]

        self.assertEqual(ChartDataTransformer.aggregate_data(data, 'sum'), 100)
        self.assertEqual(ChartDataTransformer.aggregate_data(data, 'average'), 25)
        self.assertEqual(ChartDataTransformer.aggregate_data(data, 'max'), 40)
        self.assertEqual(ChartDataTransformer.aggregate_data(data, 'min'), 10)


if __name__ == '__main__':
    unittest.main()
