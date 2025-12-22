"""
Raw SQL queries for fast report data retrieval.
All queries are optimized for performance using raw SQL.
"""
from django.db import connection
from django.utils import timezone
from datetime import datetime, timedelta
from data_entry.models import WaterAnalysis, WaterSystem


def get_report_analyses_raw(user, water_system_id, analysis_type, start_date, end_date):
    """
    Get water analyses for report generation using raw SQL.
    Returns queryset-like list that can be converted to WaterAnalysis objects.
    """
    vendor = connection.vendor
    
    with connection.cursor() as cursor:
        # Build the base query
        base_query = """
            SELECT 
                wa.id,
                wa.user_id,
                wa.plant_id,
                wa.water_system_id,
                wa.analysis_name,
                wa.analysis_date,
                wa.analysis_type,
                wa.ph,
                wa.tds,
                wa.hardness,
                wa.total_alkalinity,
                wa.chloride,
                wa.temperature,
                wa.basin_temperature,
                wa.sulphate,
                wa.cycle,
                wa.iron,
                wa.phosphate,
                wa.m_alkalinity,
                wa.p_alkalinity,
                wa.oh_alkalinity,
                wa.sulphite,
                wa.sodium_chloride,
                wa.do,
                wa.boiler_phosphate,
                wa.lsi,
                wa.rsi,
                wa.psi,
                wa.lr,
                wa.stability_score,
                wa.lsi_status,
                wa.rsi_status,
                wa.psi_status,
                wa.lr_status,
                wa.overall_status,
                wa.notes,
                wa.created_at,
                wa.updated_at
            FROM data_entry_wateranalysis wa
            WHERE wa.water_system_id = %s
                AND wa.analysis_type = %s
                AND wa.analysis_date >= %s
                AND wa.analysis_date <= %s
        """
        
        params = [water_system_id, analysis_type, start_date, end_date]
        
        # Add user filter if not admin/staff
        if not user.is_staff:
            base_query += " AND wa.user_id = %s"
            params.append(user.id)
        
        # Add ordering
        base_query += " ORDER BY wa.analysis_date ASC"
        
        cursor.execute(base_query, params)
        
        # Fetch all results
        columns = [col[0] for col in cursor.description]
        rows = cursor.fetchall()
        
        # Convert rows to dictionaries
        analyses_data = []
        for row in rows:
            analysis_dict = dict(zip(columns, row))
            analyses_data.append(analysis_dict)
        
        # Convert to WaterAnalysis objects for compatibility
        # We'll create a list that can be used like a queryset
        analyses = []
        for data in analyses_data:
            # Get the WaterAnalysis object by ID to ensure all relationships work
            try:
                analysis = WaterAnalysis.objects.get(id=data['id'])
                analyses.append(analysis)
            except WaterAnalysis.DoesNotExist:
                # If not found, create a temporary instance (shouldn't happen)
                continue
        
        return analyses


def get_water_system_raw(water_system_id):
    """
    Get water system using raw SQL for faster access.
    """
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT 
                ws.id,
                ws.plant_id,
                ws.name,
                ws.system_type,
                ws.is_active,
                ws.cooling_ph_min,
                ws.cooling_ph_max,
                ws.cooling_tds_min,
                ws.cooling_tds_max,
                ws.cooling_hardness_max,
                ws.cooling_alkalinity_max,
                ws.cooling_total_alkalinity_min,
                ws.cooling_total_alkalinity_max,
                ws.cooling_temperature_min,
                ws.cooling_temperature_max,
                ws.cooling_hot_temperature_min,
                ws.cooling_hot_temperature_max,
                ws.cooling_chloride_max,
                ws.cooling_chloride_enabled,
                ws.cooling_cycle_min,
                ws.cooling_cycle_max,
                ws.cooling_cycle_enabled,
                ws.cooling_iron_max,
                ws.cooling_iron_enabled,
                ws.cooling_phosphate_max,
                ws.cooling_phosphate_enabled,
                ws.cooling_lsi_min,
                ws.cooling_lsi_max,
                ws.cooling_lsi_enabled,
                ws.cooling_rsi_min,
                ws.cooling_rsi_max,
                ws.cooling_rsi_enabled,
                ws.boiler_ph_min,
                ws.boiler_ph_max,
                ws.boiler_tds_min,
                ws.boiler_tds_max,
                ws.boiler_hardness_max,
                ws.boiler_alkalinity_min,
                ws.boiler_alkalinity_max,
                ws.boiler_p_alkalinity_min,
                ws.boiler_p_alkalinity_max,
                ws.boiler_p_alkalinity_enabled,
                ws.boiler_oh_alkalinity_min,
                ws.boiler_oh_alkalinity_max,
                ws.boiler_oh_alkalinity_enabled,
                ws.boiler_sulphite_min,
                ws.boiler_sulphite_max,
                ws.boiler_sulphite_enabled,
                ws.boiler_sodium_chloride_max,
                ws.boiler_sodium_chloride_enabled,
                ws.boiler_do_min,
                ws.boiler_do_max,
                ws.boiler_do_enabled,
                ws.boiler_phosphate_min,
                ws.boiler_phosphate_max,
                ws.boiler_phosphate_enabled,
                ws.boiler_iron_max,
                ws.boiler_iron_enabled,
                ws.created_at,
                ws.updated_at
            FROM data_entry_watersystem ws
            WHERE ws.id = %s AND ws.is_active = 1
        """, [water_system_id])
        
        row = cursor.fetchone()
        if not row:
            return None
        
        columns = [col[0] for col in cursor.description]
        system_dict = dict(zip(columns, row))
        
        # Get the WaterSystem object by ID to ensure all relationships work
        try:
            water_system = WaterSystem.objects.get(id=system_dict['id'])
            return water_system
        except WaterSystem.DoesNotExist:
            return None


def check_water_system_access_raw(user, water_system_id):
    """
    Check if user has access to water system using raw SQL.
    Returns True if user has access, False otherwise.
    """
    with connection.cursor() as cursor:
        # Check if user is admin/staff
        if user.is_staff:
            return True
        
        # For general users, check assigned_users
        if user.is_general_user:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM data_entry_watersystem_assigned_users wsau
                WHERE wsau.watersystem_id = %s AND wsau.customuser_id = %s
            """, [water_system_id, user.id])
            return cursor.fetchone()[0] > 0
        
        # For admin users, check both water system assignment and plant ownership
        # Note: ManyToMany table uses customuser_id, not user_id
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT wsau.customuser_id) as ws_access,
                COUNT(DISTINCT po.customuser_id) as plant_owner_access,
                COUNT(DISTINCT p.owner_id) as plant_legacy_owner
            FROM data_entry_watersystem ws
            LEFT JOIN data_entry_watersystem_assigned_users wsau 
                ON ws.id = wsau.watersystem_id AND wsau.customuser_id = %s
            LEFT JOIN data_entry_plant p ON ws.plant_id = p.id
            LEFT JOIN data_entry_plant_owners po ON p.id = po.plant_id AND po.customuser_id = %s
            WHERE ws.id = %s
                AND (wsau.customuser_id = %s OR po.customuser_id = %s OR p.owner_id = %s)
        """, [user.id, user.id, water_system_id, user.id, user.id, user.id])
        
        result = cursor.fetchone()
        return result[0] > 0 or result[1] > 0 or result[2] > 0

