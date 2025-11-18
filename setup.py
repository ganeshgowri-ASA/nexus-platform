"""Setup configuration for NEXUS Platform."""
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

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
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.10",
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
)
