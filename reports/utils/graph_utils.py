"""
Graph Utilities for Report Generation
Reusable components for generating trend graphs and analyzing parameter trends
"""
from io import BytesIO
from datetime import datetime
import base64
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.figure import Figure
from matplotlib.ticker import FixedLocator


def parse_recommended_range(range_str):
    """Parse recommended range string into min/max values"""
    if not range_str:
        return None
    
    range_str = str(range_str).strip()
    
    # Handle ranges like "6.5 - 7.8"
    if ' - ' in range_str or '-' in range_str:
        parts = range_str.replace(' - ', '-').split('-')
        if len(parts) == 2:
            try:
                min_val = float(parts[0].strip())
                max_val = float(parts[1].strip().replace(' ppm', '').replace(' ppm', ''))
                return {'min': min_val, 'max': max_val}
            except ValueError:
                pass
    
    # Handle "< 300 ppm" or "Min 600 ppm"
    if range_str.startswith('<'):
        try:
            max_val = float(range_str.replace('<', '').replace('ppm', '').strip())
            return {'max': max_val}
        except ValueError:
            pass
    
    if range_str.startswith('Min'):
        try:
            min_val = float(range_str.replace('Min', '').replace('ppm', '').strip())
            return {'min': min_val}
        except ValueError:
            pass
    
    # Handle single value like "0"
    try:
        val = float(range_str)
        return {'min': val - 0.5, 'max': val + 0.5}
    except ValueError:
        pass
    
    return None


