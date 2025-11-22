"""Tests for post composer module."""

import pytest
from uuid import uuid4
from modules.social_media.composer import PostComposer, ValidationError
from modules.social_media.social_types import PlatformType, MediaType, Media


@pytest.fixture
def composer():
    """Create a PostComposer instance."""
    return PostComposer()


@pytest.fixture
def author_id():
    """Create a test author ID."""
    return uuid4()


def test_create_post(composer, author_id):
    """Test creating a new post."""
    post = composer.create_post(
        title="Test Post",
        platforms=[PlatformType.FACEBOOK, PlatformType.TWITTER],
        author_id=author_id,
        base_content="This is a test post",
    )

    assert post.title == "Test Post"
    assert len(post.platforms) == 2
    assert PlatformType.FACEBOOK in post.platforms
    assert PlatformType.TWITTER in post.platforms


def test_update_content(composer, author_id):
    """Test updating post content for a platform."""
    post = composer.create_post(
        title="Test Post",
        platforms=[PlatformType.INSTAGRAM],
        author_id=author_id,
    )

    updated_post = composer.update_content(
        post_id=post.id,
        platform=PlatformType.INSTAGRAM,
        text="Updated content",
        hashtags=["#test", "#social"],
    )

    content = updated_post.content_by_platform[PlatformType.INSTAGRAM]
    assert content.text == "Updated content"
    assert len(content.hashtags) == 2


def test_add_media(composer, author_id):
    """Test adding media to a post."""
    post = composer.create_post(
        title="Test Post",
        platforms=[PlatformType.FACEBOOK],
        author_id=author_id,
    )

    media = Media(
        media_type=MediaType.IMAGE,
        url="https://example.com/image.jpg",
    )

    updated_post = composer.add_media(
        post_id=post.id,
        platform=PlatformType.FACEBOOK,
        media=media,
    )

    content = updated_post.content_by_platform[PlatformType.FACEBOOK]
    assert len(content.media) == 1


def test_validate_content_character_limit(composer, author_id):
    """Test content validation for character limits."""
    post = composer.create_post(
        title="Test Post",
        platforms=[PlatformType.TWITTER],
        author_id=author_id,
    )

    # Twitter has 280 character limit
    long_text = "a" * 300

    with pytest.raises(ValidationError):
        composer.update_content(
            post_id=post.id,
            platform=PlatformType.TWITTER,
            text=long_text,
        )


def test_optimize_hashtags(composer, author_id):
    """Test hashtag optimization."""
    post = composer.create_post(
        title="Test Post",
        platforms=[PlatformType.INSTAGRAM],
        author_id=author_id,
    )

    hashtags = ["marketing", "social", "business", "tech"] * 10  # 40 hashtags

    optimized = composer.optimize_hashtags(
        post_id=post.id,
        platform=PlatformType.INSTAGRAM,
        hashtags=hashtags,
    )

    # Instagram allows 30 hashtags
    assert len(optimized) <= 30
    # All should start with #
    assert all(tag.startswith("#") for tag in optimized)


def test_generate_preview(composer, author_id):
    """Test generating post preview."""
    post = composer.create_post(
        title="Test Post",
        platforms=[PlatformType.FACEBOOK],
        author_id=author_id,
        base_content="Test content",
    )

    composer.update_content(
        post_id=post.id,
        platform=PlatformType.FACEBOOK,
        text="Test content",
        hashtags=["#test"],
    )

    preview = composer.generate_preview(
        post_id=post.id,
        platform=PlatformType.FACEBOOK,
    )

    assert preview["platform"] == PlatformType.FACEBOOK.value
    assert preview["within_limit"] is True
    assert "#test" in preview["text"]


def test_duplicate_post(composer, author_id):
    """Test duplicating a post."""
    original = composer.create_post(
        title="Original Post",
        platforms=[PlatformType.FACEBOOK],
        author_id=author_id,
        base_content="Original content",
    )

    duplicate = composer.duplicate_post(
        post_id=original.id,
        new_title="Duplicate Post",
    )

    assert duplicate.id != original.id
    assert duplicate.title == "Duplicate Post"
    assert duplicate.content_by_platform.keys() == original.content_by_platform.keys()
