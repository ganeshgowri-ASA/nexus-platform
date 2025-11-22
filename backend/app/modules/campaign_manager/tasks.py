"""
Celery tasks for campaign manager.

This module contains async tasks for campaign operations.
"""

from datetime import datetime, timedelta, date
from typing import Dict, Any, List
import json

from app.core.celery_app import celery_app
from app.database import SessionLocal
from app.models.campaign import (
    Campaign,
    CampaignStatus,
    CampaignReport,
    PerformanceMetric,
    ReportType,
)
from app.modules.campaign_manager.service import AnalyticsService
from app.modules.campaign_manager.ai_service import AIService


@celery_app.task(name="calculate_campaign_performance")
def calculate_campaign_performance(campaign_id: int) -> Dict[str, Any]:
    """
    Calculate and record campaign performance metrics.

    Args:
        campaign_id: Campaign ID

    Returns:
        dict: Performance metrics
    """
    db = SessionLocal()
    try:
        metrics = AnalyticsService.calculate_campaign_roi(db, campaign_id)

        # Record performance metric
        performance = PerformanceMetric(
            campaign_id=campaign_id,
            impressions=metrics["total_impressions"],
            clicks=metrics["total_clicks"],
            conversions=metrics["total_conversions"],
            cost=metrics["total_cost"],
            revenue=metrics["total_revenue"],
            roi=metrics["roi"],
        )

        db.add(performance)
        db.commit()

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "metrics": metrics,
        }

    finally:
        db.close()


@celery_app.task(name="calculate_all_campaign_performance")
def calculate_all_campaign_performance() -> Dict[str, Any]:
    """
    Calculate performance for all active campaigns.

    Returns:
        dict: Summary of calculations
    """
    db = SessionLocal()
    try:
        active_campaigns = db.query(Campaign).filter(
            Campaign.status == CampaignStatus.ACTIVE,
            Campaign.is_deleted == False
        ).all()

        results = []
        for campaign in active_campaigns:
            try:
                metrics = AnalyticsService.calculate_campaign_roi(db, campaign.id)
                results.append({
                    "campaign_id": campaign.id,
                    "name": campaign.name,
                    "roi": metrics["roi"],
                })
            except Exception as e:
                results.append({
                    "campaign_id": campaign.id,
                    "error": str(e),
                })

        return {
            "status": "success",
            "processed": len(results),
            "results": results,
        }

    finally:
        db.close()


@celery_app.task(name="generate_campaign_report")
def generate_campaign_report(
    campaign_id: int,
    report_type: str = "weekly",
    period_start: str = None,
    period_end: str = None,
    user_id: int = None
) -> Dict[str, Any]:
    """
    Generate campaign report with AI insights.

    Args:
        campaign_id: Campaign ID
        report_type: Type of report
        period_start: Period start date (ISO format)
        period_end: Period end date (ISO format)
        user_id: User requesting report

    Returns:
        dict: Generated report info
    """
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()

        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        # Calculate metrics
        metrics = AnalyticsService.calculate_campaign_roi(db, campaign_id)

        # Generate AI insights
        ai_service = AIService()
        insights = ai_service.generate_campaign_insights(campaign, metrics)
        recommendations = ai_service.generate_recommendations(campaign, metrics)

        # Create report
        report = CampaignReport(
            campaign_id=campaign_id,
            title=f"{campaign.name} - {report_type.title()} Report",
            report_type=ReportType[report_type.upper()],
            period_start=date.fromisoformat(period_start) if period_start else campaign.start_date,
            period_end=date.fromisoformat(period_end) if period_end else date.today(),
            summary=insights.get("summary", ""),
            metrics=metrics,
            insights=insights,
            recommendations=recommendations,
            generated_by_id=user_id,
            is_automated=user_id is None,
        )

        db.add(report)
        db.commit()
        db.refresh(report)

        return {
            "status": "success",
            "report_id": report.id,
            "campaign_id": campaign_id,
            "insights": insights,
        }

    finally:
        db.close()


@celery_app.task(name="send_scheduled_reports")
def send_scheduled_reports() -> Dict[str, Any]:
    """
    Send scheduled reports for all active campaigns.

    Returns:
        dict: Summary of sent reports
    """
    db = SessionLocal()
    try:
        active_campaigns = db.query(Campaign).filter(
            Campaign.status == CampaignStatus.ACTIVE,
            Campaign.is_deleted == False
        ).all()

        reports_generated = 0
        for campaign in active_campaigns:
            # Generate weekly report
            period_end = date.today()
            period_start = period_end - timedelta(days=7)

            generate_campaign_report.delay(
                campaign_id=campaign.id,
                report_type="weekly",
                period_start=period_start.isoformat(),
                period_end=period_end.isoformat(),
            )
            reports_generated += 1

        return {
            "status": "success",
            "reports_scheduled": reports_generated,
        }

    finally:
        db.close()


@celery_app.task(name="optimize_campaign_budget")
def optimize_campaign_budget(campaign_id: int) -> Dict[str, Any]:
    """
    Optimize campaign budget allocation using AI.

    Args:
        campaign_id: Campaign ID

    Returns:
        dict: Optimization suggestions
    """
    db = SessionLocal()
    try:
        campaign = db.query(Campaign).filter(
            Campaign.id == campaign_id
        ).first()

        if not campaign:
            return {"status": "error", "message": "Campaign not found"}

        # Get current metrics
        metrics = AnalyticsService.calculate_campaign_roi(db, campaign_id)

        # Generate AI optimization
        ai_service = AIService()
        optimization = ai_service.optimize_budget_allocation(campaign, metrics)

        # Update campaign with suggestions
        campaign.optimization_suggestions = optimization

        db.commit()

        return {
            "status": "success",
            "campaign_id": campaign_id,
            "optimization": optimization,
        }

    finally:
        db.close()


@celery_app.task(name="cleanup_expired_campaigns")
def cleanup_expired_campaigns() -> Dict[str, Any]:
    """
    Mark expired campaigns as completed.

    Returns:
        dict: Summary of cleanup
    """
    db = SessionLocal()
    try:
        today = date.today()

        expired_campaigns = db.query(Campaign).filter(
            Campaign.status == CampaignStatus.ACTIVE,
            Campaign.end_date < today,
            Campaign.is_deleted == False
        ).all()

        updated = 0
        for campaign in expired_campaigns:
            campaign.status = CampaignStatus.COMPLETED
            updated += 1

        db.commit()

        return {
            "status": "success",
            "campaigns_completed": updated,
        }

    finally:
        db.close()


@celery_app.task(name="send_milestone_reminders")
def send_milestone_reminders() -> Dict[str, Any]:
    """
    Send reminders for upcoming milestones.

    Returns:
        dict: Summary of reminders
    """
    db = SessionLocal()
    try:
        from app.models.campaign import Milestone, MilestoneStatus

        # Get milestones due in next 3 days
        today = date.today()
        reminder_date = today + timedelta(days=3)

        upcoming_milestones = db.query(Milestone).filter(
            Milestone.due_date <= reminder_date,
            Milestone.due_date >= today,
            Milestone.status.in_([
                MilestoneStatus.PENDING,
                MilestoneStatus.IN_PROGRESS
            ])
        ).all()

        # Here you would send actual notifications
        # For now, just return count
        reminders_sent = len(upcoming_milestones)

        return {
            "status": "success",
            "reminders_sent": reminders_sent,
        }

    finally:
        db.close()
