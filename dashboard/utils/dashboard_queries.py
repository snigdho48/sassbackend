"""
Raw SQL queries for fast dashboard data retrieval.
All queries are optimized for performance using raw SQL.
Supports all three user levels: Super Admin, Admin, General User
"""
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from collections import defaultdict


def _get_db_vendor():
    """Get database vendor name."""
    return connection.vendor


def get_dashboard_kpis(user):
    """
    Get dashboard KPIs (Total Entries, Analytics Score) using raw SQL.
    Returns: dict with total_entries, analytics_score, and their changes
    Supports all three user levels: Super Admin, Admin, General User
    """
    vendor = _get_db_vendor()
    is_super_admin = user.can_create_plants  # Super Admin can create plants
    
    with connection.cursor() as cursor:
        # Get total entries count
        if is_super_admin:
            # Super Admin sees all data
            cursor.execute("""
                SELECT COUNT(*) as total_entries
                FROM data_entry_wateranalysis
            """)
        elif user.role == 'admin':
            # Admin sees data for accessible plants/water systems
            cursor.execute("""
                SELECT COUNT(DISTINCT wa.id) as total_entries
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_plant_owners po ON p.id = po.plant_id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE (po.customuser_id = %s OR wsau.customuser_id = %s OR p.owner_id = %s)
            """, [user.id, user.id, user.id])
        else:
            # General User sees their own analyses and assigned water systems
            cursor.execute("""
                SELECT COUNT(DISTINCT wa.id) as total_entries
                FROM data_entry_wateranalysis wa
                LEFT JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE (wa.user_id = %s OR wsau.customuser_id = %s)
            """, [user.id, user.id])
        
        total_entries = cursor.fetchone()[0]
        
        # Get total entries from previous period (30 days ago)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        if is_super_admin:
            cursor.execute("""
                SELECT COUNT(*) as prev_total_entries
                FROM data_entry_wateranalysis
                WHERE created_at < %s
            """, [thirty_days_ago])
        elif user.role == 'admin':
            cursor.execute("""
                SELECT COUNT(DISTINCT wa.id) as prev_total_entries
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_plant_owners po ON p.id = po.plant_id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.created_at < %s
                    AND (po.customuser_id = %s OR wsau.customuser_id = %s OR p.owner_id = %s)
            """, [thirty_days_ago, user.id, user.id, user.id])
        else:
            cursor.execute("""
                SELECT COUNT(DISTINCT wa.id) as prev_total_entries
                FROM data_entry_wateranalysis wa
                LEFT JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.created_at < %s
                    AND (wa.user_id = %s OR wsau.customuser_id = %s)
            """, [thirty_days_ago, user.id, user.id])
        
        prev_total_entries = cursor.fetchone()[0] or 0
        entries_change = ((total_entries - prev_total_entries) / prev_total_entries * 100) if prev_total_entries > 0 else 0
        
        # Calculate analytics score (average stability_score)
        if is_super_admin:
            cursor.execute("""
                SELECT AVG(stability_score) as avg_score
                FROM data_entry_wateranalysis
                WHERE stability_score IS NOT NULL
            """)
        elif user.role == 'admin':
            cursor.execute("""
                SELECT AVG(wa.stability_score) as avg_score
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_plant_owners po ON p.id = po.plant_id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.stability_score IS NOT NULL
                    AND (po.customuser_id = %s OR wsau.customuser_id = %s OR p.owner_id = %s)
            """, [user.id, user.id, user.id])
        else:
            cursor.execute("""
                SELECT AVG(wa.stability_score) as avg_score
                FROM data_entry_wateranalysis wa
                LEFT JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.stability_score IS NOT NULL
                    AND (wa.user_id = %s OR wsau.customuser_id = %s)
            """, [user.id, user.id])
        
        result = cursor.fetchone()
        analytics_score = float(result[0]) if result[0] else 0.0
        
        # Get previous period analytics score
        if is_super_admin:
            cursor.execute("""
                SELECT AVG(stability_score) as prev_avg_score
                FROM data_entry_wateranalysis
                WHERE stability_score IS NOT NULL AND created_at < %s
            """, [thirty_days_ago])
        elif user.role == 'admin':
            cursor.execute("""
                SELECT AVG(wa.stability_score) as prev_avg_score
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_plant_owners po ON p.id = po.plant_id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.stability_score IS NOT NULL AND wa.created_at < %s
                    AND (po.customuser_id = %s OR wsau.customuser_id = %s OR p.owner_id = %s)
            """, [thirty_days_ago, user.id, user.id, user.id])
        else:
            cursor.execute("""
                SELECT AVG(wa.stability_score) as prev_avg_score
                FROM data_entry_wateranalysis wa
                LEFT JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.stability_score IS NOT NULL AND wa.created_at < %s
                    AND (wa.user_id = %s OR wsau.customuser_id = %s)
            """, [thirty_days_ago, user.id, user.id])
        
        prev_result = cursor.fetchone()
        prev_analytics_score = float(prev_result[0]) if prev_result and prev_result[0] else 0.0
        score_change = ((analytics_score - prev_analytics_score) / prev_analytics_score * 100) if prev_analytics_score > 0 else 0
        
        return {
            'total_entries': total_entries,
            'total_entries_change': round(entries_change, 1),
            'analytics_score': round(analytics_score, 1),
            'analytics_score_change': round(score_change, 1)
        }


