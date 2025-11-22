# NEXUS Social Media Manager

A comprehensive, production-ready social media management system integrated with the NEXUS platform.

## 🚀 Features

### Multi-Platform Support
- **Facebook** - Posts, Pages, Groups
- **Twitter/X** - Tweets, Threads, Polls
- **Instagram** - Posts, Stories, Reels
- **LinkedIn** - Posts, Articles, Company Pages
- **TikTok** - Videos, Trends
- **YouTube** - Videos, Shorts, Community
- **Pinterest** - Pins, Boards

### Core Capabilities

#### 1. Content Management
- **Smart Composer** - Platform-specific customization
- **Media Library** - Asset management and organization
- **Content Templates** - Reusable post templates
- **Bulk Operations** - Schedule multiple posts at once
- **Draft Management** - Save and organize drafts

#### 2. Scheduling & Publishing
- **Visual Calendar** - Drag-and-drop scheduling
- **Optimal Times** - AI-suggested best posting times
- **Queue Management** - Organize posting queues
- **Recurring Posts** - Schedule repeating content
- **Multi-Platform** - Publish to multiple platforms simultaneously

#### 3. Engagement Management
- **Unified Inbox** - All comments/messages in one place
- **Sentiment Analysis** - Automated sentiment detection
- **Priority Sorting** - Focus on high-priority interactions
- **Auto-Responses** - AI-powered response suggestions
- **Bulk Actions** - Mark multiple as read, reply to many

#### 4. Analytics & Reporting
- **Cross-Platform Analytics** - Unified metrics across all platforms
- **Engagement Tracking** - Likes, comments, shares, etc.
- **Audience Insights** - Demographics and behavior
- **ROI Tracking** - Revenue and conversion tracking
- **Custom Reports** - Generate tailored reports
- **Export Options** - JSON, CSV, PDF formats

#### 5. Social Listening & Monitoring
- **Brand Mentions** - Track brand mentions across platforms
- **Hashtag Tracking** - Monitor hashtag performance
- **Competitor Analysis** - Track competitor activity
- **Keyword Alerts** - Get notified of specific keywords
- **Sentiment Monitoring** - Track brand sentiment

#### 6. Campaign Management
- **Campaign Organization** - Group posts by campaign
- **Budget Tracking** - Monitor spending and ROI
- **Goal Setting** - Define and track campaign goals
- **A/B Testing** - Test different content variations
- **Performance Comparison** - Compare campaign results

#### 7. Hashtag Intelligence
- **Trending Hashtags** - Discover trending tags
- **Performance Tracking** - Track hashtag effectiveness
- **Suggestions** - AI-powered hashtag recommendations
- **Saved Sets** - Create reusable hashtag collections
- **Analytics** - Detailed hashtag performance metrics

#### 8. AI-Powered Features
- **Caption Generation** - AI-written post captions
- **Content Ideas** - Topic and content suggestions
- **Optimal Timing** - Best time to post recommendations
- **Image Suggestions** - AI-recommended visuals
- **Performance Predictions** - Forecast post performance

#### 9. Team Collaboration
- **Approval Workflows** - Multi-level content approval
- **Role Management** - Admin, Manager, Editor, Contributor roles
- **Revision Requests** - Request changes with feedback
- **Team Permissions** - Granular access control
- **Audit Trail** - Complete activity history

#### 10. Link Management
- **URL Shortening** - Create short, trackable links
- **UTM Parameters** - Campaign tracking parameters
- **Click Analytics** - Detailed click tracking
- **Bio Links** - Manage profile link pages
- **Performance Tracking** - Monitor link performance

## 📦 Installation

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Node.js 16+ (for UI development)

### Install Dependencies

```bash
cd modules/social_media
pip install -r requirements.txt
```

### Environment Configuration

Create a `.env` file in the module directory:

