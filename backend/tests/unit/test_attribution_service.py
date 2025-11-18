"""
Unit tests for Attribution Service
"""
import pytest
from sqlalchemy.orm import Session

from backend.app.services.attribution_service import AttributionService, AttributionCalculator
from backend.app.models.attribution import (
    Channel,
    Journey,
    Touchpoint,
    Conversion,
    AttributionModel,
)
from backend.app.core.exceptions import NotFoundException, AttributionException


class TestAttributionCalculator:
    """Test attribution calculation algorithms."""

    def test_first_touch_attribution(self, db_session: Session, complete_test_journey: Journey):
        """Test first-touch attribution calculation."""
        calculator = AttributionCalculator(db_session)

        # Get touchpoints
        touchpoints = (
            db_session.query(Touchpoint)
            .filter(Touchpoint.journey_id == complete_test_journey.id)
            .all()
        )

        # Calculate first-touch attribution
        result = calculator.calculate_first_touch(touchpoints, 150.0)

        # First touchpoint should get 100% credit
        assert len(result) == 1
        assert 150.0 in result.values()

    def test_last_touch_attribution(self, db_session: Session, complete_test_journey: Journey):
        """Test last-touch attribution calculation."""
        calculator = AttributionCalculator(db_session)

        touchpoints = (
            db_session.query(Touchpoint)
            .filter(Touchpoint.journey_id == complete_test_journey.id)
            .all()
        )

        result = calculator.calculate_last_touch(touchpoints, 150.0)

        # Last touchpoint should get 100% credit
        assert len(result) == 1
        assert 150.0 in result.values()

    def test_linear_attribution(self, db_session: Session, complete_test_journey: Journey):
        """Test linear attribution calculation."""
        calculator = AttributionCalculator(db_session)

        touchpoints = (
            db_session.query(Touchpoint)
            .filter(Touchpoint.journey_id == complete_test_journey.id)
            .all()
        )

        result = calculator.calculate_linear(touchpoints, 150.0)

        # Each touchpoint should get equal credit
        assert len(result) == 1  # All touchpoints same channel
        assert result[touchpoints[0].channel_id] == 150.0

    def test_time_decay_attribution(self, db_session: Session, complete_test_journey: Journey):
        """Test time-decay attribution calculation."""
        calculator = AttributionCalculator(db_session)

        touchpoints = (
            db_session.query(Touchpoint)
            .filter(Touchpoint.journey_id == complete_test_journey.id)
            .all()
        )

        result = calculator.calculate_time_decay(touchpoints, 150.0, halflife_days=7.0)

        # Should return attribution for channel
        assert len(result) > 0
        # Total credit should equal conversion value
        assert abs(sum(result.values()) - 150.0) < 0.01

    def test_position_based_attribution(
        self, db_session: Session, complete_test_journey: Journey
    ):
        """Test position-based attribution calculation."""
        calculator = AttributionCalculator(db_session)

        touchpoints = (
            db_session.query(Touchpoint)
            .filter(Touchpoint.journey_id == complete_test_journey.id)
            .all()
        )

        result = calculator.calculate_position_based(touchpoints, 150.0)

        # Should return attribution for channel
        assert len(result) > 0
        # Total credit should equal conversion value
        assert abs(sum(result.values()) - 150.0) < 0.01


class TestAttributionService:
    """Test attribution service functionality."""

    def test_create_journey(self, db_session: Session):
        """Test journey creation."""
        service = AttributionService(db_session)

        journey = service.create_journey(
            user_id="test_user",
            session_id="test_session",
        )

        assert journey.id is not None
        assert journey.user_id == "test_user"
        assert journey.session_id == "test_session"
        assert journey.total_touchpoints == 0
        assert journey.has_conversion is False

    def test_get_journey(self, db_session: Session, test_journey: Journey):
        """Test getting journey by ID."""
        service = AttributionService(db_session)

        journey = service.get_journey(test_journey.id)

        assert journey.id == test_journey.id
        assert journey.user_id == test_journey.user_id

    def test_get_nonexistent_journey(self, db_session: Session):
        """Test getting non-existent journey raises exception."""
        service = AttributionService(db_session)

        with pytest.raises(NotFoundException):
            service.get_journey(99999)

    def test_add_touchpoint(
        self, db_session: Session, test_journey: Journey, test_channel: Channel
    ):
        """Test adding touchpoint to journey."""
        service = AttributionService(db_session)

        touchpoint = service.add_touchpoint(
            journey_id=test_journey.id,
            channel_id=test_channel.id,
            touchpoint_type="click",
        )

        assert touchpoint.id is not None
        assert touchpoint.journey_id == test_journey.id
        assert touchpoint.channel_id == test_channel.id
        assert touchpoint.position_in_journey == 1

        # Check journey was updated
        db_session.refresh(test_journey)
        assert test_journey.total_touchpoints == 1

    def test_add_conversion(self, db_session: Session, test_journey: Journey):
        """Test adding conversion to journey."""
        service = AttributionService(db_session)

        conversion = service.add_conversion(
            journey_id=test_journey.id,
            conversion_type="purchase",
            revenue=100.0,
        )

        assert conversion.id is not None
        assert conversion.journey_id == test_journey.id
        assert conversion.revenue == 100.0

        # Check journey was updated
        db_session.refresh(test_journey)
        assert test_journey.has_conversion is True
        assert test_journey.conversion_value == 100.0

    def test_calculate_attribution(
        self,
        db_session: Session,
        complete_test_journey: Journey,
        test_attribution_model: AttributionModel,
    ):
        """Test attribution calculation."""
        service = AttributionService(db_session)

        results = service.calculate_attribution(
            complete_test_journey.id,
            test_attribution_model.id,
        )

        assert len(results) > 0
        for result in results:
            assert result.journey_id == complete_test_journey.id
            assert result.attribution_model_id == test_attribution_model.id
            assert result.attributed_revenue > 0
            assert result.credit >= 0 and result.credit <= 1

    def test_calculate_attribution_without_conversion(
        self, db_session: Session, test_journey: Journey, test_attribution_model: AttributionModel
    ):
        """Test attribution calculation fails without conversion."""
        service = AttributionService(db_session)

        with pytest.raises(AttributionException):
            service.calculate_attribution(
                test_journey.id,
                test_attribution_model.id,
            )

    def test_create_channel(self, db_session: Session):
        """Test channel creation."""
        service = AttributionService(db_session)

        channel = service.create_channel(
            name="New Channel",
            channel_type="paid_search",
            cost_per_click=2.0,
        )

        assert channel.id is not None
        assert channel.name == "New Channel"
        assert channel.cost_per_click == 2.0

    def test_list_channels(self, db_session: Session, test_channel: Channel):
        """Test listing channels."""
        service = AttributionService(db_session)

        channels = service.list_channels(active_only=True)

        assert len(channels) > 0
        assert any(ch.id == test_channel.id for ch in channels)

    def test_create_attribution_model(self, db_session: Session):
        """Test attribution model creation."""
        service = AttributionService(db_session)

        model = service.create_attribution_model(
            name="Test Model",
            model_type="first_touch",
        )

        assert model.id is not None
        assert model.name == "Test Model"
        assert model.model_type.value == "first_touch"

    def test_list_attribution_models(
        self, db_session: Session, test_attribution_model: AttributionModel
    ):
        """Test listing attribution models."""
        service = AttributionService(db_session)

        models = service.list_attribution_models(active_only=True)

        assert len(models) > 0
        assert any(m.id == test_attribution_model.id for m in models)
