<<<<<<< HEAD
<<<<<<< HEAD
"""Setup script for Nexus Search."""

from setuptools import setup, find_packages
=======
"""
NEXUS Knowledge Base Setup Script
"""

from setuptools import find_packages, setup
>>>>>>> origin/claude/knowledge-base-system-01HD8qcvb4Kv97GrLFgPph4a
=======
"""Setup configuration for NEXUS Platform."""
from setuptools import setup, find_packages
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

<<<<<<< HEAD
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
<<<<<<< HEAD
    name="nexus-search",
    version="1.0.0",
    author="Nexus Platform",
    description="Production-ready Elasticsearch search engine for Nexus Platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(exclude=["tests*", "examples*"]),
    python_requires=">=3.8",
    install_requires=requirements,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="elasticsearch search indexing nexus",
    project_urls={
        "Source": "https://github.com/nexus/nexus-platform",
=======
    name="nexus-knowledge-base",
    version="1.0.0",
    author="NEXUS Platform Team",
    author_email="dev@nexus.com",
    description="Comprehensive AI-powered knowledge base system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/nexus-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
=======
setup(
    name="nexus-platform",
    version="0.1.0",
    author="NEXUS Team",
    author_email="info@nexus-platform.io",
    description="Unified AI-powered productivity platform with 24 integrated modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/ganeshgowri-ASA/nexus-platform",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
<<<<<<< HEAD
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
            "black>=24.0.0",
            "ruff>=0.2.0",
            "mypy>=1.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "nexus-kb=modules.knowledge_base.cli:main",
        ],
>>>>>>> origin/claude/knowledge-base-system-01HD8qcvb4Kv97GrLFgPph4a
    },
=======
    install_requires=[
        "streamlit>=1.31.0",
        "fastapi>=0.109.0",
        "uvicorn>=0.27.0",
        "anthropic>=0.18.0",
        "sqlalchemy>=2.0.25",
        "psycopg2-binary>=2.9.9",
        "alembic>=1.13.1",
        "pydantic>=2.6.1",
        "celery>=5.3.6",
        "redis>=5.0.1",
    ],
    extras_require={
        "dev": [
            "pytest>=8.0.0",
            "black>=24.1.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
    },
>>>>>>> origin/claude/marketing-automation-module-01QZjZLNDEejmtRGTMvcovNS
)
