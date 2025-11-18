"""
CORS middleware configuration
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List


def setup_cors(
    app: FastAPI,
    allowed_origins: List[str] = None,
    allow_credentials: bool = True,
    allowed_methods: List[str] = None,
    allowed_headers: List[str] = None,
) -> None:
    """
    Configure CORS middleware for the FastAPI application

    Args:
        app: FastAPI application instance
        allowed_origins: List of allowed origins (default: ["*"])
        allow_credentials: Allow credentials in requests
        allowed_methods: List of allowed HTTP methods (default: ["*"])
        allowed_headers: List of allowed headers (default: ["*"])
    """
    if allowed_origins is None:
        allowed_origins = [
            "http://localhost:3000",  # React dev server
            "http://localhost:8000",  # FastAPI dev server
            "http://localhost:5173",  # Vite dev server
            "https://nexus-platform.com",  # Production domain
        ]

    if allowed_methods is None:
        allowed_methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]

    if allowed_headers is None:
        allowed_headers = [
            "Content-Type",
            "Authorization",
            "Accept",
            "Origin",
            "X-Requested-With",
        ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=allow_credentials,
        allow_methods=allowed_methods,
        allow_headers=allowed_headers,
        expose_headers=["Content-Range", "X-Content-Range"],
    )