def generate_trend_graph(param_name, dates, values, recommended_range, param_key):
    """
    Generate a trend graph for a parameter and return as base64 PNG
    
    Args:
        param_name: Name of the parameter (e.g., 'pH', 'TDS')
        dates: List of datetime objects for x-axis
        values: List of numeric values for y-axis
        recommended_range: String representation of recommended range (e.g., '6.5 - 7.8')
        param_key: Parameter key for identification
    
    Returns:
        Base64-encoded PNG image string or None if generation fails
    """
    try:
        if not values or not dates or len(values) == 0:
            return None
        
        # Filter out None values
        valid_data = [(d, v) for d, v in zip(dates, values) if v is not None]
        if not valid_data:
            return None
        
        valid_dates, valid_values = zip(*valid_data)
        
        # Create figure with larger height and transparent background
        fig = Figure(figsize=(6, 4.5), facecolor='none')
        ax = fig.add_subplot(111)
        ax.set_facecolor('none')
        
        # Plot actual values
        ax.plot(valid_dates, valid_values, 'b-', linewidth=2, marker='o', markersize=4, label='Actual')
        
        # Parse and plot recommended range
        range_dict = parse_recommended_range(recommended_range)
        if range_dict:
            min_val = range_dict.get('min')
            max_val = range_dict.get('max')
            
            if min_val is not None and max_val is not None:
                # Draw horizontal lines for min and max
                ax.axhline(y=min_val, color='g', linestyle='--', linewidth=1.5, label='Recommended Range', alpha=0.7)
                ax.axhline(y=max_val, color='g', linestyle='--', linewidth=1.5, alpha=0.7)
                # Fill between min and max
                ax.axhspan(min_val, max_val, alpha=0.1, color='green')
            elif max_val is not None:
                ax.axhline(y=max_val, color='g', linestyle='--', linewidth=1.5, label='Recommended Max', alpha=0.7)
            elif min_val is not None:
                ax.axhline(y=min_val, color='g', linestyle='--', linewidth=1.5, label='Recommended Min', alpha=0.7)
        
        # Format x-axis dates - adjust based on date range and data points
        date_span = (max(valid_dates) - min(valid_dates)).days if len(valid_dates) > 1 else 0
        num_points = len(valid_dates)
        
        # Normalize all dates to first day of month for comparison
        normalized_dates = [d.replace(day=1) if hasattr(d, 'replace') else d for d in valid_dates]
        unique_month_count = len(set(d.strftime('%b %Y') if hasattr(d, 'strftime') else str(d) for d in normalized_dates))
        
        # Determine if this is monthly/yearly data or daily data
        # If we have data spanning multiple months OR few data points spread across months, use monthly format
        is_monthly_data = date_span > 60 or (date_span > 31 and unique_month_count > 1) or (num_points <= 12 and unique_month_count == num_points)
        
        if not is_monthly_data:  # Daily data (within a month)
            # Use daily format for monthly reports
            formatter = mdates.DateFormatter('%d-%m')
            # Use AutoDateLocator with max_ticks to prevent too many ticks
            locator = mdates.AutoDateLocator(maxticks=12)  # Max 12 ticks
        else:  # Monthly or longer data (yearly reports)
            # Use monthly format for yearly reports
            formatter = mdates.DateFormatter('%b %Y')
            # For yearly reports, use only the actual data dates (months with data)
            # This ensures we only show months that have data points
            unique_months = []
            seen_months = set()
            for date in valid_dates:
                # Create a date at the first day of the month
                if hasattr(date, 'replace'):
                    month_start = date.replace(day=1)
                else:
                    # If it's already a datetime, use it directly
                    month_start = date
                month_key = month_start.strftime('%b %Y') if hasattr(month_start, 'strftime') else str(month_start)
                if month_key not in seen_months:
                    seen_months.add(month_key)
                    unique_months.append(month_start)
            
            # Use FixedLocator with only the months that have data
            if unique_months:
                # Convert dates to numeric values for FixedLocator
                unique_months_numeric = [mdates.date2num(d) for d in unique_months]
                locator = FixedLocator(unique_months_numeric)
            else:
                locator = mdates.MonthLocator(interval=1)
        
        # Set formatter first so we can format ticks correctly
        ax.xaxis.set_major_formatter(formatter)
        
        # Set locator to generate tick positions
        ax.xaxis.set_major_locator(locator)
        
        # Format labels and ensure no duplicates (fallback check)
        labels = ax.xaxis.get_majorticklabels()
        seen_label_texts = set()
        for label in labels:
            label_text = label.get_text().strip()
            if label_text:
                if label_text in seen_label_texts:
                    # Hide duplicate
                    label.set_text('')
                    label.set_visible(False)
                else:
                    seen_label_texts.add(label_text)
            label.set_rotation(45)
            label.set_ha('right')
        
        # Labels and title
        if not is_monthly_data:  # Daily data
            ax.set_xlabel('Date', fontsize=9)
        else:  # Monthly or longer
            ax.set_xlabel('Month & Year', fontsize=9)
        ax.set_ylabel('Value', fontsize=9)
        ax.set_title(param_name, fontsize=10, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(fontsize=7, loc='best')
        
        # Save to buffer with transparent background
        buf = BytesIO()
        fig.tight_layout()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', transparent=True, facecolor='none')
        buf.seek(0)
        
        # Convert to base64
        img_base64 = base64.b64encode(buf.read()).decode('utf-8')
        buf.close()
        plt.close(fig)
        
        return f'data:image/png;base64,{img_base64}'
    except Exception as e:
        print(f"Error generating graph for {param_name}: {e}")
        return None


def analyze_trend(param_name, dates, values, recommended_range, param_key):
    """
    Analyze trend and generate interpretation and recommendation
    
    Args:
        param_name: Name of the parameter (e.g., 'pH', 'TDS')
        dates: List of datetime objects
        values: List of numeric values
        recommended_range: String representation of recommended range
        param_key: Parameter key for identification
    
    Returns:
        Tuple of (trend_description, interpretation, recommendation) or (None, None, None) if analysis fails
    """
    if not values or not dates or len(values) == 0:
        return None, None, None
    
    # Filter out None values
    valid_data = [(d, v) for d, v in zip(dates, values) if v is not None]
    if not valid_data:
        return None, None, None
    
    valid_dates, valid_values = list(zip(*valid_data))
    valid_values = list(valid_values)
    
    # Calculate trend direction
    if len(valid_values) >= 2:
        first_half = valid_values[:len(valid_values)//2]
        second_half = valid_values[len(valid_values)//2:]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        trend_direction = "increasing" if avg_second > avg_first * 1.05 else "decreasing" if avg_second < avg_first * 0.95 else "stable"
    else:
        trend_direction = "stable"
    
    # Format trend description
    if len(valid_values) >= 2:
        trend_desc = f"Values range from {min(valid_values):.2f} to {max(valid_values):.2f}"
        if len(valid_values) > 2:
            trend_desc += f", with {trend_direction} trend"
    else:
        trend_desc = f"Value: {valid_values[0]:.2f}"
    
    # Parse recommended range
    range_dict = parse_recommended_range(recommended_range)
    
    # Generate interpretation
    interpretation = ""
    recommendation = ""
    
    if range_dict:
        min_val = range_dict.get('min')
        max_val = range_dict.get('max')
        
        # Check how many values are within range
        if min_val is not None and max_val is not None:
            within_range = sum(1 for v in valid_values if min_val <= v <= max_val)
            out_of_range = len(valid_values) - within_range
            
            if out_of_range == 0:
                interpretation = f"All values are within the optimal range ({min_val:.2f}-{max_val:.2f})."
                recommendation = "Maintain current treatment practices."
            elif out_of_range <= len(valid_values) * 0.3:
                interpretation = f"Most values are within range ({min_val:.2f}-{max_val:.2f}), with some exceptions."
                if param_name.lower() == 'ph':
                    recommendation = "Adjust chemical dosing & blowdown to stabilize pH within the recommended range."
                elif param_name.lower() == 'tds':
                    recommendation = "Improve blowdown control to reduce TDS concentration."
                else:
                    recommendation = f"Adjust treatment to bring values consistently within {min_val:.2f}-{max_val:.2f} range."
            else:
                interpretation = f"Values frequently exceed the optimal range ({min_val:.2f}-{max_val:.2f})."
                if param_name.lower() == 'ph':
                    interpretation += " This indicates potential for scaling and reduced corrosion protection."
                    recommendation = "Adjust chemical dosing & blowdown to stabilize pH within the recommended range."
                elif param_name.lower() == 'tds':
                    interpretation += " High TDS can lead to scaling, fouling, and reduced heat transfer efficiency."
                    recommendation = "Improve blowdown control and water softening."
                elif param_name.lower() in ['lsi', 'rsi']:
                    if param_name.upper() == 'LSI':
                        interpretation += " Positive LSI suggests scaling tendency."
                        recommendation = "Maintain LSI closer to zero to minimize scaling risk."
                    else:  # RSI
                        interpretation += " Values >8 indicate increased corrosion risk."
                        recommendation = "Improve corrosion inhibitor program and water chemistry balance."
                else:
                    recommendation = f"Increase blowdown frequency or adjust chemical dosing to reduce {param_name.lower()}."
        
        elif max_val is not None:
            above_max = sum(1 for v in valid_values if v > max_val)
            if above_max == 0:
                interpretation = f"All values are below the maximum limit ({max_val:.2f})."
                recommendation = "Maintain current treatment practices."
            else:
                interpretation = f"Some values exceed the maximum limit ({max_val:.2f})."
                if param_name.lower() == 'tds':
                    recommendation = "High TDS. Increase blowdown to reduce concentration."
                else:
                    recommendation = f"Reduce {param_name.lower()} to acceptable levels below {max_val:.2f}."
        
        elif min_val is not None:
            below_min = sum(1 for v in valid_values if v < min_val)
            if below_min == 0:
                interpretation = f"All values meet the minimum requirement ({min_val:.2f})."
                recommendation = "Maintain current treatment practices."
            else:
                interpretation = f"Some values are below the minimum requirement ({min_val:.2f})."
                recommendation = f"Increase {param_name.lower()} to acceptable levels above {min_val:.2f}."
    
    # Special handling for LSI and RSI
    if param_name.upper() == 'LSI':
        if not range_dict:
            interpretation = "LSI values indicate scaling tendency when positive (>0.5)."
            recommendation = "Maintain LSI closer to zero to minimize scaling risk."
    elif param_name.upper() == 'RSI':
        if not range_dict:
            interpretation = "Optimal range is 6-8. Values >8 indicate increased corrosion risk."
            recommendation = "Improve corrosion inhibitor program and water chemistry balance."
    
    return trend_desc, interpretation, recommendation

