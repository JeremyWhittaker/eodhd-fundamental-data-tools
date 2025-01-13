import os
import json
import argparse
import logging
import plotly.graph_objs as go
from datetime import datetime

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
        if k.lower() == 'seclink' and val != "None" and "http" in val:
            val = f'<a href="{v}" target="_blank">{v}</a>'
        html += f"<dt>{k}:</dt><dd>{val}</dd><br>"
    html += "</dl>"
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
    if not data:
        return "<p>No Outstanding Shares Data Available</p>"

    # Example plot: replace with actual plotting logic as needed
    trace = go.Scatter(
        x=list(range(len(data))),
        y=data,
        mode='lines+markers',
        name='Outstanding Shares'
    )
    layout = go.Layout(title=title, xaxis=dict(title='Period'), yaxis=dict(title='Shares'))
    fig = go.Figure(data=[trace], layout=layout)
    plot_html = fig.to_html(full_html=False, include_plotlyjs='cdn')
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
    """
    Formats a single financial section (e.g., Balance Sheet) with Quarterly and Yearly dropdowns.
    """
    logging.debug(f"Processing {title} - Quarterly Data Keys: {list(financial_data.get('quarterly', {}).keys())}")
    logging.debug(f"Processing {title} - Yearly Data Keys: {list(financial_data.get('yearly', {}).keys())}")

    quarterly_data = financial_data.get('quarterly', {})
    yearly_data = financial_data.get('yearly', {})

    # Generate nested tabs for Quarterly and Yearly
    nested_tabs_html = '''
    <div class="nested-tabs-second-level">
        <div class="nested-tab-second-level">Quarterly</div>
        <div class="nested-tab-second-level">Yearly</div>
    </div>
    '''

    # Generate dropdowns and content for Quarterly
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
            logging.debug(f"Created Quarterly dropdown-content for {date_key} with ID {content_id}.")
    else:
        quarterly_html = "<p>No Quarterly Data Available</p>"

    # Generate dropdowns and content for Yearly
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
            logging.debug(f"Created Yearly dropdown-content for {date_key} with ID {content_id}.")
    else:
        yearly_html = "<p>No Yearly Data Available</p>"

    # Combine all HTML
    html = f"<h4>{title}</h4>"
    html += nested_tabs_html
    html += "<div class='nested-content-second-level-container'>"  # Updated class name

    # Quarterly Content
    html += f"<div class='nested-content-second-level'>{quarterly_html}</div>"

    # Yearly Content
    html += f"<div class='nested-content-second-level'>{yearly_html}</div>"

    html += "</div>"

    return html


def format_financials(financials):
    """
    Formats the Financials section into tabs for Balance Sheet, Cash Flow, and Income Statement,
    each containing nested tabs for Quarterly and Yearly data with date dropdowns.
    """
    if not financials or not isinstance(financials, dict):
        logging.warning("No Financials data available.")
        return "<p>No Financial Data Available</p>"

    tabs_html = '<div class="nested-tabs">'
    contents_html = ''

    for section, section_data in financials.items():
        # Replace underscores with spaces and capitalize
        section_title = section.replace("_", " ").title()
        tabs_html += f'<div class="nested-tab">{section_title}</div>'
        section_html = format_financial_section(section_data, section_title)
        contents_html += f"<div class='nested-content'>{section_html}</div>"
        logging.debug(f"Added nested tab for {section_title}.")

    tabs_html += '</div>'
    return tabs_html + contents_html


def format_holders(holders):
    institutions = holders.get("Institutions", {})
    funds = holders.get("Funds", {})

    def render_holders(data, title):
        if not data:
            return f"<p>No {title} Data</p>"
        html = '<table border="1" style="width: 100%; text-align: left; border-collapse: collapse;">'
        html += '<thead><tr><th>Name</th><th>Date</th><th>Total Shares</th><th>Total Assets</th>'
        html += '<th>Current Shares</th><th>Change</th><th>Change (%)</th></tr></thead><tbody>'
        for _, item in data.items():
            html += (
                f"<tr><td>{format_value('name', item.get('name', ''))}</td>"
                f"<td>{format_value('date', item.get('date', ''))}</td>"
                f"<td>{format_value('totalShares', item.get('totalShares', ''))}</td>"
                f"<td>{format_value('totalAssets', item.get('totalAssets', ''))}</td>"
                f"<td>{format_value('currentShares', item.get('currentShares', ''))}</td>"
                f"<td>{format_value('change', item.get('change', ''))}</td>"
                f"<td>{format_value('change_p', item.get('change_p', ''))}%</td></tr>"
            )
        html += '</tbody></table>'
        return html

    institutions_html = render_holders(institutions, "Institutions")
    funds_html = render_holders(funds, "Funds")

    tabs_html = '<div class="nested-tabs">'
    tabs_html += '<div class="nested-tab">Institutions</div>'
    tabs_html += '<div class="nested-tab">Funds</div>'
    tabs_html += '</div>'

    contents_html = f"<div class='nested-content'>{institutions_html}</div>"
    contents_html += f"<div class='nested-content'>{funds_html}</div>"

    return tabs_html + contents_html