def get_system_hierarchy(user):
    """
    Get system hierarchy (Cooling Tower and Boiler systems) using raw SQL.
    Returns: dict with cooling_tower and boiler hierarchies
    Supports all three user levels: Super Admin, Admin, General User
    """
    vendor = _get_db_vendor()
    is_super_admin = user.can_create_plants  # Super Admin can create plants
    
    with connection.cursor() as cursor:
        # Get cooling tower systems
        if is_super_admin:
            # Super Admin sees all systems
            cursor.execute("""
                SELECT 
                    ws.id,
                    ws.name,
                    p.name as plant_name,
                    COUNT(wa.id) as analysis_count
                FROM data_entry_watersystem ws
                INNER JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_wateranalysis wa ON wa.water_system_id = ws.id
                WHERE ws.system_type = 'cooling' AND ws.is_active = 1
                GROUP BY ws.id, ws.name, p.name
                ORDER BY p.name, ws.name
            """)
        elif user.role == 'admin':
            # Admin sees systems for accessible plants/water systems
            cursor.execute("""
                SELECT DISTINCT
                    ws.id,
                    ws.name,
                    p.name as plant_name,
                    COUNT(wa.id) as analysis_count
                FROM data_entry_watersystem ws
                INNER JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_wateranalysis wa ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_plant_owners po ON p.id = po.plant_id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE ws.system_type = 'cooling' 
                    AND ws.is_active = 1
                    AND (po.customuser_id = %s OR wsau.customuser_id = %s OR p.owner_id = %s)
                GROUP BY ws.id, ws.name, p.name
                ORDER BY p.name, ws.name
            """, [user.id, user.id, user.id])
        else:
            # General User sees assigned water systems AND systems where they created analyses
            cursor.execute("""
                SELECT DISTINCT
                    ws.id,
                    ws.name,
                    p.name as plant_name,
                    COUNT(wa.id) as analysis_count
                FROM data_entry_watersystem ws
                INNER JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_wateranalysis wa ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE ws.system_type = 'cooling' 
                    AND ws.is_active = 1
                    AND (wsau.customuser_id = %s OR wa.user_id = %s)
                GROUP BY ws.id, ws.name, p.name
                ORDER BY p.name, ws.name
            """, [user.id, user.id])
        
        cooling_towers = []
        for row in cursor.fetchall():
            cooling_towers.append({
                'id': row[0],
                'name': row[1],
                'plant_name': row[2],
                'analysis_count': row[3]
            })
        
        # Get boiler systems
        if is_super_admin:
            # Super Admin sees all systems
            cursor.execute("""
                SELECT 
                    ws.id,
                    ws.name,
                    p.name as plant_name,
                    COUNT(wa.id) as analysis_count
                FROM data_entry_watersystem ws
                INNER JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_wateranalysis wa ON wa.water_system_id = ws.id
                WHERE ws.system_type = 'boiler' AND ws.is_active = 1
                GROUP BY ws.id, ws.name, p.name
                ORDER BY p.name, ws.name
            """)
        elif user.role == 'admin':
            # Admin sees systems for accessible plants/water systems
            cursor.execute("""
                SELECT DISTINCT
                    ws.id,
                    ws.name,
                    p.name as plant_name,
                    COUNT(wa.id) as analysis_count
                FROM data_entry_watersystem ws
                INNER JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_wateranalysis wa ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_plant_owners po ON p.id = po.plant_id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE ws.system_type = 'boiler' 
                    AND ws.is_active = 1
                    AND (po.customuser_id = %s OR wsau.customuser_id = %s OR p.owner_id = %s)
                GROUP BY ws.id, ws.name, p.name
                ORDER BY p.name, ws.name
            """, [user.id, user.id, user.id])
        else:
            # General User sees assigned water systems AND systems where they created analyses
            cursor.execute("""
                SELECT DISTINCT
                    ws.id,
                    ws.name,
                    p.name as plant_name,
                    COUNT(wa.id) as analysis_count
                FROM data_entry_watersystem ws
                INNER JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_wateranalysis wa ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE ws.system_type = 'boiler' 
                    AND ws.is_active = 1
                    AND (wsau.customuser_id = %s OR wa.user_id = %s)
                GROUP BY ws.id, ws.name, p.name
                ORDER BY p.name, ws.name
            """, [user.id, user.id])
        
        boilers = []
        for row in cursor.fetchall():
            boilers.append({
                'id': row[0],
                'name': row[1],
                'plant_name': row[2],
                'analysis_count': row[3]
            })
        
        return {
            'cooling_tower': {
                'systems': cooling_towers,
                'total_count': len(cooling_towers)
            },
            'boiler': {
                'systems': boilers,
                'total_count': len(boilers)
            }
        }


