"""
NEXUS E-commerce - Products Module
Handles product catalog, variants, pricing, inventory, and reviews.
Rival to Shopify and WooCommerce platforms.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import json


class ProductStatus(Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    OUT_OF_STOCK = "out_of_stock"


class ProductType(Enum):
    PHYSICAL = "physical"
    DIGITAL = "digital"
    SERVICE = "service"
    SUBSCRIPTION = "subscription"


@dataclass
class ProductVariant:
    """Product variant (size, color, etc.)"""
    id: str
    sku: str
    name: str

    # Variant attributes
    attributes: Dict[str, str] = field(default_factory=dict)  # {"size": "Large", "color": "Red"}

    # Pricing
    price: float = 0.0
    compare_at_price: Optional[float] = None
    cost_per_item: Optional[float] = None

    # Inventory
    inventory_quantity: int = 0
    track_inventory: bool = True
    allow_backorder: bool = False

    # Physical attributes
    weight: Optional[float] = None
    weight_unit: str = "kg"
    requires_shipping: bool = True

    # Images
    image_url: Optional[str] = None

    # Status
    is_available: bool = True
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Product:
    """Main product entity"""
    id: str
    name: str
    description: str
    product_type: ProductType
    status: ProductStatus

    # Pricing
    price: float = 0.0
    compare_at_price: Optional[float] = None
    on_sale: bool = False
    sale_price: Optional[float] = None

    # Organization
    category: str = ""
    subcategory: str = ""
    brand: str = ""
    tags: List[str] = field(default_factory=list)
    collections: List[str] = field(default_factory=list)

    # Variants
    variants: List[ProductVariant] = field(default_factory=list)
    has_variants: bool = False

    # Media
    images: List[str] = field(default_factory=list)  # image URLs
    videos: List[str] = field(default_factory=list)
    featured_image: str = ""

    # SEO
    seo_title: str = ""
    seo_description: str = ""
    url_handle: str = ""  # slug

    # Inventory
    total_inventory: int = 0
    track_inventory: bool = True
    inventory_policy: str = "deny"  # "deny" or "continue" (allow backorder)

    # Shipping
    requires_shipping: bool = True
    weight: Optional[float] = None
    weight_unit: str = "kg"
    dimensions: Dict[str, float] = field(default_factory=dict)  # length, width, height

    # Digital product
    download_url: Optional[str] = None
    download_limit: Optional[int] = None

    # Reviews and ratings
    average_rating: float = 0.0
    total_reviews: int = 0
    rating_distribution: Dict[int, int] = field(default_factory=dict)  # {5: 10, 4: 5, ...}

    # Analytics
    total_sales: int = 0
    total_revenue: float = 0.0
    views: int = 0

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    published_at: Optional[datetime] = None


@dataclass
class ProductReview:
    """Customer product review"""
    id: str
    product_id: str
    customer_id: str
    customer_name: str

    # Review content
    rating: int  # 1-5
    title: str
    content: str

    # Verification
    is_verified_purchase: bool = False

    # Engagement
    helpful_count: int = 0
    not_helpful_count: int = 0

    # Moderation
    is_approved: bool = False
    is_featured: bool = False

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class ProductCategory:
    """Product category"""
    id: str
    name: str
    description: str
    parent_id: Optional[str] = None

    # Display
    image_url: str = ""
    icon: str = ""
    color: str = ""

    # SEO
    url_handle: str = ""

    # Metadata
    product_count: int = 0
    display_order: int = 0
    is_active: bool = True


class ProductManager:
    """Manages product catalog and related operations"""

    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.reviews: Dict[str, List[ProductReview]] = {}  # key: product_id
        self.categories: Dict[str, ProductCategory] = {}

    # Product management

    def create_product(
        self,
        name: str,
        description: str,
        price: float,
        product_type: ProductType = ProductType.PHYSICAL,
        **kwargs
    ) -> Product:
        """Create a new product"""
        import uuid
        product_id = kwargs.get('id', str(uuid.uuid4()))

        # Generate URL handle (slug)
        url_handle = kwargs.get('url_handle', self._generate_url_handle(name))

        product = Product(
            id=product_id,
            name=name,
            description=description,
            price=price,
            product_type=product_type,
            status=ProductStatus.DRAFT,
            url_handle=url_handle,
            **{k: v for k, v in kwargs.items() if k not in ['id', 'url_handle']}
        )

        self.products[product_id] = product
        return product

    def _generate_url_handle(self, name: str) -> str:
        """Generate URL-friendly slug from product name"""
        import re
        handle = name.lower()
        handle = re.sub(r'[^a-z0-9\s-]', '', handle)
        handle = re.sub(r'\s+', '-', handle)
        return handle.strip('-')

    def add_variant(self, product_id: str, variant: ProductVariant) -> bool:
        """Add a variant to a product"""
        if product_id not in self.products:
            return False

        product = self.products[product_id]
        product.variants.append(variant)
        product.has_variants = True

        # Update total inventory
        self._update_product_inventory(product_id)

        product.updated_at = datetime.now()
        return True

    def update_product(self, product_id: str, **updates) -> Optional[Product]:
        """Update product details"""
        if product_id not in self.products:
            return None

        product = self.products[product_id]
        for key, value in updates.items():
            if hasattr(product, key):
                setattr(product, key, value)

        product.updated_at = datetime.now()
        return product

    def publish_product(self, product_id: str) -> bool:
        """Publish a product"""
        if product_id not in self.products:
            return False

        product = self.products[product_id]
        product.status = ProductStatus.ACTIVE
        product.published_at = datetime.now()
        product.updated_at = datetime.now()

        return True

    def archive_product(self, product_id: str) -> bool:
        """Archive a product"""
        if product_id not in self.products:
            return False

        self.products[product_id].status = ProductStatus.ARCHIVED
        self.products[product_id].updated_at = datetime.now()
        return True

    def _update_product_inventory(self, product_id: str) -> None:
        """Update total inventory count for product"""
        product = self.products[product_id]

        if product.has_variants:
            product.total_inventory = sum(v.inventory_quantity for v in product.variants)
        # else: inventory managed at product level

        # Update stock status
        if product.total_inventory <= 0 and product.inventory_policy == "deny":
            product.status = ProductStatus.OUT_OF_STOCK
        elif product.status == ProductStatus.OUT_OF_STOCK and product.total_inventory > 0:
            product.status = ProductStatus.ACTIVE

    # Product search and filtering

    def get_product(self, product_id: str) -> Optional[Product]:
        """Get a product by ID"""
        product = self.products.get(product_id)
        if product:
            product.views += 1
        return product

    def get_product_by_handle(self, url_handle: str) -> Optional[Product]:
        """Get a product by URL handle"""
        for product in self.products.values():
            if product.url_handle == url_handle:
                product.views += 1
                return product
        return None

    def search_products(
        self,
        query: str = "",
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        tags: Optional[List[str]] = None,
        in_stock_only: bool = False,
        on_sale_only: bool = False,
        min_rating: float = 0.0,
        sort_by: str = "relevance"  # relevance, price_asc, price_desc, newest, popular
    ) -> List[Product]:
        """Search and filter products"""
        results = [p for p in self.products.values() if p.status == ProductStatus.ACTIVE]

        # Text search
        if query:
            query_lower = query.lower()
            results = [
                p for p in results
                if (query_lower in p.name.lower()
                    or query_lower in p.description.lower()
                    or query_lower in p.brand.lower()
                    or any(query_lower in tag.lower() for tag in p.tags))
            ]

        # Category filter
        if category:
            results = [p for p in results if p.category == category]

        # Price range
        if min_price is not None:
            results = [p for p in results if p.price >= min_price]
        if max_price is not None:
            results = [p for p in results if p.price <= max_price]

        # Tags
        if tags:
            results = [
                p for p in results
                if any(tag in p.tags for tag in tags)
            ]

        # Stock filter
        if in_stock_only:
            results = [p for p in results if p.total_inventory > 0]

        # Sale filter
        if on_sale_only:
            results = [p for p in results if p.on_sale]

        # Rating filter
        if min_rating > 0:
            results = [p for p in results if p.average_rating >= min_rating]

        # Sorting
        if sort_by == "price_asc":
            results.sort(key=lambda p: p.price)
        elif sort_by == "price_desc":
            results.sort(key=lambda p: p.price, reverse=True)
        elif sort_by == "newest":
            results.sort(key=lambda p: p.created_at, reverse=True)
        elif sort_by == "popular":
            results.sort(key=lambda p: p.total_sales, reverse=True)
        elif sort_by == "rating":
            results.sort(key=lambda p: p.average_rating, reverse=True)

        return results

    def get_category_products(self, category: str) -> List[Product]:
        """Get all products in a category"""
        return [
            p for p in self.products.values()
            if p.category == category and p.status == ProductStatus.ACTIVE
        ]

    def get_related_products(self, product_id: str, limit: int = 4) -> List[Product]:
        """Get related products based on category and tags"""
        if product_id not in self.products:
            return []

        product = self.products[product_id]

        # Find products with same category or overlapping tags
        related = []
        for p in self.products.values():
            if p.id == product_id or p.status != ProductStatus.ACTIVE:
                continue

            score = 0
            if p.category == product.category:
                score += 2
            if p.brand == product.brand:
                score += 1

            common_tags = set(p.tags) & set(product.tags)
            score += len(common_tags)

            if score > 0:
                related.append((score, p))

        # Sort by score and return top N
        related.sort(key=lambda x: x[0], reverse=True)
        return [p for _, p in related[:limit]]

    # Reviews

    def add_review(
        self,
        product_id: str,
        customer_id: str,
        customer_name: str,
        rating: int,
        title: str,
        content: str,
        is_verified_purchase: bool = False
    ) -> ProductReview:
        """Add a product review"""
        if product_id not in self.products:
            raise ValueError("Product not found")

        if not 1 <= rating <= 5:
            raise ValueError("Rating must be between 1 and 5")

        import uuid
        review = ProductReview(
            id=str(uuid.uuid4()),
            product_id=product_id,
            customer_id=customer_id,
            customer_name=customer_name,
            rating=rating,
            title=title,
            content=content,
            is_verified_purchase=is_verified_purchase
        )

        if product_id not in self.reviews:
            self.reviews[product_id] = []

        self.reviews[product_id].append(review)

        # Update product rating
        self._update_product_rating(product_id)

        return review

    def approve_review(self, review_id: str, product_id: str) -> bool:
        """Approve a review"""
        if product_id not in self.reviews:
            return False

        for review in self.reviews[product_id]:
            if review.id == review_id:
                review.is_approved = True
                review.updated_at = datetime.now()
                return True

        return False

    def _update_product_rating(self, product_id: str) -> None:
        """Recalculate product rating"""
        product = self.products[product_id]
        reviews = self.reviews.get(product_id, [])

        approved_reviews = [r for r in reviews if r.is_approved]

        if not approved_reviews:
            return

        # Calculate average
        total_rating = sum(r.rating for r in approved_reviews)
        product.average_rating = total_rating / len(approved_reviews)
        product.total_reviews = len(approved_reviews)

        # Update distribution
        product.rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for review in approved_reviews:
            product.rating_distribution[review.rating] += 1

    def get_product_reviews(
        self,
        product_id: str,
        approved_only: bool = True,
        sort_by: str = "newest"  # newest, oldest, highest, lowest, helpful
    ) -> List[ProductReview]:
        """Get reviews for a product"""
        if product_id not in self.reviews:
            return []

        reviews = self.reviews[product_id]

        if approved_only:
            reviews = [r for r in reviews if r.is_approved]

        # Sorting
        if sort_by == "newest":
            reviews = sorted(reviews, key=lambda r: r.created_at, reverse=True)
        elif sort_by == "oldest":
            reviews = sorted(reviews, key=lambda r: r.created_at)
        elif sort_by == "highest":
            reviews = sorted(reviews, key=lambda r: r.rating, reverse=True)
        elif sort_by == "lowest":
            reviews = sorted(reviews, key=lambda r: r.rating)
        elif sort_by == "helpful":
            reviews = sorted(reviews, key=lambda r: r.helpful_count, reverse=True)

        return reviews

    # Categories

    def create_category(
        self,
        name: str,
        description: str,
        **kwargs
    ) -> ProductCategory:
        """Create a product category"""
        import uuid
        category_id = kwargs.get('id', str(uuid.uuid4()))

        url_handle = kwargs.get('url_handle', self._generate_url_handle(name))

        category = ProductCategory(
            id=category_id,
            name=name,
            description=description,
            url_handle=url_handle,
            **{k: v for k, v in kwargs.items() if k not in ['id', 'url_handle']}
        )

        self.categories[category_id] = category
        return category

    def get_category(self, category_id: str) -> Optional[ProductCategory]:
        """Get a category"""
        return self.categories.get(category_id)


# Example usage
if __name__ == "__main__":
    manager = ProductManager()

    # Create a product
    product = manager.create_product(
        name="Premium Wireless Headphones",
        description="High-quality wireless headphones with noise cancellation",
        price=299.99,
        category="Electronics",
        brand="AudioTech",
        tags=["wireless", "audio", "headphones", "bluetooth"]
    )

    # Add variant
    variant = ProductVariant(
        id="var_001",
        sku="HEADPHONES-BLACK",
        name="Black",
        attributes={"color": "Black"},
        price=299.99,
        inventory_quantity=50
    )
    manager.add_variant(product.id, variant)

    # Publish product
    manager.publish_product(product.id)

    # Add review
    review = manager.add_review(
        product.id,
        "customer_001",
        "John Doe",
        5,
        "Excellent sound quality!",
        "These headphones exceeded my expectations.",
        is_verified_purchase=True
    )
    manager.approve_review(review.id, product.id)

    # Search products
    results = manager.search_products(query="wireless", category="Electronics")

    print(f"Product: {product.name}")
    print(f"Price: ${product.price}")
    print(f"Rating: {product.average_rating:.1f}/5.0")
