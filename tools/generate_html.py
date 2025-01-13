import os
import json
import argparse
import logging
import plotly.graph_objs as go
from datetime import datetime
from pathlib import Path
import plotly.graph_objs as go

# Configure logging to display DEBUG messages
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')

def is_numeric(val):
    try:
        float(val)
        return True
    except:
        return False

def strip_commas_from_years_or_dates(key, val):
    if key.lower() in ['date', 'year'] or 'date' in key.lower():
        if isinstance(val, str):
            return val.replace(',', '')
    return val

def format_number(val):
    try:
        f = float(val)
        if f.is_integer():
            return f"{int(f):,}"
        else:
            if '.' in val:
                decimals = len(val.split('.')[-1])
                format_str = f"{{:,.{decimals}f}}"
                return format_str.format(f)
            else:
                return f"{f:,}"
    except:
        return val

def format_value(k, v):
    if v is None:
        return "None"
    v = strip_commas_from_years_or_dates(k, v)
    v_str = str(v)
    if is_numeric(v_str):
        return format_number(v_str)
    return v_str

def dict_to_dl(d):
    html = "<dl>"
    for k, v in d.items():
        val = format_value(k, v)
        # Link formatting if needed
        if k.lower() == 'seclink' and val != "None" and "http" in val:
            val = f'<a href="{v}" target="_blank">{v}</a>'
        html += f"<dt>{k}:</dt><dd>{val}</dd><br>"
    html += "</dl>"
    return html

def list_of_dicts_to_table(l):
    if not l:
        return "<p>No Data Available</p>"
    # Collect all keys from all dicts for the header
    keys = set()
    for item in l:
        keys.update(item.keys())
    keys = list(keys)

    html = "<table border='1' style='width: 100%; text-align: left; border-collapse: collapse;'>"
    html += "<thead><tr>"
    for k in keys:
        html += f"<th>{k}</th>"
    html += "</tr></thead><tbody>"
    for item in l:
        html += "<tr>"
        for k in keys:
            html += f"<td>{format_value(k, item.get(k))}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

def list_of_dicts_to_dl(l, use_name_as_heading=False):
    if not l:
        return "<p>No Data Available</p>"
    html = ""
    for item in l:
        if use_name_as_heading and 'name' in item:
            html += f"<h5>{item['name']}</h5>"
        html += dict_to_dl(item)
    return html

def create_outstandingshares_plot(data, title):
    # data structure:
    # {
    #   "0": {
    #       "date": "2024",
    #       "dateFormatted": "2024-12-31",
    #       "sharesMln": "15242.8530",
    #       "shares": 15242853000
    #   },
    #   ...
    # }
    dates = []
    shares = []
    for v in data.values():
        if isinstance(v, dict):
            # Prefer dateFormatted if available, else date
            x_val = v.get('dateFormatted', v.get('date'))
            y_val = v.get('shares')
            if x_val and y_val:
                dates.append(x_val)
                shares.append(y_val)

    if not dates or not shares:
        return "<p>No Outstanding Shares Data Available</p>"

    trace = go.Scatter(x=dates, y=shares, mode='lines+markers', name=title)
    layout = go.Layout(title=title, xaxis=dict(title='Date'), yaxis=dict(title='Shares'), autosize=True)
    fig = go.Figure(data=[trace], layout=layout)
    plot_html = f"<div style='width:100%;'>{fig.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
    return plot_html

def dict_keys_to_sorted_list(d):
    return sorted(d.keys(), reverse=True)

def dict_to_options(d, prefix):
    options = '<option value="">Select a date</option>'
    sorted_keys = dict_keys_to_sorted_list(d)
    for key in sorted_keys:
        options += f'<option value="{key}">{key}</option>'
    return options

