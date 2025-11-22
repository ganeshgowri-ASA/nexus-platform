"""
Form service for managing lead capture forms.
"""
from typing import List, Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modules.lead_generation.models import Form
from modules.lead_generation.schemas import FormCreate, FormUpdate


class FormService:
    """Service for managing forms."""

    @staticmethod
    async def create_form(db: AsyncSession, form_data: FormCreate) -> Form:
        """
        Create a new form.

        Args:
            db: Database session
            form_data: Form creation data

        Returns:
            Created form
        """
        try:
            form = Form(**form_data.model_dump())
            db.add(form)
            await db.commit()
            await db.refresh(form)
            logger.info(f"Form created: {form.id}")
            return form
        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating form: {e}")
            raise

    @staticmethod
    async def get_form(db: AsyncSession, form_id: UUID) -> Optional[Form]:
        """
        Get a form by ID.

        Args:
            db: Database session
            form_id: Form ID

        Returns:
            Form or None
        """
        try:
            result = await db.execute(
                select(Form).where(Form.id == form_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting form: {e}")
            raise

    @staticmethod
    async def list_forms(
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None
    ) -> List[Form]:
        """
        List forms with optional filtering.

        Args:
            db: Database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            is_active: Filter by active status

        Returns:
            List of forms
        """
        try:
            query = select(Form)

            if is_active is not None:
                query = query.where(Form.is_active == is_active)

            query = query.offset(skip).limit(limit).order_by(Form.created_at.desc())

            result = await db.execute(query)
            return list(result.scalars().all())
        except Exception as e:
            logger.error(f"Error listing forms: {e}")
            raise

    @staticmethod
    async def update_form(
        db: AsyncSession,
        form_id: UUID,
        form_data: FormUpdate
    ) -> Optional[Form]:
        """
        Update a form.

        Args:
            db: Database session
            form_id: Form ID
            form_data: Form update data

        Returns:
            Updated form or None
        """
        try:
            result = await db.execute(
                select(Form).where(Form.id == form_id)
            )
            form = result.scalar_one_or_none()

            if not form:
                return None

            update_data = form_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(form, field, value)

            await db.commit()
            await db.refresh(form)
            logger.info(f"Form updated: {form.id}")
            return form
        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating form: {e}")
            raise

    @staticmethod
    async def delete_form(db: AsyncSession, form_id: UUID) -> bool:
        """
        Delete a form.

        Args:
            db: Database session
            form_id: Form ID

        Returns:
            True if deleted, False if not found
        """
        try:
            result = await db.execute(
                select(Form).where(Form.id == form_id)
            )
            form = result.scalar_one_or_none()

            if not form:
                return False

            await db.delete(form)
            await db.commit()
            logger.info(f"Form deleted: {form_id}")
            return True
        except Exception as e:
            await db.rollback()
            logger.error(f"Error deleting form: {e}")
            raise

    @staticmethod
    async def increment_views(db: AsyncSession, form_id: UUID) -> None:
        """
        Increment form view count.

        Args:
            db: Database session
            form_id: Form ID
        """
        try:
            result = await db.execute(
                select(Form).where(Form.id == form_id)
            )
            form = result.scalar_one_or_none()

            if form:
                form.views += 1
                await db.commit()
        except Exception as e:
            logger.error(f"Error incrementing form views: {e}")

    @staticmethod
    async def increment_submissions(db: AsyncSession, form_id: UUID) -> None:
        """
        Increment form submission count and update conversion rate.

        Args:
            db: Database session
            form_id: Form ID
        """
        try:
            result = await db.execute(
                select(Form).where(Form.id == form_id)
            )
            form = result.scalar_one_or_none()

            if form:
                form.submissions += 1
                if form.views > 0:
                    form.conversion_rate = (form.submissions / form.views) * 100
                await db.commit()
        except Exception as e:
            logger.error(f"Error incrementing form submissions: {e}")
