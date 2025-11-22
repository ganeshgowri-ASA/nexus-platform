"""Tests for entity extractor."""

import pytest
from modules.voice.nlp.entity_extractor import EntityExtractor


def test_extract_emails():
    """Test email extraction."""
    extractor = EntityExtractor()

    text = "Send an email to john@example.com and jane@test.org"
    emails = extractor.extract_emails(text)

    assert len(emails) == 2
    assert "john@example.com" in emails
    assert "jane@test.org" in emails


def test_extract_numbers():
    """Test number extraction."""
    extractor = EntityExtractor()

    text = "I need 5 items and 3.14 units"
    numbers = extractor.extract_numbers(text)

    assert len(numbers) >= 2
    values = [n['value'] for n in numbers]
    assert 5 in values
    assert 3.14 in values


def test_extract_phone_numbers():
    """Test phone number extraction."""
    extractor = EntityExtractor()

    text = "Call me at 555-123-4567 or (555) 987-6543"
    phones = extractor.extract_phone_numbers(text)

    assert len(phones) == 2


def test_extract_urls():
    """Test URL extraction."""
    extractor = EntityExtractor()

    text = "Visit https://example.com and http://test.org"
    urls = extractor.extract_urls(text)

    assert len(urls) == 2
    assert "https://example.com" in urls


def test_extract_dates():
    """Test date extraction."""
    extractor = EntityExtractor()

    text = "Schedule for tomorrow and next week"
    dates = extractor.extract_dates(text)

    assert len(dates) >= 1


def test_extract_times():
    """Test time extraction."""
    extractor = EntityExtractor()

    text = "Meeting at 2pm and 14:30"
    times = extractor.extract_times(text)

    assert len(times) >= 1


def test_extract_durations():
    """Test duration extraction."""
    extractor = EntityExtractor()

    text = "Wait for 5 minutes and 2 hours"
    durations = extractor.extract_durations(text)

    assert len(durations) == 2
    units = [d['unit'] for d in durations]
    assert 'minute' in units
    assert 'hour' in units


def test_extract_entities():
    """Test combined entity extraction."""
    extractor = EntityExtractor()

    text = "Send email to john@example.com at 2pm tomorrow"
    entities = extractor.extract_entities(text)

    assert 'emails' in entities
    assert 'times' in entities
    assert 'dates' in entities