def format_financial_section(financial_data, title):
    quarterly_data = financial_data.get('quarterly', {})
    yearly_data = financial_data.get('yearly', {})

    nested_tabs_html = '''
    <div class="nested-tabs-second-level">
        <div class="nested-tab-second-level">Quarterly</div>
        <div class="nested-tab-second-level">Yearly</div>
    </div>
    '''

    # Quarterly section
    quarterly_html = ""
    if quarterly_data:
        quarterly_dropdown_id = f"{title.lower().replace(' ', '_')}_quarterly_dropdown"
        quarterly_html += f"""
        <div class='financial-dropdown'>
            <label for='{quarterly_dropdown_id}'>Select Quarterly Date:</label><br>
            <select id='{quarterly_dropdown_id}'>
                {dict_to_options(quarterly_data, quarterly_dropdown_id)}
            </select>
        </div>
        """
        for date_key, report in quarterly_data.items():
            content_id = f"{title.lower().replace(' ', '_')}_quarterly_{date_key}"
            content_html = dict_to_dl(report) if isinstance(report, dict) else "<p>No Data Available</p>"
            quarterly_html += f"<div id='{content_id}' class='dropdown-content'>{content_html}</div>"
    else:
        quarterly_html = "<p>No Quarterly Data Available</p>"

    # Yearly section
    yearly_html = ""
    if yearly_data:
        yearly_dropdown_id = f"{title.lower().replace(' ', '_')}_yearly_dropdown"
        yearly_html += f"""
        <div class='financial-dropdown'>
            <label for='{yearly_dropdown_id}'>Select Yearly Date:</label><br>
            <select id='{yearly_dropdown_id}'>
                {dict_to_options(yearly_data, yearly_dropdown_id)}
            </select>
        </div>
        """
        for date_key, report in yearly_data.items():
            content_id = f"{title.lower().replace(' ', '_')}_yearly_{date_key}"
            content_html = dict_to_dl(report) if isinstance(report, dict) else "<p>No Data Available</p>"
            yearly_html += f"<div id='{content_id}' class='dropdown-content'>{content_html}</div>"
    else:
        yearly_html = "<p>No Yearly Data Available</p>"

    html = f"<h4>{title}</h4>"
    html += nested_tabs_html
    html += "<div class='nested-content-second-level-container'>"
    html += f"<div class='nested-content-second-level'>{quarterly_html}</div>"
    html += f"<div class='nested-content-second-level'>{yearly_html}</div>"
    html += "</div>"

    return html

def format_financials(financials):
    if not financials or not isinstance(financials, dict):
        return "<p>No Financial Data Available</p>"

    tabs_html = '<div class="nested-tabs">'
    contents_html = ''

    for section, section_data in financials.items():
        section_title = section.replace("_", " ").title()
        tabs_html += f'<div class="nested-tab">{section_title}</div>'
        section_html = format_financial_section(section_data, section_title)
        contents_html += f"<div class='nested-content'>{section_html}</div>"
    tabs_html += '</div>'
    return tabs_html + contents_html

def render_holders(data, title):
    if not data:
        return f"<p>No {title} Data</p>"
    # Convert to list
    rows = list(data.values())
    # Sort by totalAssets descending if that field exists
    rows.sort(key=lambda x: x.get('totalAssets', 0), reverse=True)

    # Build table
    if not rows:
        return f"<p>No {title} Data</p>"

    # Collect columns from the first entry
    keys = sorted(rows[0].keys())
    html = "<table border='1' style='width: 100%; text-align: left; border-collapse: collapse;'>"
    html += "<thead><tr>"
    for k in keys:
        html += f"<th>{k}</th>"
    html += "</tr></thead><tbody>"
    for item in rows:
        html += "<tr>"
        for k in keys:
            val = item.get(k)
            html += f"<td>{format_value(k, val)}</td>"
        html += "</tr>"
    html += "</tbody></table>"
    return html

def format_holders(holders):
    institutions = holders.get("Institutions", {})
    funds = holders.get("Funds", {})

    institutions_html = render_holders(institutions, "Institutions")
    funds_html = render_holders(funds, "Funds")

    tabs_html = '<div class="nested-tabs">'
    tabs_html += '<div class="nested-tab">Institutions</div>'
    tabs_html += '<div class="nested-tab">Funds</div>'
    tabs_html += '</div>'

    contents_html = f"<div class='nested-content'>{institutions_html}</div>"
    contents_html += f"<div class='nested-content'>{funds_html}</div>"

    return tabs_html + contents_html

