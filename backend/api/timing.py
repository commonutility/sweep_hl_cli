"""
API endpoints for timing analysis.
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Optional
import sys
import os

# Add parent directories to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from analysis.timing_tracker import timing_tracker
from analysis.latency_analyzer import LatencyAnalyzer

router = APIRouter()

# Initialize analyzer
analyzer = LatencyAnalyzer()

@router.get("/timing/requests")
async def get_all_timing_requests():
    """Get a list of all tracked request IDs."""
    return {
        "requests": timing_tracker.get_all_requests(),
        "count": len(timing_tracker.get_all_requests())
    }

@router.get("/timing/request/{request_id}")
async def get_request_timing(request_id: str):
    """Get timing data for a specific request."""
    summary = timing_tracker.get_request_summary(request_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Also get detailed analysis
    analysis = analyzer.analyze_request(request_id)
    
    return {
        "summary": summary,
        "analysis": analysis
    }

@router.get("/timing/stage/{stage_name}/stats")
async def get_stage_statistics(stage_name: str):
    """Get statistics for a specific stage across all requests."""
    stats = analyzer.analyze_stage_statistics(stage_name)
    if "error" in stats:
        raise HTTPException(status_code=404, detail=stats["error"])
    return stats

@router.get("/timing/report")
async def generate_timing_report():
    """Generate a comprehensive timing report."""
    report = analyzer.generate_report()
    if "error" in report:
        raise HTTPException(status_code=404, detail=report["error"])
    return report

@router.get("/timing/breakdown")
async def get_stage_breakdown():
    """Get average breakdown of all stages across all requests."""
    return analyzer.get_stage_breakdown_summary()

@router.get("/timing/visualization/{request_id}")
async def get_visualization_data(request_id: str):
    """Get timing data formatted for visualization."""
    data = analyzer.create_visualization_data(request_id)
    if "error" in data:
        raise HTTPException(status_code=404, detail=data["error"])
    return data

@router.delete("/timing/request/{request_id}")
async def clear_request_timing(request_id: str):
    """Clear timing data for a specific request."""
    timing_tracker.clear_request(request_id)
    return {"message": f"Cleared timing data for request {request_id}"}

@router.get("/timing/live/{request_id}")
async def get_live_timing(request_id: str):
    """Get live timing data for an ongoing request."""
    events = timing_tracker.get_request_events(request_id)
    if not events:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Calculate current state
    active_stages = {}
    completed_stages = {}
    
    for event in events:
        if event.stage.endswith("_start"):
            stage_name = event.stage[:-6]
            active_stages[stage_name] = event.timestamp
        elif event.stage.endswith("_end"):
            stage_name = event.stage[:-4]
            if stage_name in active_stages:
                del active_stages[stage_name]
            completed_stages[stage_name] = event.duration_ms
    
    return {
        "request_id": request_id,
        "active_stages": list(active_stages.keys()),
        "completed_stages": completed_stages,
        "total_events": len(events)
    } 