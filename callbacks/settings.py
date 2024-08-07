import pandas as pd
import ast
from dash.dependencies import Input, Output, State
from dash import html
import dash
from data_management import DataManager
from logging_config import setup_logging

logger = setup_logging()

def transform_job_costs_for_datatable(job_costs):
    """
    Transform the job_costs dictionary into a list of dictionaries
    suitable for use in a DataTable.
    """
    transformed_data = []
    for job_title, costs in job_costs.items():
        transformed_data.append({
            'job_title': job_title,
            'cost': costs['cost'],
            'revenue': costs['revenue']
        })
    return transformed_data

def register_settings_callbacks(app, data_manager: DataManager):
    @app.callback(
        Output('job-costs-save-status', 'children'),
        [Input('save-cost-revenue', 'n_clicks')],
        State('job-costs-table', 'data')
    )
    def save_job_costs_callback(n_clicks, table_data):
        if n_clicks is None or n_clicks == 0:
            return ""

        try:
            job_costs = {item['job_title']: {'cost': item['cost'], 'revenue': item['revenue']} for item in table_data if item['job_title']}
            data_manager.save_job_costs(job_costs)
            return html.Div("Job costs saved successfully", style={'color': 'green'})
        except Exception as e:
            return html.Div(f"Error saving job costs: {str(e)}", style={'color': 'red'})

    @app.callback(
        Output('job-costs-table', 'data', allow_duplicate=True),
        [Input('add-job-title', 'n_clicks')],
        State('job-costs-table', 'data'),
        prevent_initial_call=True
    )
    def add_job_title(n_clicks, current_data):
        if n_clicks is None or n_clicks == 0:
            return dash.no_update
        
        new_row = {'job_title': '', 'cost': '', 'revenue': ''}
        return current_data + [new_row]

    @app.callback(
        Output('job-costs-table', 'data', allow_duplicate=True),
        [Input('tabs', 'value')],
        prevent_initial_call=True
    )
    def update_job_costs_table(current_tab):
        if current_tab != 'Settings':
            return dash.no_update

        # Get all job titles from current data
        
        all_job_titles = set(data_manager.job_costs.keys())

        # Get job titles from employees
        employee_job_titles = set()
        if 'job_title' in data_manager.df_employees.columns:
            employee_job_titles = set(data_manager.df_employees['job_title'].dropna().unique())
        elif 'job_id' in data_manager.df_employees.columns:
            employee_job_titles = set(data_manager.df_employees['job_id'].dropna().apply(lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else x).unique())

        # Combine all job titles
        unique_job_titles = all_job_titles.union(employee_job_titles)
        logger.debug(f"Combined unique job titles: {unique_job_titles}")

        # If there are no job titles, return the current data
        if not unique_job_titles:
            logger.warning("No job titles found. Returning current data.")
            return data_manager.job_costs

        # Filter the job costs
        filtered_job_costs = {title: cost for title, cost in data_manager.job_costs.items() if title in unique_job_titles}

        job_costs_data = transform_job_costs_for_datatable(filtered_job_costs)
        
        # Convert to DataFrame for easier manipulation if needed
        df = pd.DataFrame(job_costs_data)
        
        # You can perform additional operations on the DataFrame here if needed
        # For example, sorting:
        df = df.sort_values('job_title')
        
        # Convert back to list of dictionaries for the DataTable
        table_data = df.to_dict('records')
        
        return table_data

    @app.callback(
        Output('employees-job-titles-table', 'data'),
        [Input('tabs', 'value')]
    )
    def update_employees_job_titles_table(current_tab):
        if current_tab != 'Settings':
            return dash.no_update

        # Use safe_get_columns to process df_employees
        df_employees_processed = safe_get_columns(data_manager.df_employees, ['name', 'job_id', 'job_title'])

        if 'job_id' in df_employees_processed.columns:
            df_employees_processed['job_id_original'] = df_employees_processed['job_id']
            df_employees_processed['job_id'] = df_employees_processed['job_id_original'].apply(
                lambda x: x[0] if isinstance(x, (list, tuple)) and len(x) > 0 else x
            )
            df_employees_processed['job_title'] = df_employees_processed['job_id_original'].apply(
                lambda x: x[1] if isinstance(x, (list, tuple)) and len(x) > 1 else ''
            )
            df_employees_processed.drop('job_id_original', axis=1, inplace=True)
        
        # Select only the required columns
        df_employees_processed = df_employees_processed[['name', 'job_id', 'job_title']]
        
        # Convert to list of dictionaries for the DataTable
        table_data = df_employees_processed.to_dict('records')
        
        return table_data
    
    # Function to safely get DataFrame columns and process job_id
def safe_get_columns(df, columns):
    result = df[[col for col in columns if col in df.columns]].copy()
    if 'job_id' in result.columns:
        result['job_id_original'] = result['job_id']
        result['job_id'] = result['job_id_original'].apply(
            lambda x: ast.literal_eval(str(x))[0] if isinstance(x, (list, str)) and str(x).startswith('[') else x
        )
        result['job_title'] = result['job_id_original'].apply(
            lambda x: ast.literal_eval(str(x))[1] if isinstance(x, (list, str)) and str(x).startswith('[') else ''
        )
        result.drop('job_id_original', axis=1, inplace=True)
    return result