def format_earnings_section(earnings_history):
    # We want a plotly chart: date on x, epsActual and epsEstimate as bars
    # Hover displays other fields: reportDate, currency, epsDifference, surprisePercent
    # We'll create a grouped bar chart

    dates = []
    eps_actual = []
    eps_estimate = []
    hover_texts_actual = []
    hover_texts_estimate = []

    for date_key, data_point in sorted(earnings_history.items(), key=lambda x: x[0]):
        d = data_point
        # Extract info
        dt = d.get('date')
        if not dt:
            dt = date_key
        epsA = d.get('epsActual')
        epsE = d.get('epsEstimate')

        # Build a hover text that shows other fields
        hover_info = f"ReportDate: {d.get('reportDate', 'N/A')}<br>"
        hover_info += f"Currency: {d.get('currency', 'N/A')}<br>"
        hover_info += f"EPS Difference: {d.get('epsDifference', 'N/A')}<br>"
        hover_info += f"Surprise %: {d.get('surprisePercent', 'N/A')}"

        dates.append(dt)
        eps_actual.append(epsA)
        hover_texts_actual.append(hover_info)
        eps_estimate.append(epsE)
        hover_texts_estimate.append(hover_info)

    if not dates:
        return "<p>No Earnings Data Available</p>"

    trace_actual = go.Bar(
        x=dates,
        y=eps_actual,
        name='EPS Actual',
        hovertext=hover_texts_actual,
        hoverinfo='text'
    )
    trace_estimate = go.Bar(
        x=dates,
        y=eps_estimate,
        name='EPS Estimate',
        hovertext=hover_texts_estimate,
        hoverinfo='text'
    )

    layout = go.Layout(
        title="Earnings (Actual vs Estimate)",
        xaxis=dict(title='Date'),
        yaxis=dict(title='EPS'),
        barmode='group'
    )

    fig = go.Figure(data=[trace_actual, trace_estimate], layout=layout)
    chart_html = f"<div style='width:100%;'>{fig.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
    return chart_html

def format_outstandingshares(value):
    annual = value.get("annual", {})
    quarterly = value.get("quarterly", {})

    annual_plot = create_outstandingshares_plot(annual, "Annual Outstanding Shares")
    quarterly_plot = create_outstandingshares_plot(quarterly, "Quarterly Outstanding Shares")

    tabs_html = """
    <div class='nested-tabs'>
        <div class='nested-tab'>Annual</div>
        <div class='nested-tab'>Quarterly</div>
    </div>
    """

    contents_html = f"<div class='nested-content'>{annual_plot}</div>"
    contents_html += f"<div class='nested-content'>{quarterly_plot}</div>"

    return tabs_html + contents_html

def format_earnings_dropdown(earnings):
    dropdown_html = """
    <div class='financial-dropdown'>
        <label for='earnings-dropdown'>Select Earnings Date:</label><br>
        <select id='earnings-dropdown'>
            <option value="">Select a date</option>
    """
    if isinstance(earnings, dict):
        sorted_earnings = sorted(earnings.keys(), reverse=True)
        for date in sorted_earnings:
            dropdown_html += f'<option value="{date}">{date}</option>'
    dropdown_html += "</select></div>"

    # Generate content divs for Earnings History
    content_html = ""
    if isinstance(earnings, dict):
        sorted_earnings = sorted(earnings.items(), key=lambda x: x[0], reverse=True)
        for date, details in sorted_earnings:
            content_id = f"earnings_{date}"
            content_html += f"<div id='{content_id}' class='dropdown-content'>{dict_to_dl(details)}</div>"
    else:
        content_html += "<p>No Earnings Data Available</p>"

    earnings_html = dropdown_html + content_html
    return earnings_html

def format_general_section(value):
    # We want to format AddressData, Listings, Officers in a nicer way.
    # Start with a dl for general fields
    # We'll extract AddressData, Listings, Officers separately and remove them from dict before calling dict_to_dl

    val_copy = dict(value)
    address_data = val_copy.pop("AddressData", {})
    listings = val_copy.pop("Listings", {})
    officers = val_copy.pop("Officers", {})

    html = dict_to_dl(val_copy)

    # AddressData as a dl
    if address_data and isinstance(address_data, dict):
        html += "<h4>Address Data</h4>"
        html += dict_to_dl(address_data)

    # Listings as a table
    if listings and isinstance(listings, dict):
        listings_list = list(listings.values())
        html += "<h4>Listings</h4>"
        html += list_of_dicts_to_table(listings_list)

    # Officers as a table
    if officers and isinstance(officers, dict):
        officers_list = list(officers.values())
        html += "<h4>Officers</h4>"
        html += list_of_dicts_to_table(officers_list)

    return html

