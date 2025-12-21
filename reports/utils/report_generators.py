"""
Report Generators for Water Analysis Reports
Generates Daily, Monthly, and Yearly PDF reports using HTML/CSS
"""
from io import BytesIO
from datetime import datetime
import weasyprint
from weasyprint import HTML

# Import from parent module
from reports.pdf_generator import (
    get_parameter_info,
    get_analysis_value,
    get_logo_base64,
    format_recommended_range
)

# Import utilities
from reports.utils.graph_utils import generate_trend_graph, analyze_trend
from reports.utils.action_utils import get_suggested_action_with_status


def generate_daily_report_pdf(analyses, water_system, analysis_type, report_date):
    """Generate daily report PDF using HTML/CSS"""
    buffer = BytesIO()
    
    # Get the analysis (should be one for daily)
    analysis = analyses.first() if analyses.exists() else None
    
    if not analysis:
        # Return empty PDF
        return buffer
    
    # Get plant and water system names
    plant_name = water_system.plant.name if water_system and water_system.plant else 'N/A'
    water_system_name = water_system.name if water_system else 'N/A'
    project_name = f'{plant_name} - {water_system_name}'
    
    # Get logo
    logo_base64 = get_logo_base64()
    
    # Get parameter info - pass analysis so temperature can be included if it has values
    param_info = get_parameter_info(analysis_type, water_system, analysis)
    primary_color = '#1e40af' if analysis_type == 'cooling' else '#7c3aed'
    
    # Build water analysis table data
    analysis_rows = []
    for param_tuple in param_info['parameters']:
        # Handle both 3-tuple (legacy) and 4-tuple (new) formats
        if len(param_tuple) == 4:
            param_name, method, recommended, param_key = param_tuple
        else:
            param_name, method, recommended = param_tuple
            param_key = param_name.lower().replace('-', '_').replace(' ', '_')
        
        # Skip Appearance
        if param_name == 'Appearance':
            continue
        
        # Use param_key if available, otherwise fallback to param_name
        value = get_analysis_value(analysis, param_key) if param_key else None
        
        # Skip parameters with no value (except for calculated indices like LSI/RSI which might be None)
        # For calculated indices, show them even if None (they'll show as '-')
        # For measured parameters, skip if no value
        if value is None and param_key and param_key not in ['lsi', 'rsi', 'psi', 'lr']:
            continue
        
        value_str = f'{value:.2f}' if value is not None and isinstance(value, (int, float)) else str(value) if value else '-'
        analysis_rows.append({
            'parameter': param_name,
            'method': method,
            'value': value_str,
            'recommended': recommended
        })
    
    # Get recommendations from the analysis (like water analysis page)
    from data_entry.models import WaterRecommendation
    recommendations = WaterRecommendation.objects.filter(analysis=analysis).order_by('-priority', '-created_at')
    
    # If no recommendations exist, fallback to parameter-based suggestions
    if not recommendations.exists():
        # Build suggested action table data as fallback
        action_rows = []
        for param_tuple in param_info['parameters']:
            # Handle both 3-tuple (legacy) and 4-tuple (new) formats
            if len(param_tuple) == 4:
                param_name, method, recommended, param_key = param_tuple
            else:
                param_name, method, recommended = param_tuple
                param_key = param_name.lower().replace('-', '_').replace(' ', '_')
            
            if param_name in ['Appearance']:
                continue
            
            # Use param_key if available, otherwise fallback to param_name
            value = get_analysis_value(analysis, param_key) if param_key else None
            if value is None:
                continue
            
            suggested_action_text, is_within_range = get_suggested_action_with_status(param_name, value, recommended, analysis_type)
            icon = '✓' if is_within_range else '■'
            
            action_rows.append({
                'parameter': param_name,
                'target_range': recommended,
                'current_value': f'{value:.2f}' if isinstance(value, (int, float)) else str(value),
                'suggested_action': suggested_action_text,
                'icon': icon,
                'is_within_range': is_within_range
            })
        use_table_format = True
    else:
        use_table_format = False
    
    # Generate HTML
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 1cm;
            }}
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                font-size: 10pt;
                color: #000;
                line-height: 1.4;
            }}
            .header {{
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }}
            .header-left {{
                flex: 1;
            }}
            .header-right {{
                text-align: right;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 5px;
            }}
            .header-row {{
                margin-bottom: 5px;
            }}
            .header-label {{
                font-weight: normal;
                margin-right: 5px;
            }}
            .header-value {{
                font-weight: bold;
                color: {primary_color};
            }}
            .logo-img {{
                height: 50px;
                width: auto;
                max-width: 200px;
            }}
            .sample-date {{
                font-size: 9pt;
                color: #666;
            }}
            .title {{
                text-align: center;
                font-size: 18pt;
                font-weight: bold;
                color: {primary_color};
                margin: 20px 0;
            }}
            .table-container {{
                margin-bottom: 30px;
                page-break-inside: avoid;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                font-size: 9pt;
            }}
            table th {{
                background-color: {primary_color};
                color: white;
                padding: 10px 8px;
                text-align: left;
                font-weight: bold;
                border: 1px solid #ddd;
            }}
            table td {{
                padding: 8px;
                border: 1px solid #ddd;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            table.analysis-table td {{
                background-color: white;
            }}
            .recommendations-title {{
                background-color: {primary_color};
                color: white;
                padding: 10px;
                text-align: center;
                font-weight: bold;
                margin-bottom: 15px;
                font-size: 14pt;
            }}
            .recommendations-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 12px;
                margin-bottom: 20px;
            }}
            .recommendation-card {{
                border: 1px solid #ddd;
                border-radius: 4px;
                padding: 12px;
                page-break-inside: avoid;
                background-color: #ffffff;
            }}
            .recommendation-card.dynamic {{
                border-color: #93c5fd;
                background-color: #eff6ff;
            }}
            .recommendation-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
                width: 100%;
            }}
            .recommendation-title-section {{
                display: flex;
                align-items: center;
                flex: 1;
                gap: 8px;
                min-width: 0;
                margin-right: 8px;
            }}
            .recommendation-title {{
                font-weight: bold;
                font-size: 10pt;
                color: #111827;
                margin: 0;
                flex-shrink: 1;
            }}
            .dynamic-badge {{
                background-color: #dbeafe;
                color: #1e40af;
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 7pt;
                font-weight: normal;
                white-space: nowrap;
                display: inline-block;
                flex-shrink: 0;
            }}
            .priority-badge {{
                padding: 2px 8px;
                border-radius: 12px;
                font-size: 7pt;
                font-weight: normal;
                white-space: nowrap;
                display: inline-block;
                flex-shrink: 0;
                margin-left: auto;
            }}
            .priority-high {{
                background-color: #fee2e2;
                color: #991b1b;
            }}
            .priority-medium {{
                background-color: #fef3c7;
                color: #92400e;
            }}
            .priority-low {{
                background-color: #dcfce7;
                color: #166534;
            }}
            .recommendation-description {{
                font-size: 9pt;
                color: #4b5563;
                margin-bottom: 8px;
                line-height: 1.4;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            .recommendation-footer {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                font-size: 7pt;
                color: #6b7280;
            }}
            .recommendation-type {{
                text-transform: capitalize;
            }}
            .recommendation-source {{
                color: #2563eb;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-left">
                <div class="header-row">
                    <span class="header-label">Project Name:</span>
                    <span class="header-value">{project_name}</span>
                </div>
            </div>
            <div class="header-right">
                {f'<img src="{logo_base64}" alt="WaterSight" class="logo-img" />' if logo_base64 else '<span class="header-value">WaterSight</span>'}
                <span class="sample-date">Sample Date: {report_date}</span>
            </div>
        </div>
        
        <div class="table-container">
            <table class="analysis-table">
                <thead>
                    <tr>
                        <th>Parameters</th>
                        <th>Method of Analysis</th>
                        <th>{water_system.name}</th>
                        <th>Recommended Water Range {analysis_type.capitalize()}</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    for row in analysis_rows:
        html_content += f"""
                    <tr>
                        <td>{row['parameter']}</td>
                        <td>{row['method']}</td>
                        <td>{row['value']}</td>
                        <td>{row['recommended']}</td>
                    </tr>
        """
    
    html_content += """
                </tbody>
            </table>
        </div>
        
        <div class="table-container">
            <div class="recommendations-title">Suggested Action</div>
    """
    
    if use_table_format:
        # Fallback to table format if no recommendations exist
        html_content += """
            <table class="action-table">
                <thead>
                    <tr>
                        <th>PARAMETER</th>
                        <th>TARGET RANGE</th>
                        <th>CURRENT VALUE</th>
                        <th>SUGGESTED ACTION</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for row in action_rows:
            row_class = 'within-range' if row['is_within_range'] else 'out-of-range'
            html_content += f"""
                        <tr class="{row_class}">
                            <td>{row['parameter']}</td>
                            <td>{row['target_range']}</td>
                            <td>{row['current_value']}</td>
                            <td>
                                <span class="action-icon">{row['icon']}</span>
                                <span class="action-text">{row['suggested_action']}</span>
                            </td>
                        </tr>
            """
        
        html_content += """
                </tbody>
            </table>
        """
    else:
        # Card format matching water analysis page
        html_content += """
            <div class="recommendations-grid">
        """
        
        for rec in recommendations:
            # Determine card class - check if source exists (from calculation view) or use recommendation_type
            # For database recommendations, we'll use a simple heuristic: if it's based on indices, consider it dynamic
            has_source = hasattr(rec, 'source')
            is_dynamic = rec.source == 'dynamic' if has_source else False
            
            # If no source field, check if recommendation_type suggests it's dynamic (corrosion/scaling are usually dynamic)
            if not has_source:
                is_dynamic = rec.recommendation_type in ['corrosion', 'scaling']
            
            card_class = 'recommendation-card dynamic' if is_dynamic else 'recommendation-card'
            
            # Determine priority badge class
            priority_class = f'priority-{rec.priority}'
            
            # Escape HTML in text fields
            title = str(rec.title).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            description = str(rec.description).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            # Use recommendation_type field from model
            rec_type = str(getattr(rec, 'recommendation_type', getattr(rec, 'type', 'monitoring'))).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            
            html_content += f"""
                <div class="{card_class}">
                    <div class="recommendation-header">
                        <div class="recommendation-title-section">
                            <span class="recommendation-title">{title}</span>
            """
            
            if is_dynamic:
                html_content += """
                            <span class="dynamic-badge">Dynamic</span>
                """
            
            html_content += f"""
                        </div>
                        <span class="priority-badge {priority_class}">{rec.priority}</span>
                    </div>
                    <div class="recommendation-description">{description}</div>
                    <div class="recommendation-footer">
                        <span class="recommendation-type">{rec_type}</span>
            """
            
            if is_dynamic:
                html_content += """
                        <span class="recommendation-source">Based on latest analysis</span>
                """
            else:
                html_content += """
                        <span></span>
                """
            
            html_content += """
                    </div>
                </div>
            """
        
        html_content += """
            </div>
        """
    
    html_content += """
        </div>
    </body>
    </html>
    """
    
    # Convert HTML to PDF
    html_doc = HTML(string=html_content)
    html_doc.write_pdf(buffer)
    buffer.seek(0)
    return buffer


def generate_monthly_report_pdf(analyses, water_system, analysis_type, month_str):
    """Generate monthly report PDF with daily data for the selected month and graphs (no suggested actions)"""
    buffer = BytesIO()
    
    if not analyses.exists():
        return buffer
    
    # Get plant and water system names
    plant_name = water_system.plant.name if water_system and water_system.plant else 'N/A'
    water_system_name = water_system.name if water_system else 'N/A'
    project_name = f'{plant_name} - {water_system_name}'
    
    # Get logo
    logo_base64 = get_logo_base64()
    
    # Get parameter info - use first analysis if available, otherwise None
    first_analysis = analyses.first() if analyses.exists() else None
    param_info = get_parameter_info(analysis_type, water_system, first_analysis)
    primary_color = '#1e40af' if analysis_type == 'cooling' else '#7c3aed'
    
    # Parse month_str (format: "YYYY-MM")
    try:
        year_month = datetime.strptime(month_str, '%Y-%m')
        month_start = year_month.replace(day=1).date()
        # Get last day of month
        if month_start.month == 12:
            month_end = month_start.replace(year=month_start.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            month_end = month_start.replace(month=month_start.month + 1, day=1) - timedelta(days=1)
    except:
        # Fallback: use first and last analysis dates
        month_start = analyses.order_by('analysis_date').first().analysis_date
        month_end = analyses.order_by('-analysis_date').first().analysis_date
    
    # Group analyses by actual date (daily) - only for the selected month
    analyses_by_date = {}
    for analysis in analyses.order_by('analysis_date'):
        # Only include analyses within the selected month
        if month_start <= analysis.analysis_date <= month_end:
            date_key = analysis.analysis_date.strftime('%Y-%m-%d')
            analyses_by_date[date_key] = analysis
    
    # Build table data and prepare data for graphs
    table_rows = []
    graph_data = []
    
    # Get sorted daily dates for the month
    sorted_dates_str = sorted(analyses_by_date.keys())
    
    for param_tuple in param_info['parameters']:
        # Handle both 3-tuple (legacy) and 4-tuple (new) formats
        if len(param_tuple) == 4:
            param_name, method, recommended, param_key = param_tuple
        else:
            param_name, method, recommended = param_tuple
            param_key = param_name.lower().replace('-', '_').replace(' ', '_')
        
        row_data = {
            'parameter': param_name,
            'method': method,
            'values': [],
            'recommended': recommended,
            'param_key': param_key
        }
        
        # Collect values for table and graph (daily data)
        values_for_graph = []
        dates_for_graph = []
        numeric_values = []  # For calculating average
        
        for date_key in sorted_dates_str:
            analysis = analyses_by_date[date_key]
            # Use param_key if available, otherwise fallback to param_name
            value = get_analysis_value(analysis, param_key) if param_key else None
            value_str = f'{value:.2f}' if value is not None and isinstance(value, (int, float)) else str(value) if value else '-'
            row_data['values'].append(value_str)
            
            # For graph and average calculation
            if value is not None:
                numeric_values.append(float(value))
                values_for_graph.append(float(value))
                # Parse date for graph
                try:
                    dt = datetime.strptime(date_key, '%Y-%m-%d')
                    dates_for_graph.append(dt)
                except:
                    pass
        
        # Calculate average
        if numeric_values:
            avg_value = sum(numeric_values) / len(numeric_values)
            row_data['average'] = f'{avg_value:.2f}'
        else:
            row_data['average'] = '-'
        
        # Skip parameters with no values (except calculated indices like LSI/RSI/PSI/LR)
        # These calculated indices might be None but should still be shown
        calculated_indices = ['lsi', 'rsi', 'psi', 'lr']
        is_calculated_index = param_key and param_key.lower() in calculated_indices
        
        # Only add to table if we have at least one value OR it's a calculated index
        if numeric_values or is_calculated_index:
            table_rows.append(row_data)
        
        # Generate graph and action if we have data (daily points)
        if len(values_for_graph) > 0 and len(dates_for_graph) > 0:
            graph_base64 = generate_trend_graph(param_name, dates_for_graph, values_for_graph, recommended, param_key)
            if graph_base64:
                # Analyze trend for suggested action
                trend_desc, interpretation, recommendation = analyze_trend(
                    param_name, dates_for_graph, values_for_graph, recommended, param_key
                )
                
                graph_data.append({
                    'param_name': param_name,
                    'graph': graph_base64,
                    'trend': trend_desc if trend_desc else '',
                    'interpretation': interpretation if interpretation else '',
                    'recommendation': recommendation if recommendation else ''
                })
    
    # Generate HTML
    # Format date headers as day only (e.g., "21" instead of "21-12-2025")
    date_headers = []
    for date_key in sorted_dates_str:
        try:
            dt = datetime.strptime(date_key, '%Y-%m-%d')
            date_headers.append(dt.strftime('%d'))  # Format: "21" (day only)
        except:
            date_headers.append(date_key)
    
    # Format month display name
    try:
        month_display = datetime.strptime(month_str, '%Y-%m').strftime('%B %Y')  # "January 2024"
    except:
        month_display = month_str
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 1cm;
            }}
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                font-size: 9pt;
                color: #000;
                line-height: 1.4;
            }}
            .header {{
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }}
            .header-left {{
                flex: 1;
            }}
            .header-right {{
                text-align: right;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 5px;
            }}
            .header-row {{
                margin-bottom: 5px;
            }}
            .header-label {{
                font-weight: normal;
                margin-right: 5px;
            }}
            .header-value {{
                font-weight: bold;
                color: {primary_color};
            }}
            .logo-img {{
                height: 50px;
                width: auto;
                max-width: 200px;
            }}
            .sample-date {{
                font-size: 9pt;
                color: #666;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                font-size: 7pt;
            }}
            table th {{
                background-color: {primary_color};
                color: white;
                padding: 6px 4px;
                text-align: left;
                font-weight: bold;
                border: 1px solid #ddd;
            }}
            table td {{
                padding: 4px;
                border: 1px solid #ddd;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            .curve-section {{
                margin: 30px 0;
                page-break-inside: avoid;
            }}
            .curve-title {{
                text-align: center;
                font-size: 14pt;
                font-weight: bold;
                margin-bottom: 20px;
                color: {primary_color};
            }}
            .graphs-grid {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}
            .graph-action-pair {{
                display: flex;
                flex-direction: row;
                gap: 15px;
                margin-bottom: 30px;
                page-break-inside: avoid;
                align-items: center;
                justify-content: center;
            }}

            .graph-container {{
                page-break-inside: avoid;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 50%;
                flex: 1;
                overflow: hidden;
                min-width: 0;
                text-align: center;
            }}
            .graph-img {{
                width: 100%;
                height: auto;
                max-width: 100%;
                display: block;
                object-fit: contain;
                margin: 0 auto;
            }}
            .action-card {{
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 10px;
                background-color: #f9f9f9;
                page-break-inside: avoid;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                width: 50%;
                flex: 1;
                box-sizing: border-box;
                overflow: hidden;
                min-width: 0;
                word-wrap: break-word;
            }}
            .action-parameter {{
                font-weight: bold;
                font-size: 11pt;
                color: {primary_color};
                margin-bottom: 8px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 6px;
                word-wrap: break-word;
                overflow-wrap: break-word;
                text-align: left;
                width: 100%;
            }}
            .action-label {{
                font-weight: bold;
                font-size: 9pt;
                color: #333;
                margin-top: 6px;
                margin-bottom: 3px;
                word-wrap: break-word;
                text-align: left;
                width: 100%;
            }}
            .action-content {{
                font-size: 9pt;
                color: #555;
                line-height: 1.4;
                margin-bottom: 6px;
                word-wrap: break-word;
                overflow-wrap: break-word;
                hyphens: auto;
                max-width: 100%;
                text-align: left;
                width: 100%;
            }}
            .action-trend {{
                font-size: 9pt;
                color: #555;
                line-height: 1.4;
                margin-bottom: 6px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 100%;
                text-align: left;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-left">
                <div class="header-row">
                    <span class="header-label">Project Name:</span>
                    <span class="header-value">{project_name}</span>
                </div>
            </div>
            <div class="header-right">
                {f'<img src="{logo_base64}" alt="WaterSight" class="logo-img" />' if logo_base64 else '<span class="header-value">WaterSight</span>'}
                <span class="sample-date">Sample Date: {month_display}</span>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Parameters</th>
                    <th>Method of Analysis</th>
    """
    
    # Add daily date columns
    for date_header in date_headers:
        html_content += f"<th>{date_header}</th>"
    
    # Add Average column
    html_content += "<th>Average</th>"
    
    # Add Recommended Range column
    html_content += f"<th>Recommended Water Range {analysis_type.capitalize()}</th>"
    html_content += """
                </tr>
            </thead>
            <tbody>
    """
    
    for row in table_rows:
        html_content += f"""
                <tr>
                    <td>{row['parameter']}</td>
                    <td>{row['method']}</td>
        """
        # Add daily values
        for value in row['values']:
            html_content += f"<td>{value}</td>"
        # Add average
        html_content += f"<td><strong>{row['average']}</strong></td>"
        # Add recommended range
        html_content += f"<td>{row['recommended']}</td>"
        html_content += "</tr>"
    
    html_content += """
            </tbody>
        </table>
        
        <div class="curve-section">
            <div class="curve-title">Curve</div>
            <div class="graphs-grid">
    """
    
    # Add graphs with their suggested actions side by side
    for graph_item in graph_data:
        html_content += f"""
                <div class="graph-action-pair">
                    <div class="graph-container">
                        <img src="{graph_item['graph']}" alt="{graph_item['param_name']}" class="graph-img" />
                    </div>
                    <div class="action-card">
                        <div class="action-parameter">{graph_item['param_name']}</div>
        """
        
        if graph_item.get('trend'):
            html_content += f"""
                        <div class="action-label">Trend:</div>
                        <div class="action-trend">{graph_item['trend']}</div>
            """
        
        if graph_item.get('interpretation'):
            html_content += f"""
                        <div class="action-label">Interpretation:</div>
                        <div class="action-content">{graph_item['interpretation']}</div>
            """
        
        if graph_item.get('recommendation'):
            html_content += f"""
                        <div class="action-label">Recommendation:</div>
                        <div class="action-content">{graph_item['recommendation']}</div>
            """
        
        html_content += """
                    </div>
                </div>
        """
    
    html_content += """
            </div>
        </div>
    </body>
    </html>
    """
    
    html_doc = HTML(string=html_content)
    html_doc.write_pdf(buffer)
    buffer.seek(0)
    return buffer


def generate_yearly_report_pdf(analyses, water_system, analysis_type, year):
    """Generate yearly report PDF with monthly data, trend curves, and suggested actions"""
    buffer = BytesIO()
    
    if not analyses.exists():
        return buffer
    
    # Get plant and water system names
    plant_name = water_system.plant.name if water_system and water_system.plant else 'N/A'
    water_system_name = water_system.name if water_system else 'N/A'
    project_name = f'{plant_name} - {water_system_name}'
    
    # Get logo
    logo_base64 = get_logo_base64()
    
    # Get parameter info - use first analysis if available, otherwise None
    first_analysis = analyses.first() if analyses.exists() else None
    param_info = get_parameter_info(analysis_type, water_system, first_analysis)
    primary_color = '#1e40af' if analysis_type == 'cooling' else '#7c3aed'
    
    # Group analyses by month
    analyses_by_month = {}
    for analysis in analyses.order_by('analysis_date'):
        month_key = analysis.analysis_date.strftime('%b %Y')
        if month_key not in analyses_by_month:
            analyses_by_month[month_key] = []
        analyses_by_month[month_key].append(analysis)
    
    # Build table data and prepare data for graphs and suggested actions
    table_rows = []
    graph_data = []
    
    # Get sorted month keys
    sorted_month_keys = sorted(analyses_by_month.keys())
    
    for param_tuple in param_info['parameters']:
        # Handle both 3-tuple (legacy) and 4-tuple (new) formats
        if len(param_tuple) == 4:
            param_name, method, recommended, param_key = param_tuple
        else:
            param_name, method, recommended = param_tuple
            param_key = param_name.lower().replace('-', '_').replace(' ', '_')
        
        row_data = {
            'parameter': param_name,
            'method': method,
            'values': [],
            'recommended': recommended,
            'param_key': param_key
        }
        
        # Collect values for table, graph, and trend analysis
        values_for_graph = []
        dates_for_graph = []
        numeric_values = []  # For checking if parameter has values
        
        for month_key in sorted_month_keys:
            month_analyses = analyses_by_month[month_key]
            # Get average value for the month - use param_key if available
            values = [get_analysis_value(a, param_key) if param_key else None for a in month_analyses]
            values = [v for v in values if v is not None]
            if values:
                avg_value = sum(values) / len(values)
                value_str = f'{avg_value:.2f}'
                numeric_values.append(avg_value)
                values_for_graph.append(avg_value)
                # Parse month for graph - use first day of month for yearly reports
                try:
                    dt = datetime.strptime(month_key, '%b %Y')
                    # Ensure it's the first day of the month for consistent monthly display
                    dt = dt.replace(day=1)
                    dates_for_graph.append(dt)
                except:
                    pass
            else:
                value_str = '-'
            row_data['values'].append(value_str)
        
        # Skip parameters with no values (except calculated indices like LSI/RSI/PSI/LR)
        calculated_indices = ['lsi', 'rsi', 'psi', 'lr']
        is_calculated_index = param_key and param_key.lower() in calculated_indices
        
        # Only add to table if we have at least one value OR it's a calculated index
        if numeric_values or is_calculated_index:
            table_rows.append(row_data)
        
        # Generate graph and action if we have data
        if len(values_for_graph) > 0 and len(dates_for_graph) > 0:
            graph_base64 = generate_trend_graph(param_name, dates_for_graph, values_for_graph, recommended, param_key)
            if graph_base64:
                # Analyze trend for suggested action
                trend_desc, interpretation, recommendation = analyze_trend(
                    param_name, dates_for_graph, values_for_graph, recommended, param_key
                )
                
                graph_data.append({
                    'param_name': param_name,
                    'graph': graph_base64,
                    'trend': trend_desc if trend_desc else '',
                    'interpretation': interpretation if interpretation else '',
                    'recommendation': recommendation if recommendation else ''
                })
    
    # Generate HTML (similar to monthly but with more data)
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            @page {{
                size: A4;
                margin: 1cm;
            }}
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: Arial, Helvetica, sans-serif;
                font-size: 8pt;
                color: #000;
                line-height: 1.4;
            }}
            .header {{
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
            }}
            .header-left {{
                flex: 1;
            }}
            .header-right {{
                text-align: right;
                display: flex;
                flex-direction: column;
                align-items: flex-end;
                gap: 5px;
            }}
            .header-row {{
                margin-bottom: 5px;
            }}
            .header-label {{
                font-weight: normal;
                margin-right: 5px;
            }}
            .header-value {{
                font-weight: bold;
                color: {primary_color};
            }}
            .logo-img {{
                height: 50px;
                width: auto;
                max-width: 200px;
            }}
            .sample-date {{
                font-size: 9pt;
                color: #666;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-bottom: 20px;
                font-size: 7pt;
            }}
            table th {{
                background-color: {primary_color};
                color: white;
                padding: 6px 4px;
                text-align: left;
                font-weight: bold;
                border: 1px solid #ddd;
            }}
            table td {{
                padding: 4px;
                border: 1px solid #ddd;
                word-wrap: break-word;
                overflow-wrap: break-word;
            }}
            .curve-section {{
                margin: 30px 0;
                page-break-inside: avoid;
            }}
            .curve-title {{
                text-align: center;
                font-size: 14pt;
                font-weight: bold;
                margin-bottom: 20px;
                color: {primary_color};
            }}
            .graphs-grid {{
                display: grid;
                grid-template-columns: 1fr;
                gap: 20px;
                margin-bottom: 20px;
            }}
            .graph-action-pair {{
                display: flex;
                flex-direction: row;
                gap: 15px;
                margin-bottom: 30px;
                page-break-inside: avoid;
                align-items: center;
                justify-content: center;
            }}
            @media print {{
                .graph-action-pair {{
                    flex-direction: row;
                }}
            }}
            .graph-container {{
                page-break-inside: avoid;
                display: flex;
                align-items: center;
                justify-content: center;
                width: 50%;
                flex: 1;
                overflow: hidden;
                min-width: 0;
                text-align: center;
            }}
            .graph-img {{
                width: 100%;
                height: auto;
                max-width: 100%;
                display: block;
                object-fit: contain;
                margin: 0 auto;
            }}
            .action-card {{
                border: 2px solid #ddd;
                border-radius: 6px;
                padding: 10px;
                background-color: #f9f9f9;
                page-break-inside: avoid;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                display: flex;
                flex-direction: column;
                width: 50%;
                flex: 1;
                box-sizing: border-box;
                overflow: hidden;
                min-width: 0;
                word-wrap: break-word;
            }}
            .action-parameter {{
                font-weight: bold;
                font-size: 11pt;
                color: {primary_color};
                margin-bottom: 8px;
                border-bottom: 1px solid #ddd;
                padding-bottom: 6px;
                word-wrap: break-word;
                overflow-wrap: break-word;
                text-align: left;
                width: 100%;
            }}
            .action-label {{
                font-weight: bold;
                font-size: 9pt;
                color: #333;
                margin-top: 6px;
                margin-bottom: 3px;
                word-wrap: break-word;
                text-align: left;
                width: 100%;
            }}
            .action-content {{
                font-size: 9pt;
                color: #555;
                line-height: 1.4;
                margin-bottom: 6px;
                word-wrap: break-word;
                overflow-wrap: break-word;
                hyphens: auto;
                max-width: 100%;
                text-align: left;
                width: 100%;
            }}
            .action-trend {{
                font-size: 9pt;
                color: #555;
                line-height: 1.4;
                margin-bottom: 6px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
                max-width: 100%;
                text-align: left;
                width: 100%;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="header-left">
                <div class="header-row">
                    <span class="header-label">Project Name:</span>
                    <span class="header-value">{project_name}</span>
                </div>
            </div>
            <div class="header-right">
                {f'<img src="{logo_base64}" alt="WaterSight" class="logo-img" />' if logo_base64 else '<span class="header-value">WaterSight</span>'}
                <span class="sample-date">Sample Date: {year}</span>
            </div>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Parameters</th>
                    <th>Method of Analysis</th>
    """
    
    for month_header in sorted_month_keys:
        html_content += f"<th>{month_header}</th>"
    
    html_content += f"<th>Recommended Water Range {analysis_type.capitalize()}</th>"
    html_content += """
                </tr>
            </thead>
            <tbody>
    """
    
    for row in table_rows:
        html_content += f"""
                <tr>
                    <td>{row['parameter']}</td>
                    <td>{row['method']}</td>
        """
        for value in row['values']:
            html_content += f"<td>{value}</td>"
        html_content += f"<td>{row['recommended']}</td>"
        html_content += "</tr>"
    
    html_content += """
            </tbody>
        </table>
        
        <div class="curve-section">
            <div class="curve-title">Graph</div>
            <div class="graphs-grid">
    """
    
    # Add graphs with their suggested actions side by side
    for graph_item in graph_data:
        html_content += f"""
                <div class="graph-action-pair">
                    <div class="graph-container">
                        <img src="{graph_item['graph']}" alt="{graph_item['param_name']}" class="graph-img" />
                    </div>
                    <div class="action-card">
                        <div class="action-parameter">{graph_item['param_name']}</div>
        """
        
        if graph_item.get('trend'):
            html_content += f"""
                        <div class="action-label">Trend:</div>
                        <div class="action-trend">{graph_item['trend']}</div>
            """
        
        if graph_item.get('interpretation'):
            html_content += f"""
                        <div class="action-label">Interpretation:</div>
                        <div class="action-content">{graph_item['interpretation']}</div>
            """
        
        if graph_item.get('recommendation'):
            html_content += f"""
                        <div class="action-label">Recommendation:</div>
                        <div class="action-content">{graph_item['recommendation']}</div>
            """
        
        html_content += """
                    </div>
                </div>
        """
    
    html_content += """
            </div>
        </div>
    </body>
    </html>
    """
    
    html_doc = HTML(string=html_content)
    html_doc.write_pdf(buffer)
    buffer.seek(0)
    return buffer