def format_outstandingshares(value):
    annual = value.get("annual", {})
    quarterly = value.get("quarterly", {})

    annual_list = list(annual.values())
    quarterly_list = list(quarterly.values())

    annual_plot = create_outstandingshares_plot(annual_list, "Annual Outstanding Shares")
    quarterly_plot = create_outstandingshares_plot(quarterly_list, "Quarterly Outstanding Shares")

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
            logging.debug(f"Created Earnings dropdown-content for {date} with ID {content_id}.")
    else:
        content_html += "<p>No Earnings Data Available</p>"

    # Combine dropdown and content
    earnings_html = dropdown_html + content_html
    return earnings_html


def format_tab_content(key, value):
    kl = key.lower()
    if kl == "esgscores":
        return ""
    elif kl == "general":
        return dict_to_dl(value)
    elif kl == "highlights":
        return dict_to_dl(value)
    elif kl == "valuation":
        return dict_to_dl(value)
    elif kl == "sharesstats":
        return dict_to_dl(value)
    elif kl == "technicals":
        return dict_to_dl(value)
    elif kl == "splitsdividends":
        # Enhanced Debugging for SplitsDividends
        logging.debug("Processing SplitsDividends tab.")
        try:
            if not isinstance(value, dict):
                logging.error(f"SplitsDividends data is not a dictionary. Type found: {type(value)}")
                return "<p>Invalid SplitsDividends Data Format</p>"

            logging.debug(f"SplitsDividends Data Keys: {list(value.keys())}")

            # Assuming SplitsDividends has 'splits' and 'dividends' keys
            splits = value.get("splits", [])
            dividends = value.get("dividends", [])

            logging.debug(f"Number of Splits: {len(splits)}")
            logging.debug(f"Number of Dividends: {len(dividends)}")

            splits_html = "<h4>Splits</h4>"
            if splits:
                splits_html += list_of_dicts_to_table(splits, use_name_as_heading=True)
            else:
                splits_html += "<p>No Splits Data Available</p>"

            dividends_html = "<h4>Dividends</h4>"
            if dividends:
                dividends_html += list_of_dicts_to_table(dividends, use_name_as_heading=True)
            else:
                dividends_html += "<p>No Dividends Data Available</p>"

            combined_html = splits_html + dividends_html
            logging.debug("Successfully formatted SplitsDividends content.")
            return combined_html
        except Exception as e:
            logging.exception(f"Exception occurred while processing SplitsDividends: {e}")
            return f"<p>Error processing SplitsDividends data: {e}</p>"
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
        logging.debug(f"Added main tab for {key}.")
    tabs_html += '</div>'
    return tabs_html + contents_html