def format_splits_dividends_section(value):
    # Just a plotly chart with year on x and count on y
    number_dividends = value.get("NumberDividendsByYear", {})
    if not number_dividends:
        return "<p>No Dividends Data Available</p>"

    # Extract years and counts
    years = []
    counts = []
    for v in number_dividends.values():
        if isinstance(v, dict) and 'Year' in v and 'Count' in v:
            years.append(v['Year'])
            counts.append(v['Count'])

    if not years or not counts:
        return "<p>No Valid Dividends Data Available</p>"

    trace = go.Bar(x=years, y=counts, name='Dividends Count')
    layout = go.Layout(title="Number of Dividends by Year", xaxis=dict(title='Year'), yaxis=dict(title='Count'), barmode='group')
    fig = go.Figure(data=[trace], layout=layout)
    chart_html = f"<div style='width:100%;'>{fig.to_html(full_html=False, include_plotlyjs='cdn')}</div>"
    return chart_html

########################################################
# NEW CODE: Add a function to format ETF-specific data #
########################################################

def format_etf_data_subdict(d: dict) -> str:
    """Helper: Given a sub-dict for, e.g., Market_Capitalisation or World_Regions,
       convert to an HTML table or DL as appropriate."""
    # If the dict values are themselves dict-like, let's create a table. Otherwise, just do dict_to_dl.
    # We check one item to see if it's a nested dict with multiple keys.
    if not d:
        return "<p>No Data Available</p>"

    # Check if all values are also dicts
    if all(isinstance(val, dict) for val in d.values()):
        # Build a list of dicts for table
        rows = []
        # The row "key" might be the parent key, plus the sub-keys
        for key, subdict in d.items():
            row = {"Name": key}
            if isinstance(subdict, dict):
                for k2, v2 in subdict.items():
                    row[k2] = v2
            else:
                row["Value"] = subdict
            rows.append(row)
        return list_of_dicts_to_table(rows)
    else:
        # Just a top-level dictionary
        return dict_to_dl(d)

def format_etf_data(value: dict) -> str:
    """Creates sub-tabs for the various parts of 'ETF_Data'."""
    # We'll check for sub-sections: "Market_Capitalisation", "Asset_Allocation",
    # "World_Regions", "Sector_Weights", "Fixed_Income", "Holdings_Count",
    # "Top_10_Holdings", "Holdings", "Valuations_Growth", "MorningStar", "Performance".
    # Then we'll remove them from a copy so we can do a simple dict_to_dl for the remainder.

    val_copy = dict(value)
    market_cap = val_copy.pop("Market_Capitalisation", {})
    asset_alloc = val_copy.pop("Asset_Allocation", {})
    world_regions = val_copy.pop("World_Regions", {})
    sector_weights = val_copy.pop("Sector_Weights", {})
    fixed_income = val_copy.pop("Fixed_Income", {})
    top_10 = val_copy.pop("Top_10_Holdings", {})
    holdings_count = val_copy.pop("Holdings_Count", None)
    holdings = val_copy.pop("Holdings", {})
    valuations_growth = val_copy.pop("Valuations_Growth", {})
    morningstar = val_copy.pop("MorningStar", {})
    performance = val_copy.pop("Performance", {})

    # The rest we'll display as a simple dl
    main_dl = dict_to_dl(val_copy)

    # Now build sub-tabs for each chunk if it has data
    tabs_html = '<div class="nested-tabs">'
    contents_html = ''

    # We'll define a small helper to reduce repetition:
    def add_subtab_if_data(data, title, formatter=None):
        nonlocal tabs_html, contents_html
        if data:
            tabs_html += f'<div class="nested-tab">{title}</div>'
            if formatter:
                sub_html = formatter(data)
            else:
                # fallback to dict->dl or something
                sub_html = format_etf_data_subdict(data)
            contents_html += f"<div class='nested-content'>{sub_html}</div>"

    # Start with the top-level data (ISIN, Company_Name, etc.)
    tabs_html += '<div class="nested-tab">Main</div>'
    contents_html += f"<div class='nested-content'>{main_dl}</div>"

    add_subtab_if_data(market_cap, "Market Capitalization", format_etf_data_subdict)
    add_subtab_if_data(asset_alloc, "Asset Allocation", format_etf_data_subdict)
    add_subtab_if_data(world_regions, "World Regions", format_etf_data_subdict)
    add_subtab_if_data(sector_weights, "Sector Weights", format_etf_data_subdict)
    add_subtab_if_data(fixed_income, "Fixed Income", format_etf_data_subdict)

    # If there's a "Holdings_Count", just show it as a small dl
    if holdings_count is not None:
        add_subtab_if_data({"Holdings_Count": holdings_count}, "Holdings Count", dict_to_dl)

    add_subtab_if_data(top_10, "Top 10 Holdings", format_etf_data_subdict)
    add_subtab_if_data(holdings, "All Holdings", format_etf_data_subdict)
    add_subtab_if_data(valuations_growth, "Valuations & Growth", format_etf_data_subdict)
    add_subtab_if_data(morningstar, "MorningStar", format_etf_data_subdict)
    add_subtab_if_data(performance, "Performance", format_etf_data_subdict)

    tabs_html += '</div>'
    return tabs_html + contents_html

