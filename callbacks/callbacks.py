from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
import dash
import pandas as pd
from data_management import DataManager
from logging_config import setup_logging

logger = setup_logging()

from callbacks.global_kpi import register_global_kpi_callbacks
from callbacks.financials import register_financials_callbacks
from callbacks.projects import register_portfolio_callbacks
from callbacks.employees import register_employees_callbacks
from callbacks.llm import register_llm_callback
from callbacks.project import register_project_callback
from callbacks.reporting import register_reporting_callback
from callbacks.settings import register_settings_callbacks
from callbacks.pivot_table import register_pivot_table_callbacks

def register_callbacks(app, data_manager: DataManager):
    logger.info("Registering callbacks")
    register_global_kpi_callbacks(app, data_manager)
    register_financials_callbacks(app, data_manager)
    register_portfolio_callbacks(app, data_manager)
    register_employees_callbacks(app, data_manager)
    register_llm_callback(app, data_manager)
    register_project_callback(app, data_manager)
    register_reporting_callback(app, data_manager)
    register_settings_callbacks(app, data_manager)
    register_pivot_table_callbacks(app, data_manager)
    logger.info("All callbacks registered")

    @app.callback(
        Output('last-update-time', 'children'),
        [Input('refresh-data', 'n_clicks')]
    )
    def refresh_dashboard_data(n_clicks):
        logger.info(f"refresh_dashboard_data called. n_clicks: {n_clicks}")
        ctx = dash.callback_context
        if not ctx.triggered:
            logger.info("Initial load")
            data_manager.load_all_data()
        else:
            logger.info("Force refresh")
            data_manager.load_all_data(force=True)
        
        if data_manager.data:
            logger.info("Data loaded successfully")
            
            last_update = f"Last updated: {data_manager.last_update.strftime('%Y-%m-%d %H:%M:%S')}"
            logger.info(f"Returning data and {last_update}")
            return last_update
        else:
            logger.warning("Data is empty")
            return "Failed to update data"

    @app.callback(
        [Output('project-filter', 'options'),
         Output('employee-filter', 'options')]
    )
    def update_filter_options():

        if data_manager.data is None:
            return [], []

        df_projects, df_employees = data_manager.data[:2]
        project_options = [{'label': i, 'value': i} for i in df_projects['name'].unique() if pd.notna(i)]
        employee_options = [{'label': i, 'value': i} for i in df_employees['name'].unique() if pd.notna(i)]
        return project_options, employee_options

    @app.callback(
        Output('project-filter', 'disabled'),
        [Input('tabs', 'value')]
    )
    def disable_project_filter(tab):
        return tab in ['project-tab', 'Settings']

    @app.callback(
        Output('sales-chart', 'figure'),
        [Input('date-range', 'start_date'),
         Input('date-range', 'end_date')],
        [State('sales-task-filter', 'value')]
    )
    def update_sales(start_date, end_date, task_filter):
        start_date = pd.to_datetime(start_date)
        end_date = pd.to_datetime(end_date)

        # Check if 'date_order' column exists, if not, try to find an alternative
        date_column = 'date_order'
        if date_column not in data_manager.df_sales.columns:
            date_columns = [col for col in data_manager.df_sales.columns if 'date' in col.lower()]
            if date_columns:
                date_column = date_columns[0]
            else:
                return go.Figure()  # Return empty figure if no suitable date column found
        
        filtered_sales = data_manager.df_sales[
            (data_manager.df_sales[date_column] >= start_date) &
            (data_manager.df_sales[date_column] <= end_date)
        ]
        
        filtered_tasks = data_manager.df_tasks[
            (data_manager.df_tasks['create_date'] >= start_date) &
            (data_manager.df_tasks['create_date'] <= end_date)
        ]
        
        if task_filter:
            keywords = [keyword.strip().lower() for keyword in task_filter.split(',')]
            filtered_tasks = filtered_tasks[filtered_tasks['name'].str.lower().str.contains('|'.join(keywords))]
        
        if filtered_sales.empty and filtered_tasks.empty:
            return go.Figure()
        
        daily_sales = filtered_sales.groupby(date_column)['amount_total'].sum().reset_index()
        daily_tasks = filtered_tasks.groupby('create_date').size().reset_index(name='task_count')
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily_sales[date_column], y=daily_sales['amount_total'], name='Sales', mode='lines'))
        fig.add_trace(go.Scatter(x=daily_tasks['create_date'], y=daily_tasks['task_count'], name='Tasks', mode='lines', yaxis='y2'))
        
        fig.update_layout(
            title='Sales and Tasks Over Time',
            xaxis_title='Date',
            yaxis_title='Sales Amount',
            yaxis2=dict(title='Number of Tasks', overlaying='y', side='right')
        )
        
        return fig
