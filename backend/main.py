from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.api.chat import router as chat_router
from backend.api.assets import router as assets_router
from backend.api.timing import router as timing_router
from src.hyperliquid_wrapper.database_handlers.database_manager import DBManager
from analysis.timing_middleware import TimingMiddleware

# Initialize FastAPI app
app = FastAPI(title="Hyperliquid Trading Backend")

# Add timing middleware (before CORS to track full request time)
app.add_middleware(TimingMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5170",
        "http://localhost:5173",
        "http://localhost:5174", 
        "http://localhost:5175",
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Processing-Time-MS"],  # Expose timing headers
)

# Initialize database
db_manager = DBManager()
print("[Backend] Database initialized successfully.")

# Include routers
app.include_router(chat_router, prefix="/api")
app.include_router(assets_router, prefix="/api")
app.include_router(timing_router, prefix="/api")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "Hyperliquid Trading Assistant API is running"}

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 