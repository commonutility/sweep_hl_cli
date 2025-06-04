"""
Timing tracker for collecting latency data throughout the request lifecycle.
"""

import time
import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import threading

@dataclass
class TimingEvent:
    """Represents a single timing event in the request lifecycle."""
    request_id: str
    stage: str
    timestamp: float
    duration_ms: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    parent_stage: Optional[str] = None

class TimingTracker:
    """
    Singleton class for tracking timing events across the application.
    Thread-safe implementation to handle concurrent requests.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(TimingTracker, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.events: Dict[str, List[TimingEvent]] = {}
        self.active_stages: Dict[str, Dict[str, float]] = {}
        self.request_metadata: Dict[str, Dict[str, Any]] = {}
        self._event_lock = threading.Lock()
        self._initialized = True
        
        # Create analysis data directory
        self.data_dir = Path("analysis/data")
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def start_request(self, request_id: str = None, metadata: Dict[str, Any] = None) -> str:
        """Start tracking a new request."""
        if request_id is None:
            request_id = str(uuid.uuid4())
        
        with self._event_lock:
            self.events[request_id] = []
            self.active_stages[request_id] = {}
            self.request_metadata[request_id] = metadata or {}
            
        self.record_event(request_id, "request_start", metadata=metadata)
        return request_id
    
    def start_stage(self, request_id: str, stage: str, metadata: Dict[str, Any] = None):
        """Start timing a specific stage of the request."""
        with self._event_lock:
            if request_id not in self.active_stages:
                self.active_stages[request_id] = {}
            self.active_stages[request_id][stage] = time.time()
        
        self.record_event(request_id, f"{stage}_start", metadata=metadata)
    
    def end_stage(self, request_id: str, stage: str, metadata: Dict[str, Any] = None):
        """End timing a specific stage and calculate duration."""
        end_time = time.time()
        duration_ms = None
        
        with self._event_lock:
            if request_id in self.active_stages and stage in self.active_stages[request_id]:
                start_time = self.active_stages[request_id][stage]
                duration_ms = (end_time - start_time) * 1000
                del self.active_stages[request_id][stage]
        
        self.record_event(
            request_id, 
            f"{stage}_end", 
            duration_ms=duration_ms,
            metadata=metadata
        )
    
    def record_event(self, request_id: str, stage: str, duration_ms: Optional[float] = None, 
                    metadata: Optional[Dict[str, Any]] = None, parent_stage: Optional[str] = None):
        """Record a timing event."""
        event = TimingEvent(
            request_id=request_id,
            stage=stage,
            timestamp=time.time(),
            duration_ms=duration_ms,
            metadata=metadata,
            parent_stage=parent_stage
        )
        
        with self._event_lock:
            if request_id not in self.events:
                self.events[request_id] = []
            self.events[request_id].append(event)
        
        # Log the event for debugging
        print(f"[Timing] {stage} - Request: {request_id[:8]}... - Duration: {duration_ms:.2f}ms" if duration_ms else f"[Timing] {stage} - Request: {request_id[:8]}...")
    
    def end_request(self, request_id: str, metadata: Dict[str, Any] = None):
        """End tracking a request and save the data."""
        self.record_event(request_id, "request_end", metadata=metadata)
        
        # Calculate total request duration
        with self._event_lock:
            if request_id in self.events:
                events = self.events[request_id]
                if len(events) >= 2:
                    total_duration = (events[-1].timestamp - events[0].timestamp) * 1000
                    self.record_event(request_id, "total_duration", duration_ms=total_duration)
        
        # Save to file
        self.save_request_data(request_id)
    
    def get_request_events(self, request_id: str) -> List[TimingEvent]:
        """Get all events for a specific request."""
        with self._event_lock:
            return self.events.get(request_id, []).copy()
    
    def get_request_summary(self, request_id: str) -> Dict[str, Any]:
        """Get a summary of timing data for a request."""
        events = self.get_request_events(request_id)
        if not events:
            return {}
        
        summary = {
            "request_id": request_id,
            "start_time": events[0].timestamp,
            "end_time": events[-1].timestamp if len(events) > 1 else None,
            "total_duration_ms": None,
            "stages": {},
            "metadata": self.request_metadata.get(request_id, {})
        }
        
        # Calculate total duration
        if summary["end_time"]:
            summary["total_duration_ms"] = (summary["end_time"] - summary["start_time"]) * 1000
        
        # Extract stage durations
        for event in events:
            if event.stage.endswith("_end") and event.duration_ms is not None:
                stage_name = event.stage[:-4]  # Remove "_end"
                summary["stages"][stage_name] = {
                    "duration_ms": event.duration_ms,
                    "metadata": event.metadata
                }
        
        return summary
    
    def save_request_data(self, request_id: str):
        """Save request timing data to a JSON file."""
        summary = self.get_request_summary(request_id)
        events = self.get_request_events(request_id)
        
        data = {
            "summary": summary,
            "events": [asdict(event) for event in events],
            "saved_at": datetime.now().isoformat()
        }
        
        filename = self.data_dir / f"timing_{request_id}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"[Timing] Saved timing data to {filename}")
    
    def clear_request(self, request_id: str):
        """Clear data for a specific request."""
        with self._event_lock:
            self.events.pop(request_id, None)
            self.active_stages.pop(request_id, None)
            self.request_metadata.pop(request_id, None)
    
    def get_all_requests(self) -> List[str]:
        """Get all tracked request IDs."""
        with self._event_lock:
            return list(self.events.keys())

# Global instance
timing_tracker = TimingTracker() 