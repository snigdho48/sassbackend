from rest_framework import status, generics, permissions, viewsets, serializers
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import json
import math
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.shortcuts import render
from django.http import JsonResponse

from .serializers import (
    UserSerializer, UserRegistrationSerializer, LoginSerializer,
    ChangePasswordSerializer, DataCategorySerializer, TechnicalDataSerializer,
    AnalyticalScoreSerializer, ReportTemplateSerializer, GeneratedReportSerializer,
    DashboardDataSerializer, AnalyticsSerializer, TokenRefreshSerializer,
    WaterAnalysisSerializer, WaterTrendSerializer, WaterRecommendationSerializer, 
    PlantListSerializer, PlantDetailSerializer
)
from users.models import CustomUser
from data_entry.models import DataCategory, TechnicalData, AnalyticalScore, WaterAnalysis, WaterTrend, WaterRecommendation, Plant
from reports.models import ReportTemplate, GeneratedReport
from dashboard.models import DashboardWidget, UserPreference
from .models import APIUsage

class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_admin

class CustomTokenObtainPairView(TokenObtainPairView):
    """Custom JWT token view that includes user information."""
    
    # Override the username field to use email instead
    username_field = 'email'
    
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
            # Use 'username' kwarg for compatibility with Django auth backends
            user = authenticate(
                request=request,
                username=request.data.get('email'),
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
        else:
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
        
                # Recent entries - with error handling and validation
        try:
            # Filter out entries with invalid foreign key references
            valid_entries = []
            recent_entries = entries_queryset.order_by('-created_at')[:10]  # Get more to filter
            
            for entry in recent_entries:
                try:
                    # Test if foreign key relationships are valid
                    if entry.category and entry.user:
                        valid_entries.append(entry)
                        if len(valid_entries) >= 5:  # Limit to 5 valid entries
                            break
                except Exception:
                    # Skip invalid entries
                    continue
            
            recent_entries_data = TechnicalDataSerializer(valid_entries, many=True).data
        except Exception as e:
            print(f"Error serializing recent entries: {e}")
            recent_entries_data = []
        
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
            'recent_entries': recent_entries_data if recent_entries_data else [],
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
        """Get users - Super Admin sees all, Admin sees only users assigned to them"""
        user = request.user
        
        # Super Admin can see all users
        if user.can_create_plants:  # Super Admin
            users = CustomUser.objects.all()
        else:
            # Admin users can only see users assigned to them
            users = CustomUser.objects.filter(
                assigned_admin=user
            )
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        user = request.user
        requested_role = request.data.get('role', 'general_user')
        assigned_admin_id = request.data.get('assigned_admin')
        
        # If Admin (not Super Admin) is creating a user, enforce restrictions
        if not user.can_create_plants:  # Admin (not Super Admin)
            # Admin can only create General Users
            # Automatically set role to general_user (ignore any role in request)
            request.data['role'] = 'general_user'
            # Automatically assign to themselves
            request.data['assigned_admin'] = user.id
            # Set company to admin's company
            if hasattr(user, 'company') and user.company:
                request.data['company'] = user.company
        
        # Check permissions based on the role being created
        if requested_role == 'admin' or requested_role == 'super_admin':
            # Only Super Admin can create Admin or Super Admin users
            if not user.can_create_admin_users:
                return Response(
                    {'error': 'Only Super Administrator can create Admin users'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            # Super Admin creating another Super Admin doesn't need assigned_admin
            # But Super Admin creating an Admin must assign an admin (themselves or another admin)
            if requested_role == 'admin':
                if not assigned_admin_id:
                    return Response(
                        {'error': 'When creating an Admin user, you must assign an admin. For Super Admin creating Admin, assign yourself or another admin.'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Validate assigned_admin is an Admin or Super Admin
                try:
                    assigned_admin = CustomUser.objects.get(id=assigned_admin_id)
                    if assigned_admin.role not in [CustomUser.UserRole.ADMIN, CustomUser.UserRole.SUPER_ADMIN]:
                        return Response(
                            {'error': 'assigned_admin must be an Admin or Super Admin'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except CustomUser.DoesNotExist:
                    return Response(
                        {'error': 'assigned_admin user not found'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
        elif requested_role == 'general_user':
            # Super Admin and Admin can create General Users
            if not user.can_create_general_users:
                return Response(
                    {'error': 'You do not have permission to create General Users'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            # Admin creating General User: automatically assign to themselves (already set above)
            if not user.can_create_plants:  # Admin (not Super Admin)
                # Already handled above, but ensure it's set
                request.data['assigned_admin'] = user.id
            # Super Admin creating General User: must assign an admin
            else:
                if not assigned_admin_id:
                    return Response(
                        {'error': 'When creating a General User, you must assign an admin'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                # Validate assigned_admin is an Admin or Super Admin
                try:
                    assigned_admin = CustomUser.objects.get(id=assigned_admin_id)
                    if assigned_admin.role not in [CustomUser.UserRole.ADMIN, CustomUser.UserRole.SUPER_ADMIN]:
                        return Response(
                            {'error': 'assigned_admin must be an Admin or Super Admin'}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except CustomUser.DoesNotExist:
                    return Response(
                        {'error': 'assigned_admin user not found'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
        
        # Ensure new users are created as active by default
        request.data['is_active'] = True
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            created_user = serializer.save()
            return Response(UserSerializer(created_user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserDetailView(APIView):
    permission_classes = [IsAdminUser]
    
    def get(self, request, user_id):
        try:
            target_user = CustomUser.objects.get(id=user_id)
            current_user = request.user
            
            # Check permissions: Admin users can only view users assigned to them
            if not current_user.can_create_plants:  # Admin (not Super Admin)
                if target_user.assigned_admin != current_user:
                    return Response(
                        {'error': 'You can only view users assigned to you'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            serializer = UserSerializer(target_user)
            return Response(serializer.data)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def put(self, request, user_id):
        try:
            target_user = CustomUser.objects.get(id=user_id)
            current_user = request.user
            
            # Check permissions: Admin users can only edit users assigned to them
            if not current_user.can_create_plants:  # Admin (not Super Admin)
                if target_user.assigned_admin != current_user:
                    return Response(
                        {'error': 'You can only edit users assigned to you'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
                # Admin cannot change role - always keep as general_user
                request.data['role'] = 'general_user'
                # Set company to admin's company
                if hasattr(current_user, 'company') and current_user.company:
                    request.data['company'] = current_user.company
            
            requested_role = request.data.get('role')
            
            # Check permissions if role is being changed (only for Super Admin)
            if requested_role and requested_role != target_user.role:
                if requested_role == 'admin' or requested_role == 'super_admin':
                    # Only Super Admin can change a user's role to Admin or Super Admin
                    if not current_user.can_create_admin_users:
                        return Response(
                            {'error': 'Only Super Administrator can assign Admin or Super Admin roles'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
                elif requested_role == 'general_user':
                    # Super Admin and Admin can assign General User role
                    if not current_user.can_create_general_users:
                        return Response(
                            {'error': 'You do not have permission to assign General User role'}, 
                            status=status.HTTP_403_FORBIDDEN
                        )
            
            serializer = UserSerializer(target_user, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except CustomUser.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, user_id):
        try:
            target_user = CustomUser.objects.get(id=user_id)
            current_user = request.user
            
            # Check permissions: Admin users can only delete users assigned to them
            if not current_user.can_create_plants:  # Admin (not Super Admin)
                if target_user.assigned_admin != current_user:
                    return Response(
                        {'error': 'You can only delete users assigned to you'}, 
                        status=status.HTTP_403_FORBIDDEN
                    )
            
            target_user.delete()
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


# Plant Views
class PlantViewSet(viewsets.ModelViewSet):
    """ViewSet for plants with optimized list/detail serializers."""
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if user.is_admin:
            # Admins can see all active plants
            return Plant.objects.filter(is_active=True)
        else:
            # Regular users can only see plants they own (check both owners ManyToMany and legacy owner field)
            return Plant.objects.filter(
                is_active=True
            ).filter(
                Q(owners=user) | Q(owner=user)
            ).distinct()
    
    def get_serializer_class(self):
        """Use lightweight serializer for list, full serializer for detail"""
        if self.action == 'list':
            return PlantListSerializer
        return PlantDetailSerializer
    
    @swagger_auto_schema(
        operation_description="List all active plants (lightweight - id and name only) with optional search",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search plants by name", type=openapi.TYPE_STRING),
        ],
        responses={
            200: openapi.Response('Plants list', openapi.Schema(
                type=openapi.TYPE_ARRAY,
                items=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                        'name': openapi.Schema(type=openapi.TYPE_STRING)
                    }
                )
            )),
            401: openapi.Response(description="Authentication required")
        }
    )
    def list(self, request, *args, **kwargs):
        # Add search functionality
        search = request.query_params.get('search', '')
        queryset = self.get_queryset()
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        # Return full list (no pagination)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @swagger_auto_schema(
        operation_description="Get detailed plant information with all parameters",
        responses={
            200: openapi.Response('Plant details', openapi.Schema(type=openapi.TYPE_OBJECT)),
            401: openapi.Response(description="Authentication required"),
            404: openapi.Response(description="Plant not found")
        }
    )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class PlantManagementViewSet(viewsets.ModelViewSet):
    """ViewSet for plant management table with full plant data."""
    serializer_class = PlantDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get all users for plant owner assignment (admin only)",
        responses={
            200: UserSerializer(many=True),
            401: openapi.Response(description="Authentication required"),
            403: openapi.Response(description="Admin access required")
        }
    )
    @action(detail=False, methods=['get'])
    def users(self, request):
        """Get users for plant owner assignment (admin only)
        - Super Admin: See all users
        - Admin: Only see users assigned to them (assigned_admin == current_user)
        """
        if not request.user.is_admin:
            return Response(
                {'error': 'Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        user = request.user
        
        # Super Admin can see all users
        if user.can_create_plants:  # Super Admin
            users = CustomUser.objects.filter(is_active=True).order_by('first_name', 'last_name')
        else:
            # Admin users can only see users assigned to them
            users = CustomUser.objects.filter(
                is_active=True,
                assigned_admin=user
            ).order_by('first_name', 'last_name')
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def admin_users(self, request):
        """Get admin users only for plant creation (Super Admin only)
        This endpoint is used when Super Admin is creating a plant and needs to assign it to a single admin.
        """
        if not request.user.can_create_plants:
            return Response(
                {'error': 'Super Admin access required'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only return Admin users (not Super Admin or General Users)
        users = CustomUser.objects.filter(
            is_active=True,
            role__in=[CustomUser.UserRole.ADMIN]
        ).order_by('first_name', 'last_name')
        
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    
    def get_queryset(self):
        user = self.request.user
        
        # Super Admin can see all plants (active and inactive)
        if user.can_create_plants:
            return Plant.objects.all()
        
        # Admin and General Users can only see plants where they are the owner
        # Check both owners ManyToMany field and legacy owner ForeignKey field
        return Plant.objects.filter(
            Q(owners__id=user.id) | Q(owner_id=user.id)
        ).distinct()
    
    @swagger_auto_schema(
        operation_description="List all plants for management table with full data",
        manual_parameters=[
            openapi.Parameter('search', openapi.IN_QUERY, description="Search plants by name", type=openapi.TYPE_STRING),
            openapi.Parameter('owners', openapi.IN_QUERY, description="Filter by owner IDs (comma-separated, admin only)", type=openapi.TYPE_STRING),
            openapi.Parameter('page', openapi.IN_QUERY, description="Page number", type=openapi.TYPE_INTEGER),
            openapi.Parameter('page_size', openapi.IN_QUERY, description="Items per page (max 100)", type=openapi.TYPE_INTEGER),
        ],
        responses={
            200: openapi.Response('Plants management list', openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'count': openapi.Schema(type=openapi.TYPE_INTEGER),
                    'next': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                    'previous': openapi.Schema(type=openapi.TYPE_STRING, nullable=True),
                    'results': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT)
                    )
                }
            )),
            401: openapi.Response(description="Authentication required")
        }
    )
    def list(self, request, *args, **kwargs):
        # Add search functionality
        search = request.query_params.get('search', '')
        owners = request.query_params.get('owners', '')
        queryset = self.get_queryset()
        
        if search:
            queryset = queryset.filter(name__icontains=search)
        
        # Add owner filtering (admin only) - check both owners ManyToMany and legacy owner field
        if owners and request.user.is_admin:
            owner_ids = [int(id.strip()) for id in owners.split(',') if id.strip().isdigit()]
            if owner_ids:
                queryset = queryset.filter(
                    Q(owners__id__in=owner_ids) | Q(owner_id__in=owner_ids)
                ).distinct()
        
        # Add pagination
        page_size = min(int(request.query_params.get('page_size', 10)), 100)
        paginator = Paginator(queryset, page_size)
        page_number = request.query_params.get('page', 1)
        
        try:
            page = paginator.page(page_number)
        except (EmptyPage, InvalidPage):
            page = paginator.page(1)
        
        serializer = self.get_serializer(page, many=True)
        return Response({
            'count': paginator.count,
            'next': page.has_next() and request.build_absolute_uri(f"?page={page.next_page_number()}&search={search}&owners={owners}&page_size={page_size}") or None,
            'previous': page.has_previous() and request.build_absolute_uri(f"?page={page.previous_page_number()}&search={search}&owners={owners}&page_size={page_size}") or None,
            'results': serializer.data
        })

    def update(self, request, *args, **kwargs):
        """Update plant - Super Admin can edit all fields, Admin can only update owners"""
        instance = self.get_object()
        user = request.user
        
        # Check if user is Admin (not Super Admin)
        if user.is_admin and not user.can_create_plants:
            # Admin users can only update owners field (owner_ids is the write-only field name in serializer)
            allowed_fields = {'owner_ids', 'owners'}  # Allow both for backward compatibility
            request_fields = set(request.data.keys())
            
            # Check if request contains only owner-related fields or no fields at all
            if request_fields and not request_fields.issubset(allowed_fields):
                # Request contains fields other than owners
                return Response(
                    {'error': 'Admin users can only assign/change plant owners. Only Super Administrator can edit other plant fields.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            # Allow the update to proceed (it's only owners)
        elif not user.can_create_plants:
            # Non-admin users cannot update plants at all
            return Response(
                {'error': 'Only Super Administrator can edit plants. Admin users can only assign/change plant owners.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().update(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create plant - only Super Admin can create plants, and must assign to a single admin"""
        user = request.user
        
        # Only Super Admin can create plants
        if not user.can_create_plants:
            return Response(
                {'error': 'Only Super Administrator can create plants'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate that owner_id is provided and is an Admin user
        owner_id = request.data.get('owner_id')
        if not owner_id:
            return Response(
                {'error': 'Plant must be assigned to an Admin user'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            assigned_admin = CustomUser.objects.get(id=owner_id)
            # Ensure the assigned user is an Admin (not Super Admin or General User)
            if assigned_admin.role != CustomUser.UserRole.ADMIN:
                return Response(
                    {'error': 'Plant can only be assigned to an Admin user'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        except CustomUser.DoesNotExist:
            return Response(
                {'error': 'Assigned admin user not found'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the plant (this will set the owner field via serializer)
        response = super().create(request, *args, **kwargs)
        
        # After creation, also add the admin to the owners ManyToMany field
        if response.status_code == 201:
            plant = Plant.objects.get(id=response.data['id'])
            # Add to ManyToMany field (this is needed for the Admin to see the plant)
            plant.owners.add(assigned_admin)
            # Ensure the owner field is also set (in case serializer didn't set it)
            if not plant.owner:
                plant.owner = assigned_admin
                plant.save()
        
        return response

    def destroy(self, request, *args, **kwargs):
        """Delete plant - only Super Admin can delete plants"""
        instance = self.get_object()
        user = request.user
        
        # Only Super Admin can delete plants
        if not user.can_create_plants:
            return Response(
                {'error': 'Only Super Administrator can delete plants. Admin users do not have permission.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        return super().destroy(request, *args, **kwargs)

# Water Analysis Views
class WaterAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for water analysis."""
    serializer_class = WaterAnalysisSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        queryset = WaterAnalysis.objects.filter(user=user)
        
        # General Users can only see analyses for plants they own (check both owners ManyToMany and legacy owner field)
        if user.is_general_user:
            queryset = queryset.filter(
                Q(plant__owners=user) | Q(plant__owner=user)
            ).distinct()
        
        return queryset
    
    def perform_create(self, serializer):
        user = self.request.user
        plant = serializer.validated_data.get('plant')
        
        # General Users can only input data for assigned plants (plants they own)
        if user.is_general_user:
            if not plant:
                raise ValidationError({'plant': 'Plant is required for General Users'})
            # Check if user is in plant.owners (ManyToMany) or plant.owner (legacy)
            if user not in plant.owners.all() and plant.owner != user:
                raise ValidationError(
                    {'plant': 'You can only input data for plants assigned to you'}
                )
        
        water_analysis = serializer.save(user=user)
        water_analysis.calculate_indices()
        try:
            water_analysis._generate_recommendations()
        except Exception as e:
            print(f"Error generating recommendations: {e}")
            # Don't fail the save if recommendations generation fails
    
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
                'analysis_type': openapi.Schema(type=openapi.TYPE_STRING, description='Analysis type: cooling or boiler'),
                'ph': openapi.Schema(type=openapi.TYPE_NUMBER, description='pH value'),
                'tds': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total Dissolved Solids (ppm)'),
                'hardness': openapi.Schema(type=openapi.TYPE_NUMBER, description='Hardness as CaCO₃ (ppm)'),
                'total_alkalinity': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total Alkalinity as CaCO₃ (ppm)'),
                'chloride': openapi.Schema(type=openapi.TYPE_NUMBER, description='Chloride as NaCl (ppm)'),
                'temperature': openapi.Schema(type=openapi.TYPE_NUMBER, description='Hot Side Temperature (°C)'),
                'basin_temperature': openapi.Schema(type=openapi.TYPE_NUMBER, description='Basin Temperature (°C)'),
                'sulphate': openapi.Schema(type=openapi.TYPE_NUMBER, description='Sulphate (ppm)'),
                'm_alkalinity': openapi.Schema(type=openapi.TYPE_NUMBER, description='M-Alkalinity as CaCO₃ (ppm)'),
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
    """Get water analysis trends with real historical data grouped by date with min/max values."""
    parameter = request.GET.get('parameter', 'ph')
    days = int(request.GET.get('days', 30))
    plant_id = request.GET.get('plant_id')
    
    # Get trends from database grouped by date
    from django.db.models import Min, Max, Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Calculate date range
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Build filter query
    filter_kwargs = {
        'parameter': parameter,
        'trend_date__gte': start_date,
        'trend_date__lte': end_date
    }
    
    # Filter by user (unless admin)
    if not request.user.is_staff:
        filter_kwargs['user'] = request.user
    
    # Filter by plant if specified
    if plant_id:
        # Get WaterAnalysis records for this plant and user
        from data_entry.models import WaterAnalysis
        
        analysis_ids = WaterAnalysis.objects.filter(
            plant=plant_id,
            **({'user': request.user} if not request.user.is_staff else {})
        ).values_list('id', flat=True)
        
        if analysis_ids:
            filter_kwargs['analysis_id__in'] = analysis_ids
        else:
            # No analyses found for this plant, return empty
            return Response([])
    
    # Get all individual trend records
    trends = WaterTrend.objects.filter(**filter_kwargs).order_by('trend_date')
    
    # Group by date and calculate min/max for each date
    from collections import defaultdict
    grouped_trends = defaultdict(list)
    
    for trend in trends:
        grouped_trends[trend.trend_date].append(float(trend.value))
    
    data = []
    for date, values in grouped_trends.items():
        min_value = min(values)
        max_value = max(values)
        
        data.append({
            'date': date.strftime('%Y-%m-%d'),
            'min_value': min_value,
            'max_value': max_value,
            'parameter': parameter,
            'formatted_date': date.strftime('%b %d'),
            'count': len(values),
            'min_status': get_trend_status(parameter, min_value),
            'max_status': get_trend_status(parameter, max_value)
        })
    
    # If no trends in database, return empty array
    if not data:
        return Response([])
    
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
    elif parameter == 'psi':
        if 4.5 <= value <= 6.5:
            return 'optimal'
        elif value < 4.5:
            return 'scaling'
        else:
            return 'corrosion'
    elif parameter == 'lr':
        if value <= 0.8:
            return 'acceptable'
        elif value <= 1.2:
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
        

            
    except Exception as e:
        return Response({
            'error': f'Calculation error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)


@swagger_auto_schema(
    method='post',
    operation_description="Calculate comprehensive water stability indices including LSI, RSI, LS, PSI, and LR with recommendations using exact formulae from industry standards",
    request_body=openapi.Schema(
        type=openapi.TYPE_OBJECT,
        required=['ph', 'tds', 'total_alkalinity', 'hardness', 'chloride', 'temperature'],
        properties={
            'ph': openapi.Schema(type=openapi.TYPE_NUMBER, description='pH value of water'),
            'tds': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total Dissolved Solids (ppm)'),
            'total_alkalinity': openapi.Schema(type=openapi.TYPE_NUMBER, description='Total Alkalinity as CaCO3 (ppm)'),
            'hardness': openapi.Schema(type=openapi.TYPE_NUMBER, description='Hardness as CaCO3 (ppm)'),
            'chloride': openapi.Schema(type=openapi.TYPE_NUMBER, description='Chloride concentration (ppm)'),
            'temperature': openapi.Schema(type=openapi.TYPE_NUMBER, description='Water temperature (°C)'),
            'sulphate': openapi.Schema(type=openapi.TYPE_NUMBER, description='Sulphate concentration (ppm)', default=0),
        }
    ),
    responses={
        200: openapi.Response(
            description="Water analysis calculation successful",
            schema=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'calculation': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'lsi': openapi.Schema(type=openapi.TYPE_NUMBER, description='Langelier Saturation Index'),
                            'rsi': openapi.Schema(type=openapi.TYPE_NUMBER, description='Ryznar Stability Index'),

                            'psi': openapi.Schema(type=openapi.TYPE_NUMBER, description='Puckorius Scaling Index'),
                            'lr': openapi.Schema(type=openapi.TYPE_NUMBER, description='Langelier Ratio'),
                            'stability_score': openapi.Schema(type=openapi.TYPE_NUMBER, description='Overall stability score (0-100)'),
                            'lsi_status': openapi.Schema(type=openapi.TYPE_STRING, description='LSI status based on industry standards'),
                            'rsi_status': openapi.Schema(type=openapi.TYPE_STRING, description='RSI status based on industry standards'),

                            'psi_status': openapi.Schema(type=openapi.TYPE_STRING, description='PSI status based on industry standards'),
                            'lr_status': openapi.Schema(type=openapi.TYPE_STRING, description='LR status based on industry standards'),
                            'overall_status': openapi.Schema(type=openapi.TYPE_STRING, description='Overall water stability status'),
                        }
                    ),
                    'recommendations': openapi.Schema(
                        type=openapi.TYPE_ARRAY,
                        items=openapi.Schema(type=openapi.TYPE_OBJECT),
                        description='List of recommendations based on analysis results'
                    )
                }
            )
        ),
        400: openapi.Response(description="Calculation error")
    }
)
@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def calculate_water_analysis_with_recommendations_view(request):
    """Calculate water analysis indices and return recommendations in a single response."""
    try:
        # Extract parameters from request and convert to float
        analysis_type = request.data.get('analysis_type', 'cooling')  # 'cooling' or 'boiler'
        plant_id = request.data.get('plant_id')
        
        # Get plant-specific parameters if plant_id is provided
        plant = None
        if plant_id:
            try:
                plant = Plant.objects.get(id=plant_id, is_active=True)
            except Plant.DoesNotExist:
                return Response({'error': 'Plant not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check analysis type and extract only required parameters
        if analysis_type == 'boiler':
            # For boiler water, only extract the 4 required fields
            ph = float(request.data.get('ph', 0))
            tds = float(request.data.get('tds', 0))
            hardness = float(request.data.get('hardness', 0))
            m_alkalinity = float(request.data.get('m_alkalinity', 0))
        else:
            # For cooling water, extract all required fields
            ph = float(request.data.get('ph', 0))
            tds = float(request.data.get('tds', 0))
            total_alkalinity = float(request.data.get('total_alkalinity', 0))
            hardness = float(request.data.get('hardness', 0))
            chloride = float(request.data.get('chloride', 0))
            temperature = float(request.data.get('temperature', 0))
            sulphate = float(request.data.get('sulphate', 0))  # New parameter for LR calculation
        
        # Check analysis type and calculate accordingly
        if analysis_type == 'boiler':
            # Boiler Water Stability Score (Simplified – 4 Parameters) as per image
            # Start score: 100 points
            stability_score = 100
            
            # Get plant-specific parameters or use defaults
            if plant:
                boiler_params = plant.get_boiler_parameters()
                ph_min = float(boiler_params['ph']['min'])
                ph_max = float(boiler_params['ph']['max'])
                tds_min = float(boiler_params['tds']['min'])
                tds_max = float(boiler_params['tds']['max'])
                hardness_max = float(boiler_params['hardness']['max'])
                alk_min = float(boiler_params['alkalinity']['min'])
                alk_max = float(boiler_params['alkalinity']['max'])
            else:
                # Default values
                ph_min, ph_max = 10.5, 11.5
                tds_min, tds_max = 2500, 3500
                hardness_max = 2.0
                alk_min, alk_max = 600, 1400
            
            # pH: Ideal Range based on plant parameters
            if ph_min <= ph <= ph_max:
                # pH is in ideal range, no deduction
                pass
            else:
                # Calculate deviation and deduct points (5 points per 0.1 deviation)
                if ph < ph_min:
                    deviation = ph_min - ph
                else:
                    deviation = ph - ph_max
                points_to_deduct = min((deviation / 0.1) * 5, 30)  # Cap at 30 points
                stability_score -= points_to_deduct
            
            # TDS: Ideal Range based on plant parameters
            if tds_min <= tds <= tds_max:
                # TDS is in ideal range, no deduction
                pass
            else:
                if tds > tds_max * 1.15:  # 15% above max
                    stability_score -= 20  # Subtract 20 points if > 15% above max
                else:
                    stability_score -= 10  # Subtract 10 points if outside ideal range
            
            # Hardness: Ideal Range based on plant parameters
            if hardness <= hardness_max:
                # Hardness is in ideal range, no deduction
                pass
            elif hardness <= hardness_max * 2.5:  # 2.5x max
                stability_score -= 10  # Subtract 10 points if 2.5x max
            else:
                stability_score -= 20  # Subtract 20 points if > 2.5x max
            
            # M-Alk: Ideal Range based on plant parameters
            if alk_min <= m_alkalinity <= alk_max:
                # M-Alk is in ideal range, no deduction
                pass
            else:
                # Calculate deviation from ideal range and deduct points
                if m_alkalinity < alk_min:
                    deviation = alk_min - m_alkalinity
                else:
                    deviation = m_alkalinity - alk_max
                points_to_deduct = (deviation / 50) * 2
                stability_score -= points_to_deduct
            
            # Cap score between 0 and 100
            stability_score = max(0, min(100, stability_score))
            
            # Determine overall status based on score
            if stability_score >= 80:
                overall_status = "Stable"
            elif stability_score >= 60:
                overall_status = "Slightly Unstable"
            elif stability_score >= 40:
                overall_status = "Unstable"
            else:
                overall_status = "Highly Unstable"
            
            # Return exact suggested actions from the table instead of generating them
            boiler_recommendations = [
                {
                    'id': 'boiler_ph_1',
                    'title': 'pH Adjustment',
                    'description': f'pH too low — corrosion risk. Adjust chemical feed to raise pH to {ph_min}-{ph_max} range.' if ph < ph_min else f'pH too high — risk of caustic embrittlement. Reduce chemical feed to {ph_min}-{ph_max} range.' if ph > ph_max else f'pH is within optimal range ({ph_min}-{ph_max}).',
                    'type': 'chemical_adjustment',
                    'priority': 'high' if ph < ph_min or ph > ph_max else 'low',
                    'is_implemented': False,
                    'created_at': timezone.now().isoformat(),
                    'source': 'boiler_table'
                },
                {
                    'id': 'boiler_tds_1',
                    'title': 'TDS Management',
                    'description': f'TDS too high — risk of carryover and foaming. Increase blowdown to maintain {tds_min}-{tds_max} ppm range.' if tds > tds_max else f'TDS is within optimal range ({tds_min}-{tds_max} ppm).',
                    'type': 'blowdown_optimization',
                    'priority': 'medium' if tds > tds_max else 'low',
                    'is_implemented': False,
                    'created_at': timezone.now().isoformat(),
                    'source': 'boiler_table'
                },
                {
                    'id': 'boiler_hardness_1',
                    'title': 'Hardness Control',
                    'description': f'Hardness detected — risk of scaling. Check softener and condensate contamination. Target: ≤{hardness_max} ppm.' if hardness > hardness_max else f'Hardness is within optimal range (≤{hardness_max} ppm).',
                    'type': 'water_treatment',
                    'priority': 'high' if hardness > hardness_max else 'low',
                    'is_implemented': False,
                    'created_at': timezone.now().isoformat(),
                    'source': 'boiler_table'
                },
                {
                    'id': 'boiler_malk_1',
                    'title': 'M-Alkalinity Management',
                    'description': f'M-Alkalinity too low — may lead to corrosion. Increase alkalinity through dosing to {alk_min}-{alk_max} ppm range.' if m_alkalinity < alk_min else f'M-Alkalinity is within optimal range ({alk_min}-{alk_max} ppm).',
                    'type': 'chemical_adjustment',
                    'priority': 'medium' if m_alkalinity < alk_min else 'low',
                    'is_implemented': False,
                    'created_at': timezone.now().isoformat(),
                    'source': 'boiler_table'
                }
            ]
            
            # Return boiler water results (only stability score)
            return Response({
                'calculation': {
                    'stability_score': round(stability_score, 2),
                    'overall_status': overall_status,
                    'analysis_type': 'boiler',
                    'plant_id': plant_id,
                    'plant_name': plant.name if plant else None
                },
                'recommendations': boiler_recommendations
            })
        
        # Cooling Water Analysis - Calculate indices directly without saving to database
        # LSI calculation using the formulae from the document
        # A = (Log10(TDS)-1)/10
        # B = -13.12 x Log10(Temp (oC)+273) + 34.55
        # C = Log10(Ca as CaCO3) - 0.4
        # D = Log10(Alk as CaCO3)
        # pHs = 9.3 + A + B - C - D
        
        if tds > 0 and temperature > 0 and hardness > 0 and total_alkalinity > 0:
            A = (math.log10(tds) - 1) / 10
            B = -13.12 * math.log10(temperature + 273) + 34.55
            C = math.log10(hardness) - 0.4
            D = math.log10(total_alkalinity)
            phs = 9.3 + A + B - C - D
        else:
            # Fallback calculation if any parameter is missing
            temp_factor = 0.1 * (temperature - 25)
            tds_factor = 0.01 * (tds - 150)
            phs = 9.3 + temp_factor + tds_factor
        
        lsi = ph - phs
        
        # RSI calculation
        rsi = 2 * phs - ph
        
        # PSI calculation (Puckorius Scaling Index)
        # pHe = 1.465 + Log10(Alk as CaCO3) + 4.54
        # PSI = 2 x pHe - pHs
        if total_alkalinity > 0:
            pHe = 1.465 + math.log10(total_alkalinity) + 4.54
            psi = 2 * pHe - phs
        else:
            psi = 0
        
        # LR calculation (Langelier Ratio) - EXACTLY as in the image
        # epm Cl = Chloride as Cl / 35.5
        # epm SO4 = Sulphate as SO4 / 96
        # Molar Alkalinity, [Alk] = Total Alk as CaCO3 / 100
        # K1 and K2 are temperature-dependent equilibrium constants from the image
        # LR = [epm Cl + epm SO4] / [epm HCO3 + epm CO3]
        if total_alkalinity > 0 and (chloride > 0 or sulphate > 0):
            # Calculate equilibrium constants K1 and K2 using EXACT formulae from image
            if temperature > 0:
                # EXACT formulae from the image:
                # K1 = 10^-(3404.71/Temp + 0.032786 × Temp - 14.8435)
                # K2 = 10^-(2902.39/Temp + 0.02379 × Temp - 6.498)
                K1 = 10**(-(3404.71/temperature + 0.032786 * temperature - 14.8435))
                K2 = 10**(-(2902.39/temperature + 0.02379 * temperature - 6.498))
            else:
                K1 = 10**(-14.8435)  # Default at 25°C
                K2 = 10**(-6.498)    # Default at 25°C
            
            # Calculate carbonate speciation with numerical stability checks
            H_plus = 10**(-ph)
            
            # Check if the equilibrium constants are too small to be numerically stable
            if K1 < 1e-20 or K2 < 1e-20:
                # Use simplified approach for very small equilibrium constants
                # This maintains the scientific accuracy while preventing numerical overflow
                if ph < 6.5:
                    # Acidic conditions - most alkalinity is HCO3-
                    alpha_hco3 = 0.95
                    alpha_co3 = 0.05
                elif ph > 8.5:
                    # Alkaline conditions - significant CO3-2
                    alpha_hco3 = 0.30
                    alpha_co3 = 0.70
                else:
                    # Neutral conditions - balanced HCO3- and CO3-2
                    alpha_hco3 = 0.80
                    alpha_co3 = 0.20
            else:
                # Use exact formulae when numerically stable
                denominator = H_plus**2 + H_plus * K1 + K1 * K2
                if denominator > 1e-20:  # Check for numerical stability
                    alpha_hco3 = (H_plus * K1) / denominator
                    alpha_co3 = (K1 * K2) / denominator
                else:
                    # Fallback to simplified approach
                    alpha_hco3 = 0.80
                    alpha_co3 = 0.20
            
            # Calculate equivalent per million values
            epm_cl = chloride / 35.5
            epm_so4 = sulphate / 96
            molar_alk = total_alkalinity / 100
            epm_hco3 = molar_alk * alpha_hco3
            epm_co3 = molar_alk * alpha_co3
            
            # Calculate LR with numerical stability checks
            if (epm_hco3 + epm_co3) > 1e-10:  # Check for very small values
                lr = (epm_cl + epm_so4) / (epm_hco3 + epm_co3)
                # Cap LR at reasonable values to prevent display issues
                if lr > 5.0:
                    lr = 5.0  # Cap at 5.0 for display purposes (high corrosion risk)
                elif lr < 0.0:
                    lr = 0.0   # Ensure non-negative
                elif lr > 100:  # Additional safety check for extremely large values
                    lr = 5.0   # Set to high corrosion risk
            else:
                # If carbonate speciation is effectively zero, set LR to indicate high corrosion risk
                lr = 2.0  # This represents high corrosion risk per the image interpretation
        else:
            lr = 0
        
        # Determine status for all indices based on EXACT ranges from the images
        # LSI status based on EXACT ranges from first image:
        # -5 to -2: Severe to Moderate Corrosion
        # -1: Mild Corrosion  
        # -0.5 to 0: Near Balance
        # 0 to 0.5: Near Balance
        # 1: Moderate Scale Forming
        # 2 to 4: Severe Scale Forming
        if lsi <= -2:
            lsi_status = "Severe to Moderate Corrosion"
        elif lsi <= -1:
            lsi_status = "Mild Corrosion"
        elif lsi <= 0.5:
            lsi_status = "Near Balance"
        elif lsi <= 1:
            lsi_status = "Moderate Scale Forming"
        else:
            lsi_status = "Severe Scale Forming"
        
        # RSI status based on EXACT ranges from first image:
        # 4.0 - 5.0: Heavy scale
        # 5.0 - 6.0: Light scale
        # 6.0 - 7.0: Little scale or corrosion
        # 7.0 - 7.5: Corrosion significant
        # 7.5 - 9.0: Heavy corrosion
        # > 9.0: Intolerable corrosion
        if rsi < 5.0:
            rsi_status = "Heavy scale"
        elif rsi < 6.0:
            rsi_status = "Light scale"
        elif rsi < 7.0:
            rsi_status = "Little scale or corrosion"
        elif rsi < 7.5:
            rsi_status = "Corrosion significant"
        elif rsi < 9.0:
            rsi_status = "Heavy corrosion"
        else:
            rsi_status = "Intolerable corrosion"
        

        
        # PSI status based on EXACT ranges from second image:
        # PSI < 4.5: Water has a tendency to scale
        # PSI 4.5 - 6.5: Water is in optimal range with no corrosion or scaling
        # PSI > 6.5: Water has a tendency to corrode
        if psi < 4.5:
            psi_status = "Water has a tendency to scale"
        elif 4.5 <= psi <= 6.5:
            psi_status = "Water is in optimal range with no corrosion or scaling"
        else:
            psi_status = "Water has a tendency to corrode"
        
        # LR status based on EXACT ranges from second image:
        # LR < 0.8: Chlorides and sulfate probably will not interfere with natural film formation
        # LR 0.8 < 1.2: Chlorides and sulfates may interfere with natural film formation. Higher than desired corrosion rates might be anticipated.
        # LR > 1.2: The tendency towards high corrosion rates of a local type should be expected as the index increases.
        if lr < 0.8:
            lr_status = "Chlorides and sulfate probably will not interfere with natural film formation"
        elif 0.8 <= lr <= 1.2:
            lr_status = "Chlorides and sulfates may interfere with natural film formation. Higher than desired corrosion rates might be anticipated."
        else:
            lr_status = "The tendency towards high corrosion rates of a local type should be expected as the index increases"
        
        # Overall status calculation including new indices based on EXACT status descriptions
        lsi_score = 1 if lsi_status == "Near Balance" else 0
        rsi_score = 1 if rsi_status == "Little scale or corrosion" else 0
        psi_score = 1 if psi_status == "Water is in optimal range with no corrosion or scaling" else 0
        lr_score = 1 if lr_status == "Chlorides and sulfate probably will not interfere with natural film formation" else (0.5 if lr_status == "Chlorides and sulfates may interfere with natural film formation. Higher than desired corrosion rates might be anticipated." else 0)
        total_score = lsi_score + rsi_score + psi_score + lr_score
        
        overall_status = "Stable" if total_score >= 3 else ("Moderate" if total_score >= 2 else "Unstable")
        
        # Calculate stability score (0-100) including new indices based on EXACT status descriptions
        base_score = 50
        if lsi_status == "Near Balance":
            base_score += 15
        elif lsi_status in ["Moderate Scale Forming", "Severe Scale Forming"]:
            base_score -= 8
        elif lsi_status in ["Mild Corrosion", "Severe to Moderate Corrosion"]:
            base_score -= 15
        
        if rsi_status == "Little scale or corrosion":
            base_score += 15
        elif rsi_status in ["Heavy scale", "Light scale"]:
            base_score -= 8
        elif rsi_status in ["Corrosion significant", "Heavy corrosion", "Intolerable corrosion"]:
            base_score -= 15
        

        
        if psi_status == "Water is in optimal range with no corrosion or scaling":
            base_score += 12
        elif psi_status == "Water has a tendency to scale":
            base_score -= 6
        elif psi_status == "Water has a tendency to corrode":
            base_score -= 12
        
        if lr_status == "Chlorides and sulfate probably will not interfere with natural film formation":
            base_score += 10
        elif lr_status == "Chlorides and sulfates may interfere with natural film formation. Higher than desired corrosion rates might be anticipated.":
            base_score += 5
        elif lr_status == "The tendency towards high corrosion rates of a local type should be expected as the index increases":
            base_score -= 10
        
        stability_score = max(0, min(100, base_score))
        
        # Generate recommendations based on calculated results
        recommendations = []
        
        # Static recommendations
        static_recommendations = [
            {
                'id': 'static_1',
                'title': 'Regular Water Testing',
                'description': 'Conduct monthly water quality tests to monitor changes in water parameters including sulphate levels.',
                'type': 'monitoring',
                'priority': 'high',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'static'
            },
            {
                'id': 'static_2',
                'title': 'Maintain Treatment Equipment',
                'description': 'Regular maintenance of water treatment systems ensures optimal performance.',
                'type': 'maintenance',
                'priority': 'medium',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'static'
            },
            {
                'id': 'static_3',
                'title': 'Document Water Quality',
                'description': 'Keep detailed records of water quality parameters and treatment actions.',
                'type': 'monitoring',
                'priority': 'medium',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'static'
            },
            {
                'id': 'static_4',
                'title': 'Monitor Chloride and Sulphate Levels',
                'description': 'Regular monitoring of chloride and sulphate levels is crucial for corrosion control and LR calculations.',
                'type': 'monitoring',
                'priority': 'high',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'static'
            },
            {
                'id': 'static_5',
                'title': 'Temperature Monitoring',
                'description': 'Monitor water temperature as it affects all stability indices calculations.',
                'type': 'monitoring',
                'priority': 'medium',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'static'
            }
        ]
        recommendations.extend(static_recommendations)
        
        # Dynamic recommendations based on calculated results
        dynamic_recommendations = []
        
        # LSI-based recommendations based on EXACT status from first image
        if lsi_status in ["Mild Corrosion", "Severe to Moderate Corrosion"]:
            dynamic_recommendations.append({
                'id': f'dynamic_lsi_corrosion_{int(timezone.now().timestamp())}',
                'title': 'Corrosion Prevention Required',
                'description': f'LSI indicates {lsi_status.lower()}. Consider pH adjustment or corrosion inhibitors.',
                'type': 'corrosion',
                'priority': 'high',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        elif lsi_status in ["Moderate Scale Forming", "Severe Scale Forming"]:
            dynamic_recommendations.append({
                'id': f'dynamic_lsi_scaling_{int(timezone.now().timestamp())}',
                'title': 'Scaling Prevention Required',
                'description': f'LSI indicates {lsi_status.lower()}. Consider pH adjustment or scale inhibitors.',
                'type': 'scaling',
                'priority': 'high',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        
        # RSI-based recommendations based on EXACT status from first image
        if rsi_status in ["Corrosion significant", "Heavy corrosion", "Intolerable corrosion"]:
            dynamic_recommendations.append({
                'id': f'dynamic_rsi_corrosion_{int(timezone.now().timestamp())}',
                'title': 'High Corrosion Risk',
                'description': f'RSI indicates {rsi_status.lower()}. Implement corrosion control measures.',
                'type': 'corrosion',
                'priority': 'high',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        elif rsi_status in ["Heavy scale", "Light scale"]:
            dynamic_recommendations.append({
                'id': f'dynamic_rsi_scaling_{int(timezone.now().timestamp())}',
                'title': 'High Scaling Risk',
                'description': f'RSI indicates {rsi_status.lower()}. Implement scale control measures.',
                'type': 'scaling',
                'priority': 'high',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        

        
        # PSI-based recommendations based on EXACT status from second image
        if psi_status == "Water has a tendency to corrode":
            dynamic_recommendations.append({
                'id': f'dynamic_psi_corrosion_{int(timezone.now().timestamp())}',
                'title': 'PSI Indicates Corrosion Risk',
                'description': 'PSI indicates water has a tendency to corrode. Consider pH adjustment or corrosion inhibitors.',
                'type': 'corrosion',
                'priority': 'high',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        elif psi_status == "Water has a tendency to scale":
            dynamic_recommendations.append({
                'id': f'dynamic_psi_scaling_{int(timezone.now().timestamp())}',
                'title': 'PSI Indicates Scaling Risk',
                'description': 'PSI indicates water has a tendency to scale. Consider pH adjustment or scale inhibitors.',
                'type': 'scaling',
                'priority': 'high',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        
        # LR-based recommendations based on EXACT status from second image
        if lr_status == "The tendency towards high corrosion rates of a local type should be expected as the index increases":
            dynamic_recommendations.append({
                'id': f'dynamic_lr_corrosion_{int(timezone.now().timestamp())}',
                'title': 'High Chloride/Sulfate Corrosion Risk',
                'description': 'LR indicates the tendency towards high corrosion rates of a local type. Implement corrosion control measures.',
                'type': 'corrosion',
                'priority': 'high',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        elif lr_status == "Chlorides and sulfates may interfere with natural film formation. Higher than desired corrosion rates might be anticipated.":
            dynamic_recommendations.append({
                'id': f'dynamic_lr_moderate_{int(timezone.now().timestamp())}',
                'title': 'Moderate Chloride/Sulfate Interference',
                'description': 'LR indicates moderate interference. Monitor corrosion rates and consider preventive measures.',
                'type': 'corrosion',
                'priority': 'medium',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        
        # pH-based recommendations
        if ph < 6.5:
            dynamic_recommendations.append({
                'id': f'dynamic_ph_low_{int(timezone.now().timestamp())}',
                'title': 'Low pH Correction',
                'description': 'pH is too low. Consider pH adjustment to prevent corrosion.',
                'type': 'treatment',
                'priority': 'medium',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        elif ph > 8.5:
            dynamic_recommendations.append({
                'id': f'dynamic_ph_high_{int(timezone.now().timestamp())}',
                'title': 'High pH Correction',
                'description': 'pH is too high. Consider pH adjustment to prevent scaling.',
                'type': 'treatment',
                'priority': 'medium',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        
        # TDS-based recommendations
        if tds > 500:
            dynamic_recommendations.append({
                'id': f'dynamic_tds_high_{int(timezone.now().timestamp())}',
                'title': 'High TDS Levels',
                'description': 'TDS is elevated. Consider water treatment or filtration.',
                'type': 'treatment',
                'priority': 'medium',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        
        # Sulphate-based recommendations
        if sulphate > 250:
            dynamic_recommendations.append({
                'id': f'dynamic_sulphate_high_{int(timezone.now().timestamp())}',
                'title': 'High Sulphate Levels',
                'description': 'Sulphate is elevated. High sulphate can contribute to corrosion and scaling.',
                'type': 'treatment',
                'priority': 'medium',
                'is_implemented': False,
                'created_at': timezone.now().isoformat(),
                'source': 'dynamic'
            })
        
        # Add dynamic recommendations to response
        recommendations.extend(dynamic_recommendations)
        
        # Sort by priority and creation date
        recommendations.sort(key=lambda x: (x['priority'] == 'high', str(x['created_at'])), reverse=True)
        
        return Response({
            'calculation': {
                'lsi': round(lsi, 2),
                'rsi': round(rsi, 2),
                'lr': round(lr, 2),
                'stability_score': round(stability_score, 2),
                'lsi_status': lsi_status,
                'rsi_status': rsi_status,
                'lr_status': lr_status,
                'overall_status': overall_status,
                'analysis_type': 'cooling'
            },
            'recommendations': recommendations
        })
            
    except Exception as e:
        return Response({
            'error': f'Calculation error: {str(e)}'
        }, status=status.HTTP_400_BAD_REQUEST)

# Debug view to test which endpoint is being hit
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def debug_login_view(request):
    """Debug view to see which endpoint is being hit and what data is received."""

    
    return Response({
        'message': 'Debug view called',
        'method': request.method,
        'path': request.path,
        'data': request.data,
        'content_type': request.content_type
    })