########################################################
# Existing code for deciding how to render each tab    #
########################################################

def format_tab_content(key, value):
    kl = key.lower()
    if kl == "esgscores":
        return ""
    elif kl == "general":
        return format_general_section(value)
    elif kl == "highlights":
        return dict_to_dl(value)
    elif kl == "valuation":
        return dict_to_dl(value)
    elif kl == "sharesstats":
        return dict_to_dl(value)
    elif kl == "technicals":
        return dict_to_dl(value)
    elif kl == "splitsdividends":
        return format_splits_dividends_section(value)
    elif kl == "holders":
        return format_holders(value)
    elif kl == "insidertransactions":
        insider_list = list(value.values())
        return list_of_dicts_to_dl(insider_list, use_name_as_heading=True)
    elif kl == "outstandingshares":
        return format_outstandingshares(value)
    elif kl == "earnings":
        if "History" in value:
            return format_earnings_dropdown(value["History"])
        else:
            return dict_to_dl(value)
    elif kl == "financials":
        return format_financials(value)
    ####################################################
    # NEW condition to handle "ETF_Data" specifically: #
    ####################################################
    elif kl == "etf_data":
        return format_etf_data(value)
    else:
        return dict_to_dl(value)

def format_tabs(data):
    tabs_html = '<div class="tabs">'
    contents_html = ''
    filtered_items = [(k, v) for k, v in data.items() if k.lower() != "esgscores"]
    for idx, (key, value) in enumerate(filtered_items):
        tabs_html += f'<div class="tab">{key}</div>'
        content = format_tab_content(key, value)
        contents_html += f"<div class='content'>{content}</div>"
    tabs_html += '</div>'
    return tabs_html + contents_html

