from setuptools import setup, find_packages

setup(
    name="nexus-api-gateway",
    version="1.0.0",
    description="NEXUS API Gateway - Request routing, rate limiting, authentication, load balancing, caching, monitoring",
    author="NEXUS Platform",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "sqlalchemy>=2.0.25",
        "psycopg2-binary>=2.9.9",
        "redis>=5.0.1",
        "pyjwt>=2.8.0",
        "httpx>=0.26.0",
        "pydantic>=2.5.3",
        "pydantic-settings>=2.1.0",
        "streamlit>=1.30.0",
        "pandas>=2.1.4",
    ],
    python_requires=">=3.11",
    entry_points={
        "console_scripts": [
            "nexus-gateway=modules.api_gateway.app.main:start",
        ],
    },
)