```env
# Database
SOCIAL_MEDIA_DB_URL=postgresql://user:pass@localhost/nexus_social

# Redis
SOCIAL_MEDIA_REDIS_URL=redis://localhost:6379/0

# Social Media API Keys
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
TWITTER_API_KEY=your_api_key
TWITTER_API_SECRET=your_api_secret
INSTAGRAM_APP_ID=your_app_id
INSTAGRAM_APP_SECRET=your_app_secret
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret

# AI/LLM
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=your_api_key

# Configuration
SHORT_LINK_DOMAIN=short.link
MEDIA_STORAGE_PATH=/var/media/social
LOG_LEVEL=INFO
```

### Database Setup

```bash
# Create database
createdb nexus_social

# Run migrations (using Alembic)
alembic upgrade head
```

### Start Services

```bash
# Start Celery worker
celery -A modules.social_media.tasks worker --loglevel=info

# Start FastAPI server
uvicorn modules.social_media.api:router --reload --host 0.0.0.0 --port 8000

# Start Streamlit dashboard
streamlit run modules/social_media/streamlit_ui.py
```

## 🎯 Quick Start

### 1. Create a Post

```python
from modules.social_media import PostComposer, PlatformType
from uuid import uuid4

composer = PostComposer()

post = composer.create_post(
    title="My First Post",
    platforms=[PlatformType.FACEBOOK, PlatformType.TWITTER],
    author_id=uuid4(),
    base_content="Hello, world! 🌍"
)

# Customize for each platform
composer.update_content(
    post_id=post.id,
    platform=PlatformType.TWITTER,
    text="Hello, Twitter! 🐦",
    hashtags=["#SocialMedia", "#Marketing"]
)
```

### 2. Schedule a Post

```python
from modules.social_media import PostScheduler
from datetime import datetime, timedelta

scheduler = PostScheduler()

# Schedule for tomorrow at 2 PM
scheduled_time = datetime.now() + timedelta(days=1, hours=2)

scheduler.schedule_post(
    post=post,
    scheduled_time=scheduled_time,
    timezone="America/New_York"
)
```

### 3. Fetch Analytics

```python
from modules.social_media import AnalyticsManager

analytics = AnalyticsManager()

# Fetch post analytics
post_analytics = await analytics.fetch_post_analytics(
    post=post,
    platform=PlatformType.FACEBOOK
)

print(f"Impressions: {post_analytics.impressions}")
print(f"Engagement: {post_analytics.engagement_count}")
print(f"Reach: {post_analytics.reach}")
```

### 4. Manage Campaigns

```python
from modules.social_media import CampaignManager

campaign_manager = CampaignManager()

campaign = campaign_manager.create_campaign(
    name="Spring 2024 Launch",
    owner_id=uuid4(),
    platforms=[PlatformType.INSTAGRAM, PlatformType.FACEBOOK],
    budget=5000.0,
    goals={"impressions": 100000, "engagement": 5000}
)

# Add posts to campaign
campaign_manager.add_post_to_campaign(campaign.id, post.id)
```

### 5. Use AI Assistant

```python
from modules.social_media import AIContentAssistant

ai_assistant = AIContentAssistant()

# Generate caption
caption = ai_assistant.generate_caption(
    topic="Product Launch",
    platform=PlatformType.INSTAGRAM,
    tone="professional",
    include_hashtags=True
)

print(caption)
# Output: "Excited to introduce our latest innovation! ✨
#ProductLaunch #Innovation #Technology"
```

## 🔌 API Endpoints

### Posts
- `POST /api/social/posts` - Create a new post
- `GET /api/social/posts` - List all posts
- `GET /api/social/posts/{id}` - Get post by ID
- `PUT /api/social/posts/{id}` - Update post
- `DELETE /api/social/posts/{id}` - Delete post
- `POST /api/social/posts/{id}/schedule` - Schedule post

