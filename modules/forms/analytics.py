"""
Analytics Module

Provides comprehensive analytics for forms including completion rates, time analysis,
drop-off tracking, and chart generation.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from collections import Counter
import statistics


@dataclass
class AnalyticsMetrics:
    """Container for form analytics metrics"""
    total_views: int = 0
    total_submissions: int = 0
    completion_rate: float = 0.0
    average_time: float = 0.0
    median_time: float = 0.0
    abandonment_rate: float = 0.0
    conversion_rate: float = 0.0


class FormAnalytics:
    """Main analytics class for form insights"""

    def __init__(self, responses: List[Any], form_fields: List[Any]):
        """
        Initialize analytics

        Args:
            responses: List of FormResponse objects
            form_fields: List of Field objects
        """
        self.responses = responses
        self.form_fields = form_fields

    def get_overview_metrics(self) -> AnalyticsMetrics:
        """Get overview metrics for the form"""
        metrics = AnalyticsMetrics()

        if not self.responses:
            return metrics

        metrics.total_submissions = len(self.responses)

        # Calculate completion rate
        complete_responses = [r for r in self.responses if r.is_complete]
        if self.responses:
            metrics.completion_rate = len(complete_responses) / len(self.responses) * 100

        # Calculate time metrics
        times = [r.time_spent for r in self.responses if r.time_spent > 0]
        if times:
            metrics.average_time = sum(times) / len(times)
            metrics.median_time = statistics.median(times)

        # Calculate abandonment rate
        incomplete_responses = len(self.responses) - len(complete_responses)
        if self.responses:
            metrics.abandonment_rate = incomplete_responses / len(self.responses) * 100

        return metrics

    def get_completion_rate(self) -> float:
        """Calculate form completion rate"""
        if not self.responses:
            return 0.0

        complete = len([r for r in self.responses if r.is_complete])
        return (complete / len(self.responses)) * 100

    def get_average_completion_time(self) -> float:
        """Get average time to complete form in seconds"""
        times = [r.time_spent for r in self.responses if r.time_spent > 0 and r.is_complete]
        return sum(times) / len(times) if times else 0.0

    def get_time_distribution(self, buckets: int = 10) -> Dict[str, int]:
        """
        Get distribution of completion times

        Args:
            buckets: Number of time buckets

        Returns:
            Dictionary of time_range: count
        """
        times = [r.time_spent for r in self.responses if r.time_spent > 0]

        if not times:
            return {}

        min_time = min(times)
        max_time = max(times)
        bucket_size = (max_time - min_time) / buckets

        distribution = {}
        for i in range(buckets):
            range_start = int(min_time + i * bucket_size)
            range_end = int(min_time + (i + 1) * bucket_size)
            range_label = f"{range_start}-{range_end}s"

            count = len([t for t in times if range_start <= t < range_end])
            distribution[range_label] = count

        return distribution

    def get_drop_off_analysis(self) -> Dict[str, Any]:
        """
        Analyze where users drop off in the form

        Returns:
            Dictionary with drop-off data per field
        """
        drop_offs = {}

        for field in self.form_fields:
            field_id = field.id
            field_label = field.label

            # Count how many responses include this field
            filled_count = len([
                r for r in self.responses
                if field_id in r.data and r.data[field_id] not in [None, "", []]
            ])

            # Count how many responses should have filled this field
            eligible_count = len(self.responses)

            completion_rate = (filled_count / eligible_count * 100) if eligible_count > 0 else 0
            drop_off_rate = 100 - completion_rate

            drop_offs[field_id] = {
                "field_label": field_label,
                "filled_count": filled_count,
                "eligible_count": eligible_count,
                "completion_rate": completion_rate,
                "drop_off_rate": drop_off_rate,
                "position": field.position,
            }

        return drop_offs

    def get_field_statistics(self, field_id: str) -> Dict[str, Any]:
        """
        Get statistics for a specific field

        Args:
            field_id: Field ID

        Returns:
            Statistics dictionary
        """
        field = next((f for f in self.form_fields if f.id == field_id), None)
        if not field:
            return {}

        values = [r.data.get(field_id) for r in self.responses if field_id in r.data]

        stats = {
            "field_id": field_id,
            "field_label": field.label,
            "field_type": field.field_type.value,
            "total_responses": len(values),
            "filled_count": len([v for v in values if v not in [None, "", []]]),
            "empty_count": len([v for v in values if v in [None, "", []]]),
        }

        # Type-specific statistics
        if field.field_type.value in ["number", "rating", "scale", "nps"]:
            numeric_values = []
            for v in values:
                try:
                    numeric_values.append(float(v))
                except (ValueError, TypeError):
                    pass

            if numeric_values:
                stats.update({
                    "min": min(numeric_values),
                    "max": max(numeric_values),
                    "average": sum(numeric_values) / len(numeric_values),
                    "median": statistics.median(numeric_values),
                    "std_dev": statistics.stdev(numeric_values) if len(numeric_values) > 1 else 0,
                })

        elif field.field_type.value in ["dropdown", "radio", "checkbox", "multi_select"]:
            # Count occurrences of each option
            all_options = []
            for v in values:
                if isinstance(v, list):
                    all_options.extend(v)
                elif v:
                    all_options.append(v)

            option_counts = Counter(all_options)
            stats["option_counts"] = dict(option_counts)
            stats["most_common"] = option_counts.most_common(5)

        elif field.field_type.value in ["short_text", "long_text"]:
            text_values = [str(v) for v in values if v]
            if text_values:
                lengths = [len(t) for t in text_values]
                stats.update({
                    "average_length": sum(lengths) / len(lengths),
                    "min_length": min(lengths),
                    "max_length": max(lengths),
                })

        return stats

    def get_response_trends(self, days: int = 30) -> Dict[str, int]:
        """
        Get response trends over time

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary of date: count
        """
        if not self.responses:
            return {}

        # Get date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)

        # Initialize all dates with 0
        trends = {}
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime("%Y-%m-%d")
            trends[date_str] = 0
            current_date += timedelta(days=1)

        # Count responses per day
        for response in self.responses:
            if start_date <= response.submitted_at <= end_date:
                date_str = response.submitted_at.strftime("%Y-%m-%d")
                trends[date_str] = trends.get(date_str, 0) + 1

        return trends

    def get_hourly_distribution(self) -> Dict[int, int]:
        """
        Get distribution of responses by hour of day

        Returns:
            Dictionary of hour: count
        """
        hourly = {i: 0 for i in range(24)}

        for response in self.responses:
            hour = response.submitted_at.hour
            hourly[hour] += 1

        return hourly

    def get_daily_distribution(self) -> Dict[str, int]:
        """
        Get distribution of responses by day of week

        Returns:
            Dictionary of day_name: count
        """
        days = {
            "Monday": 0,
            "Tuesday": 0,
            "Wednesday": 0,
            "Thursday": 0,
            "Friday": 0,
            "Saturday": 0,
            "Sunday": 0,
        }

        for response in self.responses:
            day_name = response.submitted_at.strftime("%A")
            days[day_name] += 1

        return days

    def get_device_distribution(self) -> Dict[str, int]:
        """
        Get distribution of responses by device type

        Returns:
            Dictionary of device_type: count
        """
        devices = {"Desktop": 0, "Mobile": 0, "Tablet": 0, "Unknown": 0}

        for response in self.responses:
            if response.user_agent:
                user_agent = response.user_agent.lower()
                if "mobile" in user_agent:
                    devices["Mobile"] += 1
                elif "tablet" in user_agent or "ipad" in user_agent:
                    devices["Tablet"] += 1
                elif any(x in user_agent for x in ["windows", "mac", "linux"]):
                    devices["Desktop"] += 1
                else:
                    devices["Unknown"] += 1
            else:
                devices["Unknown"] += 1

        return devices

    def get_nps_score(self, field_id: str) -> Optional[float]:
        """
        Calculate Net Promoter Score (NPS) for an NPS field

        Args:
            field_id: ID of NPS field

        Returns:
            NPS score (-100 to 100) or None
        """
        values = []
        for response in self.responses:
            value = response.data.get(field_id)
            if value is not None:
                try:
                    values.append(int(value))
                except (ValueError, TypeError):
                    pass

        if not values:
            return None

        # Calculate NPS
        promoters = len([v for v in values if v >= 9])
        detractors = len([v for v in values if v <= 6])
        total = len(values)

        nps = ((promoters - detractors) / total) * 100
        return nps

    def get_satisfaction_score(self, field_id: str) -> Optional[float]:
        """
        Calculate average satisfaction score for a rating field

        Args:
            field_id: ID of rating field

        Returns:
            Average rating or None
        """
        values = []
        for response in self.responses:
            value = response.data.get(field_id)
            if value is not None:
                try:
                    values.append(float(value))
                except (ValueError, TypeError):
                    pass

        return sum(values) / len(values) if values else None

    def get_conversion_funnel(self, page_count: int) -> List[Dict[str, Any]]:
        """
        Get conversion funnel data for multi-page forms

        Args:
            page_count: Number of pages in form

        Returns:
            List of funnel stage data
        """
        funnel = []

        for page in range(page_count):
            # Count responses that reached this page
            page_fields = [f.id for f in self.form_fields if f.page == page]

            reached_count = 0
            for response in self.responses:
                # Check if any field from this page was filled
                if any(field_id in response.data for field_id in page_fields):
                    reached_count += 1

            conversion_rate = (reached_count / len(self.responses) * 100) if self.responses else 0

            funnel.append({
                "page": page + 1,
                "reached": reached_count,
                "conversion_rate": conversion_rate,
                "drop_off": len(self.responses) - reached_count if page == 0 else None,
            })

        return funnel

    def export_summary_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive summary report

        Returns:
            Complete analytics report
        """
        metrics = self.get_overview_metrics()

        return {
            "overview": {
                "total_submissions": metrics.total_submissions,
                "completion_rate": f"{metrics.completion_rate:.2f}%",
                "average_time": f"{metrics.average_time:.0f}s",
                "median_time": f"{metrics.median_time:.0f}s",
                "abandonment_rate": f"{metrics.abandonment_rate:.2f}%",
            },
            "trends": {
                "daily": self.get_response_trends(days=7),
                "hourly": self.get_hourly_distribution(),
                "by_day_of_week": self.get_daily_distribution(),
            },
            "devices": self.get_device_distribution(),
            "drop_off_analysis": self.get_drop_off_analysis(),
            "field_statistics": {
                field.id: self.get_field_statistics(field.id)
                for field in self.form_fields
            },
        }


