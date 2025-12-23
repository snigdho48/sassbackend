"""
PDF Report Generator for Water Analysis Reports
Generates Daily, Monthly, and Yearly reports using HTML/CSS and converts to PDF
"""
from io import BytesIO
from datetime import datetime, timedelta
from django.utils import timezone
from django.template.loader import render_to_string
from django.template import Context
from django.conf import settings
import os
import base64

# Set WeasyPrint DLL directory for Windows (if not already set)
# This helps WeasyPrint find required DLLs on Windows
if os.name == 'nt':  # Windows
    dll_dir = os.environ.get('WEASYPRINT_DLL_DIRECTORIES')
    if not dll_dir:
        # Try common MSYS2 installation paths
        possible_paths = [
            r'C:\msys64\mingw64\bin',
            r'C:\msys32\mingw64\bin',
        ]
        for path in possible_paths:
            if os.path.exists(path) and os.path.exists(os.path.join(path, 'libgobject-2.0-0.dll')):
                os.environ['WEASYPRINT_DLL_DIRECTORIES'] = path
                break

import weasyprint
from weasyprint import HTML, CSS

# Import utilities
from reports.utils.graph_utils import generate_trend_graph, analyze_trend, parse_recommended_range
from reports.utils.action_utils import get_suggested_action_with_status


def format_recommended_range(param_key, param_data):
    """Format parameter data into recommended range string"""
    if not param_data:
        return ''
    
    min_val = param_data.get('min')
    max_val = param_data.get('max')
    
    if min_val is not None and max_val is not None:
        return f'{min_val} - {max_val}'
    elif min_val is not None:
        return f'Min {min_val}'
    elif max_val is not None:
        return f'< {max_val}'
    return ''


def get_parameter_info(analysis_type='cooling', water_system=None, analysis=None):
    """Get parameter information based on analysis type and water system enabled parameters"""
    
    # Parameter display info mapping
    param_display_info = {
        'cooling': {
            'ph': ('pH', 'pH meter (HI 2211) + paper'),
            'tds': ('TDS', 'TDS Meter: Eutech 6+'),
            'hardness': ('Total Hardness', 'SM2340 C'),
            'alkalinity': ('M-alkalinity', 'Titration'),
            'total_alkalinity': ('Total Alkalinity', 'Titration'),
            'chloride': ('Chloride', 'Titration with AgNO3'),
            'cycle': ('Cycle', 'Calculation'),
            'iron': ('Iron', 'SM3120 B'),
            'phosphate': ('Phosphate', 'Titration'),
            'temperature': ('Basin Temperature', 'Thermometer'),
            'basin_temperature': ('Basin Temperature', 'Thermometer'),
            'hot_temperature': ('Hot Side Temperature', 'Thermometer'),
            'lsi': ('LSI', 'Proprietary Formula'),
            'rsi': ('RSI', 'Proprietary Formula'),
        },
        'boiler': {
            'ph': ('pH', 'pH meter (HI 2211) + paper'),
            'tds': ('TDS', 'TDS Meter: Eutech 6+'),
            'hardness': ('Total Hardness', 'SM2340 C'),
            'alkalinity': ('M-alkalinity', 'Titration'),
            'p_alkalinity': ('P-alkalinity', 'Titration'),
            'oh_alkalinity': ('OH-alkalinity', 'Calculation'),
            'sulphite': ('Sulphite', 'Titration'),
            'sodium_chloride': ('Sodium Chloride', 'Titration'),
            'do': ('Dissolved Oxygen', 'SM4500-O C'),
            'phosphate': ('Phosphate', 'Titration'),
            'iron': ('Iron', 'SM3120 B'),
        }
    }
    
    parameters = []
    added_params = set()  # Track which parameters we've already added
    
    # Appearance removed - not needed in reports
    
    # Get enabled parameters from water system (initialize outside if block for scope)
    enabled_params = {}
    if water_system:
        if analysis_type == 'cooling':
            enabled_params = water_system.get_cooling_parameters()
        else:
            enabled_params = water_system.get_boiler_parameters()
    
    # Get display info for this analysis type
    display_info = param_display_info.get(analysis_type, {})
    
    # Add enabled parameters in a logical order (if water system exists)
    if water_system:
        # Core parameters first (always shown if water_system has them configured)
        core_params = ['ph', 'tds', 'hardness', 'alkalinity', 'total_alkalinity']
        for param_key in core_params:
            if param_key in enabled_params:
                param_data = enabled_params[param_key]
                if param_key in display_info:
                    name, method = display_info[param_key]
                    recommended = format_recommended_range(param_key, param_data)
                    # Store as (name, method, recommended, param_key) for value retrieval
                    parameters.append((name, method, recommended, param_key))
                    added_params.add(param_key)
        
        # Optional parameters (only if enabled)
        optional_params = {
            'cooling': ['chloride', 'cycle', 'iron', 'phosphate', 'basin_temperature', 'hot_temperature', 'temperature', 'lsi', 'rsi'],
            'boiler': ['p_alkalinity', 'oh_alkalinity', 'sulphite', 'sodium_chloride', 'do', 'phosphate', 'iron']
        }
        
        for param_key in optional_params.get(analysis_type, []):
            if param_key in enabled_params:
                param_data = enabled_params[param_key]
                if param_key in display_info:
                    name, method = display_info[param_key]
                    recommended = format_recommended_range(param_key, param_data)
                    # Store as (name, method, recommended, param_key) for value retrieval
                    parameters.append((name, method, recommended, param_key))
                    added_params.add(param_key)
    
    # Also include parameters that have values in the analysis, even if not enabled in water system
    if analysis:
        # Check all possible parameters for cooling/boiler water
        all_possible_params = {
            'cooling': ['ph', 'tds', 'hardness', 'total_alkalinity', 'alkalinity', 'chloride', 'cycle', 'iron', 
                       'phosphate', 'basin_temperature', 'hot_temperature', 'temperature', 'lsi', 'rsi'],
            'boiler': ['ph', 'tds', 'hardness', 'alkalinity', 'm_alkalinity', 'p_alkalinity', 'oh_alkalinity', 
                      'sulphite', 'sodium_chloride', 'do', 'phosphate', 'iron']
        }
        
        for param_key in all_possible_params.get(analysis_type, []):
            # Skip if already added
            if param_key in added_params:
                continue
            
            # Check if this parameter has a value in the analysis
            value = get_analysis_value(analysis, param_key)
            if value is not None:
                # Add it to the parameters list
                if param_key in display_info:
                    name, method = display_info[param_key]
                    # ALWAYS check if parameter is in enabled_params first to use configured ranges
                    if water_system and param_key in enabled_params:
                        # Use configured range from water system
                        param_data = enabled_params[param_key]
                        recommended = format_recommended_range(param_key, param_data)
                    else:
                        # Only use default ranges if parameter is NOT configured in water system
                        if analysis_type == 'cooling':
                            default_ranges = {
                                'ph': '6.5 - 7.8',
                                'tds': '500 - 800 ppm',
                                'hardness': '< 300 ppm',
                                'total_alkalinity': 'Variable',
                                'alkalinity': '< 300 ppm',
                                'chloride': '< 250 ppm',
                                'cycle': 'Variable',
                                'iron': '< 0.3 ppm',
                                'phosphate': 'Variable',
                                'basin_temperature': 'Variable',
                                'hot_temperature': 'Variable',
                                'temperature': 'Variable',
                            }
                        else:
                            default_ranges = {
                                'ph': '11.0 - 12.0',
                                'tds': '<3500 ppm',
                                'hardness': '8 - 12 ppm',
                                'alkalinity': 'Min 600 ppm',
                                'm_alkalinity': 'Min 600 ppm',
                                'p_alkalinity': 'Variable',
                                'oh_alkalinity': 'Variable',
                                'sulphite': 'Variable',
                                'sodium_chloride': '<5 ppm',
                                'do': '<0.007 ppm',
                                'phosphate': 'Variable',
                                'iron': '<0.3 ppm',
                            }
                        recommended = default_ranges.get(param_key, 'N/A')
                    
                    parameters.append((name, method, recommended, param_key))
                    added_params.add(param_key)
    else:
        # Fallback to default parameters if no water_system provided
        if analysis_type == 'cooling':
            parameters.extend([
                ('pH', 'pH meter (HI 2211) + paper', '6.5 - 7.8', 'ph'),
                ('TDS', 'TDS Meter: Eutech 6+', '500 - 800 ppm', 'tds'),
                ('Total Hardness', 'SM2340 C', '< 300 ppm', 'hardness'),
                ('Chloride', 'Titration with AgNO3', '< 250 ppm', 'chloride'),
                ('M-alkalinity', 'Titration', '< 300 ppm', 'alkalinity'),
                ('LSI', 'Proprietary Formula', '0', 'lsi'),
                ('RSI', 'Proprietary Formula', '6 - 8', 'rsi'),
            ])
        else:  # boiler
            parameters.extend([
                ('pH', 'pH meter (HI 2211) + paper', '11.0 - 12.0', 'ph'),
                ('TDS', 'TDS Meter: Eutech 6+', '<3500 ppm', 'tds'),
                ('Total Hardness', 'SM2340 C', '8 - 12 ppm', 'hardness'),
                ('Chloride', 'Titration with AgNO3', '<5 ppm', 'chloride'),
                ('M-alkalinity', 'Titration', 'Min 600 ppm', 'alkalinity'),
            ])
    
    return {'parameters': parameters}


def get_analysis_value(analysis, param_key):
    """Get analysis value for a parameter"""
    if not analysis:
        return None
    
    # Map parameter keys to model fields
    param_mapping = {
        'ph': 'ph',
        'tds': 'tds',
        'total_hardness': 'hardness',
        'hardness': 'hardness',
        'chloride': 'chloride',
        'm_alkalinity': 'm_alkalinity',
        'alkalinity': 'm_alkalinity',  # M-alkalinity
        'total_alkalinity': 'total_alkalinity',  # Total Alkalinity for cooling water
        'p_alkalinity': 'p_alkalinity',
        'oh_alkalinity': 'oh_alkalinity',
        'lsi': 'lsi',
        'rsi': 'rsi',
        'cycle': 'cycle',
        'iron': 'iron',
        'phosphate': 'phosphate',
        'sulphite': 'sulphite',
        'sodium_chloride': 'sodium_chloride',
        'do': 'do',
        'dissolved_oxygen': 'do',
        'temperature': 'basin_temperature',  # Frontend 'temperature' maps to 'basin_temperature' in model
        'basin_temperature': 'basin_temperature',  # Basin Temperature for cooling water
        'hot_temperature': 'temperature',  # Frontend 'hot_temperature' maps to 'temperature' in model (Hot Side Temperature)
    }
    
    field_name = param_mapping.get(param_key.lower().replace('-', '_').replace(' ', '_'))
    if field_name:
        return getattr(analysis, field_name, None)
    return None


def get_logo_base64():
    """Get logo as base64 string for embedding in PDF"""
    try:
        # Try to find logo - prioritize backend reports folder
        logo_paths = [
            os.path.join(settings.BASE_DIR, 'reports', 'logo.png'),  # Backend reports folder
            os.path.join(settings.BASE_DIR, '..', 'sass-frontend', 'public', 'logo.png'),  # Frontend public folder
            os.path.join(settings.BASE_DIR, 'static', 'logo.png'),
            os.path.join(settings.STATIC_ROOT, 'logo.png') if hasattr(settings, 'STATIC_ROOT') else None,
        ]
        
        for logo_path in logo_paths:
            if logo_path and os.path.exists(logo_path):
                with open(logo_path, 'rb') as logo_file:
                    logo_data = logo_file.read()
                    logo_base64 = base64.b64encode(logo_data).decode('utf-8')
                    return f'data:image/png;base64,{logo_base64}'
        
        # If logo not found, return None (will show text instead)
        return None
    except Exception as e:
        print(f"Error loading logo: {e}")
        return None


def get_icon_base64():
    """Get icon as base64 string for watermark in PDF"""
    try:
        # Try to find icon - prioritize backend reports folder
        icon_paths = [
            os.path.join(settings.BASE_DIR, 'reports', 'icon.png'),  # Backend reports folder
            os.path.join(settings.BASE_DIR, '..', 'sass-frontend', 'public', 'icon.png'),  # Frontend public folder
            os.path.join(settings.BASE_DIR, 'static', 'icon.png'),
            os.path.join(settings.STATIC_ROOT, 'icon.png') if hasattr(settings, 'STATIC_ROOT') else None,
        ]
        
        for icon_path in icon_paths:
            if icon_path and os.path.exists(icon_path):
                with open(icon_path, 'rb') as icon_file:
                    icon_data = icon_file.read()
                    icon_base64 = base64.b64encode(icon_data).decode('utf-8')
                    return f'data:image/png;base64,{icon_base64}'
        
        # If icon not found, return None
        return None
    except Exception as e:
        print(f"Error loading icon: {e}")
        return None
