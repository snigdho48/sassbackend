from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.decorators import api_view, permission_classes
from .utils.dashboard_queries import (
    get_dashboard_kpis,
    get_system_hierarchy,
    get_performance_trends,
    get_parameter_trends
)


class DashboardDataView(APIView):
    """
    API endpoint for dashboard data with real-time performance trends.
    Uses raw SQL for fast data retrieval.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        try:
            # Get KPIs
            kpis = get_dashboard_kpis(user)
            
            # Get system hierarchy
            hierarchy = get_system_hierarchy(user)
            
            # Get performance trends for cooling tower and boiler
            cooling_trends = get_performance_trends(user, 'cooling', months=6)
            boiler_trends = get_performance_trends(user, 'boiler', months=6)
            
            # Get parameter trends for cooling tower
            cooling_params = {
                'ph': get_parameter_trends(user, 'cooling', 'ph', months=6),
                'tds': get_parameter_trends(user, 'cooling', 'tds', months=6),
                'hardness': get_parameter_trends(user, 'cooling', 'hardness', months=6),
                'm_alkalinity': get_parameter_trends(user, 'cooling', 'm_alkalinity', months=6),
                'lsi': get_parameter_trends(user, 'cooling', 'lsi', months=6),
                'rsi': get_parameter_trends(user, 'cooling', 'rsi', months=6),
            }
            
            # Get parameter trends for boiler
            boiler_params = {
                'ph': get_parameter_trends(user, 'boiler', 'ph', months=6),
                'tds': get_parameter_trends(user, 'boiler', 'tds', months=6),
                'hardness': get_parameter_trends(user, 'boiler', 'hardness', months=6),
                'm_alkalinity': get_parameter_trends(user, 'boiler', 'm_alkalinity', months=6),
                'p_alkalinity': get_parameter_trends(user, 'boiler', 'p_alkalinity', months=6),
                'oh_alkalinity': get_parameter_trends(user, 'boiler', 'oh_alkalinity', months=6),
            }
            
            return Response({
                'kpis': kpis,
                'hierarchy': hierarchy,
                'performance_trends': {
                    'cooling_tower': cooling_trends,
                    'boiler': boiler_trends
                },
                'parameter_trends': {
                    'cooling_tower': cooling_params,
                    'boiler': boiler_params
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ParameterTrendView(APIView):
    """
    API endpoint for getting trend data for a specific parameter.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        system_type = request.query_params.get('system_type')  # 'cooling' or 'boiler'
        parameter_name = request.query_params.get('parameter_name')
        months = int(request.query_params.get('months', 6))
        
        if not system_type or not parameter_name:
            return Response({
                'error': 'system_type and parameter_name are required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            trends = get_parameter_trends(user, system_type, parameter_name, months)
            return Response({
                'trends': trends,
                'system_type': system_type,
                'parameter_name': parameter_name
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