def get_performance_trends(user, system_type, months=6):
    """
    Get performance trends for the last N months using raw SQL.
    Returns: list of monthly data with performance scores
    Supports all three user levels: Super Admin, Admin, General User
    """
    vendor = _get_db_vendor()
    is_super_admin = user.can_create_plants  # Super Admin can create plants
    
    with connection.cursor() as cursor:
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # Use database-specific date formatting
        if vendor == 'sqlite':
            date_format = "strftime('%%Y-%%m', wa.created_at)"
        else:  # mysql, postgresql
            date_format = "DATE_FORMAT(wa.created_at, '%%Y-%%m')"
        
        # Get monthly performance data
        if is_super_admin:
            # Super Admin sees all data
            cursor.execute(f"""
                SELECT 
                    {date_format} as month,
                    AVG(wa.stability_score) as avg_score,
                    COUNT(wa.id) as count
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                WHERE wa.analysis_type = %s
                    AND wa.created_at >= %s
                    AND wa.stability_score IS NOT NULL
                GROUP BY {date_format}
                ORDER BY month
            """, [system_type, start_date])
        elif user.role == 'admin':
            # Admin sees data for accessible plants/water systems
            cursor.execute(f"""
                SELECT 
                    {date_format} as month,
                    AVG(wa.stability_score) as avg_score,
                    COUNT(wa.id) as count
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_plant_owners po ON p.id = po.plant_id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.analysis_type = %s
                    AND wa.created_at >= %s
                    AND wa.stability_score IS NOT NULL
                    AND (po.customuser_id = %s OR wsau.customuser_id = %s OR p.owner_id = %s)
                GROUP BY {date_format}
                ORDER BY month
            """, [system_type, start_date, user.id, user.id, user.id])
        else:
            # General User sees only their own data and assigned water systems
            cursor.execute(f"""
                SELECT 
                    {date_format} as month,
                    AVG(wa.stability_score) as avg_score,
                    COUNT(wa.id) as count
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.analysis_type = %s
                    AND wa.created_at >= %s
                    AND wa.stability_score IS NOT NULL
                    AND (wa.user_id = %s OR wsau.customuser_id = %s)
                GROUP BY {date_format}
                ORDER BY month
            """, [system_type, start_date, user.id, user.id])
        
        # Convert to dict for easy lookup
        monthly_data = {}
        for row in cursor.fetchall():
            monthly_data[row[0]] = {
                'score': float(row[1]) if row[1] else 0.0,
                'count': row[2]
            }
        
        # Generate complete monthly list for the last N months
        trends = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i in range(months):
            date = end_date - timedelta(days=i * 30)
            month_key = date.strftime('%Y-%m')
            month_name = month_names[date.month - 1]
            
            if month_key in monthly_data:
                trends.append({
                    'name': month_name,
                    'score': round(monthly_data[month_key]['score'], 1)
                })
            else:
                trends.append({
                    'name': month_name,
                    'score': 0.0
                })
        
        # Reverse to show oldest to newest
        trends.reverse()
        return trends


