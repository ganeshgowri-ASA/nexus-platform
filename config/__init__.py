"""Configuration package for Nexus Platform"""
from config.settings import settings
from config.celery_config import celery_app

__all__ = ['settings', 'celery_app']