def generate_html_with_dropdown(data, output_filepath):
    logging.debug("Starting generate_html_with_dropdown")

    if not data or not isinstance(data, dict):
        logging.error("Data is empty or not a dict.")
        return

    # Ensure output directory exists
    output_dir = os.path.dirname(output_filepath)
    if not os.path.exists(output_dir):
        logging.debug(f"Output directory {output_dir} does not exist. Creating it.")
        try:
            os.makedirs(output_dir, exist_ok=True)
            logging.debug(f"Created directory {output_dir}.")
        except Exception as e:
            logging.error(f"Failed to create directory {output_dir}: {e}")
            return
    else:
        logging.debug(f"Output directory {output_dir} exists.")

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

        /* Nested Tabs (Financials) */
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
            // Function to handle main and first-level nested tab clicks
            function setupTabs(tabSelector, contentSelector) {
                const tabs = document.querySelectorAll(tabSelector);
                const contents = document.querySelectorAll(contentSelector);

                tabs.forEach((tab, index) => {
                    tab.addEventListener('click', () => {
                        tabs.forEach(t => t.classList.remove('active'));
                        contents.forEach(c => c.classList.remove('active'));

                        tab.classList.add('active');
                        contents[index].classList.add('active');

                        // Debugging: Log which tab was clicked
                        console.log('Tab clicked:', tab.textContent);
                    });
                });

                // Activate the first tab by default
                if (tabs.length > 0) {
                    tabs[0].classList.add('active');
                    contents[0].classList.add('active');
                }
            }

            // Function to handle second-level nested tab clicks (Quarterly and Yearly)
            function setupNestedTabs(tabSelector, contentSelector) {
                const tabs = document.querySelectorAll(tabSelector);
                const contents = document.querySelectorAll(contentSelector);

                tabs.forEach((tab, index) => {
                    tab.addEventListener('click', () => {
                        tabs.forEach(t => t.classList.remove('active'));
                        contents.forEach(c => c.classList.remove('active'));

                        tab.classList.add('active');
                        contents[index].classList.add('active');

                        // Debugging: Log which nested tab was clicked
                        console.log('Nested Tab clicked:', tab.textContent);
                    });
                });

                // Activate the first nested tab by default
                if (tabs.length > 0) {
                    tabs[0].classList.add('active');
                    contents[0].classList.add('active');
                }
            }

            // Function to handle dropdown changes
            function setupDropdown(dropdownId, contentPrefix) {
                const dropdown = document.getElementById(dropdownId);
                if (!dropdown) {
                    console.warn(`Dropdown with ID ${dropdownId} not found.`);
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

                    // Debugging: Log the selected value
                    console.log(`Dropdown ${dropdownId} changed to: ${selectedValue}`);
                });

                // Optionally, you can activate the first available option
                // Uncomment the following lines if you want to show the first option by default
                /*
                if (dropdown.options.length > 1) { // Exclude the default "Select a date" option
                    dropdown.selectedIndex = 1;
                    const firstValue = dropdown.options[1].value;
                    const firstContent = document.getElementById(`${contentPrefix}_${firstValue}`);
                    if (firstContent) {
                        firstContent.classList.add('active');
                        console.log(`Dropdown ${dropdownId} set to first value: ${firstValue}`);
                    }
                }
                */
            }

            // Setup main tabs
            setupTabs('.tab', '.content');

            // Setup first level nested tabs within Financials
            setupTabs('.nested-tab', '.nested-content');

            // Setup second level nested tabs within Financials > [Balance Sheet / Cash Flow / Income Statement]
            setupNestedTabs('.nested-tab-second-level', '.nested-content-second-level');

            // Setup dropdowns for Financials > Balance Sheet, Cash Flow, and Income Statement
            const financialSections = ['balance_sheet', 'cash_flow', 'income_statement'];
            financialSections.forEach(section => {
                const quarterlyDropdownId = `${section}_quarterly_dropdown`;
                const yearlyDropdownId = `${section}_yearly_dropdown`;
                setupDropdown(quarterlyDropdownId, `${section}_quarterly`);
                setupDropdown(yearlyDropdownId, `${section}_yearly`);
            });

            // Setup Earnings dropdown
            setupDropdown('earnings-dropdown', 'earnings');

            // Debugging: Check if all expected tabs are present
            console.log('Main tabs initialized:', document.querySelectorAll('.tab').length);
            console.log('First-level nested tabs initialized:', document.querySelectorAll('.nested-tab').length);
            console.log('Second-level nested tabs initialized:', document.querySelectorAll('.nested-tab-second-level').length);
            console.log('Financial dropdowns initialized:', document.querySelectorAll('.financial-dropdown select').length);
            console.log('Earnings dropdown initialized with options:', document.querySelectorAll('#earnings-dropdown option').length);
        });
    </script>
    """

    try:
        logging.debug(f"Opening file {output_filepath} for writing.")
        with open(output_filepath, "w") as file:
            file.write("<html><head>")
            file.write(styles)
            file.write(script)
            file.write("</head><body>")
            # Assuming format_tabs is defined elsewhere in your script
            tabs_content = format_tabs(data)
            file.write(tabs_content)
            file.write("</body></html>")
        logging.info(f"Saved HTML to {output_filepath}")
    except Exception as e:
        logging.error(f"Exception occurred while writing HTML: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate HTML from JSON data.")
    parser.add_argument(
        "--rss",
        type=str,
        required=True,
        help="Path to the RSS (JSON) file containing data (e.g., './data/fundamental_data/aapl.us.json')."
    )
    args = parser.parse_args()

    # Ensure the RSS file exists
    if not os.path.exists(args.rss):
        logging.error(f"Error: File {args.rss} not found.")
        exit(1)

    # Derive the symbol from the RSS filename
    rss_filename = os.path.basename(args.rss)
    symbol = rss_filename.split(".")[0]  # Extract the symbol (e.g., 'aapl')
    output_filepath = f"./html/{symbol}.html"  # Save as 'aapl.html' in './html/'

    try:
        with open(args.rss, "r") as file:
            data = json.load(file)
    except Exception as e:
        logging.error(f"Error reading JSON file: {e}")
        exit(1)

    # Log top-level keys
    logging.debug("Top-level keys in data: %s", list(data.keys()))

    # Generate the HTML
    generate_html_with_dropdown(data, output_filepath)