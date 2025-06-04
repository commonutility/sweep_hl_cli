#!/usr/bin/env python3
"""
Script to generate timing analysis reports from collected data.
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from latency_analyzer import LatencyAnalyzer

def main():
    parser = argparse.ArgumentParser(description="Generate timing analysis reports")
    parser.add_argument("--data-dir", default="analysis/data", help="Directory containing timing data")
    parser.add_argument("--output", default="analysis/report.json", help="Output file for report")
    parser.add_argument("--format", choices=["json", "text"], default="json", help="Output format")
    parser.add_argument("--request-id", help="Analyze specific request ID")
    
    args = parser.parse_args()
    
    analyzer = LatencyAnalyzer(args.data_dir)
    
    if args.request_id:
        # Analyze specific request
        analysis = analyzer.analyze_request(args.request_id)
        if "error" in analysis:
            print(f"Error: {analysis['error']}")
            return
        
        if args.format == "json":
            print(json.dumps(analysis, indent=2))
        else:
            print_request_analysis(analysis)
    else:
        # Generate full report
        report = analyzer.generate_report(args.output)
        if "error" in report:
            print(f"Error: {report['error']}")
            return
        
        print(f"Report generated: {args.output}")
        
        if args.format == "text":
            print_report_summary(report)

def print_request_analysis(analysis):
    """Print request analysis in human-readable format."""
    print(f"\n=== Request Analysis: {analysis['request_id']} ===")
    print(f"Total Duration: {analysis['total_duration_ms']:.2f}ms")
    
    print("\nStage Breakdown:")
    for stage, info in analysis['stages'].items():
        percentage = (info['duration_ms'] / analysis['total_duration_ms']) * 100
        print(f"  {stage}: {info['duration_ms']:.2f}ms ({percentage:.1f}%)")
    
    if analysis['bottlenecks']:
        print("\nBottlenecks (>30% of total time):")
        for bottleneck in analysis['bottlenecks']:
            print(f"  {bottleneck['stage']}: {bottleneck['duration_ms']:.2f}ms ({bottleneck['percentage']:.1f}%)")

def print_report_summary(report):
    """Print report summary in human-readable format."""
    print(f"\n=== Timing Analysis Report ===")
    print(f"Generated: {report['generated_at']}")
    print(f"Total Requests Analyzed: {report['total_requests_analyzed']}")
    
    overall = report['overall_statistics']
    print(f"\nOverall Statistics:")
    print(f"  Mean Total Duration: {overall['mean_total_duration_ms']:.2f}ms")
    print(f"  Median Total Duration: {overall['median_total_duration_ms']:.2f}ms")
    print(f"  Min Total Duration: {overall['min_total_duration_ms']:.2f}ms")
    print(f"  Max Total Duration: {overall['max_total_duration_ms']:.2f}ms")
    print(f"  P95 Total Duration: {overall['p95_total_duration_ms']:.2f}ms")
    print(f"  P99 Total Duration: {overall['p99_total_duration_ms']:.2f}ms")
    
    print(f"\nStage Breakdown (Average):")
    for stage, avg_duration in report['stage_breakdown']['stages'].items():
        print(f"  {stage}: {avg_duration:.2f}ms")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")

if __name__ == "__main__":
    main() 