def generate_html_with_dropdown(data, output_filepath):
    if not data or not isinstance(data, dict):
        logging.error("Data is empty or not a dict.")
        return

    # Ensure output directory exists
    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            logging.error(f"Failed to create directory {output_dir}: {e}")
            return

    styles = """
    <style>
        /* Basic Styles */
        html, body {
            width: 100%;
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f9f9f9;
            color: #333;
            width: 100%;
        }
        dl {
            margin: 0 0 10px 0;
            padding: 0;
        }
        dt, dd {
            display: inline-block;
            margin: 0;
            padding: 2px;
            vertical-align: top;
        }
        dt {
            font-weight: bold;
        }
        dd {
            margin-left: 5px;
        }

        /* Main Tabs */
        .tabs {
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-bottom: 1em;
            flex-wrap: wrap;
        }
        .tab {
            padding: 10px 20px;
            cursor: pointer;
            border: 1px solid #ddd;
            border-bottom: none;
            background-color: #f1f1f1;
            margin-right: 5px;
            border-radius: 5px 5px 0 0;
        }
        .tab.active, .tab:hover {
            background-color: #ddd;
        }
        .content {
            display: none;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 0 5px 5px 5px;
            background-color: #fff;
            margin-top: -1px;
        }
        .content.active {
            display: block;
        }

        /* Nested Tabs (Financials, ETF, etc.) */
        .nested-tabs {
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-top: 20px;
            margin-bottom: 1em;
            flex-wrap: wrap;
        }
        .nested-tab {
            padding: 8px 16px;
            cursor: pointer;
            border: 1px solid #ddd;
            border-bottom: none;
            background-color: #e6e6e6;
            margin-right: 5px;
            font-size: 0.9em;
            border-radius: 5px 5px 0 0;
        }
        .nested-tab.active, .nested-tab:hover {
            background-color: #ccc;
        }
        .nested-content {
            display: none;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 0 5px 5px 5px;
            background-color: #f9f9f9;
            margin-top: -1px;
        }
        .nested-content.active {
            display: block;
        }

        /* Nested Tabs Second Level (Quarterly and Yearly) */
        .nested-tabs-second-level {
            display: flex;
            border-bottom: 1px solid #ddd;
            margin-top: 10px;
            margin-bottom: 1em;
            flex-wrap: wrap;
        }
        .nested-tab-second-level {
            padding: 6px 12px;
            cursor: pointer;
            border: 1px solid #ddd;
            border-bottom: none;
            background-color: #d9d9d9;
            margin-right: 5px;
            font-size: 0.8em;
            border-radius: 5px 5px 0 0;
        }
        .nested-tab-second-level.active, .nested-tab-second-level:hover {
            background-color: #b3b3b3;
        }
        .nested-content-second-level {
            display: none;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 0 5px 5px 5px;
            background-color: #f0f0f0;
            margin-top: -1px;
        }
        .nested-content-second-level.active {
            display: block;
        }

        /* Dropdown Content */
        .dropdown-content {
            display: none;
            margin-top: 10px;
            padding: 15px;
            border: 1px solid #ddd;
            background-color: #f9f9f9;
            border-radius: 5px;
        }
        .dropdown-content.active {
            display: block;
        }

        /* Headings */
        h4 {
            margin-bottom: 0.3em;
            margin-top: 1em;
        }

        /* Tables */
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 15px;
        }
        th, td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        th {
            background-color: #f2f2f2;
        }

        /* Select Dropdown */
        select {
            margin-bottom: 10px;
            padding: 5px;
        }

        /* Financial Dropdowns */
        .financial-dropdown {
            margin-bottom: 20px;
        }
    </style>
    """

    script = """
    <script>
        document.addEventListener('DOMContentLoaded', function () {
            function setupTabs(tabSelector, contentSelector) {
                const tabs = document.querySelectorAll(tabSelector);
                const contents = document.querySelectorAll(contentSelector);

                tabs.forEach((tab, index) => {
                    tab.addEventListener('click', () => {
                        tabs.forEach(t => t.classList.remove('active'));
                        contents.forEach(c => c.classList.remove('active'));
                        tab.classList.add('active');
                        contents[index].classList.add('active');
                    });
                });

                if (tabs.length > 0) {
                    tabs[0].classList.add('active');
                    contents[0].classList.add('active');
                }
            }

            function setupNestedTabs(tabSelector, contentSelector) {
                const tabs = document.querySelectorAll(tabSelector);
                const contents = document.querySelectorAll(contentSelector);

                tabs.forEach((tab, index) => {
                    tab.addEventListener('click', () => {
                        tabs.forEach(t => t.classList.remove('active'));
                        contents.forEach(c => c.classList.remove('active'));
                        tab.classList.add('active');
                        contents[index].classList.add('active');
                    });
                });

                if (tabs.length > 0) {
                    tabs[0].classList.add('active');
                    contents[0].classList.add('active');
                }
            }

            function setupDropdown(dropdownId, contentPrefix) {
                const dropdown = document.getElementById(dropdownId);
                if (!dropdown) {
                    return;
                }

                dropdown.addEventListener('change', function () {
                    const selectedValue = this.value;
                    const allContents = document.querySelectorAll(`.dropdown-content`);
                    allContents.forEach(content => {
                        if (content.id === `${contentPrefix}_${selectedValue}`) {
                            content.classList.add('active');
                        } else {
                            content.classList.remove('active');
                        }
                    });
                });
            }

            setupTabs('.tab', '.content');
            setupTabs('.nested-tab', '.nested-content');
            setupNestedTabs('.nested-tab-second-level', '.nested-content-second-level');

            const financialSections = ['balance_sheet', 'cash_flow', 'income_statement'];
            financialSections.forEach(section => {
                const quarterlyDropdownId = `${section}_quarterly_dropdown`;
                const yearlyDropdownId = `${section}_yearly_dropdown`;
                setupDropdown(quarterlyDropdownId, `${section}_quarterly`);
                setupDropdown(yearlyDropdownId, `${section}_yearly`);
            });

            setupDropdown('earnings-dropdown', 'earnings');
        });
    </script>
    """

    try:
        with open(output_filepath, "w") as file:
            file.write("<html><head>")
            file.write(styles)
            file.write(script)
            file.write("</head><body>")
            tabs_content = format_tabs(data)
            file.write(tabs_content)
            file.write("</body></html>")
        logging.info(f"Saved HTML to {output_filepath}")
    except Exception as e:
        logging.error(f"Exception occurred while writing HTML: {e}")

