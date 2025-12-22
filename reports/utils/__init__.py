"""
Utils module for report generation
Contains reusable components for graph generation, trend analysis, action recommendations, and report generators
"""
from .graph_utils import generate_trend_graph, analyze_trend, parse_recommended_range
from .action_utils import get_suggested_action_with_status
from .report_generators import (
    generate_daily_report_pdf,
    generate_monthly_report_pdf,
    generate_yearly_report_pdf
)
from .report_queries import (
    get_report_analyses_raw,
    get_water_system_raw,
    check_water_system_access_raw
)

__all__ = [
    'generate_trend_graph', 
    'analyze_trend', 
    'parse_recommended_range',
    'get_suggested_action_with_status',
    'generate_daily_report_pdf',
    'generate_monthly_report_pdf',
    'generate_yearly_report_pdf'
]

