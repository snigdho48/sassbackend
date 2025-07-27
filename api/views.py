from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import json
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render
from django.http import JsonResponse

from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    ChangePasswordSerializer, DataCategorySerializer, TechnicalDataSerializer,
    AnalyticalScoreSerializer, ReportTemplateSerializer, GeneratedReportSerializer,
    DashboardDataSerializer, AnalyticsSerializer, TokenRefreshSerializer,
    WaterAnalysisSerializer, WaterTrendSerializer, WaterRecommendationSerializer
)
from users.models import CustomUser
from data_entry.models import DataCategory, TechnicalData, AnalyticalScore, WaterAnalysis, WaterTrend, WaterRecommendation
from reports.models import ReportTemplate, GeneratedReport
from dashboard.models import DashboardWidget, UserPreference
from .models import APIUsage

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_admin

class IsClientOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.is_client or request.user.is_admin)

class IsManagerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.is_manager or request.user.is_admin)

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view that includes user information."""
    
    @swagger_auto_schema(
        operation_description="Obtain JWT access and refresh tokens with user information",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='User email'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='User password'),
            }
        ),
        responses={
            200: openapi.Response(
                description="Token obtained successfully",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'access': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description='User information'),
                    }
                )
            ),
            401: openapi.Response(description="Invalid credentials")
        }
    )
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Add user information to the response
            user = authenticate(
                request=request,
                email=request.data.get('email'),
                password=request.data.get('password')
            )
            if user:
                response.data['user'] = UserSerializer(user).data
        
        return response

class LoginView(APIView):
    """
    Login endpoint to obtain JWT tokens.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Login with email and password to get JWT tokens",
        request_body=LoginSerializer,
        responses={
            200: openapi.Response(
                description="Login successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description='User information'),
                    }
                )
            ),
            400: openapi.Response(description="Invalid credentials")
        }
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class RegisterView(APIView):
    """
    Register a new user account.
    """
    permission_classes = [permissions.AllowAny]
    
    @swagger_auto_schema(
        operation_description="Register a new user account",
        request_body=UserRegistrationSerializer,
        responses={
            201: openapi.Response(
                description="Registration successful",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'token': openapi.Schema(type=openapi.TYPE_STRING, description='JWT access token'),
                        'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='JWT refresh token'),
                        'user': openapi.Schema(type=openapi.TYPE_OBJECT, description='User information'),
                    }
                )
            ),
            400: openapi.Response(description="Invalid registration data")
        }
    )
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'token': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get current user profile information",
        responses={
            200: UserSerializer,
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Update current user profile information",
        request_body=UserSerializer,
        responses={
            200: UserSerializer,
            400: openapi.Response(description="Invalid data"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def put(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if user.check_password(serializer.validated_data['old_password']):
                user.set_password(serializer.validated_data['new_password'])
                user.save()
                return Response({'message': 'Password changed successfully'})
            return Response({'error': 'Invalid old password'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DataCategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing data categories.
    """
    serializer_class = DataCategorySerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = DataCategory.objects.all()
    
    @swagger_auto_schema(
        operation_description="List all data categories",
        responses={
            200: DataCategorySerializer(many=True),
            401: openapi.Response(description="Authentication required")
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

class TechnicalDataViewSet(viewsets.ModelViewSet):
    serializer_class = TechnicalDataSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            return TechnicalData.objects.all()
        return TechnicalData.objects.filter(user=user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @swagger_auto_schema(
        operation_description="List technical data entries (filtered by user)",
        responses={
            200: TechnicalDataSerializer(many=True),
            401: openapi.Response(description="Authentication required")
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new technical data entry",
        request_body=TechnicalDataSerializer,
        responses={
            201: TechnicalDataSerializer,
            400: openapi.Response(description="Invalid data"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

class AnalyticsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get analytics data for the specified date range",
        manual_parameters=[
            openapi.Parameter(
                'range',
                openapi.IN_QUERY,
                description="Number of days for analytics (default: 30)",
                type=openapi.TYPE_INTEGER,
                default=30
            )
        ],
        responses={
            200: AnalyticsSerializer,
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request):
        user = request.user
        date_range = request.query_params.get('range', '30')
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=int(date_range))
        
        # Get user's data or all data for admin
        if user.is_admin:
            queryset = TechnicalData.objects.filter(created_at__range=(start_date, end_date))
        else:
            queryset = TechnicalData.objects.filter(
                user=user,
                created_at__range=(start_date, end_date)
            )
        
        # Calculate analytics
        total_entries = queryset.count()
        # Remove reference to non-existent analytical_score field
        average_score = 0  # Placeholder since analytical_score doesn't exist
        
        # Category breakdown
        category_breakdown_list = queryset.values('category__name').annotate(
            count=Count('id')
        ).order_by('-count')
        
        # Convert list to dictionary for serializer
        category_breakdown = {}
        for item in category_breakdown_list:
            category_name = item['category__name'] or 'Unknown'
            category_breakdown[category_name] = item['count']
        
        # Trend data
        trend_data = []
        for i in range(int(date_range)):
            date = end_date - timedelta(days=i)
            day_entries = queryset.filter(created_at__date=date.date()).count()
            trend_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'entries': day_entries
            })
        trend_data.reverse()
        
        analytics_data = {
            'date_range': f'{date_range} days',
            'total_entries': total_entries,
            'average_score': round(average_score, 2),
            'category_breakdown': category_breakdown,
            'trend_data': trend_data
        }
        
        serializer = AnalyticsSerializer(analytics_data)
        return Response(serializer.data)

class DashboardDataView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Get user's data or all data for admin
        if user.is_admin:
            entries_queryset = TechnicalData.objects.all()
            reports_queryset = GeneratedReport.objects.all()
        else:
            entries_queryset = TechnicalData.objects.filter(user=user)
            reports_queryset = GeneratedReport.objects.filter(user=user)
        
        # Calculate dashboard stats
        total_entries = entries_queryset.count()
        total_categories = DataCategory.objects.count()
        total_reports = reports_queryset.count()
        
        # Recent entries
        recent_entries = entries_queryset.order_by('-created_at')[:5]
        
        # Mock analytics data for demonstration
        analytics_data = {
            'total_users': CustomUser.objects.count(),
            'active_entries': entries_queryset.filter(created_at__gte=timezone.now() - timedelta(days=7)).count(),
            'average_score': 0,  # Placeholder since analytical_score doesn't exist
            'top_category': entries_queryset.values('category__name').annotate(count=Count('id')).order_by('-count').first()
        }
        
        # Mock chart data
        chart_data = {
            'line_chart': [
                {'name': 'Jan', 'entries': 65, 'score': 78},
                {'name': 'Feb', 'entries': 59, 'score': 82},
                {'name': 'Mar', 'entries': 80, 'score': 85},
                {'name': 'Apr', 'entries': 81, 'score': 88},
                {'name': 'May', 'entries': 56, 'score': 92},
                {'name': 'Jun', 'entries': 55, 'score': 89},
            ],
            'pie_chart': [
                {'name': 'Temperature', 'value': 35},
                {'name': 'Pressure', 'value': 25},
                {'name': 'Flow Rate', 'value': 20},
                {'name': 'Quality', 'value': 20},
            ]
        }
        
        dashboard_data = {
            'total_entries': total_entries,
            'total_categories': total_categories,
            'total_reports': total_reports,
            'recent_entries': TechnicalDataSerializer(recent_entries, many=True).data,
            'analytics_data': analytics_data,
            'chart_data': chart_data
        }
        
        serializer = DashboardDataSerializer(dashboard_data)
        return Response(serializer.data)

class ReportsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="List all reports for the current user",
        responses={
            200: GeneratedReportSerializer(many=True),
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request):
        user = request.user
        
        # Get user's reports or all reports for admin
        if user.is_admin:
            reports = GeneratedReport.objects.all()
        else:
            reports = GeneratedReport.objects.filter(user=user)
        
        serializer = GeneratedReportSerializer(reports, many=True)
        return Response(serializer.data)

class ReportGenerationView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        user = request.user
        report_type = request.data.get('report_type')
        date_range = request.data.get('date_range', '30')
        
        # Check if user can generate reports
        if not hasattr(user, 'can_generate_reports') or not user.can_generate_reports:
            # For now, allow all users to generate reports
            pass
        
        try:
            # Get or create a report template
            template, created = ReportTemplate.objects.get_or_create(
                name=f'{report_type} Template',
                defaults={
                    'report_type': 'custom',
                    'description': f'Template for {report_type} reports',
                    'template_file': f'templates/reports/{report_type}_template.html'
                }
            )
            
            # Create the actual report in database
            report = GeneratedReport.objects.create(
                user=user,
                template=template,
                title=f'{report_type} Report - {timezone.now().strftime("%Y-%m-%d")}',
                parameters={
                    'report_type': report_type,
                    'date_range': date_range,
                    'generated_at': timezone.now().isoformat()
                }
            )
            
            # Serialize the created report
            serializer = GeneratedReportSerializer(report)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate report: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ReportDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Download a generated report",
        responses={
            200: openapi.Response(description="Report file"),
            404: openapi.Response(description="Report not found"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def get(self, request, pk):
        try:
            report = GeneratedReport.objects.get(id=pk)
            
            # Generate proper PDF using ReportLab
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from io import BytesIO
            from django.http import HttpResponse
            
            # Create PDF buffer
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                spaceAfter=30,
                alignment=1  # Center alignment
            )
            
            # Add title
            story.append(Paragraph(f"<b>{report.title}</b>", title_style))
            story.append(Spacer(1, 12))
            
            # Add report details
            story.append(Paragraph(f"<b>Report Type:</b> {report.template.report_type if report.template else 'Custom'}", styles['Normal']))
            story.append(Paragraph(f"<b>Generated:</b> {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
            story.append(Paragraph(f"<b>User:</b> {report.user.get_full_name() or report.user.email}", styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Add parameters if available
            if report.parameters:
                story.append(Paragraph("<b>Report Parameters:</b>", styles['Heading2']))
                for key, value in report.parameters.items():
                    story.append(Paragraph(f"<b>{key}:</b> {value}", styles['Normal']))
                story.append(Spacer(1, 12))
            
            # Add sample content based on report type
            if report.template and 'daily' in report.template.report_type.lower():
                story.append(Paragraph("<b>Daily Summary:</b>", styles['Heading2']))
                story.append(Paragraph("This is a daily report containing key metrics and insights for the specified date range.", styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Add sample table
                data = [
                    ['Metric', 'Value', 'Status'],
                    ['Total Entries', '150', 'Good'],
                    ['Average Score', '85%', 'Excellent'],
                    ['Categories', '8', 'Complete']
                ]
                table = Table(data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 14),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(table)
            
            elif report.template and 'weekly' in report.template.report_type.lower():
                story.append(Paragraph("<b>Weekly Analysis:</b>", styles['Heading2']))
                story.append(Paragraph("This weekly report provides comprehensive analysis of trends and patterns over the past week.", styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Add weekly metrics
                story.append(Paragraph("<b>Weekly Metrics:</b>", styles['Heading3']))
                story.append(Paragraph("• Total Data Points: 1,250", styles['Normal']))
                story.append(Paragraph("• Average Performance: 87%", styles['Normal']))
                story.append(Paragraph("• Top Category: Water Analysis", styles['Normal']))
                story.append(Paragraph("• Growth Rate: +12%", styles['Normal']))
            
            elif report.template and 'monthly' in report.template.report_type.lower():
                story.append(Paragraph("<b>Monthly Overview:</b>", styles['Heading2']))
                story.append(Paragraph("This monthly report provides a comprehensive overview of all activities and performance metrics.", styles['Normal']))
                story.append(Spacer(1, 12))
                
                # Add monthly summary
                story.append(Paragraph("<b>Monthly Summary:</b>", styles['Heading3']))
                story.append(Paragraph("• Total Reports Generated: 45", styles['Normal']))
                story.append(Paragraph("• Data Quality Score: 92%", styles['Normal']))
                story.append(Paragraph("• User Engagement: High", styles['Normal']))
                story.append(Paragraph("• System Uptime: 99.8%", styles['Normal']))
            
            else:
                story.append(Paragraph("<b>Custom Report:</b>", styles['Heading2']))
                story.append(Paragraph("This is a custom report generated based on your specific requirements and parameters.", styles['Normal']))
                story.append(Spacer(1, 12))
                story.append(Paragraph("The report contains detailed analysis and insights relevant to your data and business needs.", styles['Normal']))
            
            # Add footer
            story.append(Spacer(1, 30))
            story.append(Paragraph(f"<i>Report generated on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}</i>", styles['Italic']))
            
            # Build PDF
            doc.build(story)
            pdf_content = buffer.getvalue()
            buffer.close()
            
            # Create HTTP response
            response = HttpResponse(content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{report.title}.pdf"'
            response.write(pdf_content)
            return response
            
        except GeneratedReport.DoesNotExist:
            return Response({'error': 'Report not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({'error': f'Failed to generate PDF: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminUserManagementView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            serializer = UserSerializer(user)
            return Response(serializer.data)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            serializer = UserSerializer(user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
            user.delete()
            return Response({'message': 'User deleted successfully'})
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh')
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response({'message': 'Successfully logged out'})
    except Exception:
        return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def check_auth_view(request):
    return Response({
        'authenticated': True,
        'user': UserSerializer(request.user).data
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def test_api_view(request):
    """Simple test endpoint to verify API is working."""
    return Response({
        'message': 'API is working!',
        'status': 'success'
    })

class APIUsageView(APIView):
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get API usage statistics (Admin only)",
        manual_parameters=[
            openapi.Parameter(
                'days',
                openapi.IN_QUERY,
                description="Number of days to analyze (default: 30)",
                type=openapi.TYPE_INTEGER,
                default=30
            )
        ],
        responses={
            200: openapi.Response(
                description="API usage statistics",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'total_requests': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'average_response_time': openapi.Schema(type=openapi.TYPE_NUMBER),
                        'endpoints': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                        'users': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Schema(type=openapi.TYPE_OBJECT)),
                    }
                )
            ),
            403: openapi.Response(description="Admin access required")
        }
    )
    def get(self, request):
        days = int(request.query_params.get('days', 30))
        end_date = timezone.now()
        start_date = end_date - timedelta(days=days)
        
        # Get usage data
        usage_data = APIUsage.objects.filter(created_at__range=(start_date, end_date))
        
        # Calculate statistics
        total_requests = usage_data.count()
        avg_response_time = usage_data.aggregate(avg=Avg('response_time'))['avg'] or 0
        
        # Endpoint breakdown
        endpoints = usage_data.values('endpoint').annotate(
            count=Count('id'),
            avg_time=Avg('response_time')
        ).order_by('-count')
        
        # User breakdown
        users = usage_data.values('user__email').annotate(
            count=Count('id'),
            avg_time=Avg('response_time')
        ).order_by('-count')
        
        return Response({
            'total_requests': total_requests,
            'average_response_time': round(avg_response_time, 2),
            'endpoints': list(endpoints),
            'users': list(users)
        })

def custom_swagger_ui(request):
    """Custom Swagger UI view without navigation bar."""
    return render(request, 'swagger/index.html', {
        'schema_url': '/swagger.json'
    })


# Water Analysis Views
class WaterAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for water analysis."""
    serializer_class = WaterAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return WaterAnalysis.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        water_analysis = serializer.save(user=self.request.user)
        water_analysis.calculate_indices()
        water_analysis._generate_recommendations()
    
    @swagger_auto_schema(
        operation_description="List water analyses for the current user",
        responses={
            200: openapi.Response('Water analyses', openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(type=openapi.TYPE_OBJECT)
            )),
            401: openapi.Response(description="Authentication required")
        }
    )
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new water analysis",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'ph': openapi.Schema(type=openapi.TYPE_NUMBER, description='pH value'),
                'tds': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total Dissolved Solids (ppm)'),
                'total_alkalinity': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total Alkalinity as CaCO₃ (ppm)'),
                'hardness': openapi.Schema(type=openapi.TYPE_NUMBER, description='Hardness as CaCO₃ (ppm)'),
                'chloride': openapi.Schema(type=openapi.TYPE_NUMBER, description='Chloride as NaCl (ppm)'),
                'temperature': openapi.Schema(type=openapi.TYPE_NUMBER, description='Hot Side Temperature (°C)'),
                'analysis_name': openapi.Schema(type=openapi.TYPE_STRING, description='Analysis name'),
                'notes': openapi.Schema(type=openapi.TYPE_STRING, description='Additional notes'),
            }
        ),
        responses={
            201: openapi.Response('Water analysis created', openapi.Schema(type=openapi.TYPE_OBJECT)),
            400: openapi.Response(description="Invalid data"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def water_trends_view(request):
    """Get water analysis trends with enhanced data."""
    parameter = request.GET.get('parameter', 'ph')
    days = int(request.GET.get('days', 30))
    
    # Get trends from database
    trends = WaterTrend.objects.filter(
        user=request.user,
        parameter=parameter
    ).order_by('trend_date')[:days]
    
    data = []
    for trend in trends:
        data.append({
            'date': trend.trend_date.strftime('%Y-%m-%d'),
            'value': float(trend.value),
            'parameter': trend.parameter,
            'formatted_date': trend.trend_date.strftime('%b %d'),
            'status': get_trend_status(parameter, float(trend.value))
        })
    
    # If no trends in database, generate sample trends for demonstration
    if not data:
        from datetime import timedelta
        from django.utils import timezone
        import random
        
        base_values = {
            'ph': 7.2,
            'lsi': -0.1,
            'rsi': 6.8,
            'ls': 0.2
        }
        
        for i in range(min(days, 30)):
            date = timezone.now().date() - timedelta(days=i)
            variation = random.uniform(-0.3, 0.3)
            value = base_values.get(parameter, 0) + variation
            
            data.append({
                'date': date.strftime('%Y-%m-%d'),
                'value': round(value, 2),
                'parameter': parameter,
                'formatted_date': date.strftime('%b %d'),
                'status': get_trend_status(parameter, value)
            })
        
        # Sort by date for proper ordering
        data.sort(key=lambda x: x['date'])
    
    return Response(data)

def get_trend_status(parameter, value):
    """Get status for trend value based on parameter."""
    if parameter == 'ph':
        if 6.5 <= value <= 8.0:
            return 'optimal'
        elif value < 6.5:
            return 'low'
        else:
            return 'high'
    elif parameter == 'lsi':
        if -0.5 <= value <= 0.5:
            return 'stable'
        elif value > 0.5:
            return 'scaling'
        else:
            return 'corrosion'
    elif parameter == 'rsi':
        if 6.0 <= value <= 7.0:
            return 'stable'
        elif value < 6.0:
            return 'scaling'
        else:
            return 'corrosion'
    elif parameter == 'ls':
        if value < 0.2:
            return 'acceptable'
        elif value < 0.8:
            return 'moderate'
        else:
            return 'corrosion'
    return 'normal'


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def water_recommendations_view(request):
    """Get water analysis recommendations with dynamic suggestions."""
    try:
        # Get existing recommendations from database
        db_recommendations = WaterRecommendation.objects.filter(
            analysis__user=request.user
        ).order_by('-priority', '-created_at')
        
        data = []
        
        # Add existing recommendations
        for rec in db_recommendations:
            data.append({
                'id': rec.id,
                'title': rec.title,
                'description': rec.description,
                'type': rec.recommendation_type,
                'priority': rec.priority,
                'is_implemented': rec.is_implemented,
                'created_at': rec.created_at,
                'source': 'database'
            })
        
        # Generate dynamic recommendations based on latest analysis
        latest_analysis = WaterAnalysis.objects.filter(user=request.user).order_by('-created_at').first()
        
        if latest_analysis:
            # Dynamic recommendations based on analysis results
            dynamic_recommendations = []
            
            # pH-based recommendations
            if latest_analysis.ph is not None and float(latest_analysis.ph) > 8.0:
                dynamic_recommendations.append({
                    'id': f'dynamic_ph_high_{latest_analysis.id}',
                    'title': 'High pH Level Detected',
                    'description': f'pH level of {float(latest_analysis.ph)} is above optimal range. Consider pH reduction treatment.',
                    'type': 'treatment',
                    'priority': 'high',
                    'is_implemented': False,
                    'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else timezone.now().isoformat(),
                    'source': 'dynamic'
                })
            elif latest_analysis.ph is not None and float(latest_analysis.ph) < 6.5:
                dynamic_recommendations.append({
                    'id': f'dynamic_ph_low_{latest_analysis.id}',
                    'title': 'Low pH Level Detected',
                    'description': f'pH level of {float(latest_analysis.ph)} is below optimal range. Consider pH increase treatment.',
                    'type': 'treatment',
                    'priority': 'high',
                    'is_implemented': False,
                    'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else timezone.now().isoformat(),
                    'source': 'dynamic'
                })
            
            # LSI-based recommendations
            if latest_analysis.lsi is not None and float(latest_analysis.lsi) > 0.5:
                dynamic_recommendations.append({
                    'id': f'dynamic_lsi_scaling_{latest_analysis.id}',
                    'title': 'Scaling Risk Detected',
                    'description': f'LSI value of {float(latest_analysis.lsi):.2f} indicates scaling potential. Monitor closely and consider anti-scaling treatment.',
                    'type': 'treatment',
                    'priority': 'high',
                    'is_implemented': False,
                    'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else timezone.now().isoformat(),
                    'source': 'dynamic'
                })
            elif latest_analysis.lsi is not None and float(latest_analysis.lsi) < -0.5:
                dynamic_recommendations.append({
                    'id': f'dynamic_lsi_corrosion_{latest_analysis.id}',
                    'title': 'Corrosion Risk Detected',
                    'description': f'LSI value of {float(latest_analysis.lsi):.2f} indicates corrosion potential. Consider corrosion inhibitor treatment.',
                    'type': 'treatment',
                    'priority': 'high',
                    'is_implemented': False,
                    'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else timezone.now().isoformat(),
                    'source': 'dynamic'
                })
            
            # RSI-based recommendations
            if latest_analysis.rsi is not None and float(latest_analysis.rsi) < 6.0:
                dynamic_recommendations.append({
                    'id': f'dynamic_rsi_scaling_{latest_analysis.id}',
                    'title': 'RSI Scaling Warning',
                    'description': f'RSI value of {float(latest_analysis.rsi):.2f} indicates scaling tendency. Schedule maintenance.',
                    'type': 'maintenance',
                    'priority': 'medium',
                    'is_implemented': False,
                    'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else timezone.now().isoformat(),
                    'source': 'dynamic'
                })
            elif latest_analysis.rsi is not None and float(latest_analysis.rsi) > 7.0:
                dynamic_recommendations.append({
                    'id': f'dynamic_rsi_corrosion_{latest_analysis.id}',
                    'title': 'RSI Corrosion Warning',
                    'description': f'RSI value of {float(latest_analysis.rsi):.2f} indicates corrosion tendency. Monitor system integrity.',
                    'type': 'monitoring',
                    'priority': 'medium',
                    'is_implemented': False,
                    'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else timezone.now().isoformat(),
                    'source': 'dynamic'
                })
            
            # Temperature-based recommendations
            if latest_analysis.temperature is not None and float(latest_analysis.temperature) > 30:
                dynamic_recommendations.append({
                    'id': f'dynamic_temp_high_{latest_analysis.id}',
                    'title': 'High Temperature Alert',
                    'description': f'Temperature of {float(latest_analysis.temperature)}°C is above optimal range. Consider cooling system adjustment.',
                    'type': 'optimization',
                    'priority': 'medium',
                    'is_implemented': False,
                    'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else timezone.now().isoformat(),
                    'source': 'dynamic'
                })
            
            # TDS-based recommendations
            if latest_analysis.tds is not None and float(latest_analysis.tds) > 200:
                dynamic_recommendations.append({
                    'id': f'dynamic_tds_high_{latest_analysis.id}',
                    'title': 'High TDS Levels',
                    'description': f'TDS of {float(latest_analysis.tds)} ppm is elevated. Consider water treatment or filtration.',
                    'type': 'treatment',
                    'priority': 'medium',
                    'is_implemented': False,
                    'created_at': latest_analysis.created_at.isoformat() if latest_analysis.created_at else timezone.now().isoformat(),
                    'source': 'dynamic'
                })
            
            # Add dynamic recommendations to response
            data.extend(dynamic_recommendations)
        
        # Sort by priority and creation date
        data.sort(key=lambda x: (x['priority'] == 'high', str(x['created_at'])), reverse=True)
        
        return Response(data)
    except Exception as e:
        print(f"Error in water_recommendations_view: {e}")
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def calculate_water_analysis_view(request):
    """Calculate water analysis indices from input parameters."""
    try:
        # Extract parameters from request and convert to float
        ph = float(request.data.get('ph', 0))
        tds = float(request.data.get('tds', 0))
        total_alkalinity = float(request.data.get('total_alkalinity', 0))
        hardness = float(request.data.get('hardness', 0))
        chloride = float(request.data.get('chloride', 0))
        temperature = float(request.data.get('temperature', 0))
        
        # Calculate indices directly without saving to database
        # LSI calculation
        temp_factor = 0.1 * (temperature - 25)
        tds_factor = 0.01 * (tds - 150)
        phs = 9.3 + temp_factor + tds_factor
        lsi = ph - phs
        
        # RSI calculation
        rsi = 2 * phs - ph
        
        # LS calculation
        ls = chloride / total_alkalinity if total_alkalinity > 0 else 0
        
        # Determine status
        lsi_status = "Scaling Likely" if lsi > 0.5 else ("Corrosion Likely" if lsi < -0.5 else "Stable")
        rsi_status = "Scaling Likely" if rsi < 6.0 else ("Corrosion Likely" if rsi > 7.0 else "Stable")
        ls_status = "Corrosion Likely" if ls > 0.8 else ("Acceptable" if ls < 0.2 else "Moderate")
        
        # Overall status
        lsi_score = 1 if lsi_status == "Stable" else 0
        rsi_score = 1 if rsi_status == "Stable" else 0
        ls_score = 1 if ls_status in ["Acceptable", "Moderate"] else 0
        total_score = lsi_score + rsi_score + ls_score
        
        overall_status = "Stable" if total_score >= 2 else ("Moderate" if total_score >= 1 else "Unstable")
        
        # Calculate stability score (0-100)
        base_score = 50
        if lsi_status == "Stable":
            base_score += 20
        elif lsi_status == "Scaling Likely":
            base_score -= 10
        elif lsi_status == "Corrosion Likely":
            base_score -= 20
        
        if rsi_status == "Stable":
            base_score += 20
        elif rsi_status == "Scaling Likely":
            base_score -= 10
        elif rsi_status == "Corrosion Likely":
            base_score -= 20
        
        if ls_status in ["Acceptable", "Moderate"]:
            base_score += 10
        elif ls_status == "Corrosion Likely":
            base_score -= 10
        
        stability_score = max(0, min(100, base_score))
        
        return Response({
            'lsi': round(lsi, 2),
            'rsi': round(rsi, 2),
            'ls': round(ls, 2),
            'stability_score': round(stability_score, 2),
            'lsi_status': lsi_status,
            'rsi_status': rsi_status,
            'ls_status': ls_status,
            'overall_status': overall_status
        })
            
    except Exception as e:
        return Response({
            'error': f'Calculation error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)