class ChartGenerator:
    """Generates chart data for visualization"""

    @staticmethod
    def generate_bar_chart(data: Dict[str, Any], title: str) -> Dict[str, Any]:
        """Generate bar chart data"""
        return {
            "type": "bar",
            "title": title,
            "labels": list(data.keys()),
            "values": list(data.values()),
        }

    @staticmethod
    def generate_pie_chart(data: Dict[str, Any], title: str) -> Dict[str, Any]:
        """Generate pie chart data"""
        return {
            "type": "pie",
            "title": title,
            "labels": list(data.keys()),
            "values": list(data.values()),
        }

    @staticmethod
    def generate_line_chart(data: Dict[str, Any], title: str) -> Dict[str, Any]:
        """Generate line chart data"""
        return {
            "type": "line",
            "title": title,
            "labels": list(data.keys()),
            "values": list(data.values()),
        }

    @staticmethod
    def generate_funnel_chart(funnel_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate funnel chart data"""
        return {
            "type": "funnel",
            "title": "Conversion Funnel",
            "stages": [
                {
                    "label": f"Page {stage['page']}",
                    "value": stage["reached"],
                    "conversion": stage["conversion_rate"],
                }
                for stage in funnel_data
            ],
        }

    @staticmethod
    def generate_heatmap(hourly_data: Dict[int, int],
                        daily_data: Dict[str, int]) -> Dict[str, Any]:
        """Generate heatmap data for responses by time"""
        return {
            "type": "heatmap",
            "title": "Response Heatmap",
            "hourly": hourly_data,
            "daily": daily_data,
        }


class ReportGenerator:
    """Generates analytics reports"""

    def __init__(self, analytics: FormAnalytics):
        self.analytics = analytics

    def generate_executive_summary(self) -> str:
        """Generate executive summary text"""
        metrics = self.analytics.get_overview_metrics()

        summary = f"""
Form Analytics Executive Summary
================================

Total Submissions: {metrics.total_submissions}
Completion Rate: {metrics.completion_rate:.2f}%
Average Completion Time: {metrics.average_time / 60:.1f} minutes
Abandonment Rate: {metrics.abandonment_rate:.2f}%

Key Insights:
- The form has received {metrics.total_submissions} submissions
- {metrics.completion_rate:.0f}% of users complete the form
- Users take an average of {metrics.average_time / 60:.1f} minutes to complete
- Drop-off rate is {metrics.abandonment_rate:.0f}%
        """

        return summary.strip()

    def generate_field_report(self, field_id: str) -> str:
        """Generate detailed report for a specific field"""
        stats = self.analytics.get_field_statistics(field_id)

        if not stats:
            return "No data available for this field"

        report = f"""
Field: {stats['field_label']}
Type: {stats['field_type']}
Total Responses: {stats['total_responses']}
Filled: {stats['filled_count']}
Empty: {stats['empty_count']}
        """

        if "average" in stats:
            report += f"\nAverage Value: {stats['average']:.2f}"
            report += f"\nMin: {stats['min']}, Max: {stats['max']}"

        if "option_counts" in stats:
            report += "\n\nResponse Distribution:"
            for option, count in stats.get("most_common", []):
                percentage = (count / stats['total_responses'] * 100)
                report += f"\n- {option}: {count} ({percentage:.1f}%)"

        return report.strip()
