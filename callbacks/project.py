from dash.dependencies import Input, Output
import plotly.graph_objs as go
import pandas as pd
from data_management import DataManager
from project_analyser import ProjectAnalyser
from logging_config import setup_logging

logger = setup_logging()

def register_project_callback(app, data_manager: DataManager):
    project_analyser = ProjectAnalyser(data_manager)

    @app.callback(
        [Output('project-timeline-chart', 'figure'),
         Output('project-revenue-chart', 'figure'),
         Output('project-tasks-employees-chart', 'figure'),
         Output('project-total-revenue', 'children'),
         Output('project-period-revenue', 'children')],
        [Input('project-selector', 'value'),
         Input('date-range', 'start_date'),
         Input('date-range', 'end_date'),
         Input('employee-filter', 'value'),
         Input('man-hours-toggle', 'value')]
    )
    def update_project_charts(selected_project, start_date, end_date, selected_employees, use_man_hours):
        logger.info(f"Updating project charts for project: {selected_project}")
        if not selected_project:
            return go.Figure(), go.Figure(), go.Figure(), "", ""

        try:
            timeline_fig, revenue_fig, tasks_employees_fig, total_revenue_msg, period_revenue_msg = project_analyser.analyse_project(
                selected_project, start_date, end_date, selected_employees, use_man_hours
            )
            
            return timeline_fig, revenue_fig, tasks_employees_fig, total_revenue_msg, period_revenue_msg
        
        except Exception as e:
            logger.error(f"Error in update_project_charts: {str(e)}", exc_info=True)
            return go.Figure(), go.Figure(), go.Figure(), f"Error: {str(e)}", ""
