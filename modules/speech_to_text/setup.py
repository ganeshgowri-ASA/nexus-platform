"""Setup script for NEXUS Speech-to-Text module."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="nexus-speech-to-text",
    version="1.0.0",
    author="NEXUS Platform",
    author_email="contact@nexus-platform.ai",
    description="Comprehensive speech-to-text module with multiple provider support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/nexus-platform/speech-to-text",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Multimedia :: Sound/Audio :: Speech",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.4.4",
            "pytest-asyncio>=0.23.3",
            "black>=24.1.1",
            "flake8>=7.0.0",
            "mypy>=1.8.0",
        ],
        "gpu": [
            "torch==2.1.2+cu118",
            "torchaudio==2.1.2+cu118",
        ],
    },
    entry_points={
        "console_scripts": [
            "nexus-speech-api=api.app:main",
            "nexus-speech-ui=ui.app:main",
        ],
    },
)
