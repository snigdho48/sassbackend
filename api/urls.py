from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', views.LoginView.as_view(), name='api_login'),
    path('auth/register/', views.RegisterView.as_view(), name='api_register'),
    path('auth/logout/', views.logout_view, name='api_logout'),
    path('auth/token/', views.CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/check/', views.check_auth_view, name='api_check_auth'),
    
    # User profile endpoints
    path('auth/profile/', views.UserProfileView.as_view(), name='api_profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='api_change_password'),
    
    # Data management endpoints
    path('categories/', views.DataCategoryViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_categories'),
    path('categories/<int:pk>/', views.DataCategoryViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='api_category_detail'),
    path('data/', views.TechnicalDataViewSet.as_view({'get': 'list', 'post': 'create'}), name='api_data'),
    path('data/<int:pk>/', views.TechnicalDataViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='api_data_detail'),
    path('analytics/', views.AnalyticsView.as_view(), name='api_analytics'),
    path('dashboard/', views.DashboardDataView.as_view(), name='api_dashboard'),
    
    # Report endpoints
    path('reports/', views.ReportsListView.as_view(), name='api_reports'),
    path('reports/generate/', views.ReportGenerationView.as_view(), name='api_generate_report'),
    path('reports/<int:pk>/download/', views.ReportDownloadView.as_view(), name='api_report_download'),
    
    # Admin endpoints
    path('admin/users/', views.AdminUserManagementView.as_view(), name='api_admin_users'),
    path('admin/users/<int:user_id>/', views.AdminUserDetailView.as_view(), name='api_admin_user_detail'),
    path('admin/usage/', views.APIUsageView.as_view(), name='api_usage'),
    
    # Test endpoint
    path('test/', views.test_api_view, name='api_test'),
    
    # Water Analysis endpoints
    path('water-analysis/', views.WaterAnalysisViewSet.as_view({'get': 'list', 'post': 'create'}), name='water_analysis'),
    path('water-analysis/<int:pk>/', views.WaterAnalysisViewSet.as_view({'get': 'retrieve', 'put': 'update', 'delete': 'destroy'}), name='water_analysis_detail'),
    path('water-trends/', views.water_trends_view, name='water_trends'),
    path('water-recommendations/', views.water_recommendations_view, name='water_recommendations'),
    path('calculate-water-analysis/', views.calculate_water_analysis_view, name='calculate_water_analysis'),
    
    # Custom Swagger UI
] 