def get_parameter_trends(user, system_type, parameter_name, months=6):
    """
    Get trend data for a specific parameter using raw SQL.
    Returns: list of monthly average values for the parameter
    Supports all three user levels: Super Admin, Admin, General User
    """
    vendor = _get_db_vendor()
    is_super_admin = user.can_create_plants  # Super Admin can create plants
    
    with connection.cursor() as cursor:
        # Map parameter names to database columns
        param_map = {
            'cooling': {
                'ph': 'ph',
                'tds': 'tds',
                'hardness': 'hardness',
                'm_alkalinity': 'total_alkalinity',
                'lsi': 'lsi',
                'rsi': 'rsi'
            },
            'boiler': {
                'ph': 'ph',
                'tds': 'tds',
                'hardness': 'hardness',
                'm_alkalinity': 'm_alkalinity',
                'p_alkalinity': 'p_alkalinity',
                'oh_alkalinity': 'oh_alkalinity'
            }
        }
        
        if system_type not in param_map or parameter_name not in param_map[system_type]:
            return []
        
        db_column = param_map[system_type][parameter_name]
        
        # Calculate date range
        end_date = timezone.now()
        start_date = end_date - timedelta(days=months * 30)
        
        # Use database-specific date formatting
        if vendor == 'sqlite':
            date_format = "strftime('%%Y-%%m', wa.created_at)"
        else:  # mysql, postgresql
            date_format = "DATE_FORMAT(wa.created_at, '%%Y-%%m')"
        
        # Get monthly parameter averages
        if is_super_admin:
            # Super Admin sees all data
            cursor.execute(f"""
                SELECT 
                    {date_format} as month,
                    AVG(wa.{db_column}) as avg_value
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                WHERE wa.analysis_type = %s
                    AND wa.created_at >= %s
                    AND wa.{db_column} IS NOT NULL
                GROUP BY {date_format}
                ORDER BY month
            """, [system_type, start_date])
        elif user.role == 'admin':
            # Admin sees data for accessible plants/water systems
            cursor.execute(f"""
                SELECT 
                    {date_format} as month,
                    AVG(wa.{db_column}) as avg_value
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_plant p ON ws.plant_id = p.id
                LEFT JOIN data_entry_plant_owners po ON p.id = po.plant_id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.analysis_type = %s
                    AND wa.created_at >= %s
                    AND wa.{db_column} IS NOT NULL
                    AND (po.customuser_id = %s OR wsau.customuser_id = %s OR p.owner_id = %s)
                GROUP BY {date_format}
                ORDER BY month
            """, [system_type, start_date, user.id, user.id, user.id])
        else:
            # General User sees only their own data and assigned water systems
            cursor.execute(f"""
                SELECT 
                    {date_format} as month,
                    AVG(wa.{db_column}) as avg_value
                FROM data_entry_wateranalysis wa
                INNER JOIN data_entry_watersystem ws ON wa.water_system_id = ws.id
                LEFT JOIN data_entry_watersystem_assigned_users wsau ON ws.id = wsau.watersystem_id
                WHERE wa.analysis_type = %s
                    AND wa.created_at >= %s
                    AND wa.{db_column} IS NOT NULL
                    AND (wa.user_id = %s OR wsau.customuser_id = %s)
                GROUP BY {date_format}
                ORDER BY month
            """, [system_type, start_date, user.id, user.id])
        
        # Convert to dict
        monthly_data = {}
        for row in cursor.fetchall():
            monthly_data[row[0]] = float(row[1]) if row[1] else 0.0
        
        # Generate complete monthly list
        trends = []
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        for i in range(months):
            date = end_date - timedelta(days=i * 30)
            month_key = date.strftime('%Y-%m')
            month_name = month_names[date.month - 1]
            
            if month_key in monthly_data:
                trends.append({
                    'name': month_name,
                    'value': round(monthly_data[month_key], 2)
                })
            else:
                trends.append({
                    'name': month_name,
                    'value': 0.0
                })
        
        trends.reverse()
        return trends
