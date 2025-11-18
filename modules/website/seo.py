"""
SEO Manager - SEO optimization, meta tags, structured data, and analytics
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import json
from datetime import datetime


class StructuredDataType(Enum):
    """Schema.org structured data types"""
    ORGANIZATION = "Organization"
    WEBSITE = "WebSite"
    ARTICLE = "Article"
    BLOG_POSTING = "BlogPosting"
    PRODUCT = "Product"
    LOCAL_BUSINESS = "LocalBusiness"
    PERSON = "Person"
    BREADCRUMB_LIST = "BreadcrumbList"
    FAQ = "FAQPage"
    HOW_TO = "HowTo"
    RECIPE = "Recipe"
    EVENT = "Event"


@dataclass
class SEOConfig:
    """SEO configuration"""
    site_name: str
    site_url: str
    default_title: str
    default_description: str
    default_keywords: List[str] = field(default_factory=list)
    default_author: str = ""
    default_og_image: str = ""
    twitter_handle: str = ""
    facebook_app_id: str = ""
    google_site_verification: str = ""
    bing_site_verification: str = ""
    robots_txt: str = "User-agent: *\nAllow: /"
    enable_sitemap: bool = True
    enable_schema: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "site_name": self.site_name,
            "site_url": self.site_url,
            "default_title": self.default_title,
            "default_description": self.default_description,
            "default_keywords": self.default_keywords,
            "default_author": self.default_author,
            "default_og_image": self.default_og_image,
            "twitter_handle": self.twitter_handle,
            "facebook_app_id": self.facebook_app_id,
            "google_site_verification": self.google_site_verification,
            "bing_site_verification": self.bing_site_verification,
            "robots_txt": self.robots_txt,
            "enable_sitemap": self.enable_sitemap,
            "enable_schema": self.enable_schema,
        }


@dataclass
class MetaTags:
    """Meta tags for a page"""
    title: str
    description: str
    keywords: List[str] = field(default_factory=list)
    author: str = ""
    robots: str = "index, follow"
    canonical: str = ""
    language: str = "en"
    charset: str = "UTF-8"
    viewport: str = "width=device-width, initial-scale=1.0"


@dataclass
class OpenGraphTags:
    """Open Graph tags for social media"""
    og_type: str = "website"
    og_title: str = ""
    og_description: str = ""
    og_image: str = ""
    og_url: str = ""
    og_site_name: str = ""
    og_locale: str = "en_US"


@dataclass
class TwitterCardTags:
    """Twitter Card tags"""
    card_type: str = "summary_large_image"
    site: str = ""
    creator: str = ""
    title: str = ""
    description: str = ""
    image: str = ""


class SEOManager:
    """Manager for SEO optimization"""

    def __init__(self, config: SEOConfig):
        self.config = config
        self.structured_data: Dict[str, Dict[str, Any]] = {}

    def generate_meta_tags(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        author: Optional[str] = None,
        canonical: Optional[str] = None,
        robots: str = "index, follow",
    ) -> str:
        """Generate HTML meta tags"""
        meta = MetaTags(
            title=title or self.config.default_title,
            description=description or self.config.default_description,
            keywords=keywords or self.config.default_keywords,
            author=author or self.config.default_author,
            canonical=canonical or "",
            robots=robots,
        )

        tags = []
        tags.append(f'<meta charset="{meta.charset}">')
        tags.append(f'<meta name="viewport" content="{meta.viewport}">')
        tags.append(f'<title>{meta.title}</title>')
        tags.append(f'<meta name="description" content="{meta.description}">')

        if meta.keywords:
            tags.append(f'<meta name="keywords" content="{", ".join(meta.keywords)}">')

        if meta.author:
            tags.append(f'<meta name="author" content="{meta.author}">')

        tags.append(f'<meta name="robots" content="{meta.robots}">')

        if meta.canonical:
            tags.append(f'<link rel="canonical" href="{meta.canonical}">')

        tags.append(f'<meta http-equiv="content-language" content="{meta.language}">')

        return "\n".join(tags)

    def generate_open_graph_tags(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        image: Optional[str] = None,
        url: Optional[str] = None,
        og_type: str = "website",
    ) -> str:
        """Generate Open Graph meta tags"""
        og = OpenGraphTags(
            og_type=og_type,
            og_title=title or self.config.default_title,
            og_description=description or self.config.default_description,
            og_image=image or self.config.default_og_image,
            og_url=url or self.config.site_url,
            og_site_name=self.config.site_name,
        )

        tags = []
        tags.append(f'<meta property="og:type" content="{og.og_type}">')
        tags.append(f'<meta property="og:title" content="{og.og_title}">')
        tags.append(f'<meta property="og:description" content="{og.og_description}">')

        if og.og_image:
            tags.append(f'<meta property="og:image" content="{og.og_image}">')

        tags.append(f'<meta property="og:url" content="{og.og_url}">')
        tags.append(f'<meta property="og:site_name" content="{og.og_site_name}">')
        tags.append(f'<meta property="og:locale" content="{og.og_locale}">')

        if self.config.facebook_app_id:
            tags.append(f'<meta property="fb:app_id" content="{self.config.facebook_app_id}">')

        return "\n".join(tags)

    def generate_twitter_card_tags(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        image: Optional[str] = None,
        card_type: str = "summary_large_image",
    ) -> str:
        """Generate Twitter Card meta tags"""
        twitter = TwitterCardTags(
            card_type=card_type,
            site=self.config.twitter_handle,
            creator=self.config.twitter_handle,
            title=title or self.config.default_title,
            description=description or self.config.default_description,
            image=image or self.config.default_og_image,
        )

        tags = []
        tags.append(f'<meta name="twitter:card" content="{twitter.card_type}">')

        if twitter.site:
            tags.append(f'<meta name="twitter:site" content="{twitter.site}">')

        if twitter.creator:
            tags.append(f'<meta name="twitter:creator" content="{twitter.creator}">')

        tags.append(f'<meta name="twitter:title" content="{twitter.title}">')
        tags.append(f'<meta name="twitter:description" content="{twitter.description}">')

        if twitter.image:
            tags.append(f'<meta name="twitter:image" content="{twitter.image}">')

        return "\n".join(tags)

    def generate_verification_tags(self) -> str:
        """Generate site verification tags"""
        tags = []

        if self.config.google_site_verification:
            tags.append(f'<meta name="google-site-verification" content="{self.config.google_site_verification}">')

        if self.config.bing_site_verification:
            tags.append(f'<meta name="msvalidate.01" content="{self.config.bing_site_verification}">')

        return "\n".join(tags)

    def create_structured_data(
        self,
        data_type: StructuredDataType,
        data: Dict[str, Any],
    ) -> str:
        """Create JSON-LD structured data"""
        schema = {
            "@context": "https://schema.org",
            "@type": data_type.value,
            **data,
        }

        json_ld = json.dumps(schema, indent=2)
        return f'<script type="application/ld+json">\n{json_ld}\n</script>'

    def create_organization_schema(
        self,
        name: str,
        url: str,
        logo: str,
        description: str = "",
        social_links: Optional[List[str]] = None,
        contact_info: Optional[Dict[str, str]] = None,
    ) -> str:
        """Create Organization structured data"""
        data = {
            "name": name,
            "url": url,
            "logo": logo,
        }

        if description:
            data["description"] = description

        if social_links:
            data["sameAs"] = social_links

        if contact_info:
            data["contactPoint"] = {
                "@type": "ContactPoint",
                **contact_info,
            }

        return self.create_structured_data(StructuredDataType.ORGANIZATION, data)

    def create_website_schema(
        self,
        name: str,
        url: str,
        description: str = "",
        search_url: Optional[str] = None,
    ) -> str:
        """Create WebSite structured data"""
        data = {
            "name": name,
            "url": url,
        }

        if description:
            data["description"] = description

        if search_url:
            data["potentialAction"] = {
                "@type": "SearchAction",
                "target": f"{search_url}?q={{search_term_string}}",
                "query-input": "required name=search_term_string",
            }

        return self.create_structured_data(StructuredDataType.WEBSITE, data)

    def create_article_schema(
        self,
        headline: str,
        author: str,
        date_published: str,
        date_modified: str,
        image: str,
        description: str = "",
    ) -> str:
        """Create Article structured data"""
        data = {
            "headline": headline,
            "author": {
                "@type": "Person",
                "name": author,
            },
            "datePublished": date_published,
            "dateModified": date_modified,
            "image": image,
        }

        if description:
            data["description"] = description

        return self.create_structured_data(StructuredDataType.ARTICLE, data)

    def create_product_schema(
        self,
        name: str,
        description: str,
        image: str,
        price: str,
        currency: str = "USD",
        availability: str = "InStock",
        brand: Optional[str] = None,
        rating: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create Product structured data"""
        data = {
            "name": name,
            "description": description,
            "image": image,
            "offers": {
                "@type": "Offer",
                "price": price,
                "priceCurrency": currency,
                "availability": f"https://schema.org/{availability}",
            },
        }

        if brand:
            data["brand"] = {
                "@type": "Brand",
                "name": brand,
            }

        if rating:
            data["aggregateRating"] = {
                "@type": "AggregateRating",
                **rating,
            }

        return self.create_structured_data(StructuredDataType.PRODUCT, data)

    def create_breadcrumb_schema(self, items: List[Dict[str, str]]) -> str:
        """Create BreadcrumbList structured data"""
        list_items = []
        for index, item in enumerate(items, start=1):
            list_items.append({
                "@type": "ListItem",
                "position": index,
                "name": item["name"],
                "item": item["url"],
            })

        data = {
            "itemListElement": list_items,
        }

        return self.create_structured_data(StructuredDataType.BREADCRUMB_LIST, data)

    def create_faq_schema(self, questions: List[Dict[str, str]]) -> str:
        """Create FAQ structured data"""
        main_entity = []
        for qa in questions:
            main_entity.append({
                "@type": "Question",
                "name": qa["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa["answer"],
                },
            })

        data = {
            "mainEntity": main_entity,
        }

        return self.create_structured_data(StructuredDataType.FAQ, data)

    def create_local_business_schema(
        self,
        name: str,
        address: Dict[str, str],
        phone: str,
        url: str,
        opening_hours: Optional[List[str]] = None,
        geo: Optional[Dict[str, float]] = None,
    ) -> str:
        """Create LocalBusiness structured data"""
        data = {
            "name": name,
            "address": {
                "@type": "PostalAddress",
                **address,
            },
            "telephone": phone,
            "url": url,
        }

        if opening_hours:
            data["openingHours"] = opening_hours

        if geo:
            data["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": geo.get("latitude", 0),
                "longitude": geo.get("longitude", 0),
            }

        return self.create_structured_data(StructuredDataType.LOCAL_BUSINESS, data)

    def generate_robots_txt(self, custom_rules: Optional[str] = None) -> str:
        """Generate robots.txt content"""
        if custom_rules:
            return custom_rules

        robots = [
            "User-agent: *",
            "Allow: /",
            "",
            "# Disallow admin areas",
            "Disallow: /admin/",
            "Disallow: /api/",
            "",
            "# Sitemap",
            f"Sitemap: {self.config.site_url}/sitemap.xml",
        ]

        return "\n".join(robots)

    def analyze_seo_score(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze SEO score for a page"""
        score = 100
        issues = []
        recommendations = []

        # Title check
        title = page_data.get("title", "")
        if not title:
            score -= 20
            issues.append("Missing page title")
        elif len(title) < 30:
            score -= 5
            recommendations.append("Title is too short (recommended: 50-60 characters)")
        elif len(title) > 60:
            score -= 5
            recommendations.append("Title is too long (recommended: 50-60 characters)")

        # Description check
        description = page_data.get("description", "")
        if not description:
            score -= 15
            issues.append("Missing meta description")
        elif len(description) < 120:
            score -= 5
            recommendations.append("Description is too short (recommended: 150-160 characters)")
        elif len(description) > 160:
            score -= 5
            recommendations.append("Description is too long (recommended: 150-160 characters)")

        # Keywords check
        keywords = page_data.get("keywords", [])
        if not keywords:
            score -= 5
            recommendations.append("Consider adding meta keywords")

        # Image alt text check
        images_without_alt = page_data.get("images_without_alt", 0)
        if images_without_alt > 0:
            score -= min(images_without_alt * 2, 10)
            issues.append(f"{images_without_alt} images missing alt text")

        # Heading structure check
        has_h1 = page_data.get("has_h1", False)
        if not has_h1:
            score -= 10
            issues.append("Missing H1 heading")

        # Mobile friendliness
        is_mobile_friendly = page_data.get("is_mobile_friendly", True)
        if not is_mobile_friendly:
            score -= 15
            issues.append("Page is not mobile-friendly")

        # Page speed
        load_time = page_data.get("load_time", 0)
        if load_time > 3:
            score -= 10
            issues.append(f"Slow page load time: {load_time}s (recommended: <3s)")

        # Canonical URL
        has_canonical = page_data.get("has_canonical", False)
        if not has_canonical:
            score -= 5
            recommendations.append("Add canonical URL")

        # Structured data
        has_schema = page_data.get("has_schema", False)
        if not has_schema:
            score -= 5
            recommendations.append("Add structured data (Schema.org)")

        score = max(0, score)

        return {
            "score": score,
            "grade": self._get_grade(score),
            "issues": issues,
            "recommendations": recommendations,
        }

    def _get_grade(self, score: int) -> str:
        """Get letter grade from score"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"

    def generate_all_meta_tags(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        author: Optional[str] = None,
        canonical: Optional[str] = None,
        image: Optional[str] = None,
        url: Optional[str] = None,
    ) -> str:
        """Generate all meta tags (basic, OG, Twitter, verification)"""
        tags = []

        tags.append(self.generate_meta_tags(title, description, keywords, author, canonical))
        tags.append("")
        tags.append(self.generate_open_graph_tags(title, description, image, url))
        tags.append("")
        tags.append(self.generate_twitter_card_tags(title, description, image))
        tags.append("")
        tags.append(self.generate_verification_tags())

        return "\n".join(tags)
