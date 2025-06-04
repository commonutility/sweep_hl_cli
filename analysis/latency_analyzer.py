"""
Latency analyzer for processing and visualizing timing data.
"""

import json
import statistics
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import pandas as pd

class LatencyAnalyzer:
    """Analyzes timing data collected by TimingTracker."""
    
    def __init__(self, data_dir: str = "analysis/data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
    
    def load_request_data(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Load timing data for a specific request."""
        filename = self.data_dir / f"timing_{request_id}.json"
        if filename.exists():
            with open(filename, 'r') as f:
                return json.load(f)
        return None
    
    def load_all_requests(self) -> List[Dict[str, Any]]:
        """Load all available timing data."""
        data = []
        for file in self.data_dir.glob("timing_*.json"):
            with open(file, 'r') as f:
                data.append(json.load(f))
        return data
    
    def analyze_request(self, request_id: str) -> Dict[str, Any]:
        """Analyze timing data for a single request."""
        data = self.load_request_data(request_id)
        if not data:
            return {"error": "Request data not found"}
        
        summary = data.get("summary", {})
        events = data.get("events", [])
        
        # Create timeline
        timeline = []
        for event in events:
            timeline.append({
                "stage": event["stage"],
                "timestamp": event["timestamp"],
                "relative_ms": (event["timestamp"] - events[0]["timestamp"]) * 1000,
                "duration_ms": event.get("duration_ms")
            })
        
        # Identify bottlenecks (stages taking > 30% of total time)
        total_duration = summary.get("total_duration_ms", 0)
        bottlenecks = []
        if total_duration > 0:
            for stage, info in summary.get("stages", {}).items():
                duration = info["duration_ms"]
                percentage = (duration / total_duration) * 100
                if percentage > 30:
                    bottlenecks.append({
                        "stage": stage,
                        "duration_ms": duration,
                        "percentage": percentage
                    })
        
        return {
            "request_id": request_id,
            "total_duration_ms": total_duration,
            "stages": summary.get("stages", {}),
            "timeline": timeline,
            "bottlenecks": sorted(bottlenecks, key=lambda x: x["duration_ms"], reverse=True)
        }
    
    def analyze_stage_statistics(self, stage_name: str) -> Dict[str, Any]:
        """Analyze statistics for a specific stage across all requests."""
        all_data = self.load_all_requests()
        durations = []
        
        for data in all_data:
            stages = data.get("summary", {}).get("stages", {})
            if stage_name in stages:
                durations.append(stages[stage_name]["duration_ms"])
        
        if not durations:
            return {"error": f"No data found for stage: {stage_name}"}
        
        return {
            "stage": stage_name,
            "count": len(durations),
            "mean_ms": statistics.mean(durations),
            "median_ms": statistics.median(durations),
            "min_ms": min(durations),
            "max_ms": max(durations),
            "std_dev_ms": statistics.stdev(durations) if len(durations) > 1 else 0,
            "p95_ms": sorted(durations)[int(len(durations) * 0.95)] if durations else 0,
            "p99_ms": sorted(durations)[int(len(durations) * 0.99)] if durations else 0
        }
    
    def get_stage_breakdown_summary(self) -> Dict[str, Any]:
        """Get average breakdown of all stages across all requests."""
        all_data = self.load_all_requests()
        stage_totals = {}
        stage_counts = {}
        
        for data in all_data:
            stages = data.get("summary", {}).get("stages", {})
            for stage, info in stages.items():
                if stage not in stage_totals:
                    stage_totals[stage] = 0
                    stage_counts[stage] = 0
                stage_totals[stage] += info["duration_ms"]
                stage_counts[stage] += 1
        
        # Calculate averages
        stage_averages = {}
        for stage in stage_totals:
            stage_averages[stage] = stage_totals[stage] / stage_counts[stage]
        
        # Sort by average duration
        sorted_stages = sorted(stage_averages.items(), key=lambda x: x[1], reverse=True)
        
        return {
            "stages": dict(sorted_stages),
            "total_requests": len(all_data),
            "timestamp": datetime.now().isoformat()
        }
    
    def generate_report(self, output_file: str = "analysis/latency_report.json"):
        """Generate a comprehensive latency report."""
        all_data = self.load_all_requests()
        
        if not all_data:
            return {"error": "No timing data available"}
        
        # Overall statistics
        total_durations = [d["summary"]["total_duration_ms"] for d in all_data if "summary" in d and "total_duration_ms" in d["summary"]]
        
        # Stage breakdown
        stage_breakdown = self.get_stage_breakdown_summary()
        
        # Collect all stage names
        all_stages = set()
        for data in all_data:
            all_stages.update(data.get("summary", {}).get("stages", {}).keys())
        
        # Stage statistics
        stage_stats = {}
        for stage in all_stages:
            stage_stats[stage] = self.analyze_stage_statistics(stage)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "total_requests_analyzed": len(all_data),
            "overall_statistics": {
                "mean_total_duration_ms": statistics.mean(total_durations) if total_durations else 0,
                "median_total_duration_ms": statistics.median(total_durations) if total_durations else 0,
                "min_total_duration_ms": min(total_durations) if total_durations else 0,
                "max_total_duration_ms": max(total_durations) if total_durations else 0,
                "p95_total_duration_ms": sorted(total_durations)[int(len(total_durations) * 0.95)] if total_durations else 0,
                "p99_total_duration_ms": sorted(total_durations)[int(len(total_durations) * 0.99)] if total_durations else 0
            },
            "stage_breakdown": stage_breakdown,
            "stage_statistics": stage_stats,
            "recommendations": self._generate_recommendations(stage_stats, stage_breakdown)
        }
        
        # Save report
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        return report
    
    def _generate_recommendations(self, stage_stats: Dict, stage_breakdown: Dict) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Find slowest stages
        avg_durations = [(stage, stats["mean_ms"]) for stage, stats in stage_stats.items() if "mean_ms" in stats]
        avg_durations.sort(key=lambda x: x[1], reverse=True)
        
        if avg_durations:
            slowest_stage = avg_durations[0]
            recommendations.append(f"Focus optimization on '{slowest_stage[0]}' stage - average {slowest_stage[1]:.2f}ms")
        
        # Check for high variance stages
        for stage, stats in stage_stats.items():
            if "std_dev_ms" in stats and "mean_ms" in stats and stats["mean_ms"] > 0:
                cv = stats["std_dev_ms"] / stats["mean_ms"]  # Coefficient of variation
                if cv > 0.5:
                    recommendations.append(f"Stage '{stage}' has high variance (CV={cv:.2f}) - investigate inconsistencies")
        
        # Check for stages with large p99 vs median differences
        for stage, stats in stage_stats.items():
            if "p99_ms" in stats and "median_ms" in stats and stats["median_ms"] > 0:
                ratio = stats["p99_ms"] / stats["median_ms"]
                if ratio > 3:
                    recommendations.append(f"Stage '{stage}' has p99 {ratio:.1f}x higher than median - investigate outliers")
        
        return recommendations
    
    def create_visualization_data(self, request_id: str) -> Dict[str, Any]:
        """Create data suitable for visualization (e.g., Gantt chart)."""
        data = self.load_request_data(request_id)
        if not data:
            return {"error": "Request data not found"}
        
        events = data.get("events", [])
        if not events:
            return {"error": "No events found"}
        
        # Create Gantt chart data
        gantt_data = []
        start_time = events[0]["timestamp"]
        
        # Track active stages
        active_stages = {}
        
        for event in events:
            if event["stage"].endswith("_start"):
                stage_name = event["stage"][:-6]
                active_stages[stage_name] = event["timestamp"]
            elif event["stage"].endswith("_end"):
                stage_name = event["stage"][:-4]
                if stage_name in active_stages:
                    gantt_data.append({
                        "stage": stage_name,
                        "start_ms": (active_stages[stage_name] - start_time) * 1000,
                        "end_ms": (event["timestamp"] - start_time) * 1000,
                        "duration_ms": event.get("duration_ms", 0)
                    })
                    del active_stages[stage_name]
        
        return {
            "request_id": request_id,
            "total_duration_ms": data["summary"].get("total_duration_ms", 0),
            "gantt_data": sorted(gantt_data, key=lambda x: x["start_ms"])
        } 