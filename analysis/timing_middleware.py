"""
FastAPI middleware for automatic timing tracking.
"""

import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from .timing_tracker import timing_tracker

class TimingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track request timing in FastAPI.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Skip timing for certain endpoints
        skip_endpoints = ["/docs", "/redoc", "/openapi.json", "/favicon.ico"]
        if request.url.path in skip_endpoints:
            return await call_next(request)
        
        # Start timing the request
        timing_tracker.start_request(request_id, {
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params)
        })
        
        # Track backend processing
        timing_tracker.start_stage(request_id, "backend_processing")
        
        # Store request ID in state for use in endpoints
        request.state.request_id = request_id
        
        start_time = time.time()
        
        try:
            # Process the request
            response = await call_next(request)
            
            # Calculate processing time
            processing_time = (time.time() - start_time) * 1000
            
            # End backend processing
            timing_tracker.end_stage(request_id, "backend_processing", {
                "status_code": response.status_code
            })
            
            # Add timing headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Processing-Time-MS"] = str(int(processing_time))
            
            # End the request tracking
            timing_tracker.end_request(request_id, {
                "status_code": response.status_code,
                "processing_time_ms": processing_time
            })
            
            return response
            
        except Exception as e:
            # Track error
            timing_tracker.end_stage(request_id, "backend_processing", {
                "error": str(e)
            })
            timing_tracker.end_request(request_id, {
                "error": str(e)
            })
            raise

def get_request_id(request: Request) -> str:
    """Helper function to get request ID from request state."""
    return getattr(request.state, "request_id", str(uuid.uuid4())) 