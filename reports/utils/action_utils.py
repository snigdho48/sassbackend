"""
Action and Recommendation Utilities for Report Generation
Reusable components for generating suggested actions and recommendations
"""
from .graph_utils import parse_recommended_range


def get_suggested_action_with_status(param_name, value, target_range, analysis_type):
    """
    Get suggested action with status (within range or not)
    
    Args:
        param_name: Name of the parameter (e.g., 'pH', 'TDS')
        value: Current value of the parameter
        target_range: String representation of target range (e.g., '6.5 - 7.8')
        analysis_type: Type of analysis ('cooling' or 'boiler')
    
    Returns:
        Tuple of (action_message, is_within_range) where:
        - action_message: String describing the suggested action
        - is_within_range: Boolean indicating if value is within target range
    """
    if not value or not target_range:
        return 'N/A', True
    
    try:
        value_float = float(value) if not isinstance(value, (int, float)) else value
    except (ValueError, TypeError):
        return 'N/A', True
    
    range_dict = parse_recommended_range(target_range)
    
    if not range_dict:
        return 'Within target range', True
    
    min_val = range_dict.get('min')
    max_val = range_dict.get('max')
    
    # Parameter-specific action messages
    if min_val is not None and max_val is not None:
        if min_val <= value_float <= max_val:
            return 'Within target range', True
        elif value_float < min_val:
            if param_name.lower() == 'ph':
                return 'Adjust chemical dosing & blowdown to bring the pH into range.', False
            elif param_name.lower() == 'tds':
                if value_float < min_val:
                    return 'Value below target range. Increase to {:.2f}-{:.2f} range.'.format(min_val, max_val), False
                else:
                    return 'High TDS. Increase blowdown to reduce concentration.', False
            else:
                return 'Value below target range. Increase to {:.2f}-{:.2f} range.'.format(min_val, max_val), False
        else:
            if param_name.lower() == 'ph':
                return 'Adjust chemical dosing & blowdown to bring the pH into range.', False
            elif param_name.lower() == 'tds':
                return 'High TDS. Increase blowdown to reduce concentration.', False
            else:
                return 'Value above target range. Decrease to {:.2f}-{:.2f} range.'.format(min_val, max_val), False
    elif max_val is not None:
        if value_float <= max_val:
            return 'Within target range', True
        else:
            if param_name.lower() == 'tds':
                return 'High TDS. Increase blowdown to reduce concentration.', False
            else:
                return 'Value exceeds maximum ({:.2f}). Reduce to acceptable level.'.format(max_val), False
    elif min_val is not None:
        if value_float >= min_val:
            return 'Within target range', True
        else:
            return 'Value below minimum ({:.2f}). Increase to acceptable level.'.format(min_val), False
    
    # Special handling for LSI and RSI
    if param_name.upper() == 'LSI':
        if -0.5 <= value_float <= 0.5:
            return 'Within target range', True
        elif value_float < -0.5:
            return 'Value below target range. Increase to -0.50-0.50 range.', False
        else:
            return 'Scaling tendency detected. Review treatment program.', False
    elif param_name.upper() == 'RSI':
        if 6.0 <= value_float <= 8.0:
            return 'Within target range', True
        elif value_float > 8.0:
            return 'Intolerable corrosion tendency', False
        else:
            return 'Scaling tendency detected. Review treatment program.', False
    
    return 'Review parameter', False

