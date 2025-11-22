"""
Analytics Manager - Integration with Google Analytics, Facebook Pixel, and custom tracking
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
from datetime import datetime, timedelta
import json


class AnalyticsProvider(Enum):
    """Analytics providers"""
    GOOGLE_ANALYTICS = "google_analytics"
    GOOGLE_ANALYTICS_4 = "google_analytics_4"
    FACEBOOK_PIXEL = "facebook_pixel"
    MIXPANEL = "mixpanel"
    HOTJAR = "hotjar"
    MATOMO = "matomo"
    CUSTOM = "custom"


class EventType(Enum):
    """Event types"""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    FORM_SUBMIT = "form_submit"
    PURCHASE = "purchase"
    ADD_TO_CART = "add_to_cart"
    SIGNUP = "signup"
    LOGIN = "login"
    SEARCH = "search"
    VIDEO_PLAY = "video_play"
    DOWNLOAD = "download"
    CUSTOM = "custom"


@dataclass
class AnalyticsConfig:
    """Analytics configuration"""
    provider: AnalyticsProvider
    tracking_id: str
    enabled: bool = True
    track_page_views: bool = True
    track_events: bool = True
    track_ecommerce: bool = False
    anonymize_ip: bool = True
    cookie_domain: str = "auto"
    additional_config: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "provider": self.provider.value,
            "tracking_id": self.tracking_id,
            "enabled": self.enabled,
            "track_page_views": self.track_page_views,
            "track_events": self.track_events,
            "track_ecommerce": self.track_ecommerce,
            "anonymize_ip": self.anonymize_ip,
            "cookie_domain": self.cookie_domain,
            "additional_config": self.additional_config,
        }


@dataclass
class Event:
    """Analytics event"""
    event_id: str
    event_type: EventType
    event_name: str
    timestamp: datetime
    properties: Dict[str, Any] = field(default_factory=dict)
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "event_name": self.event_name,
            "timestamp": self.timestamp.isoformat(),
            "properties": self.properties,
            "user_id": self.user_id,
            "session_id": self.session_id,
        }


@dataclass
class PageView:
    """Page view tracking"""
    page_url: str
    page_title: str
    timestamp: datetime
    referrer: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None


class AnalyticsManager:
    """Manager for analytics and tracking"""

    def __init__(self):
        self.analytics_configs: Dict[str, AnalyticsConfig] = {}
        self.events: List[Event] = []
        self.page_views: List[PageView] = []

    # Configuration

    def add_analytics_provider(
        self,
        provider: AnalyticsProvider,
        tracking_id: str,
        **kwargs
    ) -> AnalyticsConfig:
        """Add analytics provider"""
        config = AnalyticsConfig(
            provider=provider,
            tracking_id=tracking_id,
            **kwargs
        )

        self.analytics_configs[provider.value] = config
        return config

    def remove_analytics_provider(self, provider: AnalyticsProvider) -> bool:
        """Remove analytics provider"""
        if provider.value in self.analytics_configs:
            del self.analytics_configs[provider.value]
            return True
        return False

    def enable_provider(self, provider: AnalyticsProvider) -> bool:
        """Enable analytics provider"""
        config = self.analytics_configs.get(provider.value)
        if config:
            config.enabled = True
            return True
        return False

    def disable_provider(self, provider: AnalyticsProvider) -> bool:
        """Disable analytics provider"""
        config = self.analytics_configs.get(provider.value)
        if config:
            config.enabled = False
            return True
        return False

    # Tracking Code Generation

    def generate_google_analytics_code(self, tracking_id: str) -> str:
        """Generate Google Analytics tracking code"""
        config = self.analytics_configs.get(AnalyticsProvider.GOOGLE_ANALYTICS.value)

        code = f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={tracking_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{tracking_id}', {{
    'anonymize_ip': {str(config.anonymize_ip).lower() if config else 'true'},
    'cookie_domain': '{config.cookie_domain if config else 'auto'}'
  }});
</script>
<!-- End Google Analytics -->
"""
        return code.strip()

    def generate_ga4_code(self, measurement_id: str) -> str:
        """Generate Google Analytics 4 tracking code"""
        config = self.analytics_configs.get(AnalyticsProvider.GOOGLE_ANALYTICS_4.value)

        code = f"""
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id={measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());

  gtag('config', '{measurement_id}', {{
    'anonymize_ip': {str(config.anonymize_ip).lower() if config else 'true'}
  }});
</script>
<!-- End Google Analytics 4 -->
"""
        return code.strip()

    def generate_facebook_pixel_code(self, pixel_id: str) -> str:
        """Generate Facebook Pixel tracking code"""
        code = f"""
<!-- Facebook Pixel Code -->
<script>
!function(f,b,e,v,n,t,s)
{{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
n.queue=[];t=b.createElement(e);t.async=!0;
t.src=v;s=b.getElementsByTagName(e)[0];
s.parentNode.insertBefore(t,s)}}(window, document,'script',
'https://connect.facebook.net/en_US/fbevents.js');
fbq('init', '{pixel_id}');
fbq('track', 'PageView');
</script>
<noscript>
  <img height="1" width="1" style="display:none"
       src="https://www.facebook.com/tr?id={pixel_id}&ev=PageView&noscript=1"/>
</noscript>
<!-- End Facebook Pixel Code -->
"""
        return code.strip()

    def generate_hotjar_code(self, site_id: str) -> str:
        """Generate Hotjar tracking code"""
        code = f"""
<!-- Hotjar Tracking Code -->
<script>
    (function(h,o,t,j,a,r){{
        h.hj=h.hj||function(){{(h.hj.q=h.hj.q||[]).push(arguments)}};
        h._hjSettings={{hjid:{site_id},hjsv:6}};
        a=o.getElementsByTagName('head')[0];
        r=o.createElement('script');r.async=1;
        r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;
        a.appendChild(r);
    }})(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');
</script>
<!-- End Hotjar Tracking Code -->
"""
        return code.strip()

    def generate_all_tracking_codes(self) -> str:
        """Generate all enabled tracking codes"""
        codes = []

        for provider, config in self.analytics_configs.items():
            if not config.enabled:
                continue

            if config.provider == AnalyticsProvider.GOOGLE_ANALYTICS:
                codes.append(self.generate_google_analytics_code(config.tracking_id))
            elif config.provider == AnalyticsProvider.GOOGLE_ANALYTICS_4:
                codes.append(self.generate_ga4_code(config.tracking_id))
            elif config.provider == AnalyticsProvider.FACEBOOK_PIXEL:
                codes.append(self.generate_facebook_pixel_code(config.tracking_id))
            elif config.provider == AnalyticsProvider.HOTJAR:
                codes.append(self.generate_hotjar_code(config.tracking_id))

        return "\n\n".join(codes)

    # Event Tracking

    def track_event(
        self,
        event_type: EventType,
        event_name: str,
        properties: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Event:
        """Track an event"""
        import uuid

        event = Event(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            event_name=event_name,
            timestamp=datetime.now(),
            properties=properties or {},
            user_id=user_id,
            session_id=session_id,
        )

        self.events.append(event)
        return event

    def track_page_view(
        self,
        page_url: str,
        page_title: str,
        referrer: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> PageView:
        """Track a page view"""
        page_view = PageView(
            page_url=page_url,
            page_title=page_title,
            timestamp=datetime.now(),
            referrer=referrer,
            user_agent=user_agent,
            session_id=session_id,
        )

        self.page_views.append(page_view)
        return page_view

    def track_ecommerce_event(
        self,
        event_type: str,
        transaction_id: Optional[str] = None,
        value: Optional[float] = None,
        currency: str = "USD",
        items: Optional[List[Dict[str, Any]]] = None,
    ) -> Event:
        """Track e-commerce event"""
        properties = {
            "transaction_id": transaction_id,
            "value": value,
            "currency": currency,
            "items": items or [],
        }

        return self.track_event(
            EventType.PURCHASE if event_type == "purchase" else EventType.CUSTOM,
            event_type,
            properties,
        )

    # Analytics Reports

    def get_page_views_report(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get page views report"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        filtered_views = [
            pv for pv in self.page_views
            if start_date <= pv.timestamp <= end_date
        ]

        # Count views by page
        page_counts: Dict[str, int] = {}
        for pv in filtered_views:
            page_counts[pv.page_url] = page_counts.get(pv.page_url, 0) + 1

        return {
            "total_page_views": len(filtered_views),
            "unique_pages": len(page_counts),
            "top_pages": sorted(
                page_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def get_events_report(
        self,
        event_type: Optional[EventType] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get events report"""
        if start_date is None:
            start_date = datetime.now() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.now()

        filtered_events = [
            e for e in self.events
            if start_date <= e.timestamp <= end_date
            and (event_type is None or e.event_type == event_type)
        ]

        # Count events by name
        event_counts: Dict[str, int] = {}
        for e in filtered_events:
            event_counts[e.event_name] = event_counts.get(e.event_name, 0) + 1

        return {
            "total_events": len(filtered_events),
            "unique_events": len(event_counts),
            "top_events": sorted(
                event_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "event_type": event_type.value if event_type else "all",
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
            },
        }

    def get_traffic_sources_report(self) -> Dict[str, Any]:
        """Get traffic sources report"""
        sources: Dict[str, int] = {}

        for pv in self.page_views:
            if pv.referrer:
                # Extract domain from referrer
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(pv.referrer).netloc
                    sources[domain] = sources.get(domain, 0) + 1
                except:
                    sources["direct"] = sources.get("direct", 0) + 1
            else:
                sources["direct"] = sources.get("direct", 0) + 1

        return {
            "traffic_sources": sorted(
                sources.items(),
                key=lambda x: x[1],
                reverse=True
            ),
        }

    def get_realtime_stats(self) -> Dict[str, Any]:
        """Get real-time statistics"""
        now = datetime.now()
        last_5_min = now - timedelta(minutes=5)

        recent_views = [
            pv for pv in self.page_views
            if pv.timestamp >= last_5_min
        ]

        recent_events = [
            e for e in self.events
            if e.timestamp >= last_5_min
        ]

        return {
            "active_users": len(set(pv.session_id for pv in recent_views if pv.session_id)),
            "page_views_5min": len(recent_views),
            "events_5min": len(recent_events),
            "timestamp": now.isoformat(),
        }

    def get_conversion_funnel(self, steps: List[str]) -> Dict[str, Any]:
        """Get conversion funnel data"""
        funnel_data = {}

        for step in steps:
            matching_events = [
                e for e in self.events
                if e.event_name == step
            ]
            funnel_data[step] = len(matching_events)

        # Calculate conversion rates
        conversion_rates = {}
        total = funnel_data.get(steps[0], 0) if steps else 0

        for i, step in enumerate(steps):
            count = funnel_data.get(step, 0)
            if i == 0:
                conversion_rates[step] = 100.0
            elif total > 0:
                conversion_rates[step] = (count / total) * 100
            else:
                conversion_rates[step] = 0.0

        return {
            "funnel_data": funnel_data,
            "conversion_rates": conversion_rates,
            "total_started": total,
            "total_completed": funnel_data.get(steps[-1], 0) if steps else 0,
        }

    def get_user_retention(self, cohort_days: int = 30) -> Dict[str, Any]:
        """Get user retention data"""
        # Simplified retention calculation
        now = datetime.now()
        cohort_start = now - timedelta(days=cohort_days)

        sessions_by_user: Dict[str, List[datetime]] = {}

        for pv in self.page_views:
            if pv.session_id and pv.timestamp >= cohort_start:
                if pv.session_id not in sessions_by_user:
                    sessions_by_user[pv.session_id] = []
                sessions_by_user[pv.session_id].append(pv.timestamp)

        # Calculate return rate
        returning_users = sum(
            1 for sessions in sessions_by_user.values()
            if len(sessions) > 1
        )

        total_users = len(sessions_by_user)

        return {
            "cohort_period_days": cohort_days,
            "total_users": total_users,
            "returning_users": returning_users,
            "retention_rate": (returning_users / total_users * 100) if total_users > 0 else 0,
        }

    # Custom Dimensions & Metrics

    def set_custom_dimension(
        self,
        dimension_name: str,
        dimension_value: str,
    ) -> Dict[str, str]:
        """Set custom dimension"""
        return {
            "dimension": dimension_name,
            "value": dimension_value,
        }

    def set_custom_metric(
        self,
        metric_name: str,
        metric_value: float,
    ) -> Dict[str, Any]:
        """Set custom metric"""
        return {
            "metric": metric_name,
            "value": metric_value,
        }

    # Goals & Conversions

    def create_goal(
        self,
        goal_name: str,
        goal_type: str,
        target_value: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Create conversion goal"""
        import uuid

        return {
            "goal_id": str(uuid.uuid4()),
            "goal_name": goal_name,
            "goal_type": goal_type,
            "target_value": target_value,
            "created_at": datetime.now().isoformat(),
        }

    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get analytics summary"""
        return {
            "total_page_views": len(self.page_views),
            "total_events": len(self.events),
            "active_providers": len([c for c in self.analytics_configs.values() if c.enabled]),
            "tracking_enabled": any(c.enabled for c in self.analytics_configs.values()),
        }