### Analytics
- `GET /api/social/analytics/posts/{id}` - Get post analytics
- `GET /api/social/analytics/campaigns/{id}` - Get campaign analytics

### Campaigns
- `POST /api/social/campaigns` - Create campaign
- `GET /api/social/campaigns` - List campaigns
- `GET /api/social/campaigns/{id}` - Get campaign

### Engagement
- `GET /api/social/engagement/inbox` - Get inbox
- `POST /api/social/engagement/{id}/reply` - Reply to engagement

### Hashtags
- `GET /api/social/hashtags/trending` - Get trending hashtags
- `POST /api/social/hashtags/suggest` - Get hashtag suggestions

### AI
- `POST /api/social/ai/generate-caption` - Generate caption
- `POST /api/social/ai/content-ideas` - Get content ideas

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest tests/social_media/

# Run with coverage
pytest tests/social_media/ --cov=modules/social_media --cov-report=html

# Run specific test file
pytest tests/social_media/test_composer.py
```

## 📊 Architecture

```
modules/social_media/
├── __init__.py              # Module exports
├── social_types.py          # Data models and types
├── platforms.py             # Platform integrations
├── composer.py              # Post composition
├── scheduling.py            # Scheduling logic
├── calendar.py              # Calendar views
├── media_library.py         # Media management
├── engagement.py            # Engagement handling
├── monitoring.py            # Social listening
├── analytics.py             # Analytics aggregation
├── reporting.py             # Report generation
├── hashtags.py              # Hashtag intelligence
├── content_ideas.py         # Content suggestions
├── approvals.py             # Approval workflows
├── campaigns.py             # Campaign management
├── influencer.py            # Influencer tracking
├── ugc.py                   # User-generated content
├── ads.py                   # Social advertising
├── links.py                 # Link management
├── ai_assistant.py          # AI features
├── streamlit_ui.py          # Streamlit dashboard
├── api.py                   # FastAPI endpoints
├── database.py              # SQLAlchemy models
├── tasks.py                 # Celery tasks
├── config.py                # Configuration
└── README.md                # This file
```

## 🔒 Security

- **API Keys** - Store in environment variables, never commit
- **OAuth Tokens** - Encrypted storage in database
- **Rate Limiting** - Prevent API abuse
- **Input Validation** - Pydantic models for all inputs
- **SQL Injection** - Parameterized queries via SQLAlchemy
- **XSS Protection** - Content sanitization

## 🎨 Streamlit Dashboard

Access the dashboard at `http://localhost:8501`:

- **Dashboard** - Overview and key metrics
- **Composer** - Create and edit posts
- **Calendar** - Visual content calendar
- **Analytics** - Performance insights
- **Inbox** - Unified engagement inbox
- **Monitoring** - Brand mentions and alerts
- **Campaigns** - Campaign management
- **Hashtags** - Hashtag intelligence
- **AI Assistant** - Content generation tools
- **Links** - Link tracking
- **Settings** - Platform connections and preferences

## 📈 Performance

- **Async Operations** - Celery for background tasks
- **Caching** - Redis for performance
- **Database Indexing** - Optimized queries
- **Rate Limiting** - Respect platform limits
- **Connection Pooling** - Efficient database connections

## 🛠️ Development

### Code Style

```bash
# Format code
black modules/social_media/

# Lint
flake8 modules/social_media/

# Type checking
mypy modules/social_media/
```

### Adding a New Platform

1. Create platform class in `platforms.py`
2. Extend `BasePlatform` abstract class
3. Implement required methods
4. Add platform to `PlatformFactory`
5. Update tests

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run test suite
5. Submit pull request

## 📄 License

Copyright © 2024 NEXUS Platform Team. All rights reserved.

## 🆘 Support

For issues and questions:
- GitHub Issues: https://github.com/nexus-platform/issues
- Documentation: https://docs.nexus-platform.com
- Email: support@nexus-platform.com

---

**Built with ❤️ for the NEXUS Platform**