#########################################
# Market Cap categorization logic       #
#########################################

def extract_market_caps(data_dir: str) -> dict:
    """
    Extracts market capitalization data from JSON files in the specified directory.
    Returns a dict mapping symbol to market cap.
    """
    market_caps = {}
    for json_file in Path(data_dir).glob("*.json"):
        try:
            with open(json_file, "r") as file:
                data = json.load(file)

            symbol = json_file.stem.upper()

            # Skip if it's a FUND type
            general_data = data.get("General", {})
            if general_data.get("Type") == "FUND":
                continue

            market_cap = data.get("Highlights", {}).get("MarketCapitalization")
            if isinstance(market_cap, str):
                market_cap = int(market_cap.replace(",", ""))
            if isinstance(market_cap, int):
                market_caps[symbol] = market_cap
        except Exception as e:
            logging.error(f"Error processing file {json_file}: {e}")
    return market_caps

def categorize_market_caps(market_caps: dict) -> dict:
    categories = {
        'nano': [],
        'micro': [],
        'small': [],
        'mid': [],
        'large': [],
        'mega': [],
        'unknown': []
    }

    for symbol, cap in market_caps.items():
        if cap < 50_000_000:
            categories['nano'].append(symbol)
        elif 50_000_000 <= cap < 300_000_000:
            categories['micro'].append(symbol)
        elif 300_000_000 <= cap < 2_000_000_000:
            categories['small'].append(symbol)
        elif 2_000_000_000 <= cap < 10_000_000_000:
            categories['mid'].append(symbol)
        elif 10_000_000_000 <= cap < 200_000_000_000:
            categories['large'].append(symbol)
        elif cap >= 200_000_000_000:
            categories['mega'].append(symbol)
        else:
            categories['unknown'].append(symbol)
    return categories

#########################################
# Main execution                        #
#########################################

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTML from JSON data.")
    parser.add_argument(
        "--symbol",
        type=str,
        required=False,
        help="Symbol to generate HTML for (e.g., 'aapl')"
    )
    parser.add_argument(
        "--market-cap",
        type=str,
        required=False,
        choices=['nano', 'micro', 'small', 'mid', 'large', 'mega', 'unknown'],
        help="Market cap category to generate HTML for all symbols in that category."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="../data/fundamental_data/",
        help="Directory where JSON files are located."
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="../html/",
        help="Directory to save generated HTML files."
    )

    args = parser.parse_args()

    # If market-cap is provided, ignore symbol and process all in that category
    if args.market_cap:
        market_caps = extract_market_caps(args.data_dir)
        categories = categorize_market_caps(market_caps)
        selected_symbols = categories.get(args.market_cap, [])
        if not selected_symbols:
            logging.info(f"No symbols found for category '{args.market_cap}'.")
        else:
            for sym in selected_symbols:
                symbol_file = os.path.join(args.data_dir, f"{sym.lower()}.json")
                if not os.path.exists(symbol_file):
                    logging.warning(f"No JSON data found for symbol: {sym}")
                    continue
                try:
                    with open(symbol_file, "r") as file:
                        data = json.load(file)
                    output_filepath = os.path.join(args.output_dir, f"{sym.lower()}.html")
                    generate_html_with_dropdown(data, output_filepath)
                except Exception as e:
                    logging.error(f"Error generating HTML for {sym}: {e}")
    else:
        # Process a single symbol
        if not args.symbol:
            logging.error("You must provide either --symbol or --market-cap.")
            exit(1)

        symbol = args.symbol.lower()
        json_file = os.path.join(args.data_dir, f"{symbol}.json")
        if not os.path.exists(json_file):
            logging.error(f"Error: File {json_file} not found.")
            exit(1)
        try:
            with open(json_file, "r") as file:
                data = json.load(file)
        except Exception as e:
            logging.error(f"Error reading JSON file: {e}")
            exit(1)

        output_filepath = os.path.join(args.output_dir, f"{symbol}.html")
        generate_html_with_dropdown(data, output_filepath